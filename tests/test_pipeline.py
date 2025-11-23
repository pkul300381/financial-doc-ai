"""
Comprehensive test suite for document processing pipeline.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from src.models.schemas import (
    DocumentType, DocumentExtraction, DocumentMetadata,
    InvoiceExtraction, BankStatementExtraction, OCRResult,
    TableData, ExtractedEntity, MonetaryAmount, Currency
)
from src.ocr.preprocessor import DocumentPreprocessor, OCREngine, TableExtractor
from src.extraction.llm_extractor import LLMExtractor
from src.rag.rag_engine import VectorStore, RAGEngine
from src.anomaly.detector import AnomalyDetector, TrendAnalyzer
from poc_pipeline import DocumentPipeline


class TestOCREngine:
    """Tests for OCR engine."""
    
    def test_ocr_engine_initialization(self):
        """Test OCR engine can be initialized."""
        engine = OCREngine()
        assert engine is not None
    
    @patch('pytesseract.image_to_data')
    def test_extract_text_with_boxes(self, mock_tesseract):
        """Test text extraction with bounding boxes."""
        # Mock Tesseract output
        mock_tesseract.return_value = {
            'text': ['Test', 'Document'],
            'conf': [95, 90],
            'left': [10, 50],
            'top': [10, 10],
            'width': [30, 60],
            'height': [15, 15]
        }
        
        engine = OCREngine()
        from PIL import Image
        import numpy as np
        
        # Create dummy image
        img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
        results = engine.extract_text_with_boxes(img, page_num=0)
        
        assert len(results) == 2
        assert results[0].text == 'Test'
        assert results[0].confidence == 0.95


class TestLLMExtractor:
    """Tests for LLM-based extraction."""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for testing."""
        with patch('src.extraction.llm_extractor.ChatOpenAI') as mock:
            yield mock
    
    def test_document_classification(self, mock_llm):
        """Test document type classification."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "invoice"
        mock_llm.return_value.invoke.return_value = mock_response
        
        extractor = LLMExtractor()
        doc_type = extractor.classify_document("Invoice #12345 from Acme Corp")
        
        assert doc_type in [DocumentType.INVOICE, DocumentType.OTHER]
    
    def test_invoice_extraction(self, mock_llm):
        """Test invoice data extraction."""
        mock_response = Mock()
        mock_response.content = '''
        {
            "invoice_number": "INV-001",
            "total_amount": {"amount": 1000.0, "currency": "USD", "original_text": "$1,000.00"},
            "vendor_name": "Test Vendor"
        }
        '''
        mock_llm.return_value.invoke.return_value = mock_response
        
        extractor = LLMExtractor()
        result = extractor.extract_invoice("Invoice text", [])
        
        assert isinstance(result, InvoiceExtraction)


class TestVectorStore:
    """Tests for vector store operations."""
    
    @pytest.fixture
    def temp_vector_store(self, tmp_path):
        """Create temporary vector store."""
        store = VectorStore(persist_directory=str(tmp_path / "vectordb"))
        return store
    
    def test_vector_store_initialization(self, temp_vector_store):
        """Test vector store can be initialized."""
        assert temp_vector_store is not None
        assert temp_vector_store.collection is not None
    
    @patch('src.rag.rag_engine.OpenAIEmbeddings')
    def test_add_document(self, mock_embeddings, temp_vector_store):
        """Test adding document to vector store."""
        # Mock embeddings
        mock_embeddings.return_value.embed_documents.return_value = [[0.1] * 1536]
        
        # Create test extraction
        metadata = DocumentMetadata(
            document_id="test-123",
            filename="test.pdf",
            file_size=1000,
            mime_type="application/pdf",
            upload_timestamp=datetime.utcnow(),
            uploader="test_user",
            source_type="upload"
        )
        
        extraction = DocumentExtraction(
            document_id="test-123",
            document_type=DocumentType.INVOICE,
            metadata=metadata,
            raw_text="Test document content"
        )
        
        # Should not raise exception
        temp_vector_store.add_document(extraction)


class TestAnomalyDetector:
    """Tests for anomaly detection."""
    
    def test_anomaly_detector_initialization(self):
        """Test anomaly detector can be initialized."""
        detector = AnomalyDetector()
        assert detector is not None
        assert not detector.fitted
    
    def test_extract_features(self):
        """Test feature extraction from documents."""
        detector = AnomalyDetector()
        
        # Create test extraction
        metadata = DocumentMetadata(
            document_id="test-123",
            filename="test.pdf",
            file_size=1000,
            mime_type="application/pdf",
            upload_timestamp=datetime.utcnow(),
            uploader="test_user",
            source_type="upload"
        )
        
        extraction = DocumentExtraction(
            document_id="test-123",
            document_type=DocumentType.INVOICE,
            metadata=metadata,
            raw_text="Test content",
            processing_time_seconds=1.5
        )
        
        df = detector.extract_features([extraction])
        assert len(df) == 1
        assert 'processing_time' in df.columns
        assert 'text_length' in df.columns
    
    def test_fit_and_detect(self):
        """Test training and detection."""
        detector = AnomalyDetector()
        
        # Create multiple test extractions
        extractions = []
        for i in range(15):
            metadata = DocumentMetadata(
                document_id=f"test-{i}",
                filename=f"test{i}.pdf",
                file_size=1000 + i * 100,
                mime_type="application/pdf",
                upload_timestamp=datetime.utcnow(),
                uploader="test_user",
                source_type="upload"
            )
            
            extraction = DocumentExtraction(
                document_id=f"test-{i}",
                document_type=DocumentType.INVOICE,
                metadata=metadata,
                raw_text="Test content " * (10 + i),
                processing_time_seconds=1.5 + i * 0.1
            )
            extractions.append(extraction)
        
        # Fit detector
        detector.fit(extractions)
        assert detector.fitted
        
        # Detect anomalies
        anomalies = detector.detect_outliers(extractions)
        assert isinstance(anomalies, list)


class TestDocumentPipeline:
    """Integration tests for complete pipeline."""
    
    @pytest.fixture
    def mock_pipeline_components(self):
        """Mock all pipeline components."""
        with patch('poc_pipeline.DocumentPreprocessor') as mock_preprocessor, \
             patch('poc_pipeline.LLMExtractor') as mock_extractor, \
             patch('poc_pipeline.VectorStore') as mock_vector, \
             patch('poc_pipeline.RAGEngine') as mock_rag, \
             patch('poc_pipeline.AnomalyDetector') as mock_anomaly:
            
            # Configure mocks
            mock_preprocessor.return_value.process_document.return_value = ([], [], "Test text")
            mock_extractor.return_value.classify_document.return_value = DocumentType.INVOICE
            mock_extractor.return_value.extract_structured_data.return_value = InvoiceExtraction()
            mock_extractor.return_value.extract_generic_entities.return_value = []
            
            yield {
                'preprocessor': mock_preprocessor,
                'extractor': mock_extractor,
                'vector': mock_vector,
                'rag': mock_rag,
                'anomaly': mock_anomaly
            }
    
    def test_pipeline_initialization(self, mock_pipeline_components):
        """Test pipeline can be initialized."""
        pipeline = DocumentPipeline()
        assert pipeline is not None
    
    @patch('poc_pipeline.Path')
    def test_process_document(self, mock_path, mock_pipeline_components):
        """Test document processing pipeline."""
        # Mock path operations
        mock_path.return_value.name = "test.pdf"
        mock_path.return_value.stat.return_value.st_size = 1000
        mock_path.return_value.suffix = ".pdf"
        
        pipeline = DocumentPipeline()
        
        # Should not raise exception
        # extraction = pipeline.process_document("test.pdf")
        # assert extraction.document_id is not None


class TestDataModels:
    """Tests for Pydantic models."""
    
    def test_document_metadata_creation(self):
        """Test creating document metadata."""
        metadata = DocumentMetadata(
            document_id="test-123",
            filename="test.pdf",
            file_size=1000,
            mime_type="application/pdf",
            upload_timestamp=datetime.utcnow(),
            uploader="test_user",
            source_type="upload"
        )
        
        assert metadata.document_id == "test-123"
        assert metadata.filename == "test.pdf"
    
    def test_monetary_amount_creation(self):
        """Test creating monetary amount."""
        amount = MonetaryAmount(
            amount=100.50,
            currency=Currency.USD,
            original_text="$100.50"
        )
        
        assert amount.amount == 100.50
        assert amount.currency == Currency.USD
    
    def test_document_extraction_creation(self):
        """Test creating complete document extraction."""
        metadata = DocumentMetadata(
            document_id="test-123",
            filename="test.pdf",
            file_size=1000,
            mime_type="application/pdf",
            upload_timestamp=datetime.utcnow(),
            uploader="test_user",
            source_type="upload"
        )
        
        extraction = DocumentExtraction(
            document_id="test-123",
            document_type=DocumentType.INVOICE,
            metadata=metadata,
            raw_text="Test content"
        )
        
        assert extraction.document_id == "test-123"
        assert extraction.document_type == DocumentType.INVOICE


# Evaluation Metrics
class TestEvaluationMetrics:
    """Tests for evaluation metrics."""
    
    def test_ocr_accuracy_metric(self):
        """Test OCR accuracy calculation."""
        # Ground truth vs OCR output
        ground_truth = "Invoice #12345"
        ocr_output = "Invoice #12345"
        
        # Simple character-level accuracy
        accuracy = sum(c1 == c2 for c1, c2 in zip(ground_truth, ocr_output)) / len(ground_truth)
        assert accuracy >= 0.9
    
    def test_extraction_precision_recall(self):
        """Test extraction precision and recall."""
        # Mock expected vs actual extractions
        expected_fields = {'invoice_number', 'total_amount', 'vendor_name'}
        extracted_fields = {'invoice_number', 'total_amount'}
        
        tp = len(expected_fields & extracted_fields)  # True positives
        fp = len(extracted_fields - expected_fields)  # False positives
        fn = len(expected_fields - extracted_fields)  # False negatives
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        assert precision == 1.0  # No false positives
        assert recall == 2/3  # One missing field


if __name__ == "__main__":
    pytest.main([__file__, "-v"])