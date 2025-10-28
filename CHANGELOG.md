# Changelog

All notable changes to the RoadSense project will be documented in this file.

## [Unreleased] - 2025-10-28

### Added - Priority Queue and Analytics Features

#### Backend
- **Data Model Extensions** (`backend/app/models.py`)
  - Added `severity` field (low/medium/high) to DetectionRecord
  - Added `priority_score` field (0-100 scale) to DetectionRecord
  - Added `area` field for neighborhood/ward name
  - Added `street_name` field from reverse geocoding
  - Added `status` field (reported/verified/scheduled/repaired)
  - Added `repair_urgency` field (routine/urgent/emergency)
  - Added `cluster_id` field for grouping nearby potholes
  - Added `road_type` field (residential/arterial/highway)

- **Feature Flags** (`backend/app/config.py`)
  - Added `ENABLE_CLUSTERING` flag for DBSCAN clustering
  - Added `ENABLE_REVERSE_GEOCODING` flag for Google Maps integration
  - Added `ENABLE_PRIORITY_SCORING` flag for priority calculation
  - Added `ENABLE_ANALYTICS` flag for analytics endpoints
  - Added `GOOGLE_MAPS_API_KEY` configuration

- **Health Check Endpoints** (`backend/app/main.py`)
  - Added `GET /v1/health/live` for liveness probes
  - Added `GET /v1/health/ready` for readiness probes with dependency checks

- **Core Algorithms** (`backend/app/main.py`)
  - Implemented severity calculation algorithm
  - Implemented priority scoring algorithm (0-100 scale)
  - Integrated Google Maps Geocoding API for reverse geocoding
  - Implemented DBSCAN clustering for hotspot identification

- **API Endpoints** (`backend/app/main.py`)
  - Added `GET /v1/detections/priority-queue` - Get potholes sorted by priority
  - Added `GET /v1/analytics/by-area` - Area-grouped statistics
  - Added `GET /v1/analytics/statistics` - Overall system statistics
  - Added `POST /v1/detections/{id}/update-status` - Update detection status
  - Added `POST /v1/analytics/run-clustering` - Trigger clustering algorithm

- **Database Migrations**
  - Created `backend/migrations/001_add_priority_fields.py` - Backfill script
  - Created `backend/migrations/README.md` - Migration documentation
  - Follows Expand-Migrate-Contract pattern
  - Idempotent execution with dry-run mode

- **Environment Configurations**
  - Created `backend/.env.staging` - Staging environment variables
  - Created `backend/.env.production` - Production environment variables
  - Created `backend/.env.example` - Configuration template
  - Created `backend/.gitignore` - Prevent committing secrets

- **Dependencies** (`backend/requirements.txt`)
  - Added `scikit-learn==1.5.1` for DBSCAN clustering
  - Added `googlemaps==4.10.0` for reverse geocoding

#### Frontend

- **Priority Dashboard** (`dashboard/public/index.html`, `dashboard/public/app.js`)
  - Created priority queue table with sortable columns
  - Added area statistics panel with bar chart
  - Implemented heatmap layer toggle
  - Added comprehensive filters:
    - Status filter (reported/verified/scheduled/repaired)
    - Severity filter (high/medium/low)
    - Area/neighborhood dropdown
    - Date range picker
  - Added CSV export functionality
  - Implemented marker clustering for better map visualization
  - Added mobile field worker view with responsive design
  - Added navigation integration (Google Maps)
  - Added "Mark as Repaired" action buttons
  - Implemented real-time Firestore updates

- **Analytics Dashboard** (`dashboard/public/analytics.html`, `dashboard/public/analytics.js`)
  - Created KPI cards (total, repaired, pending, repair rate)
  - Added repair status distribution pie chart
  - Added detections timeline line chart (30-day view)
  - Created top 5 hotspot areas table
  - Added severity distribution doughnut chart
  - Implemented cost savings calculator
  - Created interactive ROI calculator with inputs:
    - Initial investment
    - Reactive repair cost
    - Proactive repair cost
  - Added full report CSV export
  - Added executive summary PDF export (print)
  - Added average repair time metric

- **Area Analysis Dashboard** (`dashboard/public/areas.html`, `dashboard/public/areas.js`)
  - Created area/ward selection dropdown
  - Added key metrics display (total, high severity, avg priority, repair rate)
  - Implemented area-specific map with filtered markers
  - Created comparison to city average bar chart
  - Added severity breakdown doughnut chart
  - Added status breakdown pie chart
  - Created streets list for selected area
  - Implemented repair completion progress bar
  - Created city-wide comparison table with all areas
  - Added area info panel with statistics

