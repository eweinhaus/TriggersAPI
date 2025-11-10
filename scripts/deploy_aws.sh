#!/bin/bash
# AWS Deployment Script for Triggers API
# This script deploys the API to AWS using AWS CLI
#
# Prerequisites:
# - Docker (for building Lambda package with correct architecture)
# - AWS CLI configured with appropriate credentials
# - IAM permissions for Lambda, API Gateway, DynamoDB, IAM, CloudWatch

set -e

REGION="us-east-1"
STAGE="prod"
STACK_NAME="triggers-api"
FUNCTION_NAME="triggers-api-prod"
EVENTS_TABLE="triggers-api-events-prod"
API_KEYS_TABLE="triggers-api-keys-prod"
ROLE_NAME="triggers-api-lambda-role"

echo "🚀 Starting AWS deployment..."

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
echo "📋 AWS Account: $ACCOUNT_ID"
echo "🌍 Region: $REGION"

# Step 1: Create IAM Role for Lambda
echo ""
echo "1️⃣ Creating IAM Role..."
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

# Check if role exists
if aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
    echo "   ✓ Role already exists: $ROLE_NAME"
else
    echo "   Creating role: $ROLE_NAME"
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' \
        --output text
    
    # Attach basic Lambda execution policy
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    # Create and attach custom policy for DynamoDB
    POLICY_DOC=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query"
            ],
            "Resource": [
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${EVENTS_TABLE}",
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${EVENTS_TABLE}/index/status-created_at-index",
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${API_KEYS_TABLE}"
            ]
        }
    ]
}
EOF
)
    
    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "TriggersApiDynamoDBPolicy" \
        --policy-document "$POLICY_DOC"
    
    echo "   ✓ Role created: $ROLE_NAME"
    echo "   ⏳ Waiting for role to be ready..."
    sleep 10
fi

# Step 2: Create DynamoDB Tables
echo ""
echo "2️⃣ Creating DynamoDB Tables..."

# Events Table
if aws dynamodb describe-table --table-name "$EVENTS_TABLE" --region "$REGION" &>/dev/null; then
    echo "   ✓ Events table already exists: $EVENTS_TABLE"
else
    echo "   Creating Events table: $EVENTS_TABLE"
    aws dynamodb create-table \
        --table-name "$EVENTS_TABLE" \
        --attribute-definitions \
            AttributeName=event_id,AttributeType=S \
            AttributeName=created_at,AttributeType=S \
            AttributeName=status,AttributeType=S \
        --key-schema \
            AttributeName=event_id,KeyType=HASH \
            AttributeName=created_at,KeyType=RANGE \
        --global-secondary-indexes \
            "[{
                \"IndexName\": \"status-created_at-index\",
                \"KeySchema\": [
                    {\"AttributeName\": \"status\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"created_at\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            }]" \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --output text
    
    echo "   ⏳ Waiting for Events table to be active..."
    aws dynamodb wait table-exists --table-name "$EVENTS_TABLE" --region "$REGION"
    
    # Enable TTL after table is active
    echo "   Enabling TTL on Events table..."
    aws dynamodb update-time-to-live \
        --table-name "$EVENTS_TABLE" \
        --time-to-live-specification Enabled=true,AttributeName=ttl \
        --region "$REGION" \
        --output text > /dev/null
    
    echo "   ✓ Events table created"
fi

# API Keys Table
if aws dynamodb describe-table --table-name "$API_KEYS_TABLE" --region "$REGION" &>/dev/null; then
    echo "   ✓ API Keys table already exists: $API_KEYS_TABLE"
else
    echo "   Creating API Keys table: $API_KEYS_TABLE"
    aws dynamodb create-table \
        --table-name "$API_KEYS_TABLE" \
        --attribute-definitions AttributeName=api_key,AttributeType=S \
        --key-schema AttributeName=api_key,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --output text
    
    echo "   ⏳ Waiting for API Keys table to be active..."
    aws dynamodb wait table-exists --table-name "$API_KEYS_TABLE" --region "$REGION"
    echo "   ✓ API Keys table created"
fi

# Step 3: Create Lambda Function
echo ""
echo "3️⃣ Creating Lambda Function..."

if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &>/dev/null; then
    echo "   ✓ Function already exists, updating code..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb://lambda-deployment.zip \
        --region "$REGION" \
        --output text > /dev/null
    
    echo "   ⏳ Waiting for function update..."
    aws lambda wait function-updated --function-name "$FUNCTION_NAME" --region "$REGION"
    echo "   ✓ Function code updated"
