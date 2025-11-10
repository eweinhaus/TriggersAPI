# Zapier Triggers API

A unified, real-time event ingestion system that enables external systems to send events into Zapier via a standardized RESTful interface.

## Project Status

**Current Phase:** Phase 4 - Developer Experience (P1) ✅ Completed

## Local Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Virtual environment (venv or similar)

### Setup Steps

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env if needed (defaults work for local development)
   ```

4. **Start DynamoDB Local:**
   ```bash
   docker-compose up -d
   ```

5. **Start FastAPI server:**
   ```bash
   uvicorn src.main:app --reload --port 8080
   # Or use the test server script:
   ./scripts/start_test_server.sh
   ```

6. **Verify setup:**
   ```bash
   curl http://localhost:8080/v1/health
   ```

## Environment Variables

See `.env.example` for all available environment variables.

**Required for local development:**
- `DYNAMODB_ENDPOINT_URL`: `http://localhost:8000`
- `AWS_REGION`: `us-east-1`
- `AWS_ACCESS_KEY_ID`: `test` (for local)
- `AWS_SECRET_ACCESS_KEY`: `test` (for local)
- `AUTH_MODE`: `local` (uses hardcoded test key)

## API Endpoints

### GET /v1/health
Health check endpoint (no authentication required).

### POST /v1/events
Ingest a new event.

**Request Body:**
```json
{
  "source": "string",
  "event_type": "string",
  "payload": {},
  "metadata": {
    "idempotency_key": "string (optional)",
    "priority": "low|normal|high (optional)",
    "correlation_id": "string (optional)"
  }
}
```

**Idempotency:** Include `idempotency_key` in metadata to prevent duplicate event creation. If an event with the same idempotency key already exists, the existing event is returned instead of creating a new one. Idempotency keys expire after 24 hours.

**Response (201 Created):**
```json
{
  "event_id": "uuid-v4",
  "created_at": "ISO 8601",
  "status": "pending",
  "message": "Event ingested successfully",
  "request_id": "uuid-v4"
}
```

### GET /v1/events/{event_id}
Retrieve detailed information about a specific event.

**Path Parameters:**
- `event_id`: UUID v4 of the event

**Response (200 OK):**
```json
{
  "event_id": "uuid-v4",
  "created_at": "ISO 8601",
  "source": "string",
  "event_type": "string",
  "payload": {},
  "status": "pending|acknowledged",
  "metadata": {},
  "acknowledged_at": "ISO 8601 (optional, only if acknowledged)",
  "request_id": "uuid-v4"
}
```

**Error Responses:**
- `404 Not Found`: Event not found (includes suggestion in error details)
- `401 Unauthorized`: Invalid API key

## Error Handling

All error responses follow a standardized format with enhanced context and suggestions:

**Error Response Format:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "field_name (for validation errors)",
      "issue": "Description of the issue",
      "suggestion": "Actionable suggestion to fix the issue",
      "event_id": "uuid (for not found/conflict errors)",
      "current_status": "status (for conflict errors)"
    },
    "request_id": "uuid-v4"
  }
}
```

**Error Codes:**
- `VALIDATION_ERROR` (400): Invalid request payload or parameters
- `UNAUTHORIZED` (401): Missing or invalid API key
- `NOT_FOUND` (404): Resource not found (includes suggestion)
- `CONFLICT` (409): Resource conflict (e.g., already acknowledged)
- `PAYLOAD_TOO_LARGE` (413): Payload exceeds 400KB limit
- `RATE_LIMIT_EXCEEDED` (429): Rate limit exceeded
- `INTERNAL_ERROR` (500): Server error

**Example Error Response:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Event with ID 'abc-123' was not found",
    "details": {
      "event_id": "abc-123",
      "suggestion": "Verify the event ID is correct and the event exists"
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### GET /v1/inbox
Retrieve pending events with pagination and filtering.

### POST /v1/events/{event_id}/ack
Acknowledge an event.

### DELETE /v1/events/{event_id}
Delete an event.

## Testing

Phase 4 includes comprehensive automated testing with **87% code coverage** (exceeds 80% requirement).

**Test Statistics:**
- Unit tests: 117 tests passing
- Integration tests: Full workflow coverage
- E2E tests: Real server testing
- Playwright MCP tests: HTTP-based API testing

### Quick Test Commands

**Complete test execution (recommended):**
```bash
./scripts/test_complete.sh
```
This runs unit tests, generates coverage reports, and verifies the API server can start.

**Run all tests (single command):**
```bash
./scripts/run_tests.sh
# Or using Python:
python scripts/run_tests.py
```

**Run specific test suites:**
```bash
# Unit tests only (117 tests, 87% coverage)
pytest tests/unit/ -v --cov=src --cov-report=html

