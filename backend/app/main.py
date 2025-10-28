from __future__ import annotations

import io
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette import status

from google.cloud import storage
from google.cloud import firestore
from ultralytics import YOLO
from PIL import Image

from .auth import api_key_auth
from .config import StoragePaths, get_settings
from .models import (
    BoundingBox,
    DetectionMetadata,
    DetectionRecord,
    DetectionResult,
)


app = FastAPI(
    title="RoadSense AI - Pothole Detection API",
    version="1.0.0",
    description=(
        "Detections API for City of Brampton POC. Upload an image to detect potholes,"
        " store imagery in Cloud Storage, and persist metadata in Firestore."
    ),
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients (Cloud Run containers are recycled; creating once per container is efficient)
_storage_client: Optional[storage.Client] = None
_firestore_client: Optional[firestore.Client] = None
_yolo_model: Optional[YOLO] = None
_storage_paths = StoragePaths()


@app.on_event("startup")
def on_startup() -> None:
    """Initialize external dependencies and the model.

    Cost/operations:
    - Storage/Firestore clients reuse TCP connections and are thread-safe in Cloud Run.
    - YOLO model is loaded once per container to avoid repeated cold start costs.

    Compliance:
    - Only minimal metadata is stored; images retained per policy with TTL via `expiresAt`.
    """
    global _storage_client, _firestore_client, _yolo_model

    logger.remove()
    logger.add(lambda msg: print(msg, flush=True), level=settings.LOG_LEVEL)

    try:
        _storage_client = storage.Client(project=settings.GCP_PROJECT_ID or None)
        _firestore_client = firestore.Client(project=settings.GCP_PROJECT_ID or None)
    except Exception as e:
        logger.error(f"GCP client initialization failed: {e}")
        # Do not raise: health endpoint should still work to report misconfig

    # Model load
    try:
        model_path = settings.YOLO_MODEL_PATH
        if not os.path.exists(model_path):
            logger.error(
                f"YOLO weights not found at {model_path}. Upload model to container filesystem."
            )
        else:
            _yolo_model = YOLO(model_path)
            # Validation: ensure model exposes class names and appears to be pothole-capable
            model_names = getattr(_yolo_model.model, 'names', None) or getattr(_yolo_model, 'names', None)
            num_classes = len(model_names) if isinstance(model_names, (list, dict)) else 'unknown'
            logger.info(f"YOLO model loaded from {model_path}; classes={num_classes}")
            try:
                names_list = list(model_names.values()) if isinstance(model_names, dict) else list(model_names or [])
                if not names_list:
                    logger.warning("Model has no class names metadata; ensure correct weights are provided.")
                else:
                    logger.info(f"Model class names: {names_list}")
                    if not any('pothole' in str(n).lower() for n in names_list):
                        logger.warning("'pothole' class not found in model names; verify correct pothole weights.")
            except Exception:
                logger.warning("Could not introspect model class names for validation.")
    except Exception as e:
        logger.exception(f"Failed to load YOLO model: {e}")


@app.get("/v1/health")
def health() -> Dict[str, Any]:
    """Lightweight health and readiness probe."""
    return {
        "status": "ok",
        "env": settings.ENV,
        "gcpProject": settings.GCP_PROJECT_ID or None,
        "storageBucket": settings.GCS_BUCKET or None,
        "modelPresent": bool(_yolo_model),
    }


def _ensure_gcp() -> None:
    if not _storage_client or not _firestore_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GCP clients not initialized; check credentials and project configuration.",
        )

    if not settings.GCS_BUCKET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GCS_BUCKET not configured.",
        )


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _infer_potholes(img_bytes: bytes) -> DetectionResult:
    if not _yolo_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Deploy container with YOLO weights.",
        )

    start = _now_utc()
    try:
        # Use PIL to ensure consistent RGB
        with Image.open(io.BytesIO(img_bytes)) as im:
            im = im.convert("RGB")
            results = _yolo_model.predict(
                source=im,
                verbose=False,
                conf=settings.YOLO_CONFIDENCE_THRESHOLD,
                imgsz=640,
                device="cpu",
            )
    except Exception as e:
        logger.exception(f"Inference failed: {e}")
        raise HTTPException(status_code=500, detail="Inference error")

    millis = int((_now_utc() - start).total_seconds() * 1000)

    boxes: List[BoundingBox] = []
    try:
        for r in results:
            if r.boxes is None:
                continue
            for b in r.boxes:
                xywh = b.xywh[0].tolist()  # [x_center, y_center, w, h]
                conf = float(b.conf[0].item()) if hasattr(b, "conf") else 0.0
                # Convert center-based to top-left for downstream consumers
                x, y, w, h = xywh
                boxes.append(
                    BoundingBox(
                        x=float(x - w / 2),
                        y=float(y - h / 2),
                        width=float(w),
                        height=float(h),
                        confidence=conf,
                        class_name=str(b.cls[0].item()) if hasattr(b, "cls") else "pothole",
                    )
                )
    except Exception as e:
        logger.exception(f"Post-processing error: {e}")
        raise HTTPException(status_code=500, detail="Post-processing error")

    return DetectionResult(
        boundingBoxes=boxes,
        numDetections=len(boxes),
        modelVersion=str(_yolo_model.model.args.get("name", "yolov8")) if _yolo_model else "unknown",
        inferenceMs=millis,
    )


