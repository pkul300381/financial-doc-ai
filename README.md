# Financial Document Extraction PoC

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Intelligent financial document extraction system with OCR, LLM-based extraction, RAG insights, and ML anomaly detection.

## 🎯 Features

- **📄 Document Processing**: OCR extraction from PDFs and images using Tesseract
- **📊 Table Extraction**: Automated table detection with Camelot and pdfplumber
- **🤖 LLM Extraction**: Structured data extraction using OpenAI GPT-4
- **🔍 Semantic Search**: Vector-based document search with ChromaDB
- **💬 RAG Q&A**: Natural language queries over documents
- **🚨 Anomaly Detection**: ML-based outlier detection with Isolation Forest
- **📈 Trend Analysis**: Time series forecasting with Prophet
- **🌐 REST API**: FastAPI endpoints for all operations
- **📊 Monitoring**: Prometheus metrics and health checks
- **🐳 Docker**: Containerized deployment with CI/CD

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Document   │────▶│     OCR      │────▶│     LLM     │
│   Upload    │     │ Preprocessing│     │ Extraction  │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Insights  │◀────│  Vector DB   │◀────│  Structured │
│  & Anomaly  │     │   (Chroma)   │     │    Data     │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Components

- **Ingestion Layer**: File upload, S3 storage, metadata management
- **OCR Engine**: Tesseract, pdf2image, OpenCV preprocessing
- **Extraction Engine**: LangChain + OpenAI for structured extraction
- **Vector Store**: ChromaDB for embeddings and semantic search
- **Analytics**: Isolation Forest + Prophet for anomaly/trend detection
- **API Layer**: FastAPI with Prometheus monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Tesseract OCR
- OpenAI API key
- Docker (optional)

### Installation

```cmd
REM Clone repository
git clone <repository-url>
cd Financial-poc

REM Create virtual environment
python -m venv venv
venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

REM Configure environment
copy .env.example .env
REM Edit .env and add your OPENAI_API_KEY
```

### Running Locally

```cmd
REM Start API server
python api.py

REM Or run pipeline directly
python poc_pipeline.py
```

API will be available at `http://localhost:8000`

### Docker Deployment

```cmd
docker build -t financial-poc .
docker run -d -p 8000:8000 --name financial-poc financial-poc
```

## 📖 Usage

### Upload Document

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/documents/upload",
    files={"file": open("invoice.pdf", "rb")}
)
doc_id = response.json()["document_id"]
```

### Query Documents

```python
response = requests.post(
    "http://localhost:8000/api/v1/query",
    json={
        "query": "What is the total amount of all invoices?",
        "top_k": 5
    }
)
print(response.json()["answer"])
```

### Detect Anomalies

```python
response = requests.get("http://localhost:8000/api/v1/anomalies")
anomalies = response.json()
for anomaly in anomalies:
    print(f"{anomaly['severity']}: {anomaly['description']}")
```

See [API Documentation](docs/API.md) for complete endpoint reference.

## 🧪 Testing

```cmd
REM Run all tests
pytest tests/ -v

REM Run with coverage
pytest tests/ --cov=src --cov-report=html

REM Run specific test file
pytest tests/test_pipeline.py -v
```

## 📊 Monitoring

### Metrics Endpoint

Prometheus metrics available at `/metrics`:
- `documents_uploaded_total`: Total documents processed
- `document_processing_seconds`: Processing time histogram
- `queries_total`: Total queries executed
- `anomalies_detected_total`: Total anomalies found

### Health Check

```bash
curl http://localhost:8000/health
```

## 🏢 Project Structure

```
Financial-poc/
├── src/
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── ocr/
│   │   └── preprocessor.py     # OCR & preprocessing
│   ├── extraction/
│   │   └── llm_extractor.py    # LLM-based extraction
│   ├── rag/
│   │   └── rag_engine.py       # Vector DB & RAG
│   ├── anomaly/
│   │   └── detector.py         # Anomaly detection
│   ├── utils/
│   │   └── helpers.py          # Utilities
│   └── config.py               # Configuration
├── tests/
│   ├── test_pipeline.py        # Unit tests
│   └── integration/
│       └── test_api.py         # API tests
├── docs/
│   ├── API.md                  # API documentation
│   └── DEPLOYMENT.md           # Deployment guide
├── api.py                      # FastAPI application
├── poc_pipeline.py             # Main pipeline
├── requirements.txt            # Dependencies
├── Dockerfile                  # Docker configuration
├── Jenkinsfile                 # CI/CD pipeline
└── README.md                   # This file
```

## 🔧 Configuration

Key environment variables (see `.env.example`):

- `OPENAI_API_KEY`: OpenAI API key (required)
- `DATABASE_URL`: PostgreSQL connection string
- `VECTOR_DB_PATH`: ChromaDB storage path
- `S3_BUCKET_NAME`: S3 bucket for document storage
- `TESSERACT_PATH`: Path to Tesseract binary

## 📈 Performance

Typical processing times (on standard hardware):
- **OCR**: 2-5 seconds per page
- **LLM Extraction**: 3-8 seconds per document
- **Vectorization**: 1-2 seconds per document
- **Query**: 0.5-2 seconds

## 🔒 Security

- API key authentication
- PII masking in logs
- Input validation on all endpoints
- Dependencies scanned with Safety and Bandit
- Container runs as non-root user

See [Security Checklist](docs/DEPLOYMENT.md#security-checklist) for details.

## 🚢 CI/CD

Jenkins pipeline includes:
1. Code quality checks (Black, Flake8, MyPy)
2. Unit tests with coverage
3. Security scans
4. Docker image build and test
5. Integration tests
6. Deployment to staging
7. Smoke tests

## 🗺️ Roadmap

- [ ] Add support for more document types (receipts, tax forms)
- [ ] Implement async processing with Celery
- [ ] Add support for other LLM providers (Anthropic, local models)
- [ ] Build Streamlit UI for document viewer
- [ ] Add support for batch processing
- [ ] Implement document comparison features
- [ ] Add multi-language support

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Architecture Deep Dive](docs/ARCHITECTURE.md) (coming soon)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- OpenAI for GPT-4 and embeddings
- Tesseract OCR
- LangChain framework
- FastAPI framework
- ChromaDB vector database

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review test files for usage examples

---

**Built with ❤️ for financial document intelligence**