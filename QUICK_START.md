# RoadSense Quick Start Guide

## 🚀 New Features Quick Reference

### For City Staff

#### 1. Priority Queue Dashboard
**URL**: `https://your-domain.com/index.html`

**What it does**:
- Shows all potholes sorted by priority (highest first)
- Color-coded severity badges (red=high, yellow=medium, green=low)
- Filter by status, severity, area, and date range
- Export filtered results to CSV

**How to use**:
1. Select filters (optional)
2. Click "Apply Filters"
3. Sort table by clicking column headers
4. Click "Navigate" to get directions
5. Click "Mark Repaired" to update status
6. Use "Export CSV" to download data

#### 2. Analytics Dashboard
**URL**: `https://your-domain.com/analytics.html`

**What it does**:
- Shows overall statistics (total, repaired, pending)
- Visualizes trends over time
- Identifies top hotspot areas
- Calculates cost savings and ROI

**How to use**:
1. View KPI cards at the top
2. Review charts for insights
3. Use ROI calculator to estimate savings
4. Export reports for stakeholders

#### 3. Area Analysis Dashboard
**URL**: `https://your-domain.com/areas.html`

**What it does**:
- Analyzes potholes by neighborhood/ward
- Compares area performance to city average
- Shows detailed area statistics
- Lists streets with issues

**How to use**:
1. Select an area from dropdown
2. View area-specific metrics
3. Check map for pothole locations
4. Review street list
5. Click "View City-Wide Comparison" for all areas

### For Field Workers

#### Mobile View
**When to use**: Access from phone/tablet

**Features**:
- Automatically shows mobile-optimized view on small screens
- Lists assigned potholes (status=scheduled)
- One-tap navigation to Google Maps
- Quick "Mark Repaired" button
- Shows priority and severity

**How to use**:
1. Open dashboard on mobile device
2. View "My Assigned Potholes" section
3. Tap "Navigate" for directions
4. At location, tap "Mark Repaired"

### For Administrators

#### Feature Flags
Control features without redeployment:

```bash
# Enable/disable clustering
gcloud run services update roadsense-backend \
  --set-env-vars ENABLE_CLUSTERING=true

# Enable/disable reverse geocoding
gcloud run services update roadsense-backend \
  --set-env-vars ENABLE_REVERSE_GEOCODING=true

# Enable/disable priority scoring
gcloud run services update roadsense-backend \
  --set-env-vars ENABLE_PRIORITY_SCORING=true

# Enable/disable analytics
gcloud run services update roadsense-backend \
  --set-env-vars ENABLE_ANALYTICS=true
```

#### Health Checks
Monitor service health:

```bash
# Basic health
curl https://your-backend.run.app/v1/health

# Liveness check
curl https://your-backend.run.app/v1/health/live

# Readiness check (verifies all dependencies)
curl https://your-backend.run.app/v1/health/ready
```

#### Run Clustering
Update pothole clusters:

```bash
curl -X POST https://your-backend.run.app/v1/analytics/run-clustering \
  -H "X-API-Key: YOUR_API_KEY"
```

**Recommendation**: Schedule this to run daily via Cloud Scheduler.

## 🔑 API Quick Reference

### New Endpoints

#### Get Priority Queue
```http
GET /v1/detections/priority-queue?status=reported&limit=100
```

#### Get Area Analytics
```http
GET /v1/analytics/by-area
```

#### Get Statistics
```http
GET /v1/analytics/statistics?days=30
```

#### Update Detection Status
```http
POST /v1/detections/{id}/update-status?status=repaired
Headers: X-API-Key: YOUR_API_KEY
```

#### Run Clustering
```http
POST /v1/analytics/run-clustering
Headers: X-API-Key: YOUR_API_KEY
```

## 📊 Understanding Priority Scores

### Score Breakdown (0-100)

**Base Score** (Severity):
- Low: 25 points
- Medium: 50 points
- High: 75 points

**Road Type Bonus**:
- Residential: +0 points
- Arterial: +15 points
- Highway: +25 points

**Detection Count**: +5 points per pothole (max +20)

