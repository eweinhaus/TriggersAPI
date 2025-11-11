# Quick Start Guide

Get started with the Zapier Triggers API in 5 minutes.

## Prerequisites

- Python 3.11+ (for local development)
- Docker & Docker Compose (for DynamoDB Local)
- API key (for production) or use `test-api-key-12345` for local development

## Step 1: Set Up Local Environment

```bash
# Clone the repository (if applicable)
# cd triggers-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start DynamoDB Local
docker-compose up -d

# Start API server
uvicorn src.main:app --reload --port 8080
```

## Step 2: Verify Setup

```bash
# Test health endpoint
curl http://localhost:8080/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T12:00:00.000000Z",
  "version": "1.0.0"
}
```

## Step 3: Make Your First API Call

### Option A: Using Python Client

```bash
cd examples/python
pip install -r requirements.txt
python examples/basic_usage.py
```

### Option B: Using JavaScript Client

```bash
cd examples/javascript
npm install
npm run example:basic
```

### Option C: Using cURL

```bash
curl -X POST http://localhost:8080/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-first-request" \
  -d '{
    "source": "my-app",
    "event_type": "user.created",
    "payload": {
      "user_id": "123",
      "name": "John Doe"
    }
  }'
```

Expected response:
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-11-10T12:00:00.000000Z",
  "status": "pending",
  "message": "Event ingested successfully",
  "request_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

## Step 4: Explore the API

### View Interactive Documentation

Open your browser and visit:
- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`

### Try Common Operations

1. **Create an event** - POST /v1/events
2. **Get inbox** - GET /v1/inbox
3. **Get event details** - GET /v1/events/{event_id}
4. **Acknowledge event** - POST /v1/events/{event_id}/ack
5. **Delete event** - DELETE /v1/events/{event_id}

## Next Steps

- Read the [API Reference](API.md) for complete endpoint documentation
- Check out [Usage Examples](EXAMPLES.md) for common patterns
- Review [Error Handling Guide](ERRORS.md) for error codes
- See [cURL Examples](CURL_EXAMPLES.md) for command-line usage

## Common Issues

### Connection Refused

**Problem**: Can't connect to `http://localhost:8080`

**Solution**: 
- Verify the API server is running: `uvicorn src.main:app --reload --port 8080`
- Check if port 8080 is already in use
- Verify DynamoDB Local is running: `docker-compose ps`

### Authentication Errors

**Problem**: Getting 401 Unauthorized errors

**Solution**:
- For local development, use API key: `test-api-key-12345`
- Verify the `X-API-Key` header is included in requests
- Check that `AUTH_MODE=local` is set in your environment

### DynamoDB Connection Errors

**Problem**: Can't connect to DynamoDB

**Solution**:
- Start DynamoDB Local: `docker-compose up -d`
- Verify it's running: `docker-compose ps`
- Check environment variables: `DYNAMODB_ENDPOINT_URL=http://localhost:8000`

## Production Setup

For production deployment:

1. Deploy to AWS using the deployment scripts
2. Get your production API key from your account settings
3. Update the `base_url` in your client to the production API URL
4. Use your production API key for authentication

See the main [README](../README.md) for deployment instructions.

