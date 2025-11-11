# System Patterns: Zapier Triggers API

## Architecture Overview

The system follows a serverless, event-driven architecture on AWS:

```
Frontend (S3 + CloudFront) → API Gateway → Lambda (FastAPI) → DynamoDB
                                    ↓
                            CloudWatch (Logs & Metrics)
```

### Phase 1 (Local Development)
```
FastAPI App → DynamoDB Local
```

### Phase 2+ (AWS Production)
```
Frontend (S3 + CloudFront)
    ↓
API Gateway (REST API)
    ↓
Lambda Function (FastAPI via Mangum)
    ↓
DynamoDB (Events + API Keys + Idempotency tables)
    ↓
CloudWatch (Logs & Metrics)
```

**Deployment Architecture:**
- Frontend: S3 static hosting + CloudFront CDN (Phase 6)
  - S3 Bucket: `triggers-api-frontend-971422717446`
  - CloudFront Distribution: `E1392QCULSIX14`
  - Error handling: S3 error document + CloudFront custom error responses (403/404 → 200 → `/index.html`)
  - API URL: `https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod/v1` (includes `/v1` prefix)
- API Gateway: Regional REST API with `/v1/{proxy+}` catch-all route
- Lambda: Python 3.11 runtime, handler: `src.main.handler`
  - IAM Permissions: DynamoDB (GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan), CloudWatch Logs, CloudWatch Metrics (PutMetricData, GetMetricStatistics, ListMetrics)
- DynamoDB: On-demand billing, TTL enabled, GSI for inbox queries and event lookup
  - Events table: `triggers-api-events-prod`
    - GSI: `status-created_at-index` (inbox queries)
    - GSI: `event-id-index` (event lookup optimization - Phase 7)
  - API Keys table: `triggers-api-keys-prod`
  - Idempotency table: `triggers-api-idempotency-prod` (Phase 4)
  - Rate Limits table: `triggers-api-rate-limits-prod` (Phase 8)

## Component Architecture

### Backend Components

1. **FastAPI Application**
   - RESTful API framework
   - Request/response handling
   - Authentication middleware
   - Error handling
   - Request ID tracking

2. **DynamoDB Storage**
   - Events table (primary storage)
   - Inbox GSI (status-based queries)
   - Event lookup GSI (event-id-index for O(1) lookup - Phase 7)
   - API Keys table (authentication)
   - Idempotency table (Phase 4 - implemented)

3. **Authentication & Security Layer**
   - API key validation
   - Header-based authentication (X-API-Key)
   - Dependency injection pattern
   - IP allowlisting (Phase 8) - Optional IP-based access control with CIDR support
   - Rate limiting (Phase 8) - Configurable per API key with token bucket algorithm

4. **Error Handling**
   - Custom exception classes (APIException base class)
   - Standardized error responses with request IDs
   - Request ID correlation in all responses
   - Structured JSON logging with request IDs (Phase 7)
   - Exception handlers for all error types
   - Pydantic validation error handling

5. **Observability (Phase 7)**
   - Structured JSON logging (CloudWatch Log Insights compatible)
   - CloudWatch metrics (latency, success rate, error rate, request count)
   - Request context tracking (request_id, api_key, endpoint, method, duration_ms)
   - CloudWatch dashboard and alarms
   - Load testing infrastructure (k6)

## Design Patterns

### 1. API Versioning Pattern

**Implementation:**
- All endpoints prefixed with `/v1`
- Uses FastAPI `APIRouter` with prefix
- Allows future API versions without breaking changes

**Code Pattern:**
```python
v1_router = APIRouter(prefix="/v1")
app.include_router(v1_router)
```

### 2. Request ID Tracking Pattern

**Implementation:**
- Middleware extracts/generates request ID
- Stored in `request.state.request_id`
- Included in all responses (success and error)
- Logged for correlation

**Code Pattern:**
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### 3. Dependency Injection Pattern (Authentication)

**Implementation:**
- FastAPI dependency for API key validation
- Applied to all endpoints (except health check)
- Returns authenticated context or raises exception

**Code Pattern:**
```python
async def validate_api_key(request: Request):
    api_key = request.headers.get("X-API-Key")
    if not api_key or not is_valid(api_key):
        raise HTTPException(status_code=401, ...)
    return api_key
```

