# Financial PoC Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                       │
│                  (Web UI, Mobile, CLI, Scripts)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway / Load Balancer                 │
│                    (nginx, AWS ALB, Kong)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │   Auth       │  │   Upload     │  │   Query/Search     │   │
│  │  Middleware  │  │   Handler    │  │     Handler        │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Document Pipeline Core                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  1. Ingestion → 2. OCR → 3. LLM → 4. Vector → 5. Anomaly │ │
│  └────────────────────────────────────────────────────────────┘ │
└───┬───────────┬──────────┬──────────┬──────────┬────────────────┘
    │           │          │          │          │
    ▼           ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│   S3   │ │Tesseract│ │OpenAI │ │Chroma │ │Isolation │
│Storage │ │  OCR   │ │  API  │ │Vector │ │ Forest   │
└────────┘ └────────┘ └────────┘ └───DB──┘ └──────────┘
```

## Data Flow

### 1. Document Upload & Ingestion
```
User uploads file → API validates → Save to S3 → Generate metadata → Queue for processing
```

### 2. OCR & Preprocessing
```
PDF/Image → Convert to images (300 DPI) → Preprocessing:
  ├─ Grayscale conversion
  ├─ Noise removal
  ├─ Thresholding
  └─ Tesseract OCR → Text + Bounding boxes
```

### 3. Table Extraction
```
PDF → Parallel extraction:
  ├─ Camelot (bordered tables) → DataFrame
  └─ pdfplumber (borderless) → DataFrame
→ Merge results → Structured table data
```

### 4. LLM Extraction
```
Raw text + Tables → LLM Prompt (zero-temp) → Structured JSON:
  ├─ Document classification
  ├─ Field extraction (invoice/bank statement specific)
  ├─ Entity extraction (dates, amounts, names)
  └─ Data normalization (currency, date formats)
```

### 5. Vectorization
```
Document text → Chunking (1000 chars, 200 overlap) → 
OpenAI Embeddings → ChromaDB storage with metadata
```

### 6. RAG Query Processing
```
User query → Embed query → Vector search (cosine similarity) → 
Retrieve top-k chunks → LLM synthesis → Answer + sources + insights
```

### 7. Anomaly Detection
```
Historical data → Train Isolation Forest → 
New document → Extract features → Predict → 
Outlier score → Severity classification → Alert/Log
```

## Component Details

### OCR Engine
- **Technology**: Tesseract 4.x
- **Preprocessing**: OpenCV for image enhancement
- **Output**: Text blocks with confidence scores and bounding boxes
- **Performance**: ~2-5 seconds per page

### LLM Extraction
- **Model**: GPT-4-turbo-preview
- **Temperature**: 0.0 (deterministic)
- **Context window**: 128k tokens
- **Prompt engineering**: Structured JSON output with examples
- **Retry logic**: Exponential backoff for rate limits

### Vector Database
- **Engine**: ChromaDB
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Similarity**: Cosine distance
- **Indexing**: HNSW for fast similarity search
- **Metadata filtering**: Document type, date range, source

### Anomaly Detection
- **ML Model**: Isolation Forest (unsupervised)
- **Features**: Processing time, text length, amount, entity count
- **Statistical**: Z-score for amount outliers (3σ threshold)
- **Trend Analysis**: Prophet for time series forecasting

## Deployment Architecture

### Development
```
Local machine → Python venv → SQLite → Local ChromaDB → Local API
```

### Staging
```
Docker container → PostgreSQL → Shared ChromaDB → Load balancer → Prometheus/Grafana
```

### Production
```
Kubernetes cluster (3+ replicas) → RDS PostgreSQL → 
S3 for documents → Managed vector DB → 
ALB → CloudWatch/Datadog → Secrets Manager
```

## Scaling Strategy

### Horizontal Scaling
- Stateless API design allows multiple replicas
- Shared database and vector store
- Load balancer distributes traffic
- Auto-scaling based on CPU/memory/queue depth

### Performance Optimization
1. **Caching**: Redis for frequent queries
2. **Async Processing**: Celery for background document processing
3. **Batch Processing**: Group similar documents
4. **CDN**: Static assets and cached responses
5. **Connection Pooling**: Database and API clients

### Cost Optimization
- Use spot instances for non-critical workloads
- Archive old documents to Glacier
- Cache embeddings to reduce API calls
- Monitor LLM token usage

## Security Architecture

### Layers
1. **Network**: TLS/SSL, VPC, security groups
2. **Application**: API key auth, rate limiting, input validation
3. **Data**: Encryption at rest/transit, PII masking
4. **Infrastructure**: IAM roles, secrets management, audit logs

### Threat Mitigation
- **Injection attacks**: Input sanitization, parameterized queries
- **DDoS**: Rate limiting, WAF, CDN
- **Data breaches**: Encryption, access controls, audit logging
- **Unauthorized access**: Multi-factor auth, API keys, RBAC

## Monitoring & Observability

### Metrics (Prometheus)
- Request rate, latency, errors
- Document processing time
- LLM API usage and costs
- Vector search performance

### Logging (ELK Stack)
- Structured JSON logs
- Request/response logging
- Error tracking with stack traces
- PII masking

### Tracing (Jaeger)
- Distributed tracing across services
- Performance bottleneck identification
- Dependency analysis

### Alerting
- Health check failures
- High error rates
- Processing delays
- Cost threshold breaches

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | FastAPI | REST API with async support |
| OCR | Tesseract | Open-source OCR engine |
| LLM | OpenAI GPT-4 | Structured data extraction |
| Embeddings | OpenAI text-embedding-3-small | Vector representations |
| Vector DB | ChromaDB | Semantic search |
| ML | scikit-learn, Prophet | Anomaly/trend detection |
| Database | PostgreSQL | Structured data storage |
| Storage | S3 | Document storage |
| Container | Docker | Application packaging |
| Orchestration | Kubernetes | Container orchestration |
| CI/CD | Jenkins | Build and deployment |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |
| Logging | ELK Stack | Log aggregation |

## Future Enhancements

1. **Multi-modal processing**: Handle images, handwriting, forms
2. **Real-time processing**: WebSocket for live updates
3. **Collaborative features**: Multi-user annotations
4. **Advanced analytics**: Predictive models, risk scoring
5. **Integration**: Connect to accounting systems, ERPs
