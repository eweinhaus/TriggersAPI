#!/bin/bash
# AWS Deployment Script for Triggers API
# This script deploys the API to AWS using AWS CLI
#
# Prerequisites:
# - Docker (for building Lambda package with correct architecture)
# - AWS CLI configured with appropriate credentials
# - IAM permissions for Lambda, API Gateway, DynamoDB, IAM, CloudWatch, SQS, EventBridge

set -e

REGION="us-east-1"
STAGE="prod"
STACK_NAME="triggers-api"
FUNCTION_NAME="triggers-api-prod"
EVENTS_TABLE="triggers-api-events-prod"
API_KEYS_TABLE="triggers-api-keys-prod"
IDEMPOTENCY_TABLE="triggers-api-idempotency-prod"
RATE_LIMITS_TABLE="triggers-api-rate-limits-prod"
WEBHOOKS_TABLE="triggers-api-webhooks-prod"
ANALYTICS_TABLE="triggers-api-analytics-prod"
ROLE_NAME="triggers-api-lambda-role"

# New Lambda functions
WEBHOOK_DELIVERY_FUNCTION="webhook-delivery-prod"
KEY_EXPIRATION_FUNCTION="key-expiration-prod"
ANALYTICS_PROCESSOR_FUNCTION="analytics-processor-prod"

# SQS Queues
WEBHOOK_DELIVERY_QUEUE="triggers-api-webhook-delivery-prod"
WEBHOOK_DLQ="triggers-api-webhook-dlq-prod"

echo "🚀 Starting AWS deployment for Phases 7-10..."
echo "📋 This deployment includes:"
echo "   - Rate limiting (Phase 8)"
echo "   - Webhooks (Phase 10)"
echo "   - Analytics (Phase 10)"
echo "   - API key rotation (Phase 10)"
echo "   - Observability enhancements (Phase 7)"
echo ""

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
echo "📋 AWS Account: $ACCOUNT_ID"
echo "🌍 Region: $REGION"

# Step 1: Create IAM Role for Lambda
echo ""
echo "1️⃣ Creating/Updating IAM Role..."
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
    
    echo "   ✓ Role created: $ROLE_NAME"
    echo "   ⏳ Waiting for role to be ready..."
    sleep 10
fi

# Update IAM policy with all required permissions
echo "   Updating IAM policy with all required permissions..."
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
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${EVENTS_TABLE}",
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${EVENTS_TABLE}/index/status-created_at-index",
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${EVENTS_TABLE}/index/event-id-index",
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${API_KEYS_TABLE}",
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${IDEMPOTENCY_TABLE}",
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${RATE_LIMITS_TABLE}",
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${WEBHOOKS_TABLE}",
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${WEBHOOKS_TABLE}/index/api-key-is-active-index",
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${ANALYTICS_TABLE}"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData",
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:ListMetrics"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sqs:SendMessage",
                "sqs:GetQueueAttributes",
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage"
            ],
            "Resource": [
                "arn:aws:sqs:${REGION}:${ACCOUNT_ID}:${WEBHOOK_DELIVERY_QUEUE}",
                "arn:aws:sqs:${REGION}:${ACCOUNT_ID}:${WEBHOOK_DLQ}"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetRecords",
                "dynamodb:GetShardIterator",
                "dynamodb:DescribeStream",
                "dynamodb:ListStreams"
            ],
            "Resource": "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${EVENTS_TABLE}/stream/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "events:PutTargets",
                "events:PutRule",
                "events:DescribeRule"
            ],
            "Resource": "arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/*"
        }
    ]
}
EOF
)

aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "TriggersApiDynamoDBPolicy" \
    --policy-document "$POLICY_DOC" \
    --output text > /dev/null

echo "   ✓ IAM policy updated"

# Step 2: Create DynamoDB Tables
echo ""
echo "2️⃣ Creating DynamoDB Tables..."

