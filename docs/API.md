# API Documentation

## Base URL
```
Development: http://localhost:8000
Production: https://api.example.com
```

## Authentication

All API endpoints (except `/health` and `/metrics`) require API key authentication.

### Headers
```
X-API-Key: your_api_key_here
```

## Endpoints

### 1. Upload Document

Upload and process a financial document.

**Endpoint**: `POST /api/v1/documents/upload`

**Request**:
- Content-Type: `multipart/form-data`
- Body: Form data with file and optional metadata

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "X-API-Key: your_key" \
  -F "file=@invoice.pdf" \
  -F "uploader=john_doe"
```

**Response**:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "Document processed successfully",
  "metadata": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "invoice.pdf",
    "file_size": 102400,
    "mime_type": "application/pdf",
    "upload_timestamp": "2025-11-23T10:30:00Z",
    "uploader": "john_doe",
    "source_type": "upload"
  }
}
```

### 2. Get Document Status

Check processing status of a document.

**Endpoint**: `GET /api/v1/documents/{document_id}/status`

**Response**:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress_percentage": 100,
  "current_stage": "completed",
  "error_message": null,
  "updated_at": "2025-11-23T10:30:15Z"
}
```

### 3. Get Document Extraction

Retrieve complete extraction results.

**Endpoint**: `GET /api/v1/documents/{document_id}`

**Response**:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "invoice",
  "metadata": { ... },
  "ocr_results": [ ... ],
  "tables": [ ... ],
  "structured_data": {
    "invoice_number": "INV-2025-001",
    "invoice_date": "2025-11-20",
    "total_amount": {
      "amount": 1500.00,
      "currency": "USD",
      "original_text": "$1,500.00"
    },
    "vendor_name": "Acme Corp"
  },
  "extracted_entities": [ ... ],
  "raw_text": "Full OCR text...",
  "extraction_timestamp": "2025-11-23T10:30:00Z",
  "processing_time_seconds": 12.5
}
```

### 4. Query Documents (RAG)

Perform semantic search and Q&A over documents.

**Endpoint**: `POST /api/v1/query`

**Request**:
```json
{
  "query": "What is the total amount of all invoices from Acme Corp?",
  "document_ids": null,
  "document_types": ["invoice"],
  "date_range_start": null,
  "date_range_end": null,
  "top_k": 5
}
```

**Response**:
```json
{
  "answer": "Based on the processed documents, the total amount of invoices from Acme Corp is $4,250.00, comprising three invoices: INV-001 ($1,500), INV-023 ($1,750), and INV-045 ($1,000).",
  "confidence": 0.92,
  "sources": [
    {
      "document_id": "550e8400-...",
      "filename": "invoice_001.pdf",
      "excerpt": "Invoice #INV-001... Total: $1,500.00",
      "relevance_score": 0.95
    }
  ],
  "insights": [ ... ],
  "query_timestamp": "2025-11-23T10:35:00Z"
}
```

### 5. Get Insights

Generate AI insights from documents.

**Endpoint**: `GET /api/v1/insights`

**Query Parameters**:
- `document_ids` (optional): Comma-separated list of document IDs

**Response**:
```json
[
  {
    "insight_id": "insight-123",
    "insight_type": "trend",
    "title": "Increasing Invoice Amounts",
    "description": "Invoice amounts have increased by 15% over the past month, with average invoice value rising from $1,200 to $1,380.",
    "confidence": 0.88,
    "supporting_documents": ["doc-1", "doc-2", "doc-3"],
    "data_points": {
      "average_increase": 0.15,
      "sample_size": 25
    },
    "generated_at": "2025-11-23T10:40:00Z"
  }
]
```

### 6. Detect Anomalies

Run anomaly detection on documents.

**Endpoint**: `GET /api/v1/anomalies`

**Query Parameters**:
- `document_ids` (optional): Filter by specific documents

**Response**:
```json
[
  {
    "anomaly_id": "anom-456",
    "document_id": "550e8400-...",
    "anomaly_type": "outlier_amount",
    "severity": "high",
    "description": "Amount $15,000.00 is 4.2 standard deviations from mean $1,350.00",
    "field_name": "total_amount",
    "expected_value": 1350.00,
    "actual_value": 15000.00,
    "confidence_score": 0.92,
    "detected_at": "2025-11-23T10:45:00Z"
  }
]
```

### 7. Analyze Trends

Time series trend analysis.

**Endpoint**: `GET /api/v1/trends`

**Response**:
```json
{
  "trend_direction": "increasing",
  "forecast": [
    {
      "ds": "2025-12-01",
      "yhat": 1450.00,
      "yhat_lower": 1200.00,
      "yhat_upper": 1700.00
    }
  ],
  "anomalies": [ ... ],
  "average_amount": 1350.00,
  "trend_change_pct": 12.5
}
```

### 8. Delete Document

Remove document and associated data.

**Endpoint**: `DELETE /api/v1/documents/{document_id}`

**Response**:
```json
{
  "status": "deleted",
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Status Codes
- `200`: Success
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (missing/invalid API key)
- `404`: Not Found
- `500`: Internal Server Error

## Rate Limiting

- **Rate Limit**: 100 requests per minute per API key
- **Headers**: 
  - `X-RateLimit-Limit`: Total limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets

## Webhooks

Configure webhooks to receive notifications:

```json
{
  "webhook_url": "https://your-app.com/webhook",
  "events": ["document.completed", "anomaly.detected"]
}
```

## SDKs and Examples

### Python
```python
import requests

API_KEY = "your_api_key"
BASE_URL = "http://localhost:8000"

# Upload document
with open("invoice.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/v1/documents/upload",
        headers={"X-API-Key": API_KEY},
        files={"file": f}
    )
    doc_id = response.json()["document_id"]

# Query documents
response = requests.post(
    f"{BASE_URL}/api/v1/query",
    headers={"X-API-Key": API_KEY},
    json={"query": "What is the total?", "top_k": 5}
)
answer = response.json()["answer"]
print(answer)
```

### cURL Examples

See individual endpoint sections above for cURL examples.
