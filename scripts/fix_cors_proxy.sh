#!/bin/bash
# Fix CORS by ensuring Lambda handles OPTIONS via AWS_PROXY
# Remove any conflicting MOCK OPTIONS methods

set -e

REGION="us-east-1"
STAGE="prod"
STACK_NAME="triggers-api"

echo "🔧 Fixing CORS - Ensuring Lambda handles OPTIONS via AWS_PROXY..."

# Get API Gateway ID
API_ID=$(aws apigateway get-rest-apis --region "$REGION" --query "items[?name=='$STACK_NAME'].id" --output text)

if [ -z "$API_ID" ]; then
    echo "❌ API Gateway not found: $STACK_NAME"
    exit 1
fi

echo "✓ Found API Gateway: $API_ID"

# Get /v1/{proxy+} resource ID
PROXY_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query "items[?path=='/v1/{proxy+}'].id" \
    --output text)

echo "✓ Found /v1/{proxy+} resource: $PROXY_RESOURCE_ID"

# Check if OPTIONS method exists and what integration it uses
echo ""
echo "📋 Checking OPTIONS method..."

OPTIONS_METHOD=$(aws apigateway get-method \
    --rest-api-id "$API_ID" \
    --resource-id "$PROXY_RESOURCE_ID" \
    --http-method OPTIONS \
    --region "$REGION" 2>/dev/null || echo "")

if [ -n "$OPTIONS_METHOD" ]; then
    INTEGRATION_TYPE=$(echo "$OPTIONS_METHOD" | grep -o '"type":"[^"]*"' | cut -d'"' -f4 || echo "")
    
    if [ "$INTEGRATION_TYPE" = "MOCK" ]; then
        echo "⚠ Found MOCK OPTIONS method - removing it (Lambda will handle via AWS_PROXY)..."
        aws apigateway delete-method \
            --rest-api-id "$API_ID" \
            --resource-id "$PROXY_RESOURCE_ID" \
            --http-method OPTIONS \
            --region "$REGION" \
            --output text > /dev/null
        echo "✓ Removed MOCK OPTIONS method"
    else
        echo "✓ OPTIONS method uses $INTEGRATION_TYPE integration (should be AWS_PROXY via ANY)"
    fi
else
    echo "✓ No separate OPTIONS method (will use ANY method with AWS_PROXY)"
fi

# Verify ANY method uses AWS_PROXY
echo ""
echo "📋 Verifying ANY method uses AWS_PROXY..."
ANY_METHOD=$(aws apigateway get-method \
    --rest-api-id "$API_ID" \
    --resource-id "$PROXY_RESOURCE_ID" \
    --http-method ANY \
    --region "$REGION" 2>/dev/null)

if [ -n "$ANY_METHOD" ]; then
    INTEGRATION=$(aws apigateway get-integration \
        --rest-api-id "$API_ID" \
        --resource-id "$PROXY_RESOURCE_ID" \
        --http-method ANY \
        --region "$REGION" 2>/dev/null)
    
    INTEGRATION_TYPE=$(echo "$INTEGRATION" | grep -o '"type":"[^"]*"' | cut -d'"' -f4 || echo "")
    
    if [ "$INTEGRATION_TYPE" = "AWS_PROXY" ]; then
        echo "✓ ANY method uses AWS_PROXY - OPTIONS requests will reach Lambda"
    else
        echo "⚠ ANY method uses $INTEGRATION_TYPE (expected AWS_PROXY)"
    fi
else
    echo "❌ ANY method not found!"
    exit 1
fi

# Deploy API
echo ""
echo "🚀 Deploying API..."
aws apigateway create-deployment \
    --rest-api-id "$API_ID" \
    --stage-name "$STAGE" \
    --description "CORS fix - Lambda handles OPTIONS $(date +%Y-%m-%d-%H-%M-%S)" \
    --region "$REGION" \
    --output text > /dev/null

echo ""
echo "✅ CORS configuration updated!"
echo ""
echo "📝 Note: FastAPI CORS middleware should handle OPTIONS requests."
echo "   If issues persist, check Lambda logs for OPTIONS request handling."
echo ""
echo "🧪 Test with:"
echo "   curl -X OPTIONS https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/v1/health \\"
echo "     -H 'Origin: http://triggers-api-frontend-971422717446.s3-website-us-east-1.amazonaws.com' \\"
echo "     -H 'Access-Control-Request-Method: GET' \\"
echo "     -v"

