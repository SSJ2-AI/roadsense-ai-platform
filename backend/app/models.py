from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class GeoPoint(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    alt: Optional[float] = Field(default=None)


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    confidence: float = Field(..., ge=0.0, le=1.0)
    class_name: str = Field(default="pothole")


class DetectionMetadata(BaseModel):
    deviceId: Optional[str] = Field(default=None, description="Client-supplied device identifier")
    capturedAt: Optional[datetime] = Field(default=None)
    location: Optional[GeoPoint] = None


class DetectionRequest(BaseModel):
    # For multipart uploads, metadata is passed separately; this model is used for JSON requests
    metadata: DetectionMetadata
    image_base64: Optional[str] = Field(default=None, description="Optional base64 image")

    @model_validator(mode="after")
    def validate_payload(self):
        if not self.image_base64:
            raise ValueError("image_base4 is required for JSON endpoint")
        return self


class DetectionResult(BaseModel):
    boundingBoxes: List[BoundingBox]
    numDetections: int
    modelVersion: str
    inferenceMs: int


class DetectionRecord(BaseModel):
    id: str
    createdAt: datetime
    expiresAt: datetime
    metadata: DetectionMetadata
    storagePath: str
    detection: DetectionResult
