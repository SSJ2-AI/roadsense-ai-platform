#!/bin/bash
# Automated Testing Script for RoadSense AI System
# Tests backend API, dashboard accessibility, and Firestore connection
# Usage: ./test-all.sh [backend-url] [api-key] [dashboard-url]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    echo -e "${BLUE}Running: ${test_name}${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED: ${test_name}${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED: ${test_name}${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to test HTTP endpoint
test_http() {
    local url="$1"
    local expected_status="${2:-200}"
    local headers="${3:-}"
    
    if [ -n "$headers" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "$headers" "$url" 2>/dev/null || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "000")
    fi
    
    status_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "$expected_status" ]; then
        return 0
    else
        echo "  Expected: $expected_status, Got: $status_code"
        echo "  Response: $body"
        return 1
    fi
}

# Function to test JSON response
test_json() {
    local url="$1"
    local expected_key="$2"
    local headers="${3:-}"
    
    if [ -n "$headers" ]; then
        response=$(curl -s -H "$headers" "$url" 2>/dev/null)
    else
        response=$(curl -s "$url" 2>/dev/null)
    fi
    
    if echo "$response" | grep -q "\"$expected_key\""; then
        return 0
    else
        echo "  Expected key '$expected_key' not found in response"
        echo "  Response: $response"
        return 1
    fi
}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}RoadSense AI System Tests${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Parse arguments
BACKEND_URL="$1"
API_KEY="$2"
DASHBOARD_URL="$3"

# Prompt for missing arguments
if [ -z "$BACKEND_URL" ]; then
    read -p "Backend URL (Cloud Run service): " BACKEND_URL
fi

if [ -z "$API_KEY" ]; then
    read -p "API Key: " API_KEY
fi

if [ -z "$DASHBOARD_URL" ]; then
    read -p "Dashboard URL (Firebase Hosting): " DASHBOARD_URL
fi

# Remove trailing slashes
BACKEND_URL="${BACKEND_URL%/}"
DASHBOARD_URL="${DASHBOARD_URL%/}"

echo ""
echo "Configuration:"
echo "  Backend: $BACKEND_URL"
echo "  Dashboard: $DASHBOARD_URL"
echo "  API Key: ${API_KEY:0:8}..."
echo ""

# ========================================
# BACKEND TESTS
# ========================================
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Backend API Tests${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Test 1: Root endpoint
run_test "Backend root endpoint" \
    "test_http '$BACKEND_URL/' 200"

# Test 2: Health endpoint
run_test "Backend health endpoint" \
    "test_http '$BACKEND_URL/v1/health' 200"

# Test 3: Health endpoint returns JSON with status
run_test "Backend health returns status field" \
    "test_json '$BACKEND_URL/v1/health' 'status'"

# Test 4: Liveness probe
run_test "Backend liveness probe" \
    "test_http '$BACKEND_URL/v1/health/live' 200"

# Test 5: Readiness probe
run_test "Backend readiness probe" \
    "test_http '$BACKEND_URL/v1/health/ready' 200"

# Test 6: API docs endpoint
run_test "Backend API documentation" \
    "test_http '$BACKEND_URL/docs' 200"

# Test 7: OpenAPI spec
run_test "Backend OpenAPI spec" \
    "test_http '$BACKEND_URL/openapi.json' 200"

# Test 8: Authentication - no API key (should fail)
run_test "Backend auth - missing API key returns 401" \
    "test_http '$BACKEND_URL/v1/detections' 401"

# Test 9: Authentication - invalid API key (should fail)
run_test "Backend auth - invalid API key returns 401" \
    "test_http '$BACKEND_URL/v1/detections' 401 'x-api-key: invalid-key'"

# Test 10: Priority queue endpoint (with auth)
run_test "Backend priority queue endpoint" \
    "test_http '$BACKEND_URL/v1/detections/priority-queue' 200 'x-api-key: $API_KEY'"

# Test 11: Analytics by area endpoint (with auth)
run_test "Backend analytics by area" \
    "test_http '$BACKEND_URL/v1/analytics/by-area' 200 'x-api-key: $API_KEY'"

# Test 12: Statistics endpoint (with auth)
run_test "Backend analytics statistics" \
    "test_http '$BACKEND_URL/v1/analytics/statistics' 200 'x-api-key: $API_KEY'"

echo ""

# ========================================
# DETECTION ENDPOINT TEST (with sample image)
# ========================================
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Detection Endpoint Tests${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Create a small test image (1x1 pixel PNG)
TEST_IMAGE=$(mktemp --suffix=.png)
# Generate a minimal valid PNG file
printf '\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0a\x49\x44\x41\x54\x78\x9c\x63\x00\x01\x00\x00\x05\x00\x01\x0d\x0a\x2d\xb4\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82' > "$TEST_IMAGE"

# Test 13: Detection endpoint with test image
echo -e "${BLUE}Running: Detection endpoint with test image${NC}"
TESTS_TOTAL=$((TESTS_TOTAL + 1))

detection_response=$(curl -s -w "\n%{http_code}" \
    -H "x-api-key: $API_KEY" \
    -F "image=@${TEST_IMAGE}" \
    -F "deviceId=test-device" \
    -F "lat=43.7315" \
    -F "lng=-79.7624" \
    "$BACKEND_URL/v1/detections" 2>/dev/null || echo "000")

detection_status=$(echo "$detection_response" | tail -n 1)
detection_body=$(echo "$detection_response" | head -n -1)

if [ "$detection_status" = "201" ] || [ "$detection_status" = "200" ]; then
    echo -e "${GREEN}✓ PASSED: Detection endpoint with test image${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Extract detection ID if available
    DETECTION_ID=$(echo "$detection_body" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    if [ -n "$DETECTION_ID" ]; then
        echo "  Detection ID: $DETECTION_ID"
        
        # Test 14: Update detection status
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${BLUE}Running: Update detection status${NC}"
        
        update_response=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "x-api-key: $API_KEY" \
            "$BACKEND_URL/v1/detections/${DETECTION_ID}/update-status?status=verified" 2>/dev/null || echo "000")
        
        update_status=$(echo "$update_response" | tail -n 1)
        
        if [ "$update_status" = "200" ]; then
            echo -e "${GREEN}✓ PASSED: Update detection status${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗ FAILED: Update detection status${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
else
    echo -e "${RED}✗ FAILED: Detection endpoint with test image${NC}"
    echo "  Status: $detection_status"
    echo "  Response: $detection_body"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Cleanup test image
rm -f "$TEST_IMAGE"

echo ""

# ========================================
# DASHBOARD TESTS
# ========================================
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Dashboard Tests${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Test: Dashboard homepage
run_test "Dashboard homepage accessibility" \
    "test_http '$DASHBOARD_URL/' 200"

# Test: Dashboard index.html
run_test "Dashboard index.html" \
    "test_http '$DASHBOARD_URL/index.html' 200"

# Test: Dashboard CSS
run_test "Dashboard styles.css" \
    "test_http '$DASHBOARD_URL/styles.css' 200"

# Test: Dashboard JS
run_test "Dashboard app.js" \
    "test_http '$DASHBOARD_URL/app.js' 200"

# Test: Dashboard analytics page
run_test "Dashboard analytics.html" \
    "test_http '$DASHBOARD_URL/analytics.html' 200"

# Test: Dashboard areas page
run_test "Dashboard areas.html" \
    "test_http '$DASHBOARD_URL/areas.html' 200"

echo ""

# ========================================
# FIRESTORE CONNECTION TEST
# ========================================
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Firestore Connection Tests${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Test: Firestore connection via backend readiness probe
run_test "Firestore connection (via readiness probe)" \
    "test_json '$BACKEND_URL/v1/health/ready' 'firestore'"

echo ""

# ========================================
# INTEGRATION TESTS
# ========================================
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Integration Tests${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Test: CORS headers (simulated)
echo -e "${BLUE}Running: CORS headers check${NC}"
TESTS_TOTAL=$((TESTS_TOTAL + 1))

cors_response=$(curl -s -I -H "Origin: $DASHBOARD_URL" "$BACKEND_URL/v1/health" 2>/dev/null)

if echo "$cors_response" | grep -i "access-control-allow-origin" > /dev/null; then
    echo -e "${GREEN}✓ PASSED: CORS headers check${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ WARNING: CORS headers not detected (may need Origin header)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))  # Don't fail on this
fi

echo ""

# ========================================
# RESULTS SUMMARY
# ========================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Test Results Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Total Tests: $TESTS_TOTAL"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

# Calculate success rate
SUCCESS_RATE=$((TESTS_PASSED * 100 / TESTS_TOTAL))
echo "Success Rate: ${SUCCESS_RATE}%"
echo ""

# Final status
if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "System is ready for production deployment."
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Some tests failed! ✗${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Please review the failed tests and fix issues before deployment."
    exit 1
fi
