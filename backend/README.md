# RoadSense Backend (FastAPI)

Production-grade FastAPI service for pothole detection.

## Prerequisites

- Python 3.11+
- GCP account with Cloud Run and Cloud Build APIs enabled
- Google Cloud SDK (gcloud CLI)
- Model weights: `models/pothole_yolov8n.pt`

## Local Development

1. **Set up Python environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Download model weights:**
   - Download from: https://github.com/FarzadNekouee/YOLOv8_Pothole_Segmentation_Road_Damage_Assessment
   - Place at: `models/pothole_yolov8n.pt`

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run locally:**
   ```bash
   ENV=local \
   API_KEYS=test123 \
   GCS_BUCKET=your-bucket \
   GCP_PROJECT_ID=your-project \
   uvicorn app.main:app --reload --port 8080
   ```

5. **Test endpoints:**
   ```bash
   # Health check
   curl http://localhost:8080/v1/health
   
   # API documentation
   open http://localhost:8080/docs
   
   # Test detection
   curl -H "x-api-key: test123" \
        -F "image=@/path/to/pothole.jpg" \
        -F "lat=43.7315" \
        -F "lng=-79.7624" \
        http://localhost:8080/v1/detections
   ```

## Deployment to GCP Cloud Run

### Quick Deploy

```bash
chmod +x deploy.sh
./deploy.sh [PROJECT_ID] [REGION]
```

The script will:
1. Verify prerequisites (gcloud CLI, model weights)
2. Prompt for environment variables
3. Build container using Cloud Build
4. Deploy to Cloud Run
5. Output service URL

### Manual Deployment

1. **Set GCP project:**
   ```bash
   export PROJECT_ID="roadsense-ai-prod"
   gcloud config set project ${PROJECT_ID}
   ```

2. **Build container:**
   ```bash
   gcloud builds submit --tag gcr.io/${PROJECT_ID}/pothole-api .
   ```

3. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy roadsense-api \
     --image gcr.io/${PROJECT_ID}/pothole-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2 \
     --timeout 300 \
     --set-env-vars API_KEYS=your-key,GCS_BUCKET=your-bucket,GCP_PROJECT_ID=${PROJECT_ID}
   ```

4. **Get service URL:**
   ```bash
   gcloud run services describe roadsense-api \
     --region us-central1 \
     --format='value(status.url)'
   ```

## Environment Variables

See `.env.example` for complete list. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `API_KEYS` | Yes | Comma-separated API keys for authentication |
| `GCS_BUCKET` | Yes | Cloud Storage bucket for images |
| `GCP_PROJECT_ID` | Yes | GCP project ID |
| `GOOGLE_MAPS_API_KEY` | No | For reverse geocoding (recommended) |
| `FIRESTORE_COLLECTION` | No | Firestore collection name (default: detections) |
| `YOLO_CONFIDENCE_THRESHOLD` | No | Detection confidence threshold (default: 0.35) |

## API Endpoints

### Core Endpoints

- `GET /v1/health` - Health check with configuration info
- `GET /v1/health/live` - Liveness probe
- `GET /v1/health/ready` - Readiness probe (checks all dependencies)
- `GET /docs` - Interactive API documentation

### Detection Endpoints

- `POST /v1/detections` - Upload image and detect potholes
- `DELETE /v1/detections/{id}` - Delete detection record
- `POST /v1/detections/{id}/update-status` - Update repair status

### Analytics Endpoints

- `GET /v1/detections/priority-queue` - Get potholes sorted by priority
- `GET /v1/analytics/by-area` - Statistics grouped by neighborhood
- `GET /v1/analytics/statistics` - Overall system statistics
- `POST /v1/analytics/run-clustering` - Run hotspot clustering

## Authentication

All endpoints (except health checks) require API key authentication:

```bash
curl -H "x-api-key: YOUR_API_KEY" https://your-service-url/v1/detections
```

## Production Considerations

1. **Security:**
   - Store API keys in GCP Secret Manager
   - Use VPC connector for private Firestore access
   - Enable Cloud Armor for DDoS protection

2. **Scaling:**
   - Configure min/max instances based on traffic
   - Use Cloud CDN for static assets
   - Consider Cloud Tasks for batch operations

3. **Monitoring:**
   - Set up Cloud Monitoring alerts
   - Enable Cloud Logging
   - Track error rates and latency

4. **Cost Optimization:**
   - Use lifecycle policies on GCS bucket
   - Enable Firestore TTL on `expiresAt` field
   - Configure appropriate resource limits

## Testing

Run automated tests:

```bash
../scripts/test-all.sh https://your-service-url your-api-key
```

## Troubleshooting

### Model not loading
- Verify `models/pothole_yolov8n.pt` exists
- Check logs: `gcloud run services logs read roadsense-api --region us-central1`
- Ensure model is included in Dockerfile COPY

### Firestore connection issues
- Verify GCP_PROJECT_ID is correct
- Check service account permissions
- Enable Firestore API in GCP Console

### High latency
- Increase CPU/memory allocation
- Consider GPU-enabled Cloud Run (premium tier)
- Enable Cloud CDN for repeated requests

## Support

For issues related to:
- **Deployment:** Check Cloud Run logs and deployment script output
- **Detection accuracy:** Review model confidence threshold and training data
- **API errors:** Check API documentation at `/docs` endpoint