# Events Table (with event-id-index GSI and Streams)
if aws dynamodb describe-table --table-name "$EVENTS_TABLE" --region "$REGION" &>/dev/null; then
    echo "   ✓ Events table already exists: $EVENTS_TABLE"
    
    # Check if event-id-index GSI exists
    GSI_EXISTS=$(aws dynamodb describe-table --table-name "$EVENTS_TABLE" --region "$REGION" \
        --query 'Table.GlobalSecondaryIndexes[?IndexName==`event-id-index`]' --output text)
    
    if [ -z "$GSI_EXISTS" ]; then
        echo "   Adding event-id-index GSI to Events table..."
        aws dynamodb update-table \
            --table-name "$EVENTS_TABLE" \
            --attribute-definitions AttributeName=event_id,AttributeType=S \
            --global-secondary-index-updates \
            "[{
                \"Create\": {
                    \"IndexName\": \"event-id-index\",
                    \"KeySchema\": [{\"AttributeName\": \"event_id\", \"KeyType\": \"HASH\"}],
                    \"Projection\": {\"ProjectionType\": \"ALL\"}
                }
            }]" \
            --region "$REGION" \
            --output text > /dev/null
        
        echo "   ⏳ Waiting for GSI to be active..."
        while [ "$(aws dynamodb describe-table --table-name "$EVENTS_TABLE" --region "$REGION" --query 'Table.GlobalSecondaryIndexes[?IndexName==`event-id-index`].IndexStatus' --output text)" != "ACTIVE" ]; do
            GSI_STATUS=$(aws dynamodb describe-table --table-name "$EVENTS_TABLE" --region "$REGION" --query 'Table.GlobalSecondaryIndexes[?IndexName==`event-id-index`].IndexStatus' --output text)
            if [ "$GSI_STATUS" = "FAILED" ]; then
                echo "   ✗ GSI creation failed!"
                exit 1
            fi
            echo "   GSI status: $GSI_STATUS (waiting...)"
            sleep 10
        done
        echo "   ✓ event-id-index GSI added and active"
    else
        echo "   ✓ event-id-index GSI already exists"
    fi
    
    # Enable DynamoDB Streams if not enabled
    STREAM_ENABLED=$(aws dynamodb describe-table --table-name "$EVENTS_TABLE" --region "$REGION" \
        --query 'Table.StreamSpecification.StreamEnabled' --output text)
    
    if [ "$STREAM_ENABLED" != "True" ]; then
        echo "   Enabling DynamoDB Streams on Events table..."
        aws dynamodb update-table \
            --table-name "$EVENTS_TABLE" \
            --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES \
            --region "$REGION" \
            --output text > /dev/null
        echo "   ✓ DynamoDB Streams enabled"
    else
        echo "   ✓ DynamoDB Streams already enabled"
    fi
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
            }, {
                \"IndexName\": \"event-id-index\",
                \"KeySchema\": [{\"AttributeName\": \"event_id\", \"KeyType\": \"HASH\"}],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            }]" \
        --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES \
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

# Idempotency Table
if aws dynamodb describe-table --table-name "$IDEMPOTENCY_TABLE" --region "$REGION" &>/dev/null; then
    echo "   ✓ Idempotency table already exists: $IDEMPOTENCY_TABLE"
else
    echo "   Creating Idempotency table: $IDEMPOTENCY_TABLE"
    aws dynamodb create-table \
        --table-name "$IDEMPOTENCY_TABLE" \
        --attribute-definitions AttributeName=idempotency_key,AttributeType=S \
        --key-schema AttributeName=idempotency_key,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --output text
    
    echo "   ⏳ Waiting for Idempotency table to be active..."
    aws dynamodb wait table-exists --table-name "$IDEMPOTENCY_TABLE" --region "$REGION"
    
    # Enable TTL
    echo "   Enabling TTL on Idempotency table..."
    aws dynamodb update-time-to-live \
        --table-name "$IDEMPOTENCY_TABLE" \
        --time-to-live-specification Enabled=true,AttributeName=ttl \
        --region "$REGION" \
        --output text > /dev/null
    
    echo "   ✓ Idempotency table created"
fi

# Rate Limits Table
if aws dynamodb describe-table --table-name "$RATE_LIMITS_TABLE" --region "$REGION" &>/dev/null; then
    echo "   ✓ Rate Limits table already exists: $RATE_LIMITS_TABLE"
else
    echo "   Creating Rate Limits table: $RATE_LIMITS_TABLE"
    aws dynamodb create-table \
        --table-name "$RATE_LIMITS_TABLE" \
        --attribute-definitions \
            AttributeName=api_key,AttributeType=S \
            AttributeName=window_start,AttributeType=N \
        --key-schema \
            AttributeName=api_key,KeyType=HASH \
            AttributeName=window_start,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --output text
    
    echo "   ⏳ Waiting for Rate Limits table to be active..."
    aws dynamodb wait table-exists --table-name "$RATE_LIMITS_TABLE" --region "$REGION"
    
    # Enable TTL
    echo "   Enabling TTL on Rate Limits table..."
    aws dynamodb update-time-to-live \
        --table-name "$RATE_LIMITS_TABLE" \
        --time-to-live-specification Enabled=true,AttributeName=ttl \
        --region "$REGION" \
        --output text > /dev/null
    
    echo "   ✓ Rate Limits table created"
fi

# Webhooks Table
if aws dynamodb describe-table --table-name "$WEBHOOKS_TABLE" --region "$REGION" &>/dev/null; then
    echo "   ✓ Webhooks table already exists: $WEBHOOKS_TABLE"
else
    echo "   Creating Webhooks table: $WEBHOOKS_TABLE"
    aws dynamodb create-table \
        --table-name "$WEBHOOKS_TABLE" \
        --attribute-definitions \
            AttributeName=webhook_id,AttributeType=S \
            AttributeName=api_key,AttributeType=S \
            AttributeName=is_active,AttributeType=N \
        --key-schema AttributeName=webhook_id,KeyType=HASH \
        --global-secondary-indexes \
            "[{
                \"IndexName\": \"api-key-is-active-index\",
                \"KeySchema\": [
                    {\"AttributeName\": \"api_key\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"is_active\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            }]" \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --output text
    
    echo "   ⏳ Waiting for Webhooks table to be active..."
    aws dynamodb wait table-exists --table-name "$WEBHOOKS_TABLE" --region "$REGION"
    echo "   ✓ Webhooks table created"
