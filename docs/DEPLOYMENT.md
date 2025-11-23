# Deployment Guide

## Infrastructure Requirements

### Minimum Requirements (PoC)
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB
- **Python**: 3.10+
- **Docker**: 20.10+

### Recommended Production
- **CPU**: 4+ cores
- **RAM**: 16GB+
- **Storage**: 100GB+ (for document storage)
- **GPU**: Optional (for faster OCR/LLM inference)

## Deployment Options

### 1. Local Development

```cmd
REM Clone and setup
git clone <repository>
cd Financial-poc

REM Create virtual environment
python -m venv venv
venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

REM Configure environment
copy .env.example .env
REM Edit .env with your API keys

REM Run API
python api.py
```

### 2. Docker Deployment

```cmd
REM Build image
docker build -t financial-poc:latest .

REM Run container
docker run -d ^
  -p 8000:8000 ^
  -v %cd%\data:/app/data ^
  -e OPENAI_API_KEY=your_key ^
  --name financial-poc ^
  financial-poc:latest

REM Check logs
docker logs -f financial-poc
```

### 3. Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: financial-poc
spec:
  replicas: 3
  selector:
    matchLabels:
      app: financial-poc
  template:
    metadata:
      labels:
        app: financial-poc
    spec:
      containers:
      - name: financial-poc
        image: financial-poc:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-key
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
---
apiVersion: v1
kind: Service
metadata:
  name: financial-poc
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: financial-poc
```

Deploy with:
```cmd
kubectl apply -f deployment.yaml
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `VECTOR_DB_PATH` | Path to ChromaDB storage | No | `./data/vectordb` |
| `S3_BUCKET_NAME` | S3 bucket for document storage | No | - |
| `APP_ENV` | Environment (development/staging/production) | No | `development` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `SECRET_KEY` | Secret key for API security | Yes | - |

### Secrets Management

**Development**: Use `.env` file
**Production**: Use Kubernetes secrets or HashiCorp Vault

```cmd
REM Create Kubernetes secret
kubectl create secret generic api-secrets ^
  --from-literal=openai-key=sk-... ^
  --from-literal=database-url=postgresql://...
```

## Monitoring

### Health Checks

```cmd
REM Health endpoint
curl http://localhost:8000/health

REM Metrics endpoint (Prometheus)
curl http://localhost:8000/metrics
```

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'financial-poc'
    scrape_interval: 15s
    static_configs:
      - targets: ['financial-poc:8000']
```

### Grafana Dashboard

Import dashboard JSON from `monitoring/grafana-dashboard.json`

## Security Checklist

- [ ] API keys stored in secrets manager
- [ ] HTTPS/TLS enabled for API endpoints
- [ ] Database connections encrypted
- [ ] PII masking enabled in logs
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints
- [ ] CORS properly configured
- [ ] Container runs as non-root user
- [ ] Dependencies scanned for vulnerabilities
- [ ] Backup and disaster recovery plan

## Troubleshooting

### Common Issues

**Issue**: Tesseract not found
```cmd
REM Solution: Install Tesseract
REM Ubuntu/Debian:
apt-get install tesseract-ocr

REM macOS:
brew install tesseract

REM Windows: Download from GitHub releases
```

**Issue**: ChromaDB permission errors
```cmd
REM Solution: Ensure data directory is writable
mkdir data\vectordb
icacls data\vectordb /grant Everyone:(OI)(CI)F
```

**Issue**: Out of memory during processing
```
Solution: Increase Docker memory limit or process documents in smaller batches
```

## CI/CD Pipeline

Jenkins pipeline stages:
1. **Checkout**: Pull latest code
2. **Lint & Test**: Run code quality checks
3. **Build**: Create Docker image
4. **Test Image**: Verify container works
5. **Push**: Upload to registry
6. **Deploy**: Update staging/production
7. **Smoke Tests**: Verify deployment

## Scaling Considerations

### Horizontal Scaling
- Use load balancer (nginx, ALB)
- Deploy multiple replicas
- Shared database and vector store

### Performance Optimization
- Cache frequent queries
- Use async workers for document processing
- Batch process documents
- CDN for static assets

### Cost Optimization
- Use reserved instances
- Auto-scaling based on load
- Archive old documents to cold storage
- Monitor LLM API usage
