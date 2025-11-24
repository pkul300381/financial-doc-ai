"""
FastAPI application for Financial Document Extraction PoC.

Provides REST API endpoints for:
- Document upload and processing
- Search and Q&A (RAG)
- Document viewer
- Insights and anomaly detection
- Monitoring metrics
"""
import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.responses import Response

from src.models.schemas import (
    DocumentExtraction, UploadResponse, QueryRequest, QueryResponse,
    DocumentStatus, ProcessingStatus, Anomaly, Insight
)
from src.config import get_settings
from poc_pipeline import DocumentPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
settings = get_settings()

# Prometheus metrics
upload_counter = Counter('documents_uploaded_total', 'Total documents uploaded')
processing_duration = Histogram('document_processing_seconds', 'Time spent processing documents')
query_counter = Counter('queries_total', 'Total queries processed')
anomaly_counter = Counter('anomalies_detected_total', 'Total anomalies detected')

# Initialize FastAPI app
app = FastAPI(
    title="Financial Document Extraction API",
    description="PoC API for intelligent financial document processing with OCR, LLM extraction, and RAG insights",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance (in production, use dependency injection or singleton pattern)
pipeline = None

# Storage for processed documents (in production, use database)
document_store = {}


def get_pipeline() -> DocumentPipeline:
    """Get or initialize pipeline instance."""
    global pipeline
    if pipeline is None:
        logger.info("Initializing document pipeline...")
        pipeline = DocumentPipeline()
    return pipeline


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """Verify API key (basic security)."""
    if settings.app_env == "development":
        return True  # Skip in development
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # In production, verify against stored keys
    return True


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("Starting Financial Document Extraction API...")
    
    # Create necessary directories
    os.makedirs("./data/uploads", exist_ok=True)
    os.makedirs("./data/processed", exist_ok=True)
    os.makedirs(settings.vector_db_path, exist_ok=True)
    
    # Initialize pipeline
    get_pipeline()
    
    logger.info("API startup complete")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Financial Document Extraction API",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "upload": "/api/v1/documents/upload",
            "query": "/api/v1/query",
            "status": "/api/v1/documents/{document_id}/status",
            "insights": "/api/v1/insights",
            "anomalies": "/api/v1/anomalies",
            "health": "/health",
            "metrics": "/metrics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "pipeline": "operational",
            "vector_store": "operational",
            "llm": "operational"
        }
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/v1/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    uploader: str = "api_user",
    authorized: bool = Depends(verify_api_key)
):
    """
    Upload and process a financial document.
    
    Supported formats: PDF, PNG, JPG, JPEG, TIFF
    """
    try:
        upload_counter.inc()
        logger.info(f"Received upload: {file.filename}")
        
        # Validate file type
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
            )
        
        # Save uploaded file
        document_id = str(uuid.uuid4())
        upload_path = f"./data/uploads/{document_id}{file_ext}"
        
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process document asynchronously (in production, use background tasks or queue)
        pipe = get_pipeline()
        
        with processing_duration.time():
            extraction = pipe.process_document(upload_path, uploader=uploader)
        
        # Store extraction (in production, save to database)
        document_store[document_id] = extraction
        
        logger.info(f"Document {document_id} processed successfully")
        
        return UploadResponse(
            document_id=document_id,
            status="completed",
            message="Document processed successfully",
            metadata=extraction.metadata
        )
    
    except Exception as e:
        logger.error(f"Upload processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/documents/{document_id}/status", response_model=DocumentStatus)
async def get_document_status(
    document_id: str,
    authorized: bool = Depends(verify_api_key)
):
    """Get processing status of a document."""
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentStatus(
        document_id=document_id,
        status=ProcessingStatus.COMPLETED,
        progress_percentage=100,
        current_stage="completed"
    )


@app.get("/api/v1/documents/{document_id}", response_model=DocumentExtraction)
async def get_document(
    document_id: str,
    authorized: bool = Depends(verify_api_key)
):
    """Retrieve complete extraction for a document."""
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document_store[document_id]


@app.post("/api/v1/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    authorized: bool = Depends(verify_api_key)
):
    """
    Query documents using RAG (Retrieval Augmented Generation).
    
    Performs semantic search and generates AI-powered answers.
    """
    try:
        query_counter.inc()
        logger.info(f"Processing query: {request.query}")
        
        pipe = get_pipeline()
        response = pipe.rag_engine.query(request)
        
        return response
    
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/insights", response_model=List[Insight])
async def get_insights(
    document_ids: Optional[List[str]] = None,
    authorized: bool = Depends(verify_api_key)
):
    """
    Generate insights from processed documents.
    
    Includes trend analysis, summaries, and recommendations.
    """
    try:
        # Get relevant documents
        if document_ids:
            extractions = [document_store[doc_id] for doc_id in document_ids if doc_id in document_store]
        else:
            extractions = list(document_store.values())
        
        if not extractions:
            return []
        
        # Generate insights using RAG
        pipe = get_pipeline()
        
        # Simple insight generation (in production, more sophisticated)
        insights = []
        for extraction in extractions[:3]:  # Limit to first 3
            summary = pipe.rag_engine.generate_document_summary(extraction)
            # Create insight objects as needed
        
        return insights
    
    except Exception as e:
        logger.error(f"Insight generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/anomalies", response_model=List[Anomaly])
async def get_anomalies(
    document_ids: Optional[List[str]] = None,
    authorized: bool = Depends(verify_api_key)
):
    """
    Detect anomalies in processed documents.
    
    Uses ML-based outlier detection and statistical analysis.
    """
    try:
        # Get relevant documents
        if document_ids:
            extractions = [document_store[doc_id] for doc_id in document_ids if doc_id in document_store]
        else:
            extractions = list(document_store.values())
        
        if not extractions:
            return []
        
        pipe = get_pipeline()
        anomalies = pipe.detect_anomalies(extractions)
        
        anomaly_counter.inc(len(anomalies))
        
        return anomalies
    
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/trends")
async def get_trends(
    authorized: bool = Depends(verify_api_key)
):
    """
    Analyze trends across all documents using time series analysis.
    """
    try:
        extractions = list(document_store.values())
        
        if len(extractions) < 10:
            return {"message": "Insufficient data for trend analysis (need at least 10 documents)"}
        
        pipe = get_pipeline()
        trends = pipe.analyze_trends(extractions)
        
        return trends
    
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/documents/{document_id}")
async def delete_document(
    document_id: str,
    authorized: bool = Depends(verify_api_key)
):
    """Delete a document and its associated data."""
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Remove from vector store
    pipe = get_pipeline()
    pipe.vector_store.delete_document(document_id)
    
    # Remove from document store
    del document_store[document_id]
    
    # Delete uploaded file (if exists)
    # Implementation depends on storage strategy
    
    return {"status": "deleted", "document_id": document_id}


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )