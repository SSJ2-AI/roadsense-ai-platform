from __future__ import annotations

import io
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from collections import defaultdict

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette import status

from google.cloud import storage
from google.cloud import firestore
from ultralytics import YOLO
from PIL import Image
import googlemaps
from sklearn.cluster import DBSCAN
import numpy as np

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
_gmaps_client: Optional[googlemaps.Client] = None


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
    
    # Initialize Google Maps client for reverse geocoding
    if settings.ENABLE_REVERSE_GEOCODING and settings.GOOGLE_MAPS_API_KEY:
        try:
            global _gmaps_client
            _gmaps_client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
            logger.info("Google Maps client initialized for reverse geocoding")
        except Exception as e:
            logger.error(f"Google Maps client initialization failed: {e}")

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


@app.get("/v1/health/live")
def health_live() -> Dict[str, Any]:
    """Liveness probe for GCP Cloud Run - basic check that service is running."""
    return {"status": "alive", "timestamp": _now_utc().isoformat()}


@app.get("/v1/health/ready")
def health_ready() -> Dict[str, Any]:
    """Readiness probe for GCP Cloud Run - checks all dependencies are available."""
    checks = {
        "storage": bool(_storage_client),
        "firestore": bool(_firestore_client),
        "model": bool(_yolo_model),
        "gmaps": bool(_gmaps_client) if settings.ENABLE_REVERSE_GEOCODING else True,
    }
    
    all_ready = all(checks.values())
    
    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "timestamp": _now_utc().isoformat()
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


def _calculate_severity(num_detections: int, max_confidence: float) -> str:
    """Calculate severity level based on detection count and confidence.
    
    - Low: 1 pothole with confidence <0.7
    - Medium: 2 potholes OR confidence 0.7-0.9
    - High: 3+ potholes OR confidence >0.9
    """
    if not settings.ENABLE_PRIORITY_SCORING:
        return "low"
    
    if num_detections >= 3 or max_confidence > 0.9:
        return "high"
    elif num_detections == 2 or (0.7 <= max_confidence <= 0.9):
        return "medium"
    else:
        return "low"


def _calculate_priority_score(
    severity: str,
    road_type: str,
    num_detections: int,
    age_days: float = 0
) -> int:
    """Calculate priority score (0-100) for repair scheduling.
    
    - Base score from severity (low=25, medium=50, high=75)
    - Add points for road type (residential=0, arterial=15, highway=25)
    - Add points for detection count (5 points per pothole)
    - Add points for age (5 points per day unrepaired)
    """
    if not settings.ENABLE_PRIORITY_SCORING:
        return 0
    
    # Base score from severity
    severity_scores = {"low": 25, "medium": 50, "high": 75}
    score = severity_scores.get(severity, 25)
    
    # Road type bonus
    road_type_scores = {"residential": 0, "arterial": 15, "highway": 25}
    score += road_type_scores.get(road_type, 0)
    
    # Detection count bonus (5 points per pothole)
    score += min(num_detections * 5, 20)  # Cap at 20 points
    
    # Age bonus (5 points per day, capped at 20)
    score += min(int(age_days * 5), 20)
    
    # Ensure 0-100 range
    return min(max(score, 0), 100)


def _reverse_geocode(lat: float, lng: float) -> Dict[str, Optional[str]]:
    """Convert lat/lng to address components using Google Maps Geocoding API.
    
    Returns dict with: street_name, area (neighborhood), road_type
    """
    if not settings.ENABLE_REVERSE_GEOCODING or not _gmaps_client:
        return {"street_name": None, "area": None, "road_type": "residential"}
    
    try:
        results = _gmaps_client.reverse_geocode((lat, lng))
        
        if not results:
            return {"street_name": None, "area": None, "road_type": "residential"}
        
        result = results[0]
        components = {c["types"][0]: c["long_name"] for c in result.get("address_components", [])}
        
        # Extract street name
        street_name = components.get("route", None)
        
        # Extract neighborhood/area (try multiple component types)
        area = (
            components.get("neighborhood") or
            components.get("sublocality") or
            components.get("locality") or
            None
        )
        
        # Infer road type from address components (simplified heuristic)
        road_type = "residential"
        if street_name:
            street_lower = street_name.lower()
            if any(x in street_lower for x in ["highway", "hwy", "freeway"]):
                road_type = "highway"
            elif any(x in street_lower for x in ["avenue", "boulevard", "blvd", "parkway"]):
                road_type = "arterial"
        
        return {
            "street_name": street_name,
            "area": area,
            "road_type": road_type
        }
    except Exception as e:
        logger.warning(f"Reverse geocoding failed: {e}")
        return {"street_name": None, "area": None, "road_type": "residential"}


def _cluster_potholes(detections: List[Dict[str, Any]]) -> Dict[str, str]:
    """Use DBSCAN to cluster nearby potholes (within 50 meters).
    
    Returns dict mapping detection_id -> cluster_id.
    Clusters with 5+ potholes are marked as hotspots.
    """
    if not settings.ENABLE_CLUSTERING or len(detections) < 2:
        return {}
    
    # Extract coordinates
    coords = []
    detection_ids = []
    for det in detections:
        loc = det.get("metadata", {}).get("location")
        if loc and "lat" in loc and "lng" in loc:
            coords.append([loc["lat"], loc["lng"]])
            detection_ids.append(det["id"])
    
    if len(coords) < 2:
        return {}
    
    # Convert to numpy array
    coords_array = np.array(coords)
    
    # DBSCAN clustering (eps in radians for haversine distance)
    # 50 meters ≈ 0.00045 in lat/lng degrees (approximate)
    # Using euclidean for simplicity; for production use haversine
    try:
        clustering = DBSCAN(eps=0.0005, min_samples=2, metric='euclidean').fit(coords_array)
        
        # Build cluster mapping
        cluster_map = {}
        for idx, label in enumerate(clustering.labels_):
            if label != -1:  # -1 means noise (not in any cluster)
                cluster_id = f"cluster_{label}"
                detection_id = detection_ids[idx]
                cluster_map[detection_id] = cluster_id
        
        return cluster_map
    except Exception as e:
        logger.warning(f"Clustering failed: {e}")
        return {}


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

    # Calculate severity and priority
    max_conf = max([b.confidence for b in result.boundingBoxes], default=0.0)
    severity = _calculate_severity(result.numDetections, max_conf)
    
    # Reverse geocoding
    geocode_data = {"street_name": None, "area": None, "road_type": "residential"}
    if lat is not None and lng is not None:
        geocode_data = _reverse_geocode(lat, lng)
    
    # Calculate priority score
    priority_score = _calculate_priority_score(
        severity=severity,
        road_type=geocode_data.get("road_type", "residential"),
        num_detections=result.numDetections,
        age_days=0  # New detection, so age is 0
    )
    
    # Determine repair urgency
    repair_urgency = "routine"
    if severity == "high":
        repair_urgency = "emergency"
    elif severity == "medium":
        repair_urgency = "urgent"

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
        severity=severity,
        priority_score=priority_score,
        area=geocode_data.get("area"),
        street_name=geocode_data.get("street_name"),
        status="reported",
        repair_urgency=repair_urgency,
        road_type=geocode_data.get("road_type", "residential"),
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


