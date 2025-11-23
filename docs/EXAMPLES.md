# Example Document Extraction Outputs

## Invoice Extraction Example

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "invoice",
  "metadata": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "invoice_2025_001.pdf",
    "file_size": 245760,
    "mime_type": "application/pdf",
    "upload_timestamp": "2025-11-23T10:30:00Z",
    "uploader": "john_doe",
    "source_type": "upload",
    "s3_key": "documents/550e8400-e29b-41d4-a716-446655440000.pdf"
  },
  "ocr_results": [
    {
      "text": "INVOICE",
      "confidence": 0.98,
      "bounding_box": {
        "x": 100,
        "y": 50,
        "width": 200,
        "height": 30,
        "page": 0
      },
      "page_number": 0
    }
  ],
  "tables": [
    {
      "headers": ["Description", "Quantity", "Unit Price", "Total"],
      "rows": [
        ["Professional Services", "40", "150.00", "6000.00"],
        ["Software License", "1", "2500.00", "2500.00"]
      ],
      "page_number": 0,
      "confidence": 0.92
    }
  ],
  "structured_data": {
    "invoice_number": "INV-2025-001",
    "invoice_date": "2025-11-20T00:00:00Z",
    "due_date": "2025-12-20T00:00:00Z",
    "vendor_name": "Acme Consulting LLC",
    "vendor_address": "123 Business St, San Francisco, CA 94105",
    "vendor_tax_id": "12-3456789",
    "customer_name": "TechCorp Inc",
    "customer_address": "456 Tech Ave, Palo Alto, CA 94301",
    "line_items": [
      {
        "description": "Professional Services",
        "quantity": 40,
        "unit_price": 150.00,
        "total": 6000.00
      },
      {
        "description": "Software License",
        "quantity": 1,
        "unit_price": 2500.00,
        "total": 2500.00
      }
    ],
    "subtotal": {
      "amount": 8500.00,
      "currency": "USD",
      "original_text": "$8,500.00"
    },
    "tax_amount": {
      "amount": 765.00,
      "currency": "USD",
      "original_text": "$765.00 (9%)"
    },
    "total_amount": {
      "amount": 9265.00,
      "currency": "USD",
      "original_text": "$9,265.00"
    },
    "payment_terms": "Net 30"
  },
  "extracted_entities": [
    {
      "value": "INV-2025-001",
      "confidence": 0.99,
      "field_name": "invoice_number",
      "source_text": "Invoice #: INV-2025-001"
    },
    {
      "value": "Acme Consulting LLC",
      "confidence": 0.95,
      "field_name": "vendor_name",
      "source_text": "From: Acme Consulting LLC"
    }
  ],
  "raw_text": "--- Page 1 ---\nINVOICE\n\nInvoice #: INV-2025-001\nDate: November 20, 2025\nDue Date: December 20, 2025\n\nFrom:\nAcme Consulting LLC\n123 Business St\nSan Francisco, CA 94105\nTax ID: 12-3456789\n\nBill To:\nTechCorp Inc\n456 Tech Ave\nPalo Alto, CA 94301\n\nDescription                 Qty    Unit Price    Total\n─────────────────────────────────────────────────────\nProfessional Services        40    $150.00    $6,000.00\nSoftware License              1  $2,500.00    $2,500.00\n\nSubtotal:                                     $8,500.00\nTax (9%):                                       $765.00\nTotal:                                        $9,265.00\n\nPayment Terms: Net 30\nThank you for your business!",
  "extraction_timestamp": "2025-11-23T10:30:15Z",
  "processing_time_seconds": 12.5
}
```

## Bank Statement Extraction Example

```json
{
  "document_id": "660f9511-f3ac-52e5-b827-557766551111",
  "document_type": "bank_statement",
  "structured_data": {
    "account_number": "****1234",
    "account_holder": "Jane Smith",
    "statement_period_start": "2025-10-01T00:00:00Z",
    "statement_period_end": "2025-10-31T00:00:00Z",
    "opening_balance": {
      "amount": 15750.50,
      "currency": "USD",
      "original_text": "$15,750.50"
    },
    "closing_balance": {
      "amount": 18240.75,
      "currency": "USD",
      "original_text": "$18,240.75"
    },
    "transactions": [
      {
        "date": "2025-10-05",
        "description": "Salary Deposit",
        "amount": 5000.00,
        "balance": 20750.50
      },
      {
        "date": "2025-10-12",
        "description": "Rent Payment",
        "amount": -2500.00,
        "balance": 18250.50
      }
    ],
    "bank_name": "First National Bank"
  }
}
```

## Query Response Example

```json
{
  "answer": "Based on the processed documents, you have a total of 5 invoices from Acme Consulting LLC with a combined value of $42,350.00. The invoices range from September to November 2025, with an average invoice amount of $8,470.00.",
  "confidence": 0.92,
  "sources": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "invoice_2025_001.pdf",
      "excerpt": "Invoice #: INV-2025-001... Total: $9,265.00",
      "relevance_score": 0.95
    },
    {
      "document_id": "771g0622-g4bd-63f6-c938-668877662222",
      "filename": "invoice_2025_002.pdf",
      "excerpt": "Invoice #: INV-2025-002... Total: $7,500.00",
      "relevance_score": 0.93
    }
  ],
  "insights": [
    {
      "insight_id": "insight-789",
      "insight_type": "summary",
      "title": "Acme Consulting Spending Analysis",
      "description": "Your spending with Acme Consulting has increased by 15% compared to the previous quarter, driven primarily by professional services hours.",
      "confidence": 0.88,
      "supporting_documents": [
        "550e8400-e29b-41d4-a716-446655440000",
        "771g0622-g4bd-63f6-c938-668877662222"
      ],
      "data_points": {
        "total_amount": 42350.00,
        "invoice_count": 5,
        "average_invoice": 8470.00,
        "quarter_change_pct": 15.0
      },
      "generated_at": "2025-11-23T10:35:00Z"
    }
  ],
  "query_timestamp": "2025-11-23T10:35:00Z"
}
```

## Anomaly Detection Example

```json
[
  {
    "anomaly_id": "anom-456",
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "anomaly_type": "outlier_amount",
    "severity": "high",
    "description": "Amount $15,000.00 is 4.2 standard deviations from mean $1,350.00",
    "field_name": "total_amount",
    "expected_value": 1350.00,
    "actual_value": 15000.00,
    "confidence_score": 0.92,
    "detected_at": "2025-11-23T10:45:00Z"
  },
  {
    "anomaly_id": "anom-457",
    "document_id": "771g0622-g4bd-63f6-c938-668877662222",
    "anomaly_type": "missing_data",
    "severity": "medium",
    "description": "Required field 'vendor_tax_id' is missing",
    "field_name": "vendor_tax_id",
    "expected_value": null,
    "actual_value": null,
    "confidence_score": 1.0,
    "detected_at": "2025-11-23T10:46:00Z"
  },
  {
    "anomaly_id": "anom-458",
    "document_id": "882h1733-h5ce-74g7-d049-779988773333",
    "anomaly_type": "trend_deviation",
    "severity": "low",
    "description": "Unusual invoice frequency: 8 invoices this week vs average of 3 per week",
    "field_name": "frequency",
    "expected_value": 3.0,
    "actual_value": 8.0,
    "confidence_score": 0.75,
    "detected_at": "2025-11-23T10:47:00Z"
  }
]
```

## Trend Analysis Example

```json
{
  "trend_direction": "increasing",
  "forecast": [
    {
      "ds": "2025-12-01",
      "yhat": 9500.00,
      "yhat_lower": 8000.00,
      "yhat_upper": 11000.00
    },
    {
      "ds": "2025-12-08",
      "yhat": 9750.00,
      "yhat_lower": 8200.00,
      "yhat_upper": 11300.00
    }
  ],
  "anomalies": [
    {
      "date": "2025-11-15",
      "actual": 15000.00,
      "predicted": 9200.00,
      "deviation": 5800.00
    }
  ],
  "average_amount": 8470.00,
  "trend_change_pct": 12.5,
  "seasonality": {
    "weekly": "Peak on Fridays",
    "monthly": "Higher at month-end"
  }
}
```

## Error Response Example

```json
{
  "detail": "Unsupported file type: .docx. Allowed: ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']"
}
```

## Metrics Response Example

```
# TYPE financial_poc_documents_processed counter
financial_poc_documents_processed 1523

# TYPE financial_poc_total_processing_time counter
financial_poc_total_processing_time 18276.5

# TYPE financial_poc_errors counter
financial_poc_errors 12

# TYPE financial_poc_anomalies_detected counter
financial_poc_anomalies_detected 89

# TYPE financial_poc_average_processing_time gauge
financial_poc_average_processing_time 12.0
```
