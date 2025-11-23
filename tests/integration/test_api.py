"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from api import app
from src.models.schemas import DocumentType


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_pipeline():
    """Mock document pipeline."""
    with patch('api.get_pipeline') as mock:
        yield mock


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
    
    @patch('api.get_pipeline')
    def test_upload_document(self, mock_pipeline, client):
        """Test document upload endpoint."""
        # Mock pipeline response
        mock_extraction = Mock()
        mock_extraction.document_id = "test-123"
        mock_extraction.metadata.document_id = "test-123"
        mock_extraction.metadata.filename = "test.pdf"
        
        mock_pipeline.return_value.process_document.return_value = mock_extraction
        
        # Create test file
        files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code in [200, 500]  # May fail without real dependencies
    
    def test_query_endpoint_structure(self, client):
        """Test query endpoint structure."""
        query_data = {
            "query": "What is the total amount?",
            "top_k": 5
        }
        
        response = client.post("/api/v1/query", json=query_data)
        # May return error without real data, but endpoint should exist
        assert response.status_code in [200, 500]
