"""
End-to-end document processing pipeline.

This orchestrates: ingestion → OCR → LLM extraction → vectorization → anomaly detection
"""
import logging
import time
import uuid
from pathlib import Path
from typing import List, Optional

from src.models.schemas import (
    DocumentExtraction, DocumentMetadata, DocumentType, 
    ProcessingStatus, Anomaly
)
from src.ocr.preprocessor import DocumentPreprocessor
from src.extraction.llm_extractor import LLMExtractor
from src.rag.rag_engine import VectorStore, RAGEngine
from src.anomaly.detector import AnomalyDetector, TrendAnalyzer, ValidationEngine
from src.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentPipeline:
    """Main document processing pipeline."""
    
    def __init__(self):
        """Initialize pipeline components."""
        logger.info("Initializing document processing pipeline...")
        
        self.preprocessor = DocumentPreprocessor()
        self.llm_extractor = LLMExtractor()
        self.vector_store = VectorStore()
        self.rag_engine = RAGEngine(self.vector_store)
        self.anomaly_detector = AnomalyDetector()
        self.trend_analyzer = TrendAnalyzer()
        self.validator = ValidationEngine()
        
        logger.info("Pipeline initialized successfully")
    
    def process_document(
        self, 
        file_path: str,
        uploader: str = "system",
        source_type: str = "upload"
    ) -> DocumentExtraction:
        """
        Process a single document through the complete pipeline.
        
        Args:
            file_path: Path to the document file
            uploader: User/system that uploaded the document
            source_type: Source of the document (upload, email, sftp, etc.)
        
        Returns:
            DocumentExtraction with all extracted data
        """
        start_time = time.time()
        
        try:
            # Generate document ID
            document_id = str(uuid.uuid4())
            logger.info(f"Processing document {document_id}: {file_path}")
            
            # Create metadata
            path = Path(file_path)
            metadata = DocumentMetadata(
                document_id=document_id,
                filename=path.name,
                file_size=path.stat().st_size,
                mime_type=self._get_mime_type(path),
                upload_timestamp=time.time(),
                uploader=uploader,
                source_type=source_type
            )
            
            # Step 1: OCR & Preprocessing
            logger.info(f"[{document_id}] Step 1: OCR & Preprocessing")
            ocr_results, tables, full_text = self.preprocessor.process_document(file_path)
            
            # Step 2: Document Classification
            logger.info(f"[{document_id}] Step 2: Document Classification")
            doc_type = self.llm_extractor.classify_document(full_text)
            logger.info(f"[{document_id}] Classified as: {doc_type.value}")
            
            # Step 3: Structured Data Extraction
            logger.info(f"[{document_id}] Step 3: Structured Data Extraction")
            tables_dict = [{"headers": t.headers, "rows": t.rows} for t in tables]
            structured_data = self.llm_extractor.extract_structured_data(
                full_text, doc_type, tables_dict
            )
            
            # Step 4: Entity Extraction
            logger.info(f"[{document_id}] Step 4: Entity Extraction")
            entities = self.llm_extractor.extract_generic_entities(full_text, doc_type)
            
            # Create extraction result
            processing_time = time.time() - start_time
            extraction = DocumentExtraction(
                document_id=document_id,
                document_type=doc_type,
                metadata=metadata,
                ocr_results=ocr_results,
                tables=tables,
                structured_data=structured_data,
                extracted_entities=entities,
                raw_text=full_text,
                processing_time_seconds=processing_time
            )
            
            # Step 5: Vectorization & Storage
            logger.info(f"[{document_id}] Step 5: Vectorization")
            self.vector_store.add_document(extraction)
            
            # Step 6: Validation
            logger.info(f"[{document_id}] Step 6: Validation")
            validation_anomalies = self.validator.validate_extraction(extraction)
            
            logger.info(
                f"[{document_id}] Processing complete in {processing_time:.2f}s. "
                f"Extracted {len(entities)} entities, {len(tables)} tables. "
                f"Found {len(validation_anomalies)} validation issues."
            )
            
            return extraction
        
        except Exception as e:
            logger.error(f"Pipeline processing failed for {file_path}: {e}", exc_info=True)
            raise
    
    def process_batch(self, file_paths: List[str]) -> List[DocumentExtraction]:
        """Process multiple documents."""
        extractions = []
        
        for file_path in file_paths:
            try:
                extraction = self.process_document(file_path)
                extractions.append(extraction)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
        
        return extractions
    
    def detect_anomalies(self, extractions: List[DocumentExtraction]) -> List[Anomaly]:
        """Run anomaly detection on processed documents."""
        logger.info(f"Running anomaly detection on {len(extractions)} documents")
        
        all_anomalies = []
        
        # Train anomaly detector if not already fitted
        if not self.anomaly_detector.fitted:
            self.anomaly_detector.fit(extractions)
        
        # Detect outliers
        outlier_anomalies = self.anomaly_detector.detect_outliers(extractions)
        all_anomalies.extend(outlier_anomalies)
        
        # Detect amount anomalies
        amount_anomalies = self.anomaly_detector.detect_amount_anomalies(extractions)
        all_anomalies.extend(amount_anomalies)
        
        logger.info(f"Detected {len(all_anomalies)} total anomalies")
        return all_anomalies
    
    def analyze_trends(self, extractions: List[DocumentExtraction]) -> dict:
        """Analyze trends in document data."""
        logger.info(f"Analyzing trends across {len(extractions)} documents")
        return self.trend_analyzer.analyze_trends(extractions)
    
    def _get_mime_type(self, path: Path) -> str:
        """Determine MIME type from file extension."""
        suffix = path.suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.tiff': 'image/tiff',
        }
        return mime_types.get(suffix, 'application/octet-stream')


def main():
    """Example usage of the pipeline."""
    logger.info("=== Financial Document Extraction PoC ===")
    
    # Initialize pipeline
    pipeline = DocumentPipeline()
    
    # Example: Process a document
    # Uncomment and update path when you have test documents
    # extraction = pipeline.process_document("path/to/test/invoice.pdf")
    # print(f"Processed document: {extraction.document_id}")
    # print(f"Document type: {extraction.document_type}")
    # print(f"Extracted {len(extraction.extracted_entities)} entities")
    
    logger.info("Pipeline ready for processing")


if __name__ == "__main__":
    main()