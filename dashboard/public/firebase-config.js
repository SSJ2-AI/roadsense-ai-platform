// Firebase and API Configuration
// This file should be replaced during deployment with actual values

// Firebase configuration
window.__FIREBASE_CONFIG__ = {
  apiKey: 'REPLACE_WITH_YOUR_FIREBASE_API_KEY',
  authDomain: 'REPLACE_WITH_YOUR_PROJECT.firebaseapp.com',
  projectId: 'REPLACE_WITH_YOUR_PROJECT_ID',
};

// Backend API configuration
window.__API_BASE_URL__ = 'https://your-backend-service.run.app';
window.__API_KEY__ = 'REPLACE_WITH_YOUR_API_KEY';

// Note: In production, these values should be injected by your deployment script
// Example deployment script snippet:
// 
// sed -i "s|REPLACE_WITH_YOUR_FIREBASE_API_KEY|${FIREBASE_API_KEY}|g" firebase-config.js
// sed -i "s|REPLACE_WITH_YOUR_PROJECT|${PROJECT_ID}|g" firebase-config.js
// sed -i "s|https://your-backend-service.run.app|${BACKEND_URL}|g" firebase-config.js
// sed -i "s|REPLACE_WITH_YOUR_API_KEY|${API_KEY}|g" firebase-config.js