def _upload_to_gcs(object_name: str, data: bytes, content_type: str) -> str:
    assert _storage_client
    bucket = _storage_client.bucket(settings.GCS_BUCKET)
    blob = bucket.blob(object_name)
    blob.upload_from_string(data, content_type=content_type)
    # Signed URLs are optional; prefer private buckets with server-side access
    return f"gs://{settings.GCS_BUCKET}/{object_name}"


def _persist_record(record: DetectionRecord) -> None:
    assert _firestore_client
    doc_ref = (
        _firestore_client.collection(settings.FIRESTORE_COLLECTION).document(record.id)
    )
    # Convert to Firestore-friendly dict
    payload = json.loads(record.model_dump_json())
    # Firestore uses RFC3339 timestamps; client lib handles datetime conversion
    doc_ref.set(payload)


@app.post("/v1/detections", dependencies=[Depends(api_key_auth)])
async def create_detection(
    image: UploadFile = File(..., description="Image file (JPEG/PNG). Maximum 15 MB)."),
    deviceId: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    alt: Optional[float] = None,
    capturedAt: Optional[str] = None,
):
    """Create a detection from an uploaded image.

    Business:
    - Stores the original image in Cloud Storage and detection metadata in Firestore for auditing.
    - Returns model outputs for client-side visualization.

    Cost:
    - One Cloud Storage write per upload; one Firestore document write; negligible egress (no signed URL by default).
    - YOLO inference runs on CPU in Cloud Run; size accordingly (e.g., 2 vCPU/4 GiB for batch processing).

    Compliance:
    - `expiresAt` is persisted for TTL-based deletion in Firestore.
    - Only geospatial and device metadata is stored; no PII is collected by default.
    """
    _ensure_gcp()

    # File size guard (best-effort; Cloud Run also enforces request limits)
    contents = await image.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    # Inference
    result = _infer_potholes(contents)

    # Build identifiers and storage paths
    uid = str(uuid.uuid4())
    date_str = _now_utc().strftime("%Y-%m-%d")
    ext = ".jpg" if image.content_type == "image/jpeg" else ".png"

    storage_path = _storage_paths.image_object(date_str, uid, ext)
    gs_path = _upload_to_gcs(storage_path, contents, image.content_type or "image/jpeg")

    # Metadata
    dt_captured: Optional[datetime] = None
    if capturedAt:
        try:
            dt_captured = datetime.fromisoformat(capturedAt)
        except Exception:
            pass

    record = DetectionRecord(
        id=uid,
        createdAt=_now_utc(),
        expiresAt=_now_utc() + timedelta(days=settings.DATA_RETENTION_DAYS),
        metadata=DetectionMetadata(
            deviceId=deviceId,
            capturedAt=dt_captured,
            location=(
                None
                if lat is None or lng is None
                else {
                    "lat": float(lat),
                    "lng": float(lng),
                    "alt": float(alt) if alt is not None else None,
                }
            ),
        ),
        storagePath=gs_path,
        detection=result,
    )

    # Persist
    _persist_record(record)

    # Response payload excludes raw image data
    return JSONResponse(status_code=201, content=json.loads(record.model_dump_json()))


@app.delete("/v1/detections/{detection_id}", dependencies=[Depends(api_key_auth)])
async def delete_detection(detection_id: str):
    """Deletes a detection record and (optionally) its image. Supports PIPEDA deletion requests."""
    _ensure_gcp()
    assert _firestore_client

    doc_ref = _firestore_client.collection(settings.FIRESTORE_COLLECTION).document(
        detection_id
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Not found")

    data = doc.to_dict() or {}
    doc_ref.delete()

    # Optionally delete the image blob to minimize storage costs
    storage_path: Optional[str] = None
    storage_url = data.get("storagePath")
    if isinstance(storage_url, str) and storage_url.startswith("gs://"):
        parts = storage_url.replace("gs://", "").split("/", 1)
        if len(parts) == 2:
            bucket_name, object_name = parts[0], parts[1]
            try:
                client = _storage_client
                assert client
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(object_name)
                blob.delete()
            except Exception as e:
                logger.warning(f"Blob delete failed: {e}")

    return {"status": "deleted", "id": detection_id}


# Root route (optional)
@app.get("/")
def root():
    return {"service": "roadsense-backend", "version": app.version}
