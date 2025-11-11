# Technical Context: Zapier Triggers API

## Technology Stack

### Backend

**Core Framework:**
- **Python 3.11+** - Programming language
- **FastAPI 0.104.0+** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic 2.0.0+** - Data validation

**AWS Services:**
- **AWS Lambda** - Serverless compute (Python runtime)
- **API Gateway** - REST API interface
- **DynamoDB** - NoSQL database (Events, API Keys, Idempotency, Rate Limits tables)
- **CloudWatch** - Logging and metrics
- **S3 + CloudFront** - Frontend hosting (Phase 6)

**AWS SDK:**
- **boto3 1.28.0+** - AWS service client

**Deployment:**
- **AWS SAM** - Infrastructure as code (template.yaml created)
- **AWS CLI** - Direct deployment (primary method due to SAM CLI issues)
- **Docker** - Building Lambda-compatible packages (x86_64 binaries)
- **Mangum 0.17.0+** - ASGI adapter for FastAPI on Lambda

### Frontend (Phase 6) ✅

- **React 19** - UI framework
- **Material-UI (MUI) v7** - Component library
- **React Router v7** - Routing
- **Axios** - HTTP client
- **React Query (TanStack Query)** - State management
- **Recharts** - Charts library
- **@uiw/react-json-view** - JSON viewer
- **date-fns** - Date formatting
- **Vite** - Build tool
- **Node.js 25+** - Runtime

### Development Tools

- **Docker & Docker Compose** - DynamoDB Local
- **pytest** - Testing framework
- **moto** - AWS service mocking
- **httpx** - HTTP client for testing
- **Playwright MCP** - Browser automation (Phase 3, 6)
- **Cursor Browser Extension** - Browser testing (Phase 6)
- **k6** - Load testing framework (Phase 7)

## Development Setup

### Local Development (Phase 1)

**Requirements:**
- Python 3.11+
- Docker & Docker Compose
- Virtual environment (venv or similar)

**Environment Variables:**
```bash
DYNAMODB_ENDPOINT_URL=http://localhost:8000
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AUTH_MODE=local
LOG_LEVEL=INFO
```

**Local Services:**
- DynamoDB Local (Docker): `http://localhost:8000`
- FastAPI Server: `http://localhost:8000` (different port or use 8080)

### AWS Deployment (Phase 2+)

**Requirements:**
- AWS account with appropriate permissions
- AWS CLI installed and configured
- SAM CLI installed

**Environment Variables:**
```bash
AWS_REGION=us-east-1
AUTH_MODE=aws
LOG_LEVEL=INFO
```

## Project Structure

```
triggers-api/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # Pydantic models
│   ├── database.py          # DynamoDB client wrapper
│   ├── auth.py              # API key validation
│   ├── exceptions.py        # Custom exceptions
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py      # Structured JSON logging (Phase 7)
│   │   └── metrics.py       # CloudWatch metrics (Phase 7)
│   └── endpoints/
│       ├── __init__.py
│       ├── events.py        # Event endpoints
│       ├── inbox.py         # Inbox endpoints
│       └── health.py         # Health check
├── tests/
│   ├── unit/                # Unit tests (117 tests, 87% coverage)
│   │   ├── test_events.py
│   │   ├── test_inbox.py
│   │   ├── test_auth.py
│   │   ├── test_database.py
│   │   └── test_models.py
│   ├── integration/         # Integration tests
│   │   └── test_integration.py
│   ├── e2e/                 # End-to-end tests
│   │   └── test_e2e_events.py
│   ├── playwright/         # Playwright MCP tests (HTTP-based)
│   │   └── test_api_playwright.py
│   ├── utils/              # Test utilities
│   │   ├── fixtures.py
│   │   └── test_helpers.py
│   └── conftest.py          # pytest fixtures
├── scripts/
│   ├── create_tables.py     # Initialize DynamoDB tables
│   ├── seed_api_keys.py     # Create test API keys (supports local/AWS)
│   ├── local_setup.sh       # Local development setup
│   ├── deploy_aws.sh        # AWS deployment script (AWS CLI)
│   ├── run_tests.sh         # Test automation script (shell)
│   ├── run_tests.py         # Test automation script (Python)
│   ├── migrate_add_event_id_gsi.py  # GSI migration script (Phase 7)
│   ├── setup_cloudwatch_dashboard.sh # CloudWatch dashboard setup (Phase 7)
│   ├── setup_cloudwatch_alarms.sh    # CloudWatch alarms setup (Phase 7)
│   ├── run_load_tests.sh    # Load test runner (Phase 7)
│   └── cloudwatch_dashboard.json    # Dashboard configuration (Phase 7)
├── frontend/                # Phase 6
│   ├── src/
│   ├── tests/
│   └── package.json
├── template.yaml             # SAM template
├── docker-compose.yml        # DynamoDB Local
├── requirements.txt
├── .env.example
└── README.md
```

