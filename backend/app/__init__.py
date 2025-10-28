"""
RoadSense AI Platform - Backend Application Package

This package contains the FastAPI application for the City of Brampton pothole detection POC.

Acquisition-readiness notes:
- This backend is designed for GCP Cloud Run. HTTPS/TLS is provided by the Cloud Run ingress proxy.
- Core integrations: Firestore (metadata), Cloud Storage (images), YOLOv8 (ultralytics) for inference.
- Security: API key authentication via header; CORS restricted; secrets via environment variables only.
- Compliance: Minimal personal data persisted; includes `expiresAt` for Firestore TTL; deletion endpoint for data subject requests.
"""
