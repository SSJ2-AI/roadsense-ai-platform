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

## Model download and verification
1) Download the trained pothole YOLOv8n weights from the upstream research repo:
   - Source: https://github.com/FarzadNekouee/YOLOv8_Pothole_Segmentation_Road_Damage_Assessment
   - Save as `backend/models/pothole_yolov8n.pt`
2) Ensure `YOLO_MODEL_PATH=/app/models/pothole_yolov8n.pt` (already defaulted in `config.py`).
3) Build and run the container; check logs for:
   - "YOLO model loaded from /app/models/pothole_yolov8n.pt"
   - Model class names include `pothole` (a warning is logged if not)
4) Test detection:
   - `curl -H "x-api-key: test123" -F image=@/path/to/pothole.jpg http://localhost:8080/v1/detections`
   - Response should include `detection.numDetections > 0` for pothole imagery.
