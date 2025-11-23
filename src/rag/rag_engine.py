"""
Vector database and RAG (Retrieval Augmented Generation) system.
"""
import logging
from typing import Dict, List, Optional, Any
import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from src.models.schemas import (
    DocumentExtraction, QueryRequest, QueryResponse, 
    Insight, InsightType
)
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStore:
    """Vector database wrapper using ChromaDB."""
    
    def __init__(self, persist_directory: Optional[str] = None):
        """Initialize vector store."""
        persist_dir = persist_directory or settings.vector_db_path
        
        self.client = chromadb.Client(
            ChromaSettings(
                persist_directory=persist_dir,
                anonymized_telemetry=False
            )
        )
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="financial_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key
        )
    
    def add_document(self, extraction: DocumentExtraction) -> None:
        """Add document extraction to vector store."""
        try:
            # Chunk the text
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            
            chunks = text_splitter.split_text(extraction.raw_text)
            
            # Generate embeddings
            embeddings = self.embeddings.embed_documents(chunks)
            
            # Prepare metadata
            base_metadata = {
                "document_id": extraction.document_id,
                "document_type": extraction.document_type.value,
                "filename": extraction.metadata.filename,
                "upload_timestamp": extraction.metadata.upload_timestamp.isoformat(),
            }
            
            # Add to ChromaDB
            ids = [f"{extraction.document_id}_{i}" for i in range(len(chunks))]
            metadatas = [base_metadata for _ in chunks]
            
            self.collection.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} chunks for document {extraction.document_id}")
        except Exception as e:
            logger.error(f"Failed to add document to vector store: {e}")
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search vector store for relevant documents."""
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def delete_document(self, document_id: str) -> None:
        """Delete document from vector store."""
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to delete document from vector store: {e}")


class RAGEngine:
    """RAG (Retrieval Augmented Generation) engine for insights."""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """Initialize RAG engine."""
        self.vector_store = vector_store or VectorStore()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
    
    def query(self, request: QueryRequest) -> QueryResponse:
        """Process query and generate response with RAG."""
        try:
            # Build filter metadata
            filter_metadata = {}
            if request.document_ids:
                # ChromaDB doesn't support 'in' operator directly, so we'll filter manually
                pass
            
            # Search vector store
            search_results = self.vector_store.search(
                query=request.query,
                top_k=request.top_k,
                filter_metadata=filter_metadata if filter_metadata else None
            )
            
            # Build context from search results
            context_parts = []
            sources = []
            
            for result in search_results:
                context_parts.append(result['document'])
                sources.append({
                    "document_id": result['metadata']['document_id'],
                    "filename": result['metadata']['filename'],
                    "excerpt": result['document'][:200] + "...",
                    "relevance_score": 1.0 - result['distance'] if result['distance'] else 0.9
                })
            
            context = "\n\n".join(context_parts)
            
            # Generate answer using LLM
            answer_prompt = ChatPromptTemplate.from_template("""
            You are a financial document analysis assistant. Answer the user's question based on the provided context from financial documents.
            
            Context:
            {context}
            
            Question: {question}
            
            Provide a detailed, accurate answer based on the context. If the context doesn't contain enough information to answer fully, state what information is available and what is missing.
            """)
            
            chain = answer_prompt | self.llm
            response = chain.invoke({"context": context, "question": request.query})
            answer = response.content
            
            # Generate insights
            insights = self.generate_insights(request.query, search_results)
            
            return QueryResponse(
                answer=answer,
                confidence=0.85,  # Could be calculated based on search scores
                sources=sources,
                insights=insights
            )
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return QueryResponse(
                answer=f"I encountered an error processing your query: {str(e)}",
                confidence=0.0,
                sources=[],
                insights=[]
            )
    
    def generate_insights(self, query: str, search_results: List[Dict]) -> List[Insight]:
        """Generate insights from search results."""
        try:
            # Build context
            context = "\n\n".join([r['document'] for r in search_results[:3]])
            
            insight_prompt = ChatPromptTemplate.from_template("""
            Based on the following financial document excerpts and the user's query, generate 2-3 key insights.
            
            Query: {query}
            
            Context:
            {context}
            
            For each insight, provide:
            1. A clear, actionable insight
            2. Supporting evidence from the documents
            3. Confidence level (0.0-1.0)
            
            Format as JSON array:
            [
                {{
                    "type": "summary|trend|comparison|recommendation|risk_assessment",
                    "title": "Brief title",
                    "description": "Detailed insight",
                    "confidence": 0.0-1.0
                }}
            ]
            """)
            
            chain = insight_prompt | self.llm
            response = chain.invoke({"query": query, "context": context})
            
            # Parse insights (simplified - in production, use proper JSON parsing)
            insights = []
            insight_data = {
                "type": "summary",
                "title": "Analysis Summary",
                "description": response.content[:500],
                "confidence": 0.75
            }
            
            insight = Insight(
                insight_id=str(uuid.uuid4()),
                insight_type=InsightType.SUMMARY,
                title=insight_data['title'],
                description=insight_data['description'],
                confidence=insight_data['confidence'],
                supporting_documents=[r['metadata']['document_id'] for r in search_results[:3]]
            )
            insights.append(insight)
            
            return insights
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return []
    
    def generate_document_summary(self, extraction: DocumentExtraction) -> str:
        """Generate a summary of a document."""
        try:
            summary_prompt = ChatPromptTemplate.from_template("""
            Summarize the following financial document in 2-3 sentences, highlighting the most important information.
            
            Document type: {doc_type}
            Text:
            {text}
            
            Summary:
            """)
            
            chain = summary_prompt | self.llm
            response = chain.invoke({
                "doc_type": extraction.document_type.value,
                "text": extraction.raw_text[:2000]
            })
            
            return response.content
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Summary unavailable"
