from __future__ import annotations

import os
from functools import lru_cache
from pydantic import BaseModel, Field, AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized environment configuration for the backend service.

    Business/operations:
    - This service runs stateless on Cloud Run. Store all state in Firestore/Cloud Storage.
    - Rotate API keys regularly; supply via `API_KEYS` (comma-separated) in the deployment environment.
    - YOLOv8 weight file is loaded from `YOLO_MODEL_PATH` within the container filesystem.

    Compliance:
    - Only metadata necessary for operations is stored. `DATA_RETENTION_DAYS` controls retention.
    - Ensure Firestore TTL policy on `expiresAt` is enabled per `FIRESTORE_COLLECTION`.
    """

    # General
    ENV: str = Field(default="production")
    LOG_LEVEL: str = Field(default="INFO")
    ALLOWED_ORIGINS: str = Field(
        default="https://roadsense.brampton.ca,https://*.web.app,https://*.firebaseapp.com"
    )

    # Security / Auth
    API_KEYS: str = Field(
        default="",
        description="Comma-separated API keys. Rotate with Secret Manager; do not commit.",
    )

    # GCP
    GCP_PROJECT_ID: str = Field(default="")
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(
        default="", description="Path to service account JSON (mounted in Cloud Run)"
    )

    # Firestore / Storage
    FIRESTORE_COLLECTION: str = Field(default="detections")
    GCS_BUCKET: str = Field(default="")
    DATA_RETENTION_DAYS: int = Field(default=90)

    # ML
    YOLO_MODEL_PATH: str = Field(default="/app/models/weights.pt")
    YOLO_CONFIDENCE_THRESHOLD: float = Field(default=0.35)

    # API
    MAX_UPLOAD_SIZE_MB: int = Field(default=15)

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def api_keys_set(self) -> set[str]:
        return {k.strip() for k in self.API_KEYS.split(",") if k.strip()}


@lru_cache
def get_settings() -> Settings:
    # Pydantic Settings reads from environment automatically
    return Settings()  # type: ignore[call-arg]


class StoragePaths(BaseModel):
    """Canonical object names in Cloud Storage for auditability and cost tracking."""

    uploads_prefix: str = Field(default="uploads")
    detections_prefix: str = Field(default="detections")

    def image_object(self, date_str: str, object_id: str, file_ext: str) -> str:
        return f"{self.uploads_prefix}/{date_str}/{object_id}{file_ext}"

    def detections_object(self, date_str: str, object_id: str) -> str:
        return f"{self.detections_prefix}/{date_str}/{object_id}.json"