fi

# Analytics Table
if aws dynamodb describe-table --table-name "$ANALYTICS_TABLE" --region "$REGION" &>/dev/null; then
    echo "   ✓ Analytics table already exists: $ANALYTICS_TABLE"
else
    echo "   Creating Analytics table: $ANALYTICS_TABLE"
    aws dynamodb create-table \
        --table-name "$ANALYTICS_TABLE" \
        --attribute-definitions \
            AttributeName=metric_date,AttributeType=S \
            AttributeName=metric_type,AttributeType=S \
        --key-schema \
            AttributeName=metric_date,KeyType=HASH \
            AttributeName=metric_type,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --output text
    
    echo "   ⏳ Waiting for Analytics table to be active..."
    aws dynamodb wait table-exists --table-name "$ANALYTICS_TABLE" --region "$REGION"
    
    # Enable TTL
    echo "   Enabling TTL on Analytics table..."
    aws dynamodb update-time-to-live \
        --table-name "$ANALYTICS_TABLE" \
        --time-to-live-specification Enabled=true,AttributeName=ttl \
        --region "$REGION" \
        --output text > /dev/null
    
    echo "   ✓ Analytics table created"
fi

# Step 3: Create SQS Queues
echo ""
echo "3️⃣ Creating SQS Queues..."

