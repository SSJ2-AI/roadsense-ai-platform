#!/usr/bin/env bash
set -euo pipefail

# Deploy dashboard to Firebase Hosting
PROJECT_ID=${FIREBASE_PROJECT_ID:?FIREBASE_PROJECT_ID not set}

pushd dashboard/public >/dev/null
# Inject Firebase config into index via a small JS snippet
cat > firebase-config.js <<EOF
window.__FIREBASE_CONFIG__ = {
  apiKey: "${FIREBASE_API_KEY:?}",
  authDomain: "${FIREBASE_AUTH_DOMAIN:?}",
  projectId: "${PROJECT_ID}",
};
EOF
popd >/dev/null

firebase use "$PROJECT_ID"
firebase deploy --only hosting
