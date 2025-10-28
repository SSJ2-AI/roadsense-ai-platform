# RoadSense Dashboard

Static web dashboard for visualizing pothole detections with Firebase Hosting, Firebase Auth, and Firestore realtime updates.

## Features

- 🗺️ Interactive map with pothole markers (Leaflet)
- 📊 Real-time analytics and statistics
- 🔐 Firebase Authentication (Google Sign-In)
- 📍 Area-based filtering and hotspot visualization
- 📥 CSV export for reporting
- 📱 Responsive design for mobile and desktop

## Prerequisites

- Firebase project with:
  - Firestore (Native mode)
  - Authentication (Google provider enabled)
  - Hosting enabled
- Node.js and npm
- Firebase CLI: `npm install -g firebase-tools`

## Setup

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project or select existing
3. Enable Firestore Database (Native mode)
4. Enable Authentication → Sign-in method → Google
5. Enable Hosting

### 2. Configure Firebase

1. **Get Firebase configuration:**
   - Go to Project Settings → General
   - Scroll to "Your apps" section
   - Copy Firebase SDK configuration

2. **Update `public/firebase-config.js`:**
   ```javascript
   const firebaseConfig = {
     apiKey: "YOUR_API_KEY",
     authDomain: "your-project.firebaseapp.com",
     projectId: "your-project-id",
     storageBucket: "your-project.appspot.com",
     messagingSenderId: "123456789",
     appId: "1:123456789:web:abc123"
   };
   
   firebase.initializeApp(firebaseConfig);
   const auth = firebase.auth();
   const db = firebase.firestore();
   ```

### 3. Configure Backend API

Update `public/app.js` with your backend URL:

```javascript
const API_BASE_URL = 'https://your-cloud-run-url.run.app';
```

### 4. Set Up Firestore Security Rules

In Firebase Console → Firestore → Rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Detections collection - read-only for authenticated users
    match /detections/{detection} {
      allow read: if request.auth != null;
      allow write: if false; // Only backend can write
    }
  }
}
```

### 5. Authentication Setup

1. Go to Authentication → Sign-in method
2. Enable Google provider
3. Add authorized domains (your Firebase Hosting domain)
4. Configure OAuth consent screen if needed

## Deployment

### Quick Deploy

```bash
chmod +x deploy.sh
./deploy.sh [environment]
```

The script will:
1. Verify Firebase CLI is installed
2. Prompt for Firebase and backend configuration
3. Deploy to Firebase Hosting
4. Output hosting URL

### Manual Deployment

1. **Login to Firebase:**
   ```bash
   firebase login
   ```

2. **Initialize project (first time only):**
   ```bash
   firebase init hosting
   # Select existing project
   # Public directory: public
   # Single-page app: No
   # GitHub auto-deployment: No
   ```

3. **Deploy:**
   ```bash
   firebase deploy --only hosting
   ```

4. **View deployment:**
   ```bash
   firebase hosting:sites:list
   ```

## Development

### Local Testing

```bash
firebase serve --only hosting
```

Access at: http://localhost:5000

### File Structure

```
dashboard/
├── public/
│   ├── index.html          # Main dashboard page
│   ├── analytics.html      # Analytics page
│   ├── areas.html          # Areas/neighborhoods page
│   ├── app.js              # Main application logic
│   ├── analytics.js        # Analytics page logic
│   ├── areas.js            # Areas page logic
│   ├── styles.css          # Styles
│   └── firebase-config.js  # Firebase configuration
├── firebase.json           # Firebase Hosting config
├── deploy.sh              # Deployment script
└── README.md              # This file
```

## Features Guide

### Main Dashboard (index.html)

- View all potholes on interactive map
- Filter by status (reported/verified/scheduled/repaired)
- View detection details
- Export data to CSV
- Real-time updates from Firestore

### Analytics Page (analytics.html)

- Total detections over time
- Repair rate statistics
- Cost savings estimates
- Severity breakdown
- Interactive charts

### Areas Page (areas.html)

- Detections grouped by neighborhood
- Hotspot identification (>10 potholes)
- Priority areas for repair
- Area-specific statistics

## Configuration

### Backend Integration

The dashboard connects to the backend API for:
- Priority queue data
- Analytics and statistics
- Area-based reports

Ensure CORS is configured on backend to allow dashboard origin.

### Firestore Collections

Expected collection structure:

```javascript
detections/{detectionId}
{
  id: string,
  createdAt: timestamp,
  metadata: {
    location: { lat, lng, alt },
    deviceId: string,
    capturedAt: timestamp
  },
  detection: {
    numDetections: number,
    boundingBoxes: array,
    modelVersion: string,
    inferenceMs: number
  },
  severity: "low" | "medium" | "high",
  status: "reported" | "verified" | "scheduled" | "repaired",
  priority_score: number,
  area: string,
  street_name: string,
  repair_urgency: string,
  road_type: string
}
```

## Monitoring

### Firebase Hosting

- View analytics: Firebase Console → Hosting → Dashboard
- Monitor usage and bandwidth
- Check deployment history

### Performance

- Enable Firebase Performance Monitoring
- Track page load times
- Monitor API call latency

## Customization

### Branding

Update `public/index.html` and `public/styles.css`:
- Logo and colors
- City-specific branding
- Custom map styles

### Map Configuration

Edit `public/app.js`:
- Default center/zoom
- Marker styles
- Popup content
- Clustering settings

## Security

### Best Practices

1. **Never commit secrets:**
   - Add `firebase-config.js` to `.gitignore` if it contains sensitive data
   - Use environment variables for production

2. **Firestore Rules:**
   - Restrict write access to backend only
   - Require authentication for read access

3. **API Keys:**
   - Restrict Firebase API key to authorized domains
   - Use separate keys for staging/production

## Troubleshooting

### Authentication Issues

- Check authorized domains in Firebase Console
- Verify Google Sign-In is enabled
- Clear browser cache/cookies

### Data Not Loading

- Check Firestore security rules
- Verify backend CORS configuration
- Check browser console for errors
- Ensure Firestore collection name matches backend

### Deployment Failures

- Verify Firebase CLI is logged in: `firebase login --reauth`
- Check project selection: `firebase use --add`
- Review Firebase Hosting quota limits

## Production Checklist

- [ ] Firebase configuration set with production credentials
- [ ] Backend API URL updated to production URL
- [ ] Firestore security rules deployed
- [ ] Authentication configured and tested
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active
- [ ] Performance monitoring enabled
- [ ] Analytics tracking configured
- [ ] User acceptance testing completed

## Support

For issues:
- Check Firebase Console logs
- Review browser developer console
- Test Firestore connection with Firebase Emulator
- Verify backend API is accessible from dashboard origin