@app.get("/v1/detections/priority-queue")
async def get_priority_queue(
    status: Optional[str] = Query(None, description="Filter by status (reported/verified/scheduled/repaired)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
):
    """Get all potholes sorted by priority score (highest first).
    
    Returns unrepaired potholes with location, severity, priority_score, area, and street_name.
    """
    _ensure_gcp()
    assert _firestore_client
    
    try:
        # Query Firestore
        query = _firestore_client.collection(settings.FIRESTORE_COLLECTION)
        
        # Filter by status if provided, otherwise exclude repaired
        if status:
            query = query.where("status", "==", status)
        else:
            query = query.where("status", "in", ["reported", "verified", "scheduled"])
        
        # Order by priority_score descending
        query = query.order_by("priority_score", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)
        
        docs = query.stream()
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            if data:
                results.append({
                    "id": doc.id,
                    "location": data.get("metadata", {}).get("location"),
                    "severity": data.get("severity"),
                    "priority_score": data.get("priority_score"),
                    "area": data.get("area"),
                    "street_name": data.get("street_name"),
                    "status": data.get("status"),
                    "repair_urgency": data.get("repair_urgency"),
                    "numDetections": data.get("detection", {}).get("numDetections", 0),
                    "createdAt": data.get("createdAt"),
                    "cluster_id": data.get("cluster_id"),
                })
        
        return {"queue": results, "count": len(results)}
    except Exception as e:
        logger.exception(f"Priority queue query failed: {e}")
        raise HTTPException(status_code=500, detail="Query failed")


@app.get("/v1/analytics/by-area")
async def get_area_analytics():
    """Get analytics grouped by area/neighborhood.
    
    Returns:
    - Total potholes per neighborhood
    - Average severity per area
    - Hotspot areas (>10 potholes)
    - Priority areas for repair
    """
    if not settings.ENABLE_ANALYTICS:
        raise HTTPException(status_code=503, detail="Analytics disabled")
    
    _ensure_gcp()
    assert _firestore_client
    
    try:
        # Fetch all detections
        docs = _firestore_client.collection(settings.FIRESTORE_COLLECTION).stream()
        
        # Group by area
        area_stats = defaultdict(lambda: {
            "count": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "repaired": 0,
            "pending": 0,
            "avg_priority": 0,
            "priority_sum": 0,
        })
        
        for doc in docs:
            data = doc.to_dict()
            if not data:
                continue
            
            area = data.get("area") or "Unknown"
            severity = data.get("severity", "low")
            status = data.get("status", "reported")
            priority = data.get("priority_score", 0)
            
            stats = area_stats[area]
            stats["count"] += 1
            stats[severity] += 1
            stats["priority_sum"] += priority
            
            if status == "repaired":
                stats["repaired"] += 1
            else:
                stats["pending"] += 1
        
        # Calculate averages and identify hotspots
        results = []
        hotspots = []
        
        for area, stats in area_stats.items():
            if stats["count"] > 0:
                stats["avg_priority"] = stats["priority_sum"] / stats["count"]
            
            area_data = {
                "area": area,
                "total_potholes": stats["count"],
                "severity_breakdown": {
                    "high": stats["high"],
                    "medium": stats["medium"],
                    "low": stats["low"],
                },
                "status_breakdown": {
                    "repaired": stats["repaired"],
                    "pending": stats["pending"],
                },
                "avg_priority_score": round(stats["avg_priority"], 1),
            }
            
            results.append(area_data)
            
            # Identify hotspots (>10 potholes)
            if stats["count"] > 10:
                hotspots.append({
                    "area": area,
                    "count": stats["count"],
                    "avg_priority": round(stats["avg_priority"], 1),
                })
        
        # Sort results by total potholes
        results.sort(key=lambda x: x["total_potholes"], reverse=True)
        hotspots.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "by_area": results,
            "hotspots": hotspots,
            "total_areas": len(results),
        }
    except Exception as e:
        logger.exception(f"Area analytics query failed: {e}")
        raise HTTPException(status_code=500, detail="Query failed")


