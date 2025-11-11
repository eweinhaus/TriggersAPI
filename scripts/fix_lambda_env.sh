#!/bin/bash
# Quick fix script to update Lambda environment variables

set -e

REGION="us-east-1"
STAGE="prod"
FUNCTION_NAME="triggers-api-prod"
EVENTS_TABLE="triggers-api-events-prod"
API_KEYS_TABLE="triggers-api-keys-prod"

echo "🔧 Updating Lambda environment variables..."

aws lambda update-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --environment "Variables={
        STAGE=$STAGE,
        DYNAMODB_TABLE_EVENTS=$EVENTS_TABLE,
        DYNAMODB_TABLE_KEYS=$API_KEYS_TABLE,
        AUTH_MODE=aws,
        LOG_LEVEL=INFO
    }" \
    --region "$REGION" \
    --output text

echo "⏳ Waiting for update to complete..."
aws lambda wait function-updated --function-name "$FUNCTION_NAME" --region "$REGION"

echo "✅ Lambda environment variables updated!"
echo ""
echo "Current environment variables:"
aws lambda get-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    --query 'Environment.Variables' \
    --output json | python3 -m json.tool
