#!/bin/bash
# Deploy RoadSense AI Backend to GCP Cloud Run
# Usage: ./deploy.sh [PROJECT_ID] [REGION]
#
# Prerequisites:
# - gcloud CLI installed and authenticated (gcloud auth login)
# - GCP project with Cloud Run API enabled
# - Cloud Build API enabled
# - Service account with Storage/Firestore permissions
# - Model weights at backend/models/pothole_yolov8n.pt

set -e

# Configuration
PROJECT_ID="${1:-roadsense-ai-prod}"
REGION="${2:-us-central1}"
SERVICE_NAME="roadsense-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/pothole-api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}RoadSense AI Backend Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Verify prerequisites
echo -e "${YELLOW}Verifying prerequisites...${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}ERROR: gcloud CLI not found. Install from https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Check if model weights exist, download if missing
if [ ! -f "models/pothole_yolov8n.pt" ]; then
    echo -e "${YELLOW}Model weights not found. Downloading...${NC}"
    mkdir -p models
    curl -o models/pothole_yolov8n.pt https://raw.githubusercontent.com/FarzadNekouee/YOLOv8_Pothole_Segmentation_Road_Damage_Assessment/master/model/best.pt
    
    if [ ! -f "models/pothole_yolov8n.pt" ]; then
        echo -e "${RED}ERROR: Failed to download model weights${NC}"
        exit 1
    fi
    echo -e "${GREEN}Model downloaded successfully!${NC}"
fi

# Set active project
echo -e "${YELLOW}Setting GCP project...${NC}"
gcloud config set project "${PROJECT_ID}"

# Prompt for environment variables
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Environment Configuration${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "Please provide the following environment variables:"
echo "(Press Enter to skip optional variables)"
echo ""

# Required variables
read -p "API_KEY (comma-separated keys for authentication): " API_KEY
if [ -z "$API_KEY" ]; then
    echo -e "${RED}ERROR: API_KEY is required${NC}"
    exit 1
fi

read -p "GCS_BUCKET (Cloud Storage bucket name): " GCS_BUCKET
if [ -z "$GCS_BUCKET" ]; then
    echo -e "${RED}ERROR: GCS_BUCKET is required${NC}"
    exit 1
fi

# Optional variables
read -p "GOOGLE_MAPS_API_KEY (for reverse geocoding, optional): " GOOGLE_MAPS_API_KEY
read -p "FIRESTORE_COLLECTION (default: detections): " FIRESTORE_COLLECTION
FIRESTORE_COLLECTION="${FIRESTORE_COLLECTION:-detections}"

read -p "DATA_RETENTION_DAYS (default: 90): " DATA_RETENTION_DAYS
DATA_RETENTION_DAYS="${DATA_RETENTION_DAYS:-90}"

read -p "YOLO_CONFIDENCE_THRESHOLD (default: 0.35): " YOLO_CONFIDENCE_THRESHOLD
YOLO_CONFIDENCE_THRESHOLD="${YOLO_CONFIDENCE_THRESHOLD:-0.35}"

# Build environment variables string
ENV_VARS="API_KEYS=${API_KEY},GCS_BUCKET=${GCS_BUCKET},GCP_PROJECT_ID=${PROJECT_ID}"
ENV_VARS="${ENV_VARS},FIRESTORE_COLLECTION=${FIRESTORE_COLLECTION}"
ENV_VARS="${ENV_VARS},DATA_RETENTION_DAYS=${DATA_RETENTION_DAYS}"
ENV_VARS="${ENV_VARS},YOLO_CONFIDENCE_THRESHOLD=${YOLO_CONFIDENCE_THRESHOLD}"
ENV_VARS="${ENV_VARS},ENV=production,LOG_LEVEL=INFO"

if [ -n "$GOOGLE_MAPS_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}"
fi

echo ""
echo -e "${GREEN}Configuration complete!${NC}"
echo ""

# Build and push container
echo -e "${YELLOW}Building container image...${NC}"
echo "This may take 5-10 minutes..."
echo ""

gcloud builds submit --tag "${IMAGE_NAME}" .

echo ""
echo -e "${GREEN}Container built successfully!${NC}"
echo ""

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
echo ""

gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "${ENV_VARS}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)')

echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test the deployment:"
echo "  Health check: curl ${SERVICE_URL}/v1/health"
echo "  API docs: ${SERVICE_URL}/docs"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Test health endpoint: curl ${SERVICE_URL}/v1/health"
echo "2. Test detection endpoint with sample image"
echo "3. Update mobile app and dashboard with new API URL"
echo "4. Configure Firestore security rules"
echo "5. Set up monitoring and alerts"
echo ""
echo -e "${GREEN}Deployment successful! 🎉${NC}"
