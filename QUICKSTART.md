# RoadSense AI - Quick Start Guide

This guide will help you deploy the complete RoadSense AI system in under 15 minutes.

## Prerequisites

- **GCP Account**: Google Cloud Platform account with billing enabled
- **gcloud CLI**: [Install gcloud](https://cloud.google.com/sdk/docs/install)
- **Firebase Account**: For dashboard hosting
- **Flutter SDK**: For building mobile app (optional)

## Step 1: Deploy Backend API (~5 minutes)

The backend automatically downloads the YOLOv8 model if missing.

```bash
cd backend
./deploy.sh roadsense-ai-prod us-central1
```

**Required Environment Variables:**
- `API_KEY`: Comma-separated authentication keys (e.g., "key1,key2,key3")
- `GCS_BUCKET`: Cloud Storage bucket name for images
- `GOOGLE_MAPS_API_KEY`: (Optional) For reverse geocoding

**What it does:**
- Downloads YOLOv8 pothole detection model
- Builds Docker container with FastAPI backend
- Deploys to Google Cloud Run
- Configures auto-scaling (0-10 instances)
- Provisions 2GB memory, 2 vCPU per instance

**Expected Output:**
```
Service URL: https://roadsense-api-xxxxx.run.app
```

Save this URL - you'll need it for the dashboard and mobile app.

## Step 2: Deploy Dashboard (~2 minutes)

```bash
cd dashboard
./deploy.sh production
```

**What it does:**
- Builds static web dashboard
- Deploys to Firebase Hosting
- Configures Firestore security rules

**Before deploying:**
1. Update `dashboard/public/firebase-config.js` with your Firebase config
2. Update API endpoint in `dashboard/public/app.js` with your Cloud Run URL

**Expected Output:**
```
✔  Deploy complete!
Dashboard URL: https://roadsense-ai-prod.web.app
```

## Step 3: Build Mobile App (~3 minutes)

### Android APK

```bash
cd mobile
./build-android.sh production release
```

**Before building:**
1. Update `lib/services/api_client.dart` with your Cloud Run URL
2. Configure Android signing keys (for production)

**APK Location:**
```
mobile/build/app/outputs/flutter-apk/app-release.apk
```

### iOS Build

```bash
cd mobile
flutter build ios --release
```

Requires macOS with Xcode installed.

## Step 4: Verify Deployment

### Test Backend API

```bash
# Health check
curl https://roadsense-api-xxxxx.run.app/v1/health

# API documentation
open https://roadsense-api-xxxxx.run.app/docs
```

### Test Dashboard

1. Open dashboard URL in browser
2. Login with Firebase Authentication
3. View detection map and analytics

### Test Mobile App

1. Install APK on Android device
2. Grant camera and location permissions
3. Start detection session
4. Verify detections appear on dashboard

## Configuration Guide

### Backend Configuration

Edit environment variables in Cloud Run console:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEYS` | Comma-separated auth keys | Required |
| `GCS_BUCKET` | Cloud Storage bucket | Required |
| `FIRESTORE_COLLECTION` | Firestore collection name | `detections` |
| `YOLO_CONFIDENCE_THRESHOLD` | Detection confidence | `0.35` |
| `DATA_RETENTION_DAYS` | Data retention period | `90` |

### Dashboard Configuration

Edit `dashboard/public/firebase-config.js`:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};
```

### Mobile App Configuration

Edit `lib/services/api_client.dart`:

```dart
static const String baseUrl = 'https://roadsense-api-xxxxx.run.app';
static const String apiKey = 'YOUR_API_KEY';
```

## Troubleshooting

### Backend Issues

**Model download fails:**
```bash
# Manually download model
cd backend
curl -o models/pothole_yolov8n.pt https://raw.githubusercontent.com/FarzadNekouee/YOLOv8_Pothole_Segmentation_Road_Damage_Assessment/master/model/best.pt
```

**Container build fails:**
- Verify Docker is installed
- Check GCP Cloud Build API is enabled
- Verify billing is enabled

**Deployment times out:**
- Increase timeout: `--timeout 600`
- Check Cloud Run quotas

### Dashboard Issues

**Firebase deploy fails:**
```bash
# Login again
firebase login

# Initialize project
firebase init hosting
```

**Dashboard shows no data:**
- Verify Firestore security rules allow read access
- Check API endpoint configuration
- Verify mobile app is sending data

### Mobile App Issues

**Build fails:**
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter build apk
```

**API connection fails:**
- Verify API URL is correct
- Check API key is valid
- Verify device has internet connection

## Performance Optimization

### Backend Scaling

- **Min instances**: Set to 1 for faster cold starts (costs more)
- **Max instances**: Increase for high traffic
- **Memory**: Increase to 4Gi for better model performance

```bash
gcloud run services update roadsense-api \
  --min-instances 1 \
  --max-instances 20 \
  --memory 4Gi \
  --region us-central1
```

### Dashboard Performance

- Enable Firebase Performance Monitoring
- Configure CDN caching
- Optimize Firestore queries with indexes

## Cost Estimates

**Monthly costs for moderate usage (1000 detections/month):**

- Cloud Run: $20-50
- Cloud Storage: $5-10
- Firestore: $5-15
- Firebase Hosting: Free
- **Total: ~$30-75/month**

For production at scale, expect $200-500/month for 10,000+ detections.

## Security Best Practices

1. **API Keys**: Rotate regularly, use separate keys per environment
2. **Firestore Rules**: Restrict write access to authenticated users
3. **CORS**: Configure allowed origins in backend
4. **HTTPS**: Always use HTTPS (automatic with Cloud Run/Firebase)
5. **Rate Limiting**: Implement in Cloud Run or Cloud Armor

## Support

- **Documentation**: See `/docs` folder for detailed API docs
- **Issues**: Report on GitHub
- **Email**: support@roadsenseai.com

## Next Steps

1. Configure production Firebase project
2. Set up monitoring and alerts
3. Configure CI/CD pipeline
4. Enable Cloud Armor for DDoS protection
5. Set up backups for Firestore
6. Configure custom domain
7. Submit mobile app to Play Store/App Store

---

**Need help?** Check the detailed deployment guides:
- Backend: `backend/README.md`
- Dashboard: `dashboard/README.md`
- Mobile: `mobile/README.md`
- Architecture: `docs/TECHNICAL_ARCHITECTURE.md`
