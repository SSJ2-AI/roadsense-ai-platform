# RoadSense Mobile App

Flutter mobile application for capturing road images with GPS metadata and uploading to RoadSense backend for pothole detection.

## Features

- 📷 Camera integration with real-time capture
- 📍 GPS location tracking with altitude
- 🔄 Automatic upload to backend API
- 📊 View detection results
- 🔐 API key authentication
- 🎯 Offline queue for network issues
- 🔒 Privacy-first design (optional GPS)

## Prerequisites

- Flutter SDK 3.22+ ([Install Flutter](https://flutter.dev/docs/get-started/install))
- Android Studio / Xcode (for respective platforms)
- Android SDK (for Android builds)
- Physical device or emulator with camera

## Setup

### 1. Install Flutter

```bash
# Verify Flutter installation
flutter doctor

# Accept Android licenses (Android only)
flutter doctor --android-licenses
```

### 2. Install Dependencies

```bash
cd mobile
flutter pub get
```

### 3. Configure Backend API

The app requires backend API URL and API key at build time:

```bash
# Set environment variables
export API_BASE_URL="https://your-cloud-run-url.run.app"
export API_KEY="your-api-key"
```

## Development

### Run on Android

```bash
# List devices
flutter devices

# Run with configuration
flutter run -d android \
  --dart-define=API_BASE_URL=https://your-service-url.run.app \
  --dart-define=API_KEY=your-api-key
```

### Run on iOS

```bash
# Run with configuration
flutter run -d ios \
  --dart-define=API_BASE_URL=https://your-service-url.run.app \
  --dart-define=API_KEY=your-api-key
```

### Hot Reload

While running in debug mode:
- Press `r` to hot reload
- Press `R` to hot restart
- Press `q` to quit

## Building for Production

### Android APK

#### Quick Build

```bash
chmod +x build-android.sh
./build-android.sh production release
```

#### Manual Build

```bash
flutter build apk --release \
  --dart-define=API_BASE_URL=https://your-service-url.run.app \
  --dart-define=API_KEY=your-api-key
```

**Output:** `build/app/outputs/flutter-apk/app-release.apk`

### Android App Bundle (for Google Play)

```bash
flutter build appbundle --release \
  --dart-define=API_BASE_URL=https://your-service-url.run.app \
  --dart-define=API_KEY=your-api-key
```

**Output:** `build/app/outputs/bundle/release/app-release.aab`

### iOS (requires macOS)

```bash
flutter build ios --release \
  --dart-define=API_BASE_URL=https://your-service-url.run.app \
  --dart-define=API_KEY=your-api-key
```

Then archive and upload via Xcode.

## Project Structure

```
mobile/
├── lib/
│   ├── main.dart                 # App entry point
│   ├── models/
│   │   └── detection.dart        # Detection data model
│   ├── screens/
│   │   ├── home_screen.dart      # Home/landing screen
│   │   ├── camera_screen.dart    # Camera capture screen
│   │   └── results_screen.dart   # Detection results display
│   ├── services/
│   │   ├── api_client.dart       # Backend API client
│   │   └── gps_service.dart      # GPS/location service
│   └── widgets/
│       └── detection_card.dart   # Reusable UI components
├── pubspec.yaml                  # Dependencies
├── build-android.sh             # Build script
└── README.md                    # This file
```

## Permissions

### Android (AndroidManifest.xml)

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
```

### iOS (Info.plist)

```xml
<key>NSCameraUsageDescription</key>
<string>Camera access is required to capture road images for pothole detection</string>
<key>NSLocationWhenInUseUsageDescription</key>
<string>Location access helps identify where potholes are detected</string>
```

## Configuration

### Runtime Configuration

The app uses compile-time constants from `--dart-define`:

```dart
// lib/services/api_client.dart
const String apiBaseUrl = String.fromEnvironment('API_BASE_URL');
const String apiKey = String.fromEnvironment('API_KEY');
```

### Build Variants

For multiple environments, create separate build configurations:

```bash
# Development
flutter run --dart-define=API_BASE_URL=https://dev-api.example.com --dart-define=API_KEY=dev-key

# Staging
flutter run --dart-define=API_BASE_URL=https://staging-api.example.com --dart-define=API_KEY=staging-key

# Production
flutter build apk --release --dart-define=API_BASE_URL=https://api.example.com --dart-define=API_KEY=prod-key
```

## Testing

### Unit Tests

```bash
flutter test
```

### Integration Tests

```bash
flutter test integration_test/
```

### Device Testing

1. Connect physical device
2. Enable USB debugging (Android) or Developer mode (iOS)
3. Run: `flutter run`

## Distribution

### Internal Testing

#### Android

```bash
# Install APK on device
adb install build/app/outputs/flutter-apk/app-release.apk
```

#### Firebase App Distribution

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Upload to App Distribution
firebase appdistribution:distribute \
  build/app/outputs/flutter-apk/app-release.apk \
  --app YOUR_FIREBASE_APP_ID \
  --groups testers
```

### Production Release

#### Google Play Store (Android)

1. Build app bundle: `flutter build appbundle --release`
2. Upload to Google Play Console
3. Complete store listing
4. Submit for review

#### Apple App Store (iOS)

1. Build for release: `flutter build ios --release`
2. Open Xcode workspace
3. Archive and upload to App Store Connect
4. Submit for review

## Privacy & Data

### Data Collection

The app collects:
- **Images:** Road surface photos (uploaded to backend)
- **GPS Location:** Latitude, longitude, altitude (optional)
- **Device ID:** Anonymous device identifier
- **Timestamp:** When photo was captured

### User Privacy

- ✅ Location permission is optional
- ✅ No PII (personally identifiable information) collected
- ✅ Images stored securely in GCS with retention policy
- ✅ Compliant with PIPEDA (Canada privacy law)

### Data Retention

- Images retained for 90 days (configurable)
- Location data stored only as lat/lng coordinates
- No user profiles or tracking

## Troubleshooting

### Camera Not Working

- Check permissions in device settings
- Verify `<uses-permission>` in AndroidManifest.xml
- Test on physical device (emulator camera may not work)

### GPS Not Updating

- Enable location services on device
- Grant location permissions to app
- Test outdoors for better GPS signal

### Build Failures

```bash
# Clean build cache
flutter clean
flutter pub get

# Check Flutter installation
flutter doctor -v
```

### API Connection Issues

- Verify backend URL is accessible
- Check API key is correct
- Review network permissions
- Test with HTTPS (not HTTP)

## Performance Optimization

### Image Compression

Images are automatically compressed before upload to reduce bandwidth:

```dart
// Adjust quality (0-100)
final compressedImage = await FlutterImageCompress.compressWithFile(
  imageFile.path,
  quality: 85,
);
```

### Offline Support

Implement local queue for failed uploads:

```dart
// Store failed uploads locally
// Retry when network is available
```

## Production Checklist

- [ ] Backend API URL configured for production
- [ ] API key secured (not hardcoded in version control)
- [ ] App permissions tested and working
- [ ] Camera capture quality optimized
- [ ] GPS accuracy tested in various locations
- [ ] Error handling implemented
- [ ] Offline mode tested
- [ ] Battery usage optimized
- [ ] App icons and branding updated
- [ ] Version number incremented
- [ ] Privacy policy added
- [ ] Store listing completed (Google Play / App Store)
- [ ] Beta testing completed with real users

## Support

For technical issues:
- Check Flutter documentation: https://flutter.dev/docs
- Review device logs: `flutter logs`
- Test API connectivity with curl
- Verify backend is deployed and accessible

## License

See LICENSE file in project root.