# Dead Letter Queue (create first)
if aws sqs get-queue-url --queue-name "$WEBHOOK_DLQ" --region "$REGION" &>/dev/null; then
    DLQ_URL=$(aws sqs get-queue-url --queue-name "$WEBHOOK_DLQ" --region "$REGION" --query 'QueueUrl' --output text)
    DLQ_ARN=$(aws sqs get-queue-attributes --queue-url "$DLQ_URL" --attribute-names QueueArn --region "$REGION" --query 'Attributes.QueueArn' --output text)
    echo "   ✓ Webhook DLQ already exists: $WEBHOOK_DLQ"
else
    echo "   Creating Webhook DLQ: $WEBHOOK_DLQ"
    DLQ_URL=$(aws sqs create-queue \
        --queue-name "$WEBHOOK_DLQ" \
        --attributes MessageRetentionPeriod=1209600 \
        --region "$REGION" \
        --query 'QueueUrl' \
        --output text)
    DLQ_ARN=$(aws sqs get-queue-attributes --queue-url "$DLQ_URL" --attribute-names QueueArn --region "$REGION" --query 'Attributes.QueueArn' --output text)
    echo "   ✓ Webhook DLQ created"
fi

# Webhook Delivery Queue
if aws sqs get-queue-url --queue-name "$WEBHOOK_DELIVERY_QUEUE" --region "$REGION" &>/dev/null; then
    WEBHOOK_QUEUE_URL=$(aws sqs get-queue-url --queue-name "$WEBHOOK_DELIVERY_QUEUE" --region "$REGION" --query 'QueueUrl' --output text)
    echo "   ✓ Webhook Delivery Queue already exists: $WEBHOOK_DELIVERY_QUEUE"
else
    echo "   Creating Webhook Delivery Queue: $WEBHOOK_DELIVERY_QUEUE"
    # Create queue first, then set attributes separately
    WEBHOOK_QUEUE_URL=$(aws sqs create-queue \
        --queue-name "$WEBHOOK_DELIVERY_QUEUE" \
        --attributes VisibilityTimeout=30,MessageRetentionPeriod=1209600 \
        --region "$REGION" \
        --query 'QueueUrl' \
        --output text)
    
    # Set redrive policy separately
    REDRIVE_POLICY=$(cat <<EOF
{"deadLetterTargetArn":"$DLQ_ARN","maxReceiveCount":3}
EOF
)
    aws sqs set-queue-attributes \
        --queue-url "$WEBHOOK_QUEUE_URL" \
        --attributes "RedrivePolicy=$REDRIVE_POLICY" \
        --region "$REGION" \
        --output text > /dev/null
    
    echo "   ✓ Webhook Delivery Queue created"
fi

WEBHOOK_QUEUE_ARN=$(aws sqs get-queue-attributes --queue-url "$WEBHOOK_QUEUE_URL" --attribute-names QueueArn --region "$REGION" --query 'Attributes.QueueArn' --output text)

# Step 4: Create/Update Lambda Function
echo ""
echo "4️⃣ Creating/Updating Lambda Function..."

# Check package size and use S3 if needed
PACKAGE_SIZE=$(stat -f%z lambda-deployment.zip 2>/dev/null || stat -c%s lambda-deployment.zip 2>/dev/null)
S3_BUCKET="triggers-api-deployments-${ACCOUNT_ID}"
S3_KEY="lambda-deployment-$(date +%s).zip"

# Upload to S3 if package is > 50MB
if [ "$PACKAGE_SIZE" -gt 52428800 ]; then
    echo "   Package size ($(numfmt --to=iec-i --suffix=B $PACKAGE_SIZE 2>/dev/null || echo "${PACKAGE_SIZE} bytes")) exceeds 50MB, uploading to S3..."
    aws s3 cp lambda-deployment.zip "s3://${S3_BUCKET}/${S3_KEY}" --region "$REGION" --output text > /dev/null
    echo "   ✓ Package uploaded to S3: s3://${S3_BUCKET}/${S3_KEY}"
    USE_S3=true
