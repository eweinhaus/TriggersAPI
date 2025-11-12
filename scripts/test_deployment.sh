#!/bin/bash
# Test script for deployed API
# Tests all endpoints against production deployment

set -e

API_URL="${API_URL:-https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod}"
API_KEY="${API_KEY:-test-api-key-prod-12345}"

echo "🧪 Testing Deployed API: $API_URL"
echo "🔑 Using API Key: ${API_KEY:0:10}..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_count=0
pass_count=0
fail_count=0

test_endpoint() {
    local name=$1
    local method=$2
    local path=$3
    local data=$4
    local expected_status=$5
    
    test_count=$((test_count + 1))
    echo -n "Test $test_count: $name ... "
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            "$API_URL$path" \
            -H "Content-Type: application/json" \
            -H "X-API-Key: $API_KEY" \
            -d "$data" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            "$API_URL$path" \
            -H "X-API-Key: $API_KEY" 2>&1)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        pass_count=$((pass_count + 1))
        
        # Check for request_id in response
        if echo "$body" | grep -q "request_id"; then
            echo "  ✓ Request ID present"
        fi
        
        echo "$body" | python3 -m json.tool 2>/dev/null | head -10 || echo "$body"
        echo ""
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected HTTP $expected_status, got $http_code)"
        fail_count=$((fail_count + 1))
        echo "Response: $body"
        echo ""
        return 1
    fi
}

# Test 1: Health Check
test_endpoint "Health Check" "GET" "/v1/health" "" "200"

# Test 2: Create Event
EVENT_DATA='{"source":"test-deployment","event_type":"test.deployment","payload":{"test":"deployment","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}}'
test_endpoint "Create Event" "POST" "/v1/events" "$EVENT_DATA" "201"

# Extract event_id from previous response
EVENT_ID=$(curl -s -X POST "$API_URL/v1/events" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "$EVENT_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['event_id'])" 2>/dev/null)

if [ -n "$EVENT_ID" ]; then
    echo "  ✓ Created event with ID: $EVENT_ID"
    echo ""
    
    # Test 3: Get Inbox
    test_endpoint "Get Inbox" "GET" "/v1/inbox?limit=5" "" "200"
    
    # Test 4: Acknowledge Event
    test_endpoint "Acknowledge Event" "POST" "/v1/events/$EVENT_ID/ack" "" "200"
    
    # Test 5: Try to acknowledge again (should fail)
    test_endpoint "Acknowledge Already Acknowledged" "POST" "/v1/events/$EVENT_ID/ack" "" "409"
    
    # Test 6: Delete Event
    test_endpoint "Delete Event" "DELETE" "/v1/events/$EVENT_ID" "" "200"
    
    # Test 7: Delete again (idempotent)
    test_endpoint "Delete Event (Idempotent)" "DELETE" "/v1/events/$EVENT_ID" "" "200"
else
    echo -e "${YELLOW}⚠ Could not extract event_id, skipping dependent tests${NC}"
    fail_count=$((fail_count + 1))
fi

# Test 8: Invalid API Key
test_endpoint "Invalid API Key" "GET" "/v1/health" "" "401" <<< "X-API-Key: invalid-key"

# Test 9: Missing API Key
response=$(curl -s -w "\n%{http_code}" "$API_URL/v1/health" 2>&1)
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "401" ]; then
    echo -e "Test 9: Missing API Key ... ${GREEN}✓ PASS${NC} (HTTP 401)"
    pass_count=$((pass_count + 1))
else
    echo -e "Test 9: Missing API Key ... ${RED}✗ FAIL${NC} (Expected HTTP 401, got $http_code)"
    fail_count=$((fail_count + 1))
fi
test_count=$((test_count + 1))
echo ""

# Test 10: Invalid Event Data
INVALID_DATA='{"source":"test","invalid_field":"should_fail"}'
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/v1/events" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "$INVALID_DATA" 2>&1)
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "422" ]; then
    echo -e "Test 10: Invalid Event Data ... ${GREEN}✓ PASS${NC} (HTTP 422)"
    pass_count=$((pass_count + 1))
else
    echo -e "Test 10: Invalid Event Data ... ${RED}✗ FAIL${NC} (Expected HTTP 422, got $http_code)"
    fail_count=$((fail_count + 1))
fi
test_count=$((test_count + 1))
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary:"
echo "   Total Tests: $test_count"
echo -e "   ${GREEN}Passed: $pass_count${NC}"
echo -e "   ${RED}Failed: $fail_count${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi


