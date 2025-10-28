# RoadSense Backend (FastAPI)

Production-grade FastAPI service for pothole detection.

## Run locally
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt`
- Place model at `models/weights.pt`
- `ENV=local API_KEYS=test123 GCS_BUCKET=your-bucket GCP_PROJECT_ID=your-project uvicorn app.main:app --reload`

## Environment variables
See `.env.example`.

## Deploy
Use `../scripts/deploy-backend.sh`.