else
    USE_S3=false
fi

if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &>/dev/null; then
    echo "   ✓ Function already exists, updating code and configuration..."
    if [ "$USE_S3" = true ]; then
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --s3-bucket "$S3_BUCKET" \
            --s3-key "$S3_KEY" \
            --region "$REGION" \
            --output text > /dev/null
    else
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file fileb://lambda-deployment.zip \
            --region "$REGION" \
            --output text > /dev/null
    fi
    
    echo "   ⏳ Waiting for function update..."
    aws lambda wait function-updated --function-name "$FUNCTION_NAME" --region "$REGION"
    echo "   ✓ Function code updated"
    
    # Update environment variables
    echo "   Updating environment variables..."
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --environment "Variables={
            STAGE=$STAGE,
            DYNAMODB_TABLE_EVENTS=$EVENTS_TABLE,
            DYNAMODB_TABLE_KEYS=$API_KEYS_TABLE,
            DYNAMODB_TABLE_IDEMPOTENCY=$IDEMPOTENCY_TABLE,
            DYNAMODB_TABLE_RATE_LIMITS=$RATE_LIMITS_TABLE,
            DYNAMODB_TABLE_WEBHOOKS=$WEBHOOKS_TABLE,
            DYNAMODB_TABLE_ANALYTICS=$ANALYTICS_TABLE,
            WEBHOOK_DELIVERY_QUEUE_URL=$WEBHOOK_QUEUE_URL,
            AUTH_MODE=aws,
            LOG_LEVEL=INFO
        }" \
        --region "$REGION" \
        --output text > /dev/null
    
    echo "   ⏳ Waiting for configuration update..."
    aws lambda wait function-updated --function-name "$FUNCTION_NAME" --region "$REGION"
    echo "   ✓ Environment variables updated"
else
    echo "   Creating Lambda function: $FUNCTION_NAME"
    if [ "$USE_S3" = true ]; then
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --runtime python3.11 \
            --role "$ROLE_ARN" \
            --handler src.main.handler \
            --code "S3Bucket=${S3_BUCKET},S3Key=${S3_KEY}" \
            --timeout 30 \
            --memory-size 512 \
            --environment "Variables={
                STAGE=$STAGE,
                DYNAMODB_TABLE_EVENTS=$EVENTS_TABLE,
                DYNAMODB_TABLE_KEYS=$API_KEYS_TABLE,
                DYNAMODB_TABLE_IDEMPOTENCY=$IDEMPOTENCY_TABLE,
                DYNAMODB_TABLE_RATE_LIMITS=$RATE_LIMITS_TABLE,
                DYNAMODB_TABLE_WEBHOOKS=$WEBHOOKS_TABLE,
                DYNAMODB_TABLE_ANALYTICS=$ANALYTICS_TABLE,
                WEBHOOK_DELIVERY_QUEUE_URL=$WEBHOOK_QUEUE_URL,
                AWS_REGION=$REGION,
                AUTH_MODE=aws,
                LOG_LEVEL=INFO
            }" \
            --region "$REGION" \
            --output text
    else
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
                DYNAMODB_TABLE_IDEMPOTENCY=$IDEMPOTENCY_TABLE,
                DYNAMODB_TABLE_RATE_LIMITS=$RATE_LIMITS_TABLE,
                DYNAMODB_TABLE_WEBHOOKS=$WEBHOOKS_TABLE,
                DYNAMODB_TABLE_ANALYTICS=$ANALYTICS_TABLE,
                WEBHOOK_DELIVERY_QUEUE_URL=$WEBHOOK_QUEUE_URL,
                AWS_REGION=$REGION,
                AUTH_MODE=aws,
                LOG_LEVEL=INFO
            }" \
            --region "$REGION" \
            --output text
    fi
    
    echo "   ⏳ Waiting for function to be ready..."
    aws lambda wait function-active --function-name "$FUNCTION_NAME" --region "$REGION"
    echo "   ✓ Lambda function created"