### 4. Conditional Update Pattern (Idempotency)

**Implementation:**
- DynamoDB conditional updates prevent race conditions
- Used for acknowledgment to prevent double-processing
- Returns 409 Conflict if condition fails
- Also used for idempotency key storage (Phase 4)

**Code Pattern:**
```python
# Acknowledgment
UpdateExpression = "SET #status = :status, acknowledged_at = :ack_at"
ConditionExpression = "#status = :pending"

# Idempotency key storage
ConditionExpression = "attribute_not_exists(idempotency_key)"
```

### 9. Rate Limiting Pattern (Phase 8)

**Implementation:**
- Token bucket algorithm with 60-second windows
- Rate limit state stored in DynamoDB (rate limits table)
- Per-API-key configuration (default: 1000 requests/min)
- Rate limit headers in all responses
- 429 status code with Retry-After header when limit exceeded

**Code Pattern:**
```python
# Check rate limit
allowed, remaining, reset_timestamp = check_rate_limit(api_key, limit, 60)

# Increment rate limit
increment_rate_limit(api_key, window_start, limit)

# Middleware adds headers
response.headers["X-RateLimit-Limit"] = str(limit)
response.headers["X-RateLimit-Remaining"] = str(remaining)
response.headers["X-RateLimit-Reset"] = str(reset_timestamp)
```

### 10. IP Allowlisting Pattern (Phase 8)

**Implementation:**
- Optional IP-based access control per API key
- Supports exact IP matches and CIDR notation
- Extracts client IP from proxy headers (X-Forwarded-For, X-Real-IP)
- Empty allowlist = allow all (backward compatible)
- Returns 403 Forbidden for blocked IPs

**Code Pattern:**
```python
# Extract client IP
client_ip = extract_client_ip(request)

# Get allowed IPs for API key
allowed_ips = get_allowed_ips_for_api_key(api_key)

# Validate IP
if not ip_matches_allowlist(client_ip, allowed_ips or []):
    raise ForbiddenError("IP address not allowed")
```

### 11. Bulk Operations Pattern (Phase 8)

**Implementation:**
- Process up to 25 items per request (DynamoDB batch limit)
- Partial success handling (returns both successful and failed items)
- Idempotency support for bulk create
- Detailed error reporting per failed item

**Code Pattern:**
```python
# Bulk create
successful, failed = bulk_create_events(events, api_key)

# Response includes both successful and failed items
return BulkEventResponse(
    successful=successful,
    failed=[BulkItemError(index=i, error=err) for i, err in failed],
    request_id=request_id
)
```

### 12. Advanced Filtering Pattern (Phase 8)

**Implementation:**
- Dynamic FilterExpression building for DynamoDB queries
- Supports date range, priority, and metadata field filters
- Filters can be combined (AND logic)
- Applied to inbox queries

**Code Pattern:**
```python
# Build filter expression
if created_after:
    filter_expressions.append('created_at >= :created_after')
if priority:
    filter_expressions.append('metadata.#priority = :priority')
if metadata_filters:
    for key, value in metadata_filters.items():
        filter_expressions.append(f'metadata.#{key} = :{value}')

query_params['FilterExpression'] = ' AND '.join(filter_expressions)
```

### 13. Idempotency Key Pattern (Phase 4)

**Implementation:**
- Separate DynamoDB table for idempotency keys
- Check idempotency key before event creation
- Return existing event if key found
- Store idempotency key mapping with 24-hour TTL
- Conditional writes prevent race conditions

**Code Pattern:**
```python
# Check for existing event
existing_event_id = check_idempotency_key(idempotency_key)
if existing_event_id:
    return get_event(existing_event_id)

# Create new event and store idempotency key
event = create_event(...)
store_idempotency_key(idempotency_key, event['event_id'])
```

### 5. Pagination Pattern (Cursor-Based)

**Implementation:**
- Uses DynamoDB `LastEvaluatedKey` as cursor
- Base64-encoded JSON for cursor transport
- No total count (DynamoDB limitation)

**Code Pattern:**
```python
# Encode
cursor = base64.b64encode(json.dumps(last_evaluated_key).encode()).decode()

# Decode
last_evaluated_key = json.loads(base64.b64decode(cursor).decode())
```

### 5a. Event Lookup Pattern (GSI Optimization - Phase 7)