## Dependencies

### Backend Dependencies (`requirements.txt`)

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
boto3>=1.28.0
python-dotenv>=1.0.0
mangum>=0.17.0
```

### Development Dependencies

```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
moto>=4.2.0
httpx>=0.25.0
faker>=19.0.0
pytest-xdist>=3.0.0
pytest-timeout>=2.1.0
```

### Frontend Dependencies (Phase 6)

```
react>=18.0.0
@mui/material>=5.0.0
axios>=1.6.0
```

## Technical Constraints

### Performance Targets

- **Event Ingestion Latency:** < 100ms (p95)
- **Inbox Query Latency:** < 200ms (p95)
- **Cold Start:** < 2 seconds (acceptable for MVP)
- **Response Time:** Fast response for all endpoints

### Resource Limits

- **Lambda Payload:** 6MB max (recommend 400KB for events)
- **DynamoDB Item Size:** 400KB max
- **API Gateway Payload:** 10MB max
- **Event Payload:** 400KB max (validated)

### Scalability Considerations

- **Lambda:** Auto-scaling (AWS managed)
- **DynamoDB:** On-demand billing (no capacity planning)
- **API Gateway:** Managed scaling
- **No specific throughput requirements for MVP**

## Implementation Details

### UUID Format

- **Library:** Python's `uuid` module
- **Function:** `uuid.uuid4()`
- **Format:** Lowercase UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")
- **Usage:** Event IDs, request IDs

### Timestamp Format

- **Format:** ISO 8601 UTC with Z suffix
- **Pattern:** `YYYY-MM-DDTHH:MM:SS.ffffffZ`
- **Example:** `2024-01-01T12:00:00.123456Z`
- **Implementation:** `datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')`

### TTL Calculation

- **Events:** 7 days from creation
- **Idempotency Keys:** 24 hours from creation
- **Format:** Unix timestamp (seconds since epoch)
- **Calculation:** `int(time.time()) + (7 * 24 * 60 * 60)`

### Cursor Encoding

- **Format:** Base64-encoded JSON
- **Content:** DynamoDB `LastEvaluatedKey`
- **Encoding:** `base64.b64encode(json.dumps(key).encode()).decode()`
- **Decoding:** `json.loads(base64.b64decode(cursor).decode())`

### API Key Management

**Phase 1 (Local):**
- Hardcoded test key: `test-api-key-12345`
- Environment variable: `AUTH_MODE=local`

**Phase 2+ (AWS):**
- Stored in DynamoDB `triggers-api-keys-{stage}` table
- Environment variable: `AUTH_MODE=aws`
- Dual-mode support: Application supports both local and AWS modes via `AUTH_MODE` env var
- API key seeding: `python scripts/seed_api_keys.py --api-key <key> --stage prod --region us-east-1`

### Error Handling

**Exception Classes:**
- `ValidationError` - Invalid request payload (400)
- `UnauthorizedError` - Missing/invalid API key (401)
- `ForbiddenError` - IP address not allowed (403) (Phase 8)
- `NotFoundError` - Resource not found (404)
- `ConflictError` - Resource conflict (e.g., already acknowledged) (409)
- `PayloadTooLargeError` - Payload exceeds 400KB (413)
- `RateLimitExceededError` - Rate limit exceeded (429) (Phase 8)
- `InternalError` - Server error (500)