# Integration tests only
pytest tests/integration/ -v

# E2E tests (requires DynamoDB Local)
pytest tests/e2e/ -v

# Playwright MCP tests (requires running API server)
# First, start the server:
./scripts/start_test_server.sh
# Then in another terminal:
pytest tests/playwright/ -v
```

### Test Coverage

- **Current Coverage:** 87% (exceeds 80% requirement)
- **Unit Tests:** 117 tests, all passing
- **Coverage Report:** Generated in `htmlcov/index.html` after running tests

### Starting API Server for Testing

**For E2E/Playwright tests, start the server:**
```bash
./scripts/start_test_server.sh
```

This script:
- Checks if DynamoDB Local is running (starts it if needed)
- Sets up environment variables for local testing
- Starts FastAPI server on port 8080
- Handles port conflicts automatically

**Run with coverage:**
```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
```

**View coverage report:**
Open `htmlcov/index.html` in your browser after running coverage.

### Test Structure

```
tests/
├── unit/              # Unit tests (fast, isolated)
│   ├── test_events.py
│   ├── test_inbox.py
│   ├── test_auth.py
│   ├── test_database.py
│   └── test_models.py
├── integration/       # Integration tests (with mocks)
│   └── test_integration.py
├── e2e/              # End-to-end tests (real server)
│   ├── test_e2e_events.py
│   └── test_e2e_inbox.py
├── playwright/       # Playwright MCP tests
│   └── test_api_playwright.py
└── utils/            # Test utilities and helpers
    ├── fixtures.py
    └── test_helpers.py
```

### Test Requirements

- **Unit tests:** No external dependencies (use mocks)
- **Integration tests:** Use moto for AWS service mocking
- **E2E tests:** Require DynamoDB Local running (`docker-compose up -d`)
- **Playwright MCP tests:** Require MCP server configuration (optional)

### Test Fixtures

Common fixtures available in `tests/conftest.py`:
- `client`: FastAPI test client
- `api_key`: Test API key
- `sample_event`: Sample event data
- `auth_headers`: Headers with API key

### Coverage Requirements

- **Overall coverage:** >80%
- **Critical paths:** 100% coverage (endpoints, auth, database)
- **Error handling:** 100% coverage

### Example cURL Commands

**Health Check:**
```bash
curl http://localhost:8080/v1/health
```

**Create Event:**
```bash
curl -X POST http://localhost:8080/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-12345" \
  -d '{
    "source": "test",
    "event_type": "user.created",
    "payload": {"user_id": "123", "name": "John Doe"},
    "metadata": {"priority": "normal"}
  }'
```

**Get Inbox:**
```bash
curl http://localhost:8080/v1/inbox?limit=10 \
  -H "X-API-Key: test-api-key-12345"
```

**Acknowledge Event:**
```bash
curl -X POST http://localhost:8080/v1/events/<event_id>/ack \
  -H "X-API-Key: test-api-key-12345"
```

**Delete Event:**
```bash
curl -X DELETE http://localhost:8080/v1/events/<event_id> \
  -H "X-API-Key: test-api-key-12345"