**Implementation:**
- `get_event()` uses GSI `event-id-index` for O(1) lookup when available
- Falls back to scan operation for backward compatibility (tables without GSI)
- Uses `ConsistentRead=True` in scan fallback to ensure recently written items are found
- GSI query is much faster than scan (O(1) vs O(n))

**Code Pattern:**
```python
# Scan with pagination
scan_kwargs = {
    'FilterExpression': 'event_id = :event_id',
    'ExpressionAttributeValues': {':event_id': event_id},
    'ConsistentRead': True,
    'Limit': 100
}
while True:
    response = table.scan(**scan_kwargs)
    items = response.get('Items', [])
    if items:
        return items[0]
    last_evaluated_key = response.get('LastEvaluatedKey')
    if not last_evaluated_key:
        return None
    scan_kwargs['ExclusiveStartKey'] = last_evaluated_key
```

### 6. Error Response Standardization with Enhanced Messages

**Implementation:**
- Consistent error format across all endpoints
- Error codes map to HTTP status codes
- Request ID always included
- Structured error details with actionable suggestions
- Exception handlers registered in FastAPI app
- Pydantic validation errors formatted consistently
- Error message utility functions (format_validation_error, format_not_found_error, format_conflict_error)
- Error details include field names, issues, and suggestions

**Error Format:**
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

**Error Codes:**
- `VALIDATION_ERROR` (400) - Invalid request payload or parameters
- `UNAUTHORIZED` (401) - Missing or invalid API key
- `FORBIDDEN` (403) - IP address not allowed (Phase 8)
- `NOT_FOUND` (404) - Resource not found
- `CONFLICT` (409) - Resource conflict (e.g., already acknowledged)
- `PAYLOAD_TOO_LARGE` (413) - Payload exceeds 400KB limit
- `RATE_LIMIT_EXCEEDED` (429) - Rate limit exceeded (Phase 8)
- `INTERNAL_ERROR` (500) - Server error

## Data Models

### Event Model

```python
{
  "event_id": "uuid-v4",
  "created_at": "ISO 8601",
  "source": "string",
  "event_type": "string",
  "payload": {},  # Any valid JSON
  "status": "pending" | "acknowledged",
  "metadata": {
    "correlation_id": "string",
    "priority": "low" | "normal" | "high",
    "idempotency_key": "string"
  },
  "acknowledged_at": "ISO 8601",
  "ttl": 1234567890  # Unix timestamp
}
```

### API Key Model

```python
{
  "api_key": "string",
  "source": "string",
  "created_at": "ISO 8601",
  "is_active": true,
  "rate_limit": 1000,  # Optional (Phase 8) - requests per minute, default 1000
  "allowed_ips": ["1.2.3.4", "5.6.7.0/24"]  # Optional (Phase 8) - empty list = allow all
}
```

## Database Schema

### Events Table (`triggers-api-events`)

- **Partition Key:** `event_id` (String, UUID v4)
- **Sort Key:** `created_at` (String, ISO 8601)
- **Attributes:** source, event_type, payload, status, metadata, acknowledged_at, ttl
- **TTL Attribute:** `ttl` (Number, Unix timestamp, 7 days)
- **Billing Mode:** On-demand

### Inbox GSI (`status-created_at-index`)

- **Partition Key:** `status` (String)
- **Sort Key:** `created_at` (String)
- **Projection:** All attributes
- **Purpose:** Query pending events efficiently

### API Keys Table (`triggers-api-keys-{stage}`)

- **Partition Key:** `api_key` (String)
- **Attributes:** source, created_at, is_active
- **Billing Mode:** On-demand
- **Stage-based naming:** Table name includes deployment stage (e.g., `triggers-api-keys-prod`)

### Idempotency Table (`triggers-api-idempotency`) - Phase 4 ✅

- **Partition Key:** `idempotency_key` (String)
- **Attributes:** event_id (String), created_at (ISO 8601)
- **TTL Attribute:** `ttl` (Number, Unix timestamp, 24 hours)
- **Billing Mode:** On-demand
- **Status:** Implemented and functional

### Rate Limits Table (`triggers-api-rate-limits-{stage}`) - Phase 8 ✅

