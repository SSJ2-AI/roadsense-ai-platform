#!/bin/bash
# Build RoadSense Mobile App for Android
# Usage: ./build-android.sh [environment]
#
# Prerequisites:
# - Flutter SDK installed (3.22+)
# - Android SDK and tools configured
# - Android device/emulator connected (for debug builds)

set -e

# Configuration
ENVIRONMENT="${1:-production}"
BUILD_TYPE="${2:-release}"  # release or debug

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}RoadSense Mobile App - Android Build${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Environment: ${ENVIRONMENT}"
echo "Build Type: ${BUILD_TYPE}"
echo ""

# Verify prerequisites
echo -e "${YELLOW}Verifying prerequisites...${NC}"

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo -e "${RED}ERROR: Flutter not found. Install from https://flutter.dev/docs/get-started/install${NC}"
    exit 1
fi

# Check Flutter version
FLUTTER_VERSION=$(flutter --version | head -n 1)
echo "Flutter: ${FLUTTER_VERSION}"

# Verify Android toolchain
echo -e "${YELLOW}Verifying Android toolchain...${NC}"
if ! flutter doctor --android-licenses &> /dev/null; then
    echo -e "${YELLOW}WARNING: Android licenses may need to be accepted.${NC}"
    echo "Run: flutter doctor --android-licenses"
fi

echo -e "${GREEN}Prerequisites verified!${NC}"
echo ""

# Prompt for configuration
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Build Configuration${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

read -p "Backend API URL (Cloud Run service URL): " API_BASE_URL
if [ -z "$API_BASE_URL" ]; then
    echo -e "${RED}ERROR: Backend API URL is required${NC}"
    exit 1
fi

read -p "API Key (from backend deployment): " API_KEY
if [ -z "$API_KEY" ]; then
    echo -e "${RED}ERROR: API Key is required${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Configuration complete!${NC}"
echo ""

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
flutter clean

# Get dependencies
echo -e "${YELLOW}Getting dependencies...${NC}"
flutter pub get

echo ""

# Run build
echo -e "${YELLOW}Building Android APK...${NC}"
echo "This may take several minutes..."
echo ""

BUILD_ARGS="--dart-define=API_BASE_URL=${API_BASE_URL} --dart-define=API_KEY=${API_KEY}"

if [ "$BUILD_TYPE" = "release" ]; then
    flutter build apk --release ${BUILD_ARGS}
    OUTPUT_PATH="build/app/outputs/flutter-apk/app-release.apk"
else
    flutter build apk --debug ${BUILD_ARGS}
    OUTPUT_PATH="build/app/outputs/flutter-apk/app-debug.apk"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verify APK exists
if [ ! -f "${OUTPUT_PATH}" ]; then
    echo -e "${RED}ERROR: APK not found at ${OUTPUT_PATH}${NC}"
    exit 1
fi

# Get APK size
APK_SIZE=$(du -h "${OUTPUT_PATH}" | cut -f1)

echo "APK Location: ${OUTPUT_PATH}"
echo "APK Size: ${APK_SIZE}"
echo ""

# Generate QR code for easy download (optional)
if command -v qrencode &> /dev/null; then
    echo -e "${YELLOW}Generating QR code for APK download...${NC}"
    # This would require hosting the APK somewhere accessible
    echo "(QR code generation requires hosted APK URL)"
    echo ""
fi

echo -e "${YELLOW}Next steps:${NC}"
echo ""

if [ "$BUILD_TYPE" = "debug" ]; then
    echo "1. Install on device: adb install ${OUTPUT_PATH}"
    echo "2. Or drag and drop APK to Android emulator"
    echo "3. Test camera permissions and GPS functionality"
    echo "4. Test image upload to backend"
else
    echo "1. Sign the APK for production release (or build app bundle)"
    echo "   flutter build appbundle --release ${BUILD_ARGS}"
    echo "2. Upload to Google Play Console for testing/release"
    echo "3. For internal testing:"
    echo "   - Install: adb install ${OUTPUT_PATH}"
    echo "   - Test all features with real devices"
    echo "4. Set up Firebase App Distribution for beta testing"
fi

echo ""
echo -e "${GREEN}Build successful! 🎉${NC}"
echo ""

# Optional: Build app bundle for Google Play
read -p "Build App Bundle (AAB) for Google Play Store? (y/N): " BUILD_AAB
if [ "$BUILD_AAB" = "y" ] || [ "$BUILD_AAB" = "Y" ]; then
    echo ""
    echo -e "${YELLOW}Building Android App Bundle...${NC}"
    flutter build appbundle --release ${BUILD_ARGS}
    AAB_PATH="build/app/outputs/bundle/release/app-release.aab"
    AAB_SIZE=$(du -h "${AAB_PATH}" | cut -f1)
    echo ""
    echo "App Bundle Location: ${AAB_PATH}"
    echo "App Bundle Size: ${AAB_SIZE}"
    echo ""
    echo "Upload this AAB to Google Play Console for production release."
    echo ""
fi
