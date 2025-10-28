# RoadSense Dashboard

Static web dashboard on Firebase Hosting with Firebase Auth and Firestore realtime updates. Visualizes detections on a Leaflet map and supports CSV export.

Setup:
- Create a Firebase project with Firestore (Native mode) and Authentication (Google provider enabled)
- `npm i -g firebase-tools`
- `firebase login`
- Deploy with `scripts/deploy-dashboard.sh`

Security:
- Authentication required to view dashboard. Configure Firestore rules to allow read for authenticated users only.
