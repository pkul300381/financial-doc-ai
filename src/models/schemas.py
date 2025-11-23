"""
Pydantic models for document schemas and API contracts.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types."""
    INVOICE = "invoice"
    BANK_STATEMENT = "bank_statement"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    TAX_FORM = "tax_form"
    FINANCIAL_REPORT = "financial_report"
    OTHER = "other"


class Currency(str, Enum):
    """Common currencies."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CNY = "CNY"


class DocumentMetadata(BaseModel):
    """Metadata for uploaded documents."""
    document_id: str
    filename: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime
    uploader: str
    source_type: str = "upload"  # upload, email, sftp, shared_drive
    s3_key: Optional[str] = None


class BoundingBox(BaseModel):
    """Bounding box coordinates for OCR results."""
    x: float
    y: float
    width: float
    height: float
    page: int


class OCRResult(BaseModel):
    """OCR extraction results."""
    text: str
    confidence: float
    bounding_box: Optional[BoundingBox] = None
    page_number: int


class TableData(BaseModel):
    """Extracted table data."""
    headers: List[str]
    rows: List[List[str]]
    page_number: int
    confidence: float


class MonetaryAmount(BaseModel):
    """Normalized monetary amount."""
    amount: float
    currency: Currency
    original_text: Optional[str] = None


class ExtractedEntity(BaseModel):
    """Generic extracted entity with confidence."""
    value: str
    confidence: float
    field_name: str
    source_text: Optional[str] = None


class InvoiceExtraction(BaseModel):
    """Structured extraction for invoices."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_tax_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    subtotal: Optional[MonetaryAmount] = None
    tax_amount: Optional[MonetaryAmount] = None
    total_amount: Optional[MonetaryAmount] = None
    payment_terms: Optional[str] = None


class BankStatementExtraction(BaseModel):
    """Structured extraction for bank statements."""
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    statement_period_start: Optional[datetime] = None
    statement_period_end: Optional[datetime] = None
    opening_balance: Optional[MonetaryAmount] = None
    closing_balance: Optional[MonetaryAmount] = None
    transactions: List[Dict[str, Any]] = Field(default_factory=list)
    bank_name: Optional[str] = None


class DocumentExtraction(BaseModel):
    """Complete extraction result for a document."""
    document_id: str
    document_type: DocumentType
    metadata: DocumentMetadata
    ocr_results: List[OCRResult] = Field(default_factory=list)
    tables: List[TableData] = Field(default_factory=list)
    structured_data: Optional[Any] = None  # InvoiceExtraction or BankStatementExtraction
    extracted_entities: List[ExtractedEntity] = Field(default_factory=list)
    raw_text: str = ""
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_seconds: float = 0.0


class AnomalyType(str, Enum):
    """Types of anomalies detected."""
    OUTLIER_AMOUNT = "outlier_amount"
    UNUSUAL_FREQUENCY = "unusual_frequency"
    TREND_DEVIATION = "trend_deviation"
    MISSING_DATA = "missing_data"
    DUPLICATE = "duplicate"
    VALIDATION_ERROR = "validation_error"


class Anomaly(BaseModel):
    """Detected anomaly."""
    anomaly_id: str
    document_id: str
    anomaly_type: AnomalyType
    severity: str  # low, medium, high, critical
    description: str
    field_name: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    confidence_score: float
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class InsightType(str, Enum):
    """Types of insights generated."""
    SUMMARY = "summary"
    TREND = "trend"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"
    RISK_ASSESSMENT = "risk_assessment"


class Insight(BaseModel):
    """Generated insight from RAG engine."""
    insight_id: str
    insight_type: InsightType
    title: str
    description: str
    confidence: float
    supporting_documents: List[str] = Field(default_factory=list)
    data_points: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class QueryRequest(BaseModel):
    """Request for RAG-based Q&A."""
    query: str
    document_ids: Optional[List[str]] = None
    document_types: Optional[List[DocumentType]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    top_k: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    """Response from RAG query."""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    insights: List[Insight] = Field(default_factory=list)
    query_timestamp: datetime = Field(default_factory=datetime.utcnow)


class UploadResponse(BaseModel):
    """Response after document upload."""
    document_id: str
    status: str
    message: str
    metadata: DocumentMetadata


class ProcessingStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentStatus(BaseModel):
    """Current status of document processing."""
    document_id: str
    status: ProcessingStatus
    progress_percentage: int
    current_stage: str
    error_message: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
