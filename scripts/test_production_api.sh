#!/bin/bash
# Test production API with correct API key

API_URL="https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod"
API_KEY="test-api-key-prod-12345"

echo "🧪 Testing Production API"
echo "URL: $API_URL"
echo "API Key: ${API_KEY:0:12}..."
echo ""

echo "1. Testing health endpoint (no auth required):"
curl -s "$API_URL/v1/health" | python3 -m json.tool
echo ""

echo "2. Testing events endpoint with API key:"
curl -s -X POST "$API_URL/v1/events" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "source": "test",
    "event_type": "test.event",
    "payload": {"test": "data"}
  }' | python3 -m json.tool

echo ""
echo "✅ If you see an event ID above, API key authentication is working!"
echo "❌ If you see an 'Invalid API key' error, check:"
echo "   1. API key exists in DynamoDB: triggers-api-keys-prod"
echo "   2. Lambda environment variables are set correctly"
echo "   3. IAM role has DynamoDB GetItem permission"

