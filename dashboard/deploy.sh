#!/bin/bash
# Deploy RoadSense Dashboard to Firebase Hosting
# Usage: ./deploy.sh [environment]
#
# Prerequisites:
# - Node.js and npm installed
# - Firebase CLI installed (npm install -g firebase-tools)
# - Firebase project created with Hosting enabled
# - Authenticated with Firebase (firebase login)

set -e

# Configuration
ENVIRONMENT="${1:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}RoadSense Dashboard Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Environment: ${ENVIRONMENT}"
echo ""

# Verify prerequisites
echo -e "${YELLOW}Verifying prerequisites...${NC}"

# Check if firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo -e "${RED}ERROR: Firebase CLI not found. Install with: npm install -g firebase-tools${NC}"
    exit 1
fi

# Check if logged in
if ! firebase projects:list &> /dev/null; then
    echo -e "${RED}ERROR: Not authenticated with Firebase. Run: firebase login${NC}"
    exit 1
fi

# Check if firebase.json exists
if [ ! -f "firebase.json" ]; then
    echo -e "${RED}ERROR: firebase.json not found. Make sure you're in the dashboard directory.${NC}"
    exit 1
fi

# Check if public directory exists
if [ ! -d "public" ]; then
    echo -e "${RED}ERROR: public directory not found. Dashboard files missing.${NC}"
    exit 1
fi

echo -e "${GREEN}Prerequisites verified!${NC}"
echo ""

# Prompt for Firebase configuration if not already configured
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Firebase Configuration${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

if [ ! -f "public/firebase-config.js" ]; then
    echo "Firebase configuration not found. Please provide your Firebase project details:"
    echo ""
    
    read -p "Firebase API Key: " FIREBASE_API_KEY
    read -p "Firebase Auth Domain: " FIREBASE_AUTH_DOMAIN
    read -p "Firebase Project ID: " FIREBASE_PROJECT_ID
    read -p "Firebase Storage Bucket: " FIREBASE_STORAGE_BUCKET
    read -p "Firebase Messaging Sender ID: " FIREBASE_MESSAGING_SENDER_ID
    read -p "Firebase App ID: " FIREBASE_APP_ID
    
    # Create firebase-config.js
    cat > public/firebase-config.js << EOF
// Firebase configuration - DO NOT commit with real values
const firebaseConfig = {
  apiKey: "${FIREBASE_API_KEY}",
  authDomain: "${FIREBASE_AUTH_DOMAIN}",
  projectId: "${FIREBASE_PROJECT_ID}",
  storageBucket: "${FIREBASE_STORAGE_BUCKET}",
  messagingSenderId: "${FIREBASE_MESSAGING_SENDER_ID}",
  appId: "${FIREBASE_APP_ID}"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize services
const auth = firebase.auth();
const db = firebase.firestore();
EOF
    
    echo ""
    echo -e "${GREEN}Firebase configuration created!${NC}"
    echo ""
fi

# Prompt for backend API URL
echo ""
read -p "Backend API URL (Cloud Run service URL): " API_URL
if [ -z "$API_URL" ]; then
    echo -e "${RED}ERROR: Backend API URL is required${NC}"
    exit 1
fi

# Update app.js with API URL
echo -e "${YELLOW}Updating API configuration...${NC}"
if [ -f "public/app.js" ]; then
    # Check if API_BASE_URL is already set
    if grep -q "const API_BASE_URL" public/app.js; then
        # Update existing API_BASE_URL
        sed -i.bak "s|const API_BASE_URL = .*|const API_BASE_URL = '${API_URL}';|g" public/app.js
        rm public/app.js.bak 2>/dev/null || true
    else
        # Add API_BASE_URL at the beginning
        echo -e "const API_BASE_URL = '${API_URL}';\n$(cat public/app.js)" > public/app.js.tmp
        mv public/app.js.tmp public/app.js
    fi
fi

echo -e "${GREEN}API configuration updated!${NC}"
echo ""

# Select Firebase project
echo -e "${YELLOW}Selecting Firebase project...${NC}"
if [ "$ENVIRONMENT" = "staging" ]; then
    if [ -f "firebase.staging.json" ]; then
        cp firebase.staging.json .firebaserc
    fi
fi

firebase use --add 2>/dev/null || firebase use

echo ""

# Deploy to Firebase Hosting
echo -e "${YELLOW}Deploying to Firebase Hosting...${NC}"
echo "This may take a few moments..."
echo ""

if [ "$ENVIRONMENT" = "staging" ]; then
    firebase deploy --only hosting -m "Staging deployment $(date +%Y-%m-%d)"
else
    firebase deploy --only hosting -m "Production deployment $(date +%Y-%m-%d)"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get hosting URL
HOSTING_URL=$(firebase hosting:sites:list --json | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -n "$HOSTING_URL" ]; then
    echo "Dashboard URL: ${HOSTING_URL}"
    echo ""
fi

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Test dashboard: Open ${HOSTING_URL}"
echo "2. Configure Firebase Authentication (Google provider)"
echo "3. Set up Firestore security rules:"
echo "   rules_version = '2';"
echo "   service cloud.firestore {"
echo "     match /databases/{database}/documents {"
echo "       match /detections/{detection} {"
echo "         allow read: if request.auth != null;"
echo "         allow write: if false;"
echo "       }"
echo "     }"
echo "   }"
echo "4. Test detection visualization with sample data"
echo "5. Set up custom domain (optional)"
echo ""
echo -e "${GREEN}Deployment successful! 🎉${NC}"