```

**Note:** Replace `<event_id>` with an actual UUID from a created event.

## Project Structure

```
triggers-api/
├── src/
│   ├── endpoints/      # API endpoint handlers
│   ├── models.py       # Pydantic models
│   ├── database.py     # DynamoDB operations
│   ├── auth.py         # Authentication
│   ├── exceptions.py   # Custom exceptions
│   └── main.py         # FastAPI application
├── scripts/            # Utility scripts
├── tests/              # Tests (Phase 3)
├── docker-compose.yml  # DynamoDB Local
└── requirements.txt    # Python dependencies
```

## AWS Deployment

### Prerequisites

- AWS account with appropriate permissions
- AWS CLI installed and configured (`aws configure`)
- AWS SAM CLI installed (`sam --version`)
- Docker running (required for SAM build)

### Deployment Steps

1. **Build the Lambda package:**
   ```bash
   sam build
   ```

2. **First-time deployment (guided):**
   ```bash
   sam deploy --guided
   ```
   
   When prompted:
   - Stack name: `triggers-api`
   - AWS Region: `us-east-1` (or your preferred region)
   - Confirm changes before deploy: `Y`
   - Allow SAM CLI IAM role creation: `Y`
   - Disable rollback: `N` (default)
   - Save arguments to configuration file: `Y`

3. **Subsequent deployments:**
   ```bash
   sam build
   sam deploy
   ```

4. **Get API Gateway URL:**
   ```bash
   aws cloudformation describe-stacks --stack-name triggers-api --query 'Stacks[0].Outputs'
   ```
   
   Or use SAM:
   ```bash
   sam list stack-outputs --stack-name triggers-api
   ```

### API Key Management

**Create API keys in production:**
```bash
python scripts/seed_api_keys.py --api-key <your-api-key> --stage prod --region us-east-1
```

**List API keys:**
```bash
aws dynamodb scan --table-name triggers-api-keys-prod
```

**Deactivate an API key:**
```bash
aws dynamodb update-item \
  --table-name triggers-api-keys-prod \
  --key '{"api_key": {"S": "<api-key>"}}' \
  --update-expression "SET is_active = :val" \
  --expression-attribute-values '{":val": {"BOOL": false}}'
```

### Testing Deployed API

**Get API URL:**
```bash
API_URL=$(aws cloudformation describe-stacks --stack-name triggers-api --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text)
echo $API_URL
```

**Test health check:**
```bash
curl $API_URL/v1/health
```

**Test event ingestion:**
```bash
curl -X POST $API_URL/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -H "X-Request-ID: test-123" \
  -d '{"source": "test", "event_type": "test.created", "payload": {}}'
```

**Test inbox:**
```bash
curl -X GET "$API_URL/v1/inbox?limit=10" \
  -H "X-API-Key: <your-api-key>"
```

### Environment Variables

The following environment variables are automatically set by the SAM template:
- `STAGE`: Deployment stage (e.g., `prod`)
- `DYNAMODB_TABLE_EVENTS`: Events table name
- `DYNAMODB_TABLE_KEYS`: API Keys table name
- `AWS_REGION`: AWS region
- `AUTH_MODE`: `aws` (production mode)
- `LOG_LEVEL`: `INFO`

### CloudWatch Logs

**View logs:**
```bash
aws logs tail /aws/lambda/triggers-api-prod --follow
```

**Or in AWS Console:**
CloudWatch → Log groups → `/aws/lambda/triggers-api-prod`

### Troubleshooting

**Check CloudFormation stack status:**
```bash
aws cloudformation describe-stacks --stack-name triggers-api
```

**View stack events:**
```bash
aws cloudformation describe-stack-events --stack-name triggers-api
```

**Check Lambda function:**
```bash
aws lambda get-function --function-name <function-name>
```

**Verify DynamoDB tables:**
```bash
aws dynamodb list-tables
aws dynamodb describe-table --table-name triggers-api-events-prod
```

**Common Issues:**
- **Deployment fails:** Check CloudFormation events for errors
- **Permission errors:** Verify IAM permissions for SAM CLI
- **Lambda timeout:** Increase timeout in `template.yaml`
- **CORS errors:** Verify CORS configuration in SAM template

## License

Internal project for Zapier.

