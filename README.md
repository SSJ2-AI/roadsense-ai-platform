# RoadSense AI Platform

Production-ready AI pothole detection system for the City of Brampton POC.

## Components
- `backend/`: FastAPI on Cloud Run with YOLOv8, Firestore, Cloud Storage
- `mobile/`: Flutter app for capture + upload
- `dashboard/`: Firebase-hosted dashboard with map and realtime updates
- `docs/`: Privacy, Terms, Technical Architecture, API docs
- `scripts/`: Deployment and local testing helpers

## Quick Start (Backend)
1. Build: `docker build -t roadsense-backend backend`
2. Run: `docker run -p 8080:8080 -e API_KEYS=test123 -e GCP_PROJECT_ID=... -e GCS_BUCKET=... roadsense-backend`
3. Health: `curl http://localhost:8080/v1/health`
4. Detect: `curl -H 'x-api-key: test123' -F image=@sample.jpg http://localhost:8080/v1/detections`

Notes:
- Provide YOLO weights at `backend/models/weights.pt` or override `YOLO_MODEL_PATH`.
- For real GCP, mount credentials or use Workload Identity.

## Deploy
- Backend: `scripts/deploy-backend.sh` (requires `gcloud` and Secret Manager for `API_KEYS`)
- Dashboard: `scripts/deploy-dashboard.sh` (requires `firebase-tools`)

## Compliance & Security
- PIPEDA: minimal data, 90-day TTL, deletion endpoint
- Ontario Trustworthy AI: purpose-limited, transparent, human-in-the-loop dashboard
- HTTPS enforced by Cloud Run/Firebase; secrets via env/Secret Manager

## License
AGPL-3.0. See `LICENSE` and `LICENSE.md`.
