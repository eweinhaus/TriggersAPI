# System Patterns: Zapier Triggers API

## Architecture Overview

The system follows a serverless, event-driven architecture on AWS:

```
API Gateway → Lambda (FastAPI) → DynamoDB
                ↓
            CloudWatch (Logs & Metrics)
```

### Phase 1 (Local Development)
```
FastAPI App → DynamoDB Local
```

### Phase 2+ (AWS Production)
```
API Gateway (REST API)
    ↓
Lambda Function (FastAPI via Mangum)
    ↓
DynamoDB (Events + API Keys tables)
    ↓
CloudWatch (Logs & Metrics)
```

**Deployment Architecture:**
- API Gateway: Regional REST API with `/v1/{proxy+}` catch-all route
- Lambda: Python 3.11 runtime, handler: `src.main.handler`
- DynamoDB: On-demand billing, TTL enabled, GSI for inbox queries
- IAM: Lambda execution role with DynamoDB and CloudWatch permissions

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
   - API Keys table (authentication)
   - Idempotency table (Phase 4)

3. **Authentication Layer**
   - API key validation
   - Header-based authentication (X-API-Key)
   - Dependency injection pattern

4. **Error Handling**
   - Custom exception classes
   - Standardized error responses
   - Request ID correlation
   - Structured logging

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

**Code Pattern:**
```python
UpdateExpression = "SET #status = :status, acknowledged_at = :ack_at"
ConditionExpression = "#status = :pending"
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

### 6. Error Response Standardization

**Implementation:**
- Consistent error format across all endpoints
- Error codes map to HTTP status codes
- Request ID always included
- Structured error details

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
  "is_active": true
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

### Idempotency Table (`triggers-api-idempotency`) - Phase 4

- **Partition Key:** `idempotency_key` (String)
- **Attributes:** event_id, created_at
- **TTL Attribute:** `ttl` (Number, Unix timestamp, 24 hours)
- **Billing Mode:** On-demand

## Component Relationships

### Request Flow

1. **Client** → API Gateway (Phase 2+) or FastAPI directly (Phase 1)
2. **Middleware** → Request ID extraction/generation
3. **Authentication** → API key validation
4. **Endpoint Handler** → Business logic
5. **Database Layer** → DynamoDB operations
6. **Response** → Standardized format with request ID

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

**Document Status:** Active  
**Last Updated:** Initial creation

