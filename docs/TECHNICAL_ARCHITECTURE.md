# Technical Architecture

## Overview
RoadSense is a serverless-first platform:
- Backend: FastAPI on Google Cloud Run
- Storage: Google Cloud Storage (images)
- Database: Firestore (detections metadata, TTL on `expiresAt`)
- ML: YOLOv8 weights packaged into container
- Dashboard: Firebase Hosting, Firebase Auth, Firestore
- Mobile: Flutter client for capture and upload

## Data Flow
1. Mobile captures image, optionally includes GPS and timestamp
2. POST `/v1/detections` with image multipart form data and API key
3. Backend runs YOLOv8 inference, stores image in GCS, writes metadata to Firestore
4. Firestore listener updates Dashboard map in realtime
5. Deletion requests DELETE `/v1/detections/{id}` remove Firestore doc and GCS blob

## Security
- API keys via environment, passed in `x-api-key` header
- TLS provided by Cloud Run / Firebase Hosting
- Private GCS bucket, server-side access only
- Firestore rules restrict access (dashboard read only to authenticated users)
- Cloud Audit Logs enabled

## Compliance
- PIPEDA: minimal collection, retention via TTL, deletion endpoint, encryption in transit
- Ontario Trustworthy AI: clear purpose, transparency, risk mitigation, human oversight via dashboard

## Cost Model (POC)
- Cloud Run: 2 vCPU/4GiB min instances=0 for bursty load; cost ~$0-50/mo depending on use
- Storage: ~$0.023/GB-mo; 90-day retention caps growth
- Firestore: write/read ops; budget guardrails with alerts
- Firebase Hosting/Auth: minimal

## Observability
- Loguru logs to stdout; Cloud Logging sinks
- 200/500 metrics for health; consider Cloud Monitoring uptime checks

## Deployment
- Backend: Docker build + deploy to Cloud Run via `scripts/deploy-backend.sh`
- Dashboard: `scripts/deploy-dashboard.sh` uses `firebase deploy`