fi

# Step 5: Create Additional Lambda Functions
echo ""
echo "5️⃣ Creating Additional Lambda Functions..."

# Webhook Delivery Function
if aws lambda get-function --function-name "$WEBHOOK_DELIVERY_FUNCTION" --region "$REGION" &>/dev/null; then
    echo "   ✓ Webhook Delivery function already exists, updating..."
    if [ "$USE_S3" = true ]; then
        aws lambda update-function-code \
            --function-name "$WEBHOOK_DELIVERY_FUNCTION" \
            --s3-bucket "$S3_BUCKET" \
            --s3-key "$S3_KEY" \
            --region "$REGION" \
            --output text > /dev/null
    else
        aws lambda update-function-code \
            --function-name "$WEBHOOK_DELIVERY_FUNCTION" \
            --zip-file fileb://lambda-deployment.zip \
            --region "$REGION" \
            --output text > /dev/null
    fi
    aws lambda wait function-updated --function-name "$WEBHOOK_DELIVERY_FUNCTION" --region "$REGION"
else
    echo "   Creating Webhook Delivery function: $WEBHOOK_DELIVERY_FUNCTION"
    if [ "$USE_S3" = true ]; then
        aws lambda create-function \
            --function-name "$WEBHOOK_DELIVERY_FUNCTION" \
            --runtime python3.11 \
            --role "$ROLE_ARN" \
            --handler src.lambda_handlers.webhook_delivery.handler \
            --code "S3Bucket=${S3_BUCKET},S3Key=${S3_KEY}" \
            --timeout 60 \
            --memory-size 256 \
            --environment "Variables={
            STAGE=$STAGE,
            DYNAMODB_TABLE_WEBHOOKS=$WEBHOOKS_TABLE
            }" \
            --region "$REGION" \
            --output text
    else
        aws lambda create-function \
            --function-name "$WEBHOOK_DELIVERY_FUNCTION" \
            --runtime python3.11 \
            --role "$ROLE_ARN" \
            --handler src.lambda_handlers.webhook_delivery.handler \
            --zip-file fileb://lambda-deployment.zip \
            --timeout 60 \
            --memory-size 256 \
            --environment "Variables={
            STAGE=$STAGE,
            DYNAMODB_TABLE_WEBHOOKS=$WEBHOOKS_TABLE
            }" \
            --region "$REGION" \
            --output text
    fi
    
    aws lambda wait function-active --function-name "$WEBHOOK_DELIVERY_FUNCTION" --region "$REGION"
    
    # Grant SQS permission to invoke Lambda
    aws lambda add-permission \
        --function-name "$WEBHOOK_DELIVERY_FUNCTION" \
        --statement-id "sqs-invoke-$(date +%s)" \
        --action lambda:InvokeFunction \
        --principal sqs.amazonaws.com \
        --source-arn "$WEBHOOK_QUEUE_ARN" \
        --region "$REGION" \
        --output text > /dev/null 2>&1 || echo "   (Permission may already exist)"
    
    # Create SQS event source mapping
    aws lambda create-event-source-mapping \
        --function-name "$WEBHOOK_DELIVERY_FUNCTION" \
        --event-source-arn "$WEBHOOK_QUEUE_ARN" \
        --batch-size 10 \
        --maximum-batching-window-in-seconds 5 \
        --region "$REGION" \
        --output text > /dev/null 2>&1 || echo "   (Event source mapping may already exist)"
    
    echo "   ✓ Webhook Delivery function created"
fi

