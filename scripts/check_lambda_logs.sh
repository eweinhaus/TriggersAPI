#!/bin/bash
# Check recent Lambda logs for API key authentication errors

REGION="us-east-1"
FUNCTION_NAME="triggers-api-prod"
LOG_GROUP="/aws/lambda/$FUNCTION_NAME"

echo "📋 Checking recent Lambda logs for API key errors..."
echo ""

# Get logs from the last 10 minutes
aws logs tail "$LOG_GROUP" \
    --region "$REGION" \
    --since 10m \
    --format short \
    --filter-pattern "API key" \
    | head -50

echo ""
echo "📋 All recent logs (last 10 minutes):"
aws logs tail "$LOG_GROUP" \
    --region "$REGION" \
    --since 10m \
    --format short \
    | tail -30

