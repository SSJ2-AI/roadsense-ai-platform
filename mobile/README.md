# RoadSense Mobile App

Flutter app to capture road images, attach GPS metadata, and upload to the RoadSense backend.

Setup:
- Install Flutter 3.22+ and Android/iOS toolchains
- `flutter pub get`
- Configure API endpoint via `--dart-define=API_BASE_URL=https://<cloud-run-url>` and `--dart-define=API_KEY=<key>`

Run:
- Android: `flutter run -d android --dart-define=API_BASE_URL=... --dart-define=API_KEY=...`
- iOS: `flutter run -d ios --dart-define=API_BASE_URL=... --dart-define=API_KEY=...`

Privacy:
- Location is optional; users can disable permissions. No PII collected.
