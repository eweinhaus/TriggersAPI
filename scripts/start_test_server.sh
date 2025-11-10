#!/bin/bash

# Start FastAPI server for E2E/Playwright tests
# This script starts the server on port 8080 for testing

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}[INFO]${NC} Starting FastAPI server for testing..."

# Check if port 8080 is already in use
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}[WARNING]${NC} Port 8080 is already in use"
    echo "Killing existing process..."
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Set environment variables for local testing
export DYNAMODB_ENDPOINT_URL=http://localhost:8000
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AUTH_MODE=local
export LOG_LEVEL=INFO
export DYNAMODB_TABLE_EVENTS=triggers-api-events
export DYNAMODB_TABLE_API_KEYS=triggers-api-keys

# Check if DynamoDB Local is running
if ! docker ps | grep -q dynamodb-local; then
    echo -e "${YELLOW}[WARNING]${NC} DynamoDB Local is not running"
    echo "Starting DynamoDB Local..."
    docker-compose up -d dynamodb-local
    sleep 3
fi

# Start FastAPI server
echo -e "${GREEN}[INFO]${NC} Starting FastAPI server on http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

