# RoadSense Privacy Policy (PIPEDA Compliant)

Effective date: 2025-10-28

RoadSense processes road imagery and metadata to detect potholes for municipal maintenance. We collect only what is necessary and avoid personal information by design.

- Collection: Road images, timestamps, approximate GPS coordinates, and device identifier (optional). No faces or license plates are intentionally collected; any incidental capture is not used for identification.
- Purpose: Infrastructure maintenance, asset management, and service delivery optimization.
- Consent: Mobile client requests consent for camera and location. Location sharing is optional.
- Use and Disclosure: Data is used for detection and maintenance planning. No sale of data. Third-party processing via Google Cloud (Storage, Firestore) under municipal control.
- Safeguards: TLS in transit, private buckets at rest, least-privilege IAM, audit logging.
- Retention: Default retention is 90 days (configurable). Firestore TTL enforces automated deletion via `expiresAt`.
- Access and Correction: Individuals may request deletion by referencing detection ID via the deletion API.
- Accountability: Contact the City's Privacy Office for inquiries or complaints.
