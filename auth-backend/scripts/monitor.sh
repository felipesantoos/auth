#!/bin/bash
# Monitoring and Health Check Script
# Tests various health check and monitoring endpoints

set -e

# Configuration
BASE_URL="${API_URL:-http://localhost:8000}"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================="
echo "Auth System - Health & Monitoring Check"
echo "======================================="
echo "Base URL: $BASE_URL"
echo ""

# Function to check endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Checking $name... "
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "ERROR")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $http_code)"
        if [ -n "$body" ]; then
            echo "  Response: $(echo $body | head -c 100)..."
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        if [ "$http_code" != "ERROR" ]; then
            echo "  Response: $body"
        fi
        return 1
    fi
    
    echo ""
}

# Basic health check
check_endpoint "Basic Health" "$BASE_URL/health"

# Readiness check
check_endpoint "Readiness Check" "$BASE_URL/health/ready"

# Liveness check
check_endpoint "Liveness Check" "$BASE_URL/health/live"

# Prometheus metrics
check_endpoint "Prometheus Metrics" "$BASE_URL/metrics"

# WebSocket stats (may require auth)
echo -n "Checking WebSocket Stats... "
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/ws/stats" 2>/dev/null || echo "ERROR")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" = "200" ] || [ "$http_code" = "401" ] || [ "$http_code" = "403" ]; then
    echo -e "${GREEN}✓ OK${NC} (HTTP $http_code - endpoint exists)"
else
    echo -e "${YELLOW}⚠ WARNING${NC} (HTTP $http_code)"
fi
echo ""

# API Documentation
echo -n "Checking API Docs... "
docs_response=$(curl -s -w "\n%{http_code}" "$BASE_URL/docs" 2>/dev/null || echo "ERROR")
docs_http_code=$(echo "$docs_response" | tail -n1)

if [ "$docs_http_code" = "200" ] || [ "$docs_http_code" = "404" ]; then
    echo -e "${GREEN}✓ OK${NC} (HTTP $docs_http_code)"
else
    echo -e "${YELLOW}⚠ WARNING${NC} (HTTP $docs_http_code)"
fi
echo ""

echo "======================================="
echo "Summary"
echo "======================================="
echo "All critical endpoints are responding"
echo "System appears to be healthy"
echo ""

