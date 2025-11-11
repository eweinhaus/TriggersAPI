#!/bin/bash
# Fix CORS configuration in API Gateway

set -e

REGION="us-east-1"
STAGE="prod"
STACK_NAME="triggers-api"
FUNCTION_NAME="triggers-api-prod"

echo "🔧 Fixing CORS configuration in API Gateway..."

# Get API Gateway ID
API_ID=$(aws apigateway get-rest-apis --region "$REGION" --query "items[?name=='$STACK_NAME'].id" --output text)

if [ -z "$API_ID" ]; then
    echo "❌ API Gateway not found: $STACK_NAME"
    exit 1
fi

echo "✓ Found API Gateway: $API_ID"

# Get root resource ID
ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query 'items[?path==`/`].id' \
    --output text)

# Get /v1 resource ID
V1_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query "items[?path=='/v1'].id" \
    --output text)

# Get /v1/{proxy+} resource ID
PROXY_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query "items[?path=='/v1/{proxy+}'].id" \
    --output text)

echo "✓ Found resources:"
echo "  Root: $ROOT_RESOURCE_ID"
echo "  /v1: $V1_RESOURCE_ID"
echo "  /v1/{proxy+}: $PROXY_RESOURCE_ID"

# Add OPTIONS method to /v1/{proxy+} if it doesn't exist
echo ""
echo "📋 Checking OPTIONS method on /v1/{proxy+}..."

if aws apigateway get-method \
    --rest-api-id "$API_ID" \
    --resource-id "$PROXY_RESOURCE_ID" \
    --http-method OPTIONS \
    --region "$REGION" &>/dev/null; then
    echo "✓ OPTIONS method already exists"
else
    echo "Creating OPTIONS method..."
    
    # Create OPTIONS method
    aws apigateway put-method \
        --rest-api-id "$API_ID" \
        --resource-id "$PROXY_RESOURCE_ID" \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region "$REGION" \
        --output text > /dev/null
    
    # Create mock integration for OPTIONS (returns CORS headers)
    aws apigateway put-integration \
        --rest-api-id "$API_ID" \
        --resource-id "$PROXY_RESOURCE_ID" \
        --http-method OPTIONS \
        --type MOCK \
        --integration-http-method OPTIONS \
        --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
        --region "$REGION" \
        --output text > /dev/null
    
    # Create method response with CORS headers
    aws apigateway put-method-response \
        --rest-api-id "$API_ID" \
        --resource-id "$PROXY_RESOURCE_ID" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Headers": true,
            "method.response.header.Access-Control-Allow-Methods": true,
            "method.response.header.Access-Control-Allow-Origin": true
        }' \
        --region "$REGION" \
        --output text > /dev/null
    
    # Create integration response
    aws apigateway put-integration-response \
        --rest-api-id "$API_ID" \
        --resource-id "$PROXY_RESOURCE_ID" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-API-Key,X-Request-ID'\''",
            "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,DELETE,OPTIONS'\''",
            "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
        }' \
        --region "$REGION" \
        --output text > /dev/null
    
    echo "✓ OPTIONS method created with CORS headers"
fi

# Also add OPTIONS to /v1 if it doesn't exist
echo ""
echo "📋 Checking OPTIONS method on /v1..."

if aws apigateway get-method \
    --rest-api-id "$API_ID" \
    --resource-id "$V1_RESOURCE_ID" \
    --http-method OPTIONS \
    --region "$REGION" &>/dev/null; then
    echo "✓ OPTIONS method already exists on /v1"
else
    echo "Creating OPTIONS method on /v1..."
    
    aws apigateway put-method \
        --rest-api-id "$API_ID" \
        --resource-id "$V1_RESOURCE_ID" \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region "$REGION" \
        --output text > /dev/null
    
    aws apigateway put-integration \
        --rest-api-id "$API_ID" \
        --resource-id "$V1_RESOURCE_ID" \
        --http-method OPTIONS \
        --type MOCK \
        --integration-http-method OPTIONS \
        --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
        --region "$REGION" \
        --output text > /dev/null
    
    aws apigateway put-method-response \
        --rest-api-id "$API_ID" \
        --resource-id "$V1_RESOURCE_ID" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Headers": true,
            "method.response.header.Access-Control-Allow-Methods": true,
            "method.response.header.Access-Control-Allow-Origin": true
        }' \
        --region "$REGION" \
        --output text > /dev/null
    
    aws apigateway put-integration-response \
        --rest-api-id "$API_ID" \
        --resource-id "$V1_RESOURCE_ID" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-API-Key,X-Request-ID'\''",
            "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,DELETE,OPTIONS'\''",
            "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
        }' \
        --region "$REGION" \
        --output text > /dev/null
    
    echo "✓ OPTIONS method created on /v1"
fi

# Deploy API
echo ""
echo "🚀 Deploying API..."
aws apigateway create-deployment \
    --rest-api-id "$API_ID" \
    --stage-name "$STAGE" \
    --description "CORS fix deployment $(date +%Y-%m-%d-%H-%M-%S)" \
    --region "$REGION" \
    --output text > /dev/null

echo ""
echo "✅ CORS configuration updated!"
echo ""
echo "📡 API URL: https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}"
echo ""
echo "🧪 Test CORS with:"
echo "   curl -X OPTIONS https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/v1/health \\"
echo "     -H 'Origin: http://triggers-api-frontend-971422717446.s3-website-us-east-1.amazonaws.com' \\"
echo "     -H 'Access-Control-Request-Method: GET' \\"
echo "     -v"

