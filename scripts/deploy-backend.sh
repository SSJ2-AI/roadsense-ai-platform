#!/usr/bin/env bash
set -euo pipefail

# Deploy FastAPI backend to Cloud Run
# Requirements:
# - gcloud CLI authenticated and configured with target project
# - Artifact Registry repository exists, or use auto-repo

SERVICE_NAME=${SERVICE_NAME:-roadsense-backend}
PROJECT_ID=${GCP_PROJECT_ID:?GCP_PROJECT_ID not set}
REGION=${REGION:-us-central1}
REPO=${REPO:-roadsense}
IMAGE=us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/$SERVICE_NAME:$(date +%Y%m%d%H%M%S)

# Build and push image
gcloud builds submit --tag "$IMAGE" backend

# Deploy to Cloud Run
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars ENV=production,LOG_LEVEL=INFO,FIRESTORE_COLLECTION=detections,YOLO_MODEL_PATH=/app/models/weights.pt \
  --set-secrets API_KEYS=roadsense-api-keys:latest \
  --set-env-vars GCS_BUCKET=${GCS_BUCKET:?},GCP_PROJECT_ID=$PROJECT_ID \
  --memory 2Gi --cpu 2 \
  --port 8080

# Output service URL
URL=$(gcloud run services describe "$SERVICE_NAME" --platform managed --region "$REGION" --project "$PROJECT_ID" --format 'value(status.url)')
echo "Service deployed: $URL"
