# RoadSense Deployment Guide

This guide covers deploying the RoadSense application with zero-downtime deployment practices.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Staging Deployment](#staging-deployment)
3. [Production Deployment](#production-deployment)
4. [Database Migrations](#database-migrations)
5. [Feature Flags](#feature-flags)
6. [Rollback Procedures](#rollback-procedures)
7. [Health Checks](#health-checks)

## Pre-Deployment Checklist

### Backend

- [ ] All tests pass
- [ ] Environment variables configured for target environment
- [ ] Feature flags set appropriately
- [ ] Database migration scripts tested
- [ ] Health check endpoints verified
- [ ] API keys rotated (if needed)
- [ ] Google Maps API key configured
- [ ] YOLO model uploaded to container

### Frontend

- [ ] Firebase config updated for target environment
- [ ] All charts and visualizations tested
- [ ] Mobile responsiveness verified
- [ ] CORS origins configured correctly

## Staging Deployment

### 1. Backend (Cloud Run)

```bash
# Set environment
export PROJECT_ID="roadsense-staging"
export SERVICE_NAME="roadsense-backend"
export REGION="us-central1"

# Build and push container
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars ENV=staging \
  --set-env-vars ENABLE_CLUSTERING=true \
  --set-env-vars ENABLE_REVERSE_GEOCODING=true \
  --set-env-vars ENABLE_PRIORITY_SCORING=true \
  --set-env-vars ENABLE_ANALYTICS=true \
  --min-instances 0 \
  --max-instances 10 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300

# Verify health
curl https://roadsense-backend-staging-HASH.run.app/v1/health/ready
```

### 2. Database Migration

```bash
# Run migration in staging
python backend/migrations/001_add_priority_fields.py \
  --project roadsense-staging \
  --dry-run

# If dry-run looks good, run actual migration
python backend/migrations/001_add_priority_fields.py \
  --project roadsense-staging
```

### 3. Frontend (Firebase Hosting)

```bash
cd dashboard

# Deploy to staging
firebase use staging
firebase deploy --only hosting -m "Deploy priority queue and analytics features"

# Test staging site
open https://roadsense-staging.web.app
```

### 4. Testing in Staging

- [ ] Test all new endpoints
- [ ] Verify priority queue displays correctly
- [ ] Test analytics dashboard
- [ ] Test area analysis view
- [ ] Check mobile responsiveness
- [ ] Verify reverse geocoding works
- [ ] Test clustering algorithm
- [ ] Check CSV exports

## Production Deployment

### Important: Follow These Steps in Order

### 1. Backup Database

```bash
# Create Firestore backup
gcloud firestore export gs://roadsense-backups/$(date +%Y%m%d-%H%M%S) \
  --project roadsense-production \
  --collection-ids=detections
```

### 2. Enable Maintenance Mode (Optional)

If needed, update the backend to return a maintenance message.

### 3. Deploy Backend with Feature Flags OFF

```bash
export PROJECT_ID="roadsense-production"
export SERVICE_NAME="roadsense-backend"
export REGION="us-central1"

# Deploy with features disabled initially
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --set-env-vars ENV=production \
  --set-env-vars ENABLE_CLUSTERING=false \
  --set-env-vars ENABLE_REVERSE_GEOCODING=false \
  --set-env-vars ENABLE_PRIORITY_SCORING=false \
  --set-env-vars ENABLE_ANALYTICS=false \
  --min-instances 1 \
  --max-instances 50 \
  --memory 4Gi \
  --cpu 2
```

### 4. Run Database Migration

```bash
# Dry run first
python backend/migrations/001_add_priority_fields.py \
  --project roadsense-production \
  --dry-run

# Run actual migration
python backend/migrations/001_add_priority_fields.py \
  --project roadsense-production

# Verify results
# Check Firestore console to confirm new fields exist
```

### 5. Enable Features Gradually

```bash
# Enable priority scoring first
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars ENABLE_PRIORITY_SCORING=true

# Monitor for 10 minutes, check logs
gcloud run logs read $SERVICE_NAME --region $REGION --limit 100

# If stable, enable reverse geocoding
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars ENABLE_REVERSE_GEOCODING=true

# Monitor for 10 minutes

# Enable analytics
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars ENABLE_ANALYTICS=true

# Monitor for 10 minutes

# Finally, enable clustering
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars ENABLE_CLUSTERING=true
```

### 6. Deploy Frontend

```bash
cd dashboard

# Deploy to production
firebase use production
firebase deploy --only hosting -m "Deploy priority queue and analytics features"
```

### 7. Run Clustering Job

```bash
# Trigger initial clustering
curl -X POST https://roadsense-backend-HASH.run.app/v1/analytics/run-clustering \
  -H "X-API-Key: YOUR_API_KEY"
```

## Feature Flags

Feature flags allow enabling/disabling features without redeployment.

### Available Flags

- `ENABLE_CLUSTERING`: Enable DBSCAN clustering algorithm
- `ENABLE_REVERSE_GEOCODING`: Enable Google Maps reverse geocoding
- `ENABLE_PRIORITY_SCORING`: Enable priority score calculation
- `ENABLE_ANALYTICS`: Enable analytics endpoints

### Updating Feature Flags

```bash
# Update single flag
gcloud run services update roadsense-backend \
  --region us-central1 \
  --set-env-vars ENABLE_FEATURE_NAME=true

# Update multiple flags
gcloud run services update roadsense-backend \
  --region us-central1 \
  --set-env-vars ENABLE_CLUSTERING=true,ENABLE_ANALYTICS=true
```

## Health Checks

### Health Check Endpoints

1. **Basic Health**: `GET /v1/health`
   - Returns service status
   - Always available

2. **Liveness**: `GET /v1/health/live`
   - Checks if service is running
   - Used by Cloud Run for container health

3. **Readiness**: `GET /v1/health/ready`
   - Checks if all dependencies are available
   - Verifies: Storage, Firestore, Model, Google Maps

### Configure Cloud Run Health Checks

```bash
gcloud run services update roadsense-backend \
  --region us-central1 \
  --startup-probe-http-path=/v1/health/live \
  --startup-probe-initial-delay=10 \
  --liveness-probe-http-path=/v1/health/live \
  --liveness-probe-period=60
```

## Rollback Procedures

### If Backend Issues Occur

1. **Disable problematic feature**:
   ```bash
   gcloud run services update roadsense-backend \
     --region us-central1 \
     --set-env-vars ENABLE_FEATURE_NAME=false
   ```

2. **Rollback to previous revision**:
   ```bash
   # List revisions
   gcloud run revisions list --service roadsense-backend --region us-central1
   
   # Rollback to specific revision
   gcloud run services update-traffic roadsense-backend \
     --region us-central1 \
     --to-revisions REVISION_NAME=100
   ```

3. **Restore database from backup** (if necessary):
   ```bash
   gcloud firestore import gs://roadsense-backups/BACKUP_NAME
   ```

### If Frontend Issues Occur

```bash
# Rollback Firebase Hosting
firebase hosting:rollback

# Or deploy previous version
git checkout PREVIOUS_COMMIT
firebase deploy --only hosting
```

## Monitoring

### Key Metrics to Watch

1. **Cloud Run Metrics**:
   - Request count
   - Request latency
   - Error rate
   - Instance count
   - Memory usage
   - CPU utilization

2. **Firestore Metrics**:
   - Read operations
   - Write operations
   - Document count

3. **Application Metrics**:
   - Detection processing time
   - Geocoding success rate
   - Clustering job duration

### Logging

```bash
# View real-time logs
gcloud run logs tail roadsense-backend --region us-central1

# View recent errors
gcloud run logs read roadsense-backend \
  --region us-central1 \
  --filter="severity>=ERROR" \
  --limit 100
```

## Troubleshooting

### Common Issues

1. **Health check failing**:
   - Check GCP credentials
   - Verify Firestore/Storage bucket exists
   - Check Google Maps API key
   - Review logs for errors

2. **Reverse geocoding not working**:
   - Verify Google Maps API key is set
   - Check API key restrictions
   - Ensure billing is enabled
   - Check quota limits

3. **Clustering taking too long**:
   - Check number of detections
   - Consider increasing Cloud Run timeout
   - Monitor memory usage

4. **Frontend not connecting to backend**:
   - Verify CORS configuration
   - Check API endpoint URL
   - Verify authentication

## Support

For deployment issues:
- Check Cloud Run logs
- Review Firestore metrics
- Contact DevOps team
- Review this guide's troubleshooting section
