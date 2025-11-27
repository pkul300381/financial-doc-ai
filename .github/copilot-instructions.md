# Financial Document AI - AI Coding Agent Guide

## Project Overview
Financial document extraction system using OCR → LLM → Vector DB → ML anomaly detection pipeline. Processes PDFs/images to extract structured data from invoices, bank statements, and financial documents.

## Architecture

### Pipeline Flow
```
Upload → OCR (Tesseract) → LLM Extraction (GPT-4) → Vector Store (ChromaDB) → RAG/Anomaly Detection
```

**Core Components:**
- `poc_pipeline.py`: Orchestrates end-to-end document processing (main entry point)
- `api.py`: FastAPI REST API with Prometheus metrics
- `src/ocr/preprocessor.py`: OCR engine with OpenCV preprocessing + Camelot/pdfplumber table extraction
- `src/extraction/llm_extractor.py`: LangChain-based GPT-4 structured extraction
- `src/rag/rag_engine.py`: ChromaDB vector store + RAG query engine
- `src/anomaly/detector.py`: Isolation Forest anomaly detection + Prophet trend analysis

### Data Models (`src/models/schemas.py`)
All data uses **Pydantic v1** models (not v2). Key schemas:
- `DocumentExtraction`: Top-level container for all extracted data
- `InvoiceExtraction`, `BankStatementExtraction`: Document-specific schemas
- `OCRResult`, `TableData`, `MonetaryAmount`: Intermediate extraction types

## Critical Patterns

### 1. Pipeline Processing
Every document goes through `DocumentPipeline.process_document()`:
```python
# Step sequence is fixed and logged:
# 1. OCR & Preprocessing → 2. Classification → 3. Structured Extraction → 
# 4. Entity Extraction → 5. Vectorization → 6. Anomaly Detection
```

### 2. Configuration Management
Use `src/config.py` with Pydantic Settings. **Never hardcode API keys** - always use `.env`:
```python
from src.config import get_settings
settings = get_settings()  # Cached singleton via @lru_cache
```

### 3. LLM Extraction Pattern
All LLM calls use zero-temperature for consistency:
```python
llm = ChatOpenAI(model=settings.openai_model, temperature=0)
```
Prompts are in `src/extraction/llm_extractor.py` with structured output parsing.

### 4. Error Handling
Components log errors but don't crash pipeline - return partial results:
```python
logger.error(f"[{document_id}] Step failed: {e}")
# Continue with available data
```

## Development Workflows

### Local Setup (macOS/Linux)
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..." TESSERACT_PATH="/usr/local/bin/tesseract"
python api.py  # Starts on http://localhost:8000
```

### Testing
```bash
pytest tests/ -v                    # All tests
pytest tests/test_pipeline.py -v   # Pipeline tests
pytest --cov=src --cov-report=html  # With coverage
```
Tests use mocked LLM responses - see `tests/test_pipeline.py` for patterns.

### Docker
```bash
docker-compose up  # Full stack: API + Postgres + Prometheus + Grafana
docker-compose -f docker-compose.test.yml up --abort-on-container-exit  # Tests
```

## Key Conventions

### Code Style
- **Logging**: Every major step logs with `[{document_id}]` prefix for traceability
- **Type hints**: Required on all function signatures
- **Docstrings**: Google-style with Args/Returns sections
- **Imports**: Absolute imports from `src.*`, grouped by category (stdlib, third-party, local)

### File Organization
- Pipeline logic → `poc_pipeline.py` (not in `src/`)
- API endpoints → `api.py` (not in `src/`)
- Reusable modules → `src/<domain>/`
- All tests → `tests/` (mirror `src/` structure)
- Data → `data/uploads/`, `data/processed/`, `data/vectordb/`

### Environment Variables
Required: `OPENAI_API_KEY`, `SECRET_KEY`, `TESSERACT_PATH`
Optional: See `src/config.py` Settings class for full list

## Integration Points

### External Dependencies
- **OpenAI API**: GPT-4 for extraction, text-embedding-3-small for vectors
- **Tesseract**: System-level OCR (must be installed separately)
- **ChromaDB**: Embedded vector database (SQLite-based)
- **Prometheus**: `/metrics` endpoint for monitoring

### API Contract
All endpoints return JSON. Key endpoints:
- `POST /api/v1/documents/upload` → `UploadResponse` with `document_id`
- `POST /api/v1/query` → `QueryResponse` with RAG answer + sources
- `GET /api/v1/anomalies` → List of detected anomalies

See `docs/API.md` for full reference.

## Common Tasks

### Adding New Document Type
1. Add enum to `DocumentType` in `src/models/schemas.py`
2. Create extraction schema (e.g., `ReceiptExtraction`)
3. Add extraction method in `src/extraction/llm_extractor.py`
4. Update `extract_structured_data()` switch case

### Debugging OCR Issues
- Check preprocessor output: `preprocessor.process_document()` returns raw OCR results
- Tesseract confidence scores in `OCRResult.confidence`
- View images: `data/processed/{doc_id}/` stores intermediate images

### Tuning Anomaly Detection
- Adjust contamination: `AnomalyDetector.__init__(contamination=0.1)`
- Features extracted in `extract_features()` - modify for domain-specific checks
- Severity thresholds in `_calculate_severity()`

## Gotchas

- **Pydantic v1**: `requirements.txt` locks to `pydantic<2` - use v1 API patterns
- **Window commands**: Setup scripts (`.cmd`) are Windows-specific - adapt for Unix
- **LangChain version**: Uses `langchain==0.1.0` - newer versions have breaking changes
- **ChromaDB persistence**: Vector DB auto-saves to disk - clear `data/vectordb/` to reset
- **Tesseract path**: Varies by OS - configure in `.env` (macOS: `/usr/local/bin/tesseract`)

## Monitoring & Debugging

- **Logs**: Structured logging with timestamps and document IDs
- **Metrics**: Prometheus metrics at `/metrics` endpoint
- **Health check**: `/health` endpoint (used by Docker healthcheck)
- **Document store**: In-memory dict `document_store` in API (use database for production)