- **Partition Key:** `api_key` (String)
- **Sort Key:** `window_start` (Number, Unix timestamp)
- **Attributes:** request_count (Number), ttl (Number)
- **TTL Attribute:** `ttl` (Number, Unix timestamp, 1 hour from window_start)
- **Billing Mode:** On-demand
- **Status:** Implemented and functional

## Component Relationships

### Request Flow

1. **Client** → API Gateway (Phase 2+) or FastAPI directly (Phase 1)
2. **Middleware** → Request ID extraction/generation
3. **Authentication** → API key validation
4. **IP Validation** → IP allowlisting check (Phase 8)
5. **Rate Limiting** → Rate limit check and increment (Phase 8)
6. **Endpoint Handler** → Business logic
7. **Database Layer** → DynamoDB operations
8. **Response** → Standardized format with request ID and rate limit headers

### Error Flow

1. **Exception Raised** → Custom exception or system exception
2. **Exception Handler** → Catches and formats error
3. **Error Response** → Standardized format with request ID
4. **Logging** → Error logged with request ID for correlation

## Key Technical Decisions

### 1. FastAPI Framework
- **Rationale:** Modern, fast, async-capable, auto-documentation
- **Benefits:** Type hints, Pydantic validation, OpenAPI generation

### 2. DynamoDB Storage
- **Rationale:** Serverless, scalable, managed service
- **Benefits:** No server management, on-demand scaling, built-in encryption

### 3. Lambda Deployment
- **Rationale:** Serverless, cost-effective, auto-scaling
- **Benefits:** Pay-per-use, no infrastructure management

### 4. API Gateway
- **Rationale:** Managed HTTP interface, built-in features
- **Benefits:** CORS, throttling, authentication integration

### 5. Cursor-Based Pagination
- **Rationale:** Efficient for DynamoDB, no total count needed
- **Benefits:** Scalable, fast, simple implementation

### 6. Request ID Tracking
- **Rationale:** Essential for debugging and support
- **Benefits:** Request correlation, easier troubleshooting

## Security Patterns

### Authentication
- API key in `X-API-Key` header
- Validated on all endpoints (except health check)
- Dual-mode support:
  - **Local mode (`AUTH_MODE=local`):** Hardcoded test key `test-api-key-12345`
  - **AWS mode (`AUTH_MODE=aws`):** Validated against DynamoDB `triggers-api-keys-{stage}` table
- API keys stored in DynamoDB with `is_active` flag for revocation
- **IP Allowlisting (Phase 8):** Optional per-API-key IP allowlist with CIDR support
- **Rate Limiting (Phase 8):** Configurable per-API-key rate limits (default: 1000 requests/min)

### Data Protection
- TLS 1.2+ for data in transit
- DynamoDB encryption at rest
- Input validation via Pydantic
- Payload size limits (400KB max)

## Scalability Patterns

### Horizontal Scaling
- Lambda auto-scaling (AWS managed)
- DynamoDB on-demand billing (no capacity planning)
- Stateless API design

### Performance Optimization
- Efficient DynamoDB queries (GSI for inbox)
- Minimal data transfer (pagination)
- Fast response times (< 100ms target)

---

## Testing Patterns

### 7. Test Organization Pattern

**Implementation:**
- Unit tests: Fast, isolated, use mocks (moto for DynamoDB)
- Integration tests: Test full workflows with mocked services
- E2E tests: Test against real server with DynamoDB Local
- Playwright MCP tests: HTTP-based tests using httpx

**Test Structure:**
```
tests/
├── unit/              # Fast, isolated tests (117 tests, 87% coverage)
├── integration/       # Full workflow tests
├── e2e/              # Real server tests
├── playwright/       # HTTP-based API tests
└── utils/            # Test utilities and helpers
```

### 8. Test Fixture Pattern

**Implementation:**
- Base fixtures in `tests/conftest.py` (app, client, dynamodb_table, api_key, sample_event)
- Integration fixtures in `tests/integration/conftest.py` (mock_dynamodb_resource)
- E2E fixtures in `tests/e2e/conftest.py` (dynamodb_local, api_server, e2e_client)
- Playwright fixtures in `tests/playwright/conftest.py` (api_base_url, playwright_api_key)
- Environment reset fixture for test isolation

---

**Document Status:** Active  
**Last Updated:** 2025-11-11 (Phase 7: Observability & Performance - Architecture updated with observability components)

