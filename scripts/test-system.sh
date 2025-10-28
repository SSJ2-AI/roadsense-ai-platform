#!/usr/bin/env bash
set -euo pipefail

# Local test script for backend using uvicorn
export ENV=local
export LOG_LEVEL=DEBUG
export API_KEYS=test123
export GCP_PROJECT_ID=${GCP_PROJECT_ID:-}
export GCS_BUCKET=${GCS_BUCKET:-test-bucket}

# Requires GOOGLE_APPLICATION_CREDENTIALS if running against real GCP

python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