**Age Bonus**: +5 points per day unrepaired (max +20)

**Example**:
- High severity (75)
- Highway (+25)
- 3 potholes (+15)
- 2 days old (+10)
- **Total: 100 points** (URGENT!)

## 🎨 Color Coding

### Severity Badges
- 🔴 **Red**: High severity (3+ potholes or confidence >90%)
- 🟡 **Yellow**: Medium severity (2 potholes or confidence 70-90%)
- 🟢 **Green**: Low severity (1 pothole with confidence <70%)

### Status Badges
- **Blue**: Reported
- **Purple**: Verified
- **Orange**: Scheduled
- **Green**: Repaired

## 🗺️ Map Features

### Heatmap Layer
Shows pothole density:
1. Click "Toggle Heatmap" button
2. Red areas = high concentration
3. Yellow areas = medium concentration
4. Green areas = low concentration

### Marker Clustering
- Zoom out: Markers group into clusters
- Click cluster: Zoom in to see individual potholes
- Click marker: View pothole details

## 📥 Exporting Data

### CSV Export
**From Priority Queue**:
- Apply filters
- Click "Export CSV"
- File includes: ID, priority, severity, area, street, status, location, count, date

**From Analytics**:
- Click "Export Full Report"
- File includes all fields for all detections

### PDF Export
From Analytics dashboard:
- Click "Export Executive Summary"
- Browser print dialog opens
- Select "Save as PDF"

## 🔧 Troubleshooting

### Map not loading
- Check internet connection
- Verify CORS configuration
- Check browser console for errors

### No data showing
- Ensure you're signed in with Google
- Check Firestore rules
- Verify backend is running (health check)

### Geocoding not working
- Check Google Maps API key is set
- Verify billing is enabled
- Check API quota (40k free/month)

### Clustering not updating
- Run clustering endpoint manually
- Check Cloud Run logs
- Verify ENABLE_CLUSTERING=true

### Priority scores all zero
- Check ENABLE_PRIORITY_SCORING=true
- Re-run migration script
- Verify new detections calculate scores

## 📞 Support

### For Technical Issues
1. Check health endpoints first
2. Review Cloud Run logs
3. Check Firestore console
4. Verify environment variables
5. Contact DevOps team

### For Feature Requests
1. Check if feature flag can enable it
2. Review roadmap
3. Submit GitHub issue
4. Contact product team

## 🎓 Training Resources

### Video Tutorials (Coming Soon)
- Dashboard overview
- Priority queue filtering
- Analytics interpretation
- Mobile field worker app
- Admin configuration

### Documentation
- Full API docs: `/docs` endpoint
- Deployment guide: `DEPLOYMENT_GUIDE.md`
- Implementation details: `IMPLEMENTATION_SUMMARY.md`
- This guide: `QUICK_START.md`

## 🌟 Best Practices

### For Daily Operations
1. Check priority queue each morning
2. Assign high-priority items first
3. Update status as work progresses
4. Run clustering weekly
5. Review analytics monthly

### For Data Quality
1. Ensure GPS accuracy on mobile devices
2. Take photos at detection sites
3. Verify addresses periodically
4. Report mapping errors
5. Keep status updated

### For Performance
1. Use filters to limit results
2. Don't load all detections at once
3. Clear browser cache if slow
4. Use date filters for old data
5. Schedule clustering during off-hours

## ✅ Quick Wins

### Week 1
- [ ] Sign in and explore all three dashboards
- [ ] Apply filters on priority queue
- [ ] Export a CSV report
- [ ] View analytics charts
- [ ] Check area analysis for your ward

### Month 1
- [ ] Schedule repairs by priority score
- [ ] Compare area performance
- [ ] Calculate ROI for stakeholders
- [ ] Train field workers on mobile view
- [ ] Establish weekly clustering schedule

### Quarter 1
- [ ] Optimize repair routes by cluster
- [ ] Track repair completion rates
- [ ] Present analytics to council
- [ ] Refine priority scoring if needed
- [ ] Expand to additional areas

---

**Questions?** Contact the RoadSense support team or check the full documentation.