- **Styling Updates** (`dashboard/public/styles.css`)
  - Added navigation tabs styling
  - Created filter section styles
  - Styled priority queue table with hover effects
  - Added badge system (severity and status)
  - Created KPI card styles
  - Styled chart containers with responsive heights
  - Added ROI calculator styling
  - Created mobile-responsive layouts
  - Added progress bar animations
  - Styled area analysis components
  - Implemented dark header design
  - Added button states and transitions

- **Firebase Configuration**
  - Created `dashboard/firebase.staging.json` - Staging hosting config
  - Added security headers configuration
  - Configured caching policies

#### Documentation

- **Deployment Guide** (`DEPLOYMENT_GUIDE.md`)
  - Pre-deployment checklist
  - Staging deployment procedures
  - Production deployment with gradual rollout
  - Database migration instructions
  - Feature flag management guide
  - Rollback procedures
  - Health check configuration
  - Monitoring and troubleshooting

- **Implementation Summary** (`IMPLEMENTATION_SUMMARY.md`)
  - Complete feature list
  - Technical stack documentation
  - Success metrics
  - Security considerations
  - Testing recommendations

- **Quick Start Guide** (`QUICK_START.md`)
  - User guides for city staff, field workers, and administrators
  - API quick reference
  - Priority score explanation
  - Color coding guide
  - Map features documentation
  - Export instructions
  - Troubleshooting tips
  - Best practices

- **Changelog** (This file)

### Changed

- Updated `backend/app/main.py`:
  - Enhanced `/v1/detections` endpoint to calculate severity and priority
  - Integrated reverse geocoding on detection creation
  - Added automatic status assignment
  - Added repair urgency calculation

- Updated `dashboard/public/index.html`:
  - Restructured layout with navigation tabs
  - Added comprehensive filter controls
  - Enhanced map section with controls
  - Improved table structure with sortable headers

- Updated `dashboard/public/app.js`:
  - Refactored to support multiple views
  - Enhanced marker creation with custom icons
  - Improved data filtering logic
  - Added chart rendering with Chart.js
  - Enhanced CSV export with more fields

### Dependencies

#### Backend (Python)
- scikit-learn 1.5.1 (new)
- googlemaps 4.10.0 (new)
- fastapi 0.114.2 (existing)
- google-cloud-firestore 2.16.0 (existing)
- google-cloud-storage 2.18.2 (existing)
- ultralytics 8.3.28 (existing)

#### Frontend (JavaScript/CDN)
- Chart.js 4.4.0 (new)
- Leaflet.markercluster 1.5.3 (new)
- Leaflet.heat 0.2.0 (new)
- Leaflet 1.9.4 (existing)
- Firebase SDK 10.13.1 (existing)

### Security

- Added `.gitignore` to prevent committing environment files
- Implemented feature flags for controlled rollout
- Added health check endpoints for monitoring
- Configured environment-specific CORS settings
- Added API key authentication for write operations
- Documented Secret Manager usage for production

### Performance

- Implemented marker clustering for large datasets
- Added batch processing in migration scripts
- Configured Cloud Run min/max instances
- Added lazy loading for charts
- Implemented data filtering before rendering
- Added pagination support for large queries

### Breaking Changes

None. All changes are backward compatible:
- New fields have default values
- Old endpoints remain functional
- Feature flags allow gradual adoption
- Database migration is non-breaking

### Migration Path

1. Deploy backend with features disabled
2. Run database migration: `python backend/migrations/001_add_priority_fields.py`
3. Enable features gradually via environment variables
4. Deploy frontend
5. Run initial clustering: `POST /v1/analytics/run-clustering`

### Known Issues

- Average repair time shows "N/A" (requires `repairedAt` field - future enhancement)
- Clustering uses Euclidean distance (consider Haversine for production)
- PDF export uses browser print (consider server-side PDF generation)

### Future Enhancements

- [ ] Add `repairedAt` timestamp field
- [ ] Implement automated clustering via Cloud Scheduler
- [ ] Add push notifications for field workers
- [ ] Implement photo upload for repair verification
- [ ] Add historical trend analysis
- [ ] Create predictive maintenance models
- [ ] Implement multi-language support
- [ ] Add offline mode for mobile app
- [ ] Create administrative user management
- [ ] Add email alerts for high-priority detections

## [1.0.0] - Previous Release

See existing README.md and documentation for baseline features:
- Pothole detection using YOLOv8
- Image upload and storage
- Basic map visualization
- Firebase authentication
- Cloud Run deployment
- Mobile app (Flutter)

---

**Note**: This project follows [Semantic Versioning](https://semver.org/).
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)
