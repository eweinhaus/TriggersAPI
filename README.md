# Zapier Triggers API

A unified, real-time event ingestion system that enables external systems to send events into Zapier via a standardized RESTful interface.

## Project Status

**Current Phase:** Phase 2 - AWS Infrastructure & Deployment (In Progress)

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

### GET /v1/inbox
Retrieve pending events with pagination and filtering.

### POST /v1/events/{event_id}/ack
Acknowledge an event.

### DELETE /v1/events/{event_id}
Delete an event.

## Testing

Phase 3 includes comprehensive automated testing with >80% code coverage.

### Running Tests

**Run all tests (single command):**
```bash
./scripts/run_tests.sh
# Or using Python:
python scripts/run_tests.py
```

**Run specific test suites:**
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only (requires DynamoDB Local)
pytest tests/e2e/ -v

# Playwright MCP tests only
pytest tests/playwright/ -v
```

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