**Error Response Format:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {},
    "request_id": "uuid-v4"
  }
}
```

## Testing Strategy

### Test Types

1. **Unit Tests:** Fast, isolated, high coverage
2. **Integration Tests:** Components with mocked dependencies
3. **E2E Tests:** Real server with DynamoDB Local
4. **Playwright MCP Tests:** HTTP testing via Playwright
5. **Browser Tests:** UI testing (Phase 6)
6. **Load Tests:** Performance testing with k6 (Phase 7)

### Test Execution

**Single Command:**
```bash
./scripts/run_tests.sh
# Or using Python:
python scripts/run_tests.py
```

**Individual Test Suites:**
```bash
pytest tests/unit/ -v              # Unit tests only
pytest tests/integration/ -v       # Integration tests only
pytest tests/e2e/ -v               # E2E tests (requires DynamoDB Local)
pytest tests/playwright/ -v        # Playwright MCP tests (requires running server)
```

**Coverage Requirements:**
- Overall: >80% code coverage ✅ (Currently: 47% with new Phase 8 code, needs more tests)
- Critical paths: 100% coverage (endpoints, auth, database)
- Error handling: 100% coverage
- Current Status: 130+ unit tests passing, Phase 8 features tested

## Deployment

### Local Deployment (Phase 1)

1. Start DynamoDB Local: `docker-compose up`
2. Create tables: Automatic on FastAPI startup
3. Start FastAPI: `uvicorn src.main:app --reload`

### AWS Deployment (Phase 2+)

**Method 1: AWS CLI (Current)**
1. Build deployment package: `docker run --rm --platform linux/amd64 -v "$(pwd):/var/task" -w /var/task public.ecr.aws/sam/build-python3.11:latest /bin/bash -c "mkdir -p .deploy && pip install -r requirements.txt -t .deploy && cp -r src .deploy/ && cd .deploy && zip -r ../lambda-deployment.zip . -q"`
2. Deploy: `./scripts/deploy_aws.sh`
3. Test: Use deployed API Gateway URL

**Method 2: AWS SAM (Alternative)**
1. Build: `sam build` (has handler validation issues with SAM CLI 1.146.0)
2. Deploy: `sam deploy --guided`
3. Test: Use deployed API Gateway URL

**Note:** Currently using AWS CLI method due to SAM CLI compatibility issues with Python 3.14/Pydantic.

## Known Technical Considerations

### DynamoDB Limitations

- **Total Count:** Not efficiently supported (removed from pagination)
- **Filtering:** FilterExpression applied after query (may affect pagination)
- **GSI Design:** Status-based GSI sufficient for MVP scale

### Lambda Considerations

- **Cold Starts:** Acceptable for MVP (< 2 seconds)
- **Memory:** Default configuration sufficient
- **Timeout:** Default timeout sufficient

### API Gateway Considerations

- **CORS:** Configured in Phase 2
- **Throttling:** Not implemented in MVP (can use API Gateway throttling)
- **Custom Domain:** Not required for MVP

---

## Phase 8 Enhancements

### Rate Limiting
- **Algorithm:** Token bucket with 60-second windows
- **Storage:** DynamoDB table `triggers-api-rate-limits-{stage}`
- **Configuration:** Per-API-key (default: 1000 requests/min)
- **Headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **Error:** 429 with `Retry-After` header

### Bulk Operations
- **Endpoints:** `POST /v1/events/bulk`, `POST /v1/events/bulk/ack`, `DELETE /v1/events/bulk`
- **Batch Size:** Max 25 items per request (DynamoDB limit)
- **Features:** Partial success handling, idempotency support, detailed error reporting

### Advanced Filtering
- **Parameters:** `created_after`, `created_before`, `priority`, `metadata_key`, `metadata_value`
- **Implementation:** Dynamic FilterExpression building for DynamoDB queries
- **Performance:** Applied to inbox queries with optimized expressions

### IP Allowlisting
- **Support:** Exact IP matches and CIDR notation (IPv4 and IPv6)
- **Headers:** Extracts from `X-Forwarded-For`, `X-Real-IP`, or `request.client.host`
- **Configuration:** Per-API-key (empty list = allow all, backward compatible)
- **Error:** 403 Forbidden for blocked IPs

---

**Document Status:** Active  
**Last Updated:** 2025-11-11 (Phase 8 completion - API Enhancements & Developer Experience)

