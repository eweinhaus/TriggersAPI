#!/bin/bash

# Local development setup script for Triggers API

set -e

echo "🚀 Setting up Triggers API local development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start DynamoDB Local
echo "📦 Starting DynamoDB Local..."
docker-compose up -d

# Wait for DynamoDB to be ready
echo "⏳ Waiting for DynamoDB Local to be ready..."
sleep 3

# Check if DynamoDB is accessible
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ DynamoDB Local is running on http://localhost:8000"
else
    echo "⚠️  Warning: Could not verify DynamoDB Local is running"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate your virtual environment: source venv/bin/activate"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Start FastAPI server: uvicorn src.main:app --reload --port 8080"
echo "4. Test health endpoint: curl http://localhost:8080/v1/health"
echo ""
echo "Note: Tables will be created automatically when the FastAPI app starts."