@app.get("/v1/analytics/statistics")
async def get_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get overall statistics for dashboard analytics.
    
    Returns:
    - Total potholes detected
    - Potholes repaired vs pending
    - Detections over time
    - Average repair time
    - Top hotspot areas
    """
    if not settings.ENABLE_ANALYTICS:
        raise HTTPException(status_code=503, detail="Analytics disabled")
    
    _ensure_gcp()
    assert _firestore_client
    
    try:
        # Fetch detections from the last N days
        cutoff_date = _now_utc() - timedelta(days=days)
        
        docs = _firestore_client.collection(settings.FIRESTORE_COLLECTION).stream()
        
        total_count = 0
        repaired_count = 0
        pending_count = 0
        detections_by_date = defaultdict(int)
        repair_times = []
        area_counts = defaultdict(int)
        
        for doc in docs:
            data = doc.to_dict()
            if not data:
                continue
            
            created_at = data.get("createdAt")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except:
                    continue
            
            # Skip old data
            if created_at and created_at < cutoff_date:
                continue
            
            total_count += 1
            
            status = data.get("status", "reported")
            if status == "repaired":
                repaired_count += 1
            else:
                pending_count += 1
            
            # Track by date
            if created_at:
                date_key = created_at.strftime("%Y-%m-%d")
                detections_by_date[date_key] += 1
            
            # Calculate repair time if repaired
            # Note: We'd need a repairedAt field for accurate calculation
            # For now, just track counts
            
            # Track area counts
            area = data.get("area", "Unknown")
            area_counts[area] += 1
        
        # Top 5 hotspot areas
        top_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        hotspot_areas = [{"area": area, "count": count} for area, count in top_areas]
        
        # Detections timeline
        timeline = [{"date": date, "count": count} for date, count in sorted(detections_by_date.items())]
        
        # Cost savings estimate (placeholder calculation)
        # Assume proactive repair saves $500 per pothole vs reactive
        cost_savings = repaired_count * 500
        
        return {
            "total_potholes": total_count,
            "repaired": repaired_count,
            "pending": pending_count,
            "repair_rate": round(repaired_count / total_count * 100, 1) if total_count > 0 else 0,
            "detections_timeline": timeline,
            "avg_repair_time_days": 0,  # Placeholder - need repairedAt field
            "top_hotspot_areas": hotspot_areas,
            "estimated_cost_savings": cost_savings,
            "period_days": days,
        }
    except Exception as e:
        logger.exception(f"Statistics query failed: {e}")
        raise HTTPException(status_code=500, detail="Query failed")


@app.post("/v1/detections/{detection_id}/update-status", dependencies=[Depends(api_key_auth)])
async def update_detection_status(
    detection_id: str,
    status: str = Query(..., description="New status: reported/verified/scheduled/repaired"),
):
    """Update the status of a detection (for field workers marking repairs)."""
    _ensure_gcp()
    assert _firestore_client
    
    valid_statuses = ["reported", "verified", "scheduled", "repaired"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    try:
        doc_ref = _firestore_client.collection(settings.FIRESTORE_COLLECTION).document(detection_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        # Update status
        doc_ref.update({
            "status": status,
            "updatedAt": _now_utc(),
        })
        
        return {"id": detection_id, "status": status, "updated": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Status update failed: {e}")
        raise HTTPException(status_code=500, detail="Update failed")


@app.post("/v1/analytics/run-clustering", dependencies=[Depends(api_key_auth)])
async def run_clustering():
    """Run DBSCAN clustering on all detections to identify hotspots.
    
    This endpoint can be called periodically (e.g., daily) to update cluster assignments.
    """
    if not settings.ENABLE_CLUSTERING:
        raise HTTPException(status_code=503, detail="Clustering disabled")
    
    _ensure_gcp()
    assert _firestore_client
    
    try:
        # Fetch all unrepaired detections
        docs = _firestore_client.collection(settings.FIRESTORE_COLLECTION)\
            .where("status", "in", ["reported", "verified", "scheduled"])\
            .stream()
        
        detections = []
        for doc in docs:
            data = doc.to_dict()
            if data:
                detections.append({"id": doc.id, **data})
        
        # Run clustering
        cluster_map = _cluster_potholes(detections)
        
        # Update Firestore with cluster assignments
        batch = _firestore_client.batch()
        update_count = 0
        
        for detection_id, cluster_id in cluster_map.items():
            doc_ref = _firestore_client.collection(settings.FIRESTORE_COLLECTION).document(detection_id)
            batch.update(doc_ref, {"cluster_id": cluster_id})
            update_count += 1
            
            # Firestore batch limit is 500 operations
            if update_count % 500 == 0:
                batch.commit()
                batch = _firestore_client.batch()
        
        # Commit remaining updates
        if update_count % 500 != 0:
            batch.commit()
        
        # Count clusters
        unique_clusters = len(set(cluster_map.values()))
        
        return {
            "clustered_detections": len(cluster_map),
            "total_clusters": unique_clusters,
            "unclustered": len(detections) - len(cluster_map),
        }
    except Exception as e:
        logger.exception(f"Clustering failed: {e}")
        raise HTTPException(status_code=500, detail="Clustering failed")


# Root route (optional)
@app.get("/")
def root():
    return {"service": "roadsense-backend", "version": app.version}