else
    echo "   Creating Lambda function: $FUNCTION_NAME"
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime python3.11 \
        --role "$ROLE_ARN" \
        --handler src.main.handler \
        --zip-file fileb://lambda-deployment.zip \
        --timeout 30 \
        --memory-size 512 \
        --environment "Variables={
            STAGE=$STAGE,
            DYNAMODB_TABLE_EVENTS=$EVENTS_TABLE,
            DYNAMODB_TABLE_KEYS=$API_KEYS_TABLE,
            AUTH_MODE=aws,
            LOG_LEVEL=INFO
        }" \
        --region "$REGION" \
        --output text
    
    echo "   ⏳ Waiting for function to be ready..."
    aws lambda wait function-active --function-name "$FUNCTION_NAME" --region "$REGION"
    echo "   ✓ Lambda function created"
fi

# Step 4: Create API Gateway
echo ""
echo "4️⃣ Creating API Gateway..."

# Check if API Gateway already exists
API_ID=$(aws apigateway get-rest-apis --region "$REGION" --query "items[?name=='$STACK_NAME'].id" --output text)

if [ -z "$API_ID" ]; then
    echo "   Creating REST API: $STACK_NAME"
    API_ID=$(aws apigateway create-rest-api \
        --name "$STACK_NAME" \
        --description "Zapier Triggers API" \
        --endpoint-configuration types=REGIONAL \
        --region "$REGION" \
        --query 'id' \
        --output text)
    echo "   ✓ API Gateway created: $API_ID"
else
    echo "   ✓ API Gateway already exists: $API_ID"
fi

# Get root resource ID
ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query 'items[?path==`/`].id' \
    --output text)

# Create /v1 resource if it doesn't exist
V1_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query "items[?path=='/v1'].id" \
    --output text)

if [ -z "$V1_RESOURCE_ID" ]; then
    echo "   Creating /v1 resource..."
    V1_RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id "$API_ID" \
        --parent-id "$ROOT_RESOURCE_ID" \
        --path-part "v1" \
        --region "$REGION" \
        --query 'id' \
        --output text)
    echo "   ✓ /v1 resource created"
else
    echo "   ✓ /v1 resource already exists"
fi

# Create proxy resource {proxy+}
PROXY_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query "items[?path=='/v1/{proxy+}'].id" \
    --output text)

if [ -z "$PROXY_RESOURCE_ID" ]; then
    echo "   Creating /v1/{proxy+} resource..."
    PROXY_RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id "$API_ID" \
        --parent-id "$V1_RESOURCE_ID" \
        --path-part "{proxy+}" \
        --region "$REGION" \
        --query 'id' \
        --output text)
    echo "   ✓ /v1/{proxy+} resource created"
else
    echo "   ✓ /v1/{proxy+} resource already exists"
fi

# Create ANY method for proxy
echo "   Setting up ANY method for proxy..."
LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${FUNCTION_NAME}"

# Check if method exists
if aws apigateway get-method \
    --rest-api-id "$API_ID" \
    --resource-id "$PROXY_RESOURCE_ID" \
    --http-method ANY \
    --region "$REGION" &>/dev/null; then
    echo "   ✓ ANY method already exists"
else
    aws apigateway put-method \
        --rest-api-id "$API_ID" \
        --resource-id "$PROXY_RESOURCE_ID" \
        --http-method ANY \
        --authorization-type NONE \
        --region "$REGION" \
        --output text > /dev/null
    
    # Set up Lambda integration
    aws apigateway put-integration \
        --rest-api-id "$API_ID" \
        --resource-id "$PROXY_RESOURCE_ID" \
        --http-method ANY \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
        --region "$REGION" \
        --output text > /dev/null
    
    echo "   ✓ ANY method and Lambda integration configured"
fi

# Grant API Gateway permission to invoke Lambda
echo "   Granting API Gateway permission to invoke Lambda..."
STATEMENT_ID="apigateway-invoke-$(date +%s)"
aws lambda add-permission \
    --function-name "$FUNCTION_NAME" \
    --statement-id "$STATEMENT_ID" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/*" \
    --region "$REGION" \
    --output text > /dev/null 2>&1 || echo "   (Permission may already exist)"

# Enable CORS - FastAPI will handle CORS, but we can add OPTIONS method for preflight
echo "   CORS will be handled by FastAPI application"

# Deploy API
echo "   Deploying API to stage: $STAGE"
aws apigateway create-deployment \
    --rest-api-id "$API_ID" \
    --stage-name "$STAGE" \
    --region "$REGION" \
    --output text > /dev/null 2>&1 || \
aws apigateway create-deployment \
    --rest-api-id "$API_ID" \
    --stage-name "$STAGE" \
    --description "Deployment $(date +%Y-%m-%d-%H-%M-%S)" \
    --region "$REGION" \
    --output text > /dev/null

API_URL="https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}"
echo "   ✓ API deployed"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📡 API Gateway URL: $API_URL"
echo "🔗 Health Check: $API_URL/v1/health"
echo ""
echo "📝 Next steps:"
echo "   1. Create API keys: python scripts/seed_api_keys.py --api-key <your-key> --stage prod"
echo "   2. Test the API using the URL above"
echo ""

