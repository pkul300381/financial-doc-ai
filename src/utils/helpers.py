"""
Utility functions for logging, monitoring, and security.
"""
import logging
import json
from datetime import datetime
from functools import wraps
from typing import Any, Callable
import hashlib
import secrets

from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, Gauge


# Prometheus metrics
request_count = Counter('app_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('app_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
active_users = Gauge('app_active_users', 'Number of active users')


class StructuredLogger:
    """Structured JSON logger for better log aggregation."""
    
    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        
        # Add JSON handler
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            timestamp=True
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, **kwargs):
        """Log info with additional context."""
        self.logger.info(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error with additional context."""
        self.logger.error(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning with additional context."""
        self.logger.warning(message, extra=kwargs)


def timed_operation(metric_name: str = "operation"):
    """Decorator to time operations and record metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                # Log success
                logger = logging.getLogger(func.__module__)
                logger.info(f"{metric_name} completed in {duration:.2f}s")
                
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger = logging.getLogger(func.__module__)
                logger.error(f"{metric_name} failed after {duration:.2f}s: {e}")
                raise
        
        return wrapper
    return decorator


class SecurityUtils:
    """Security utilities for data protection."""
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data using SHA-256."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def mask_pii(text: str) -> str:
        """Mask PII (Personal Identifiable Information) in text."""
        import re
        
        # Mask email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Mask phone numbers (simple pattern)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Mask SSN (XXX-XX-XXXX)
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        return text
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal attacks."""
        import re
        
        # Remove path separators and dangerous characters
        filename = re.sub(r'[/\\]', '', filename)
        filename = re.sub(r'[^\w\s.-]', '', filename)
        
        return filename[:255]  # Limit length


class MetricsCollector:
    """Collect and export application metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics = {
            'documents_processed': 0,
            'total_processing_time': 0.0,
            'errors': 0,
            'anomalies_detected': 0
        }
    
    def record_document_processed(self, processing_time: float):
        """Record document processing metrics."""
        self.metrics['documents_processed'] += 1
        self.metrics['total_processing_time'] += processing_time
    
    def record_error(self):
        """Record error occurrence."""
        self.metrics['errors'] += 1
    
    def record_anomaly(self):
        """Record anomaly detection."""
        self.metrics['anomalies_detected'] += 1
    
    def get_metrics(self) -> dict:
        """Get current metrics."""
        avg_time = (
            self.metrics['total_processing_time'] / self.metrics['documents_processed']
            if self.metrics['documents_processed'] > 0 else 0
        )
        
        return {
            **self.metrics,
            'average_processing_time': avg_time
        }
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        metrics = self.get_metrics()
        lines = []
        
        for key, value in metrics.items():
            lines.append(f'financial_poc_{key} {value}')
        
        return '\n'.join(lines)


def validate_environment():
    """Validate that all required environment variables are set."""
    from src.config import get_settings
    
    required_vars = [
        'openai_api_key',
        'database_url',
        'secret_key'
    ]
    
    settings = get_settings()
    missing = []
    
    for var in required_vars:
        if not getattr(settings, var, None):
            missing.append(var)
    
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
    
    logging.info("Environment validation successful")