# Key Expiration Function
if aws lambda get-function --function-name "$KEY_EXPIRATION_FUNCTION" --region "$REGION" &>/dev/null; then
    echo "   ✓ Key Expiration function already exists, updating..."
    if [ "$USE_S3" = true ]; then
        aws lambda update-function-code \
            --function-name "$KEY_EXPIRATION_FUNCTION" \
            --s3-bucket "$S3_BUCKET" \
            --s3-key "$S3_KEY" \
            --region "$REGION" \
            --output text > /dev/null
    else
        aws lambda update-function-code \
            --function-name "$KEY_EXPIRATION_FUNCTION" \
            --zip-file fileb://lambda-deployment.zip \
            --region "$REGION" \
            --output text > /dev/null
    fi
    aws lambda wait function-updated --function-name "$KEY_EXPIRATION_FUNCTION" --region "$REGION"
else
    echo "   Creating Key Expiration function: $KEY_EXPIRATION_FUNCTION"
    if [ "$USE_S3" = true ]; then
        aws lambda create-function \
            --function-name "$KEY_EXPIRATION_FUNCTION" \
            --runtime python3.11 \
            --role "$ROLE_ARN" \
            --handler src.lambda_handlers.key_expiration.handler \
            --code "S3Bucket=${S3_BUCKET},S3Key=${S3_KEY}" \
            --timeout 300 \
            --memory-size 256 \
            --environment "Variables={
            STAGE=$STAGE,
            DYNAMODB_TABLE_KEYS=$API_KEYS_TABLE
            }" \
            --region "$REGION" \
            --output text
    else
        aws lambda create-function \
            --function-name "$KEY_EXPIRATION_FUNCTION" \
            --runtime python3.11 \
            --role "$ROLE_ARN" \
            --handler src.lambda_handlers.key_expiration.handler \
            --zip-file fileb://lambda-deployment.zip \
            --timeout 300 \
            --memory-size 256 \
            --environment "Variables={
            STAGE=$STAGE,
            DYNAMODB_TABLE_KEYS=$API_KEYS_TABLE
            }" \
            --region "$REGION" \
            --output text
    fi
    
    aws lambda wait function-active --function-name "$KEY_EXPIRATION_FUNCTION" --region "$REGION"
    
    # Create EventBridge rule for daily schedule
    RULE_NAME="key-expiration-daily-${STAGE}"
    if aws events describe-rule --name "$RULE_NAME" --region "$REGION" &>/dev/null; then
        echo "   ✓ EventBridge rule already exists"
    else
        aws events put-rule \
            --name "$RULE_NAME" \
            --schedule-expression "rate(1 day)" \
            --description "Daily cleanup of expired API keys" \
            --region "$REGION" \
            --output text > /dev/null
        
        aws lambda add-permission \
            --function-name "$KEY_EXPIRATION_FUNCTION" \
            --statement-id "events-invoke-$(date +%s)" \
            --action lambda:InvokeFunction \
            --principal events.amazonaws.com \
            --source-arn "arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/${RULE_NAME}" \
            --region "$REGION" \
            --output text > /dev/null 2>&1 || echo "   (Permission may already exist)"
        
        aws events put-targets \
            --rule "$RULE_NAME" \
            --targets "Id=1,Arn=arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${KEY_EXPIRATION_FUNCTION}" \
            --region "$REGION" \
            --output text > /dev/null
        
        echo "   ✓ EventBridge rule created"
    fi
    
    echo "   ✓ Key Expiration function created"
fi

# Analytics Processor Function
EVENTS_STREAM_ARN=$(aws dynamodb describe-table --table-name "$EVENTS_TABLE" --region "$REGION" \
    --query 'Table.LatestStreamArn' --output text)

