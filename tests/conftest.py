import pytest
from chromadb.api.client import SharedSystemClient

@pytest.fixture(autouse=True)
def reset_chroma_client():
    """Reset ChromaDB client state before each test."""
    SharedSystemClient._identifer_to_system = {}
