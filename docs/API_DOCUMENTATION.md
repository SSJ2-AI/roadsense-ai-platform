# API Documentation

Base URL: `https://<cloud-run-url>`

## Authentication
Provide API key via header:
- `x-api-key: <key>` or `Authorization: ApiKey <key>`

## POST /v1/detections
Create a detection from an image upload.

- Content-Type: `multipart/form-data`
- Fields:
  - `image` (file, required)
  - `deviceId` (string, optional)
  - `lat`, `lng`, `alt` (float, optional)
  - `capturedAt` (ISO8601 string, optional)

Response 201:
```json
{
  "id": "uuid",
  "createdAt": "2025-10-28T12:00:00Z",
  "expiresAt": "2026-01-26T12:00:00Z",
  "metadata": {
    "deviceId": "abc",
    "capturedAt": "2025-10-28T11:59:59Z",
    "location": {"lat": 43.7, "lng": -79.7, "alt": 230}
  },
  "storagePath": "gs://bucket/uploads/2025-10-28/uuid.jpg",
  "detection": {
    "boundingBoxes": [{"x": 10, "y": 10, "width": 64, "height": 64, "confidence": 0.92, "class_name": "pothole"}],
    "numDetections": 1,
    "modelVersion": "yolov8",
    "inferenceMs": 120
  }
}
```

## DELETE /v1/detections/{id}
Deletes a detection record and its image blob.

Response 200:
```json
{"status": "deleted", "id": "uuid"}
```

## GET /v1/health
Lightweight readiness indicator.
