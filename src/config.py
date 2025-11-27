"""
Configuration management using Pydantic Settings.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    # LLM Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/financial_poc"
    vector_db_path: str = "./data/vectordb"
    
    # Storage
    s3_bucket_name: str = "financial-docs-poc"
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # OCR Configuration
    tesseract_path: str = "/usr/bin/tesseract"
    ocr_language: str = "eng"
    
    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    max_file_size_mb: int = 50
    
    # Security
    secret_key: str
    api_key_header: str = "X-API-Key"
    
    # Monitoring
    prometheus_port: int = 9090


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