if [ -n "$EVENTS_STREAM_ARN" ] && [ "$EVENTS_STREAM_ARN" != "None" ]; then
    if aws lambda get-function --function-name "$ANALYTICS_PROCESSOR_FUNCTION" --region "$REGION" &>/dev/null; then
        echo "   ✓ Analytics Processor function already exists, updating..."
        if [ "$USE_S3" = true ]; then
            aws lambda update-function-code \
                --function-name "$ANALYTICS_PROCESSOR_FUNCTION" \
                --s3-bucket "$S3_BUCKET" \
                --s3-key "$S3_KEY" \
                --region "$REGION" \
                --output text > /dev/null
        else
            aws lambda update-function-code \
                --function-name "$ANALYTICS_PROCESSOR_FUNCTION" \
                --zip-file fileb://lambda-deployment.zip \
                --region "$REGION" \
                --output text > /dev/null
        fi
        aws lambda wait function-updated --function-name "$ANALYTICS_PROCESSOR_FUNCTION" --region "$REGION"
    else
        echo "   Creating Analytics Processor function: $ANALYTICS_PROCESSOR_FUNCTION"
        if [ "$USE_S3" = true ]; then
            aws lambda create-function \
                --function-name "$ANALYTICS_PROCESSOR_FUNCTION" \
                --runtime python3.11 \
                --role "$ROLE_ARN" \
                --handler src.lambda_handlers.analytics_processor.handler \
                --code "S3Bucket=${S3_BUCKET},S3Key=${S3_KEY}" \
                --timeout 300 \
                --memory-size 512 \
                --environment "Variables={
                STAGE=$STAGE,
                DYNAMODB_TABLE_ANALYTICS=$ANALYTICS_TABLE
                }" \
                --region "$REGION" \
                --output text
        else
            aws lambda create-function \
                --function-name "$ANALYTICS_PROCESSOR_FUNCTION" \
                --runtime python3.11 \
                --role "$ROLE_ARN" \
                --handler src.lambda_handlers.analytics_processor.handler \
                --zip-file fileb://lambda-deployment.zip \
                --timeout 300 \
                --memory-size 512 \
                --environment "Variables={
                STAGE=$STAGE,
                DYNAMODB_TABLE_ANALYTICS=$ANALYTICS_TABLE
                }" \
                --region "$REGION" \
                --output text
        fi
        
        aws lambda wait function-active --function-name "$ANALYTICS_PROCESSOR_FUNCTION" --region "$REGION"
        
        # Grant DynamoDB Streams permission
        aws lambda add-permission \
            --function-name "$ANALYTICS_PROCESSOR_FUNCTION" \
            --statement-id "streams-invoke-$(date +%s)" \
            --action lambda:InvokeFunction \
            --principal dynamodb.amazonaws.com \
            --source-arn "$EVENTS_STREAM_ARN" \
            --region "$REGION" \
            --output text > /dev/null 2>&1 || echo "   (Permission may already exist)"
        
        # Create DynamoDB Stream event source mapping
        aws lambda create-event-source-mapping \
            --function-name "$ANALYTICS_PROCESSOR_FUNCTION" \
            --event-source-arn "$EVENTS_STREAM_ARN" \
            --starting-position LATEST \
            --batch-size 10 \
            --maximum-batching-window-in-seconds 5 \
            --region "$REGION" \
            --output text > /dev/null 2>&1 || echo "   (Event source mapping may already exist)"
        
        echo "   ✓ Analytics Processor function created"
    fi
else
    echo "   ⚠️  Events table stream not available, skipping Analytics Processor function"
fi

# Step 6: Create API Gateway
echo ""
echo "6️⃣ Creating/Updating API Gateway..."

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
echo "📊 Deployed Resources:"
echo "   - DynamoDB Tables: Events, API Keys, Idempotency, Rate Limits, Webhooks, Analytics"
echo "   - Lambda Functions: Main API, Webhook Delivery, Key Expiration, Analytics Processor"
echo "   - SQS Queues: Webhook Delivery, Webhook DLQ"
echo "   - API Gateway: REST API with /v1/{proxy+} route"
echo ""
echo "📝 Next steps:"
echo "   1. Create API keys: python scripts/seed_api_keys.py --api-key <your-key> --stage prod"
echo "   2. Test the API using the URL above"
echo "   3. Monitor CloudWatch logs for any errors"
echo ""
