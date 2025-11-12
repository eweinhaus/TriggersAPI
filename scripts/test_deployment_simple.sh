#!/bin/bash
# Simple test script for deployed API
# Tests all endpoints against production deployment

set -e

API_URL="${API_URL:-https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod}"
API_KEY="${API_KEY:-test-api-key-prod-12345}"

echo "🧪 Testing Deployed API: $API_URL"
echo ""

# Test 1: Health Check
echo "✅ Test 1: Health Check"
curl -s "$API_URL/v1/health" | python3 -m json.tool
echo ""

# Test 2: Create Event
echo "✅ Test 2: Create Event"
EVENT_RESPONSE=$(curl -s -X POST "$API_URL/v1/events" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"source":"test-deployment","event_type":"test.deployment","payload":{"test":"deployment"}}')
echo "$EVENT_RESPONSE" | python3 -m json.tool

EVENT_ID=$(echo "$EVENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['event_id'])" 2>/dev/null)
CREATED_AT=$(echo "$EVENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['created_at'])" 2>/dev/null)
echo ""

# Test 3: Get Inbox
echo "✅ Test 3: Get Inbox"
curl -s "$API_URL/v1/inbox?limit=3" -H "X-API-Key: $API_KEY" | python3 -m json.tool | head -20
echo ""

# Test 4: Acknowledge Event (if we have event_id)
if [ -n "$EVENT_ID" ] && [ -n "$CREATED_AT" ]; then
    echo "✅ Test 4: Acknowledge Event"
    curl -s -X POST "$API_URL/v1/events/$EVENT_ID/ack?created_at=$CREATED_AT" \
        -H "X-API-Key: $API_KEY" | python3 -m json.tool
    echo ""
    
    # Test 5: Delete Event
    echo "✅ Test 5: Delete Event"
    curl -s -X DELETE "$API_URL/v1/events/$EVENT_ID" \
        -H "X-API-Key: $API_KEY" | python3 -m json.tool
    echo ""
fi

# Test 6: Invalid API Key
echo "✅ Test 6: Invalid API Key (should return 401)"
curl -s -w "\nHTTP Status: %{http_code}\n" "$API_URL/v1/health" \
    -H "X-API-Key: invalid-key" | tail -5
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All endpoint tests completed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


