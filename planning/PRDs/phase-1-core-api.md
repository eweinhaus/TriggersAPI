# Phase 1: Core API Backend - PRD

**Phase:** 1 of 6  
**Priority:** P0 (Must Have)  
**Estimated Duration:** 2-3 hours  
**Dependencies:** None

---

## 1. Executive Summary

Phase 1 delivers a working FastAPI application with all 4 P0 endpoints, testable locally using DynamoDB Local. This phase establishes the core functionality without AWS deployment complexity, enabling rapid development and testing.

**Goal:** Working API with all P0 endpoints, testable locally with cURL/Postman.

---

## 2. Scope

### In Scope
- FastAPI application structure
- All 4 P0 endpoints with /v1 prefix (POST /v1/events, GET /v1/inbox, POST /v1/events/{id}/ack, DELETE /v1/events/{id})
- Health check endpoint (GET /v1/health)
- DynamoDB integration (using DynamoDB Local)
- Basic API key authentication (hardcoded test key for MVP)
- Request ID tracking (generate and include in all responses)
- Local development environment setup
- Basic error handling
- Project structure and dependencies

### Out of Scope
- AWS deployment (Phase 2)
- Comprehensive testing (Phase 3)
- P1 features (Phase 4)
- Documentation (Phase 5)
- Frontend (Phase 6)

---

## 3. Functional Requirements

**API Versioning:** All endpoints are prefixed with `/v1` to allow for future API versions.

### 3.1 GET /v1/health - Health Check

**Purpose:** Health check endpoint for monitoring and deployment verification.

**Request:**
```
GET /v1/health
No authentication required
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "ISO 8601",
  "version": "1.0.0"
}
```

**Implementation Details:**
- No authentication required
- Simple endpoint to verify API is running
- Returns current timestamp (ISO 8601 UTC) and API version
- No database connectivity check (simple health check for MVP)
- Fast response time (< 10ms target)

### 3.2 POST /v1/events - Event Ingestion

**Purpose:** Accept events from external systems and store them durably.

**Request:**
```
POST /v1/events
Headers:
  Content-Type: application/json
  X-API-Key: <api_key> (required)
  X-Request-ID: <request_id> (optional, for request tracking)

Body:
{
  "source": "string (required)",
  "event_type": "string (required, e.g., 'user.created')",
  "payload": {} (required, any valid JSON),
  "metadata": {
    "correlation_id": "string (optional)",
    "priority": "low|normal|high (optional, default: normal)",
    "idempotency_key": "string (optional, accepted but ignored in Phase 1)"
  }
}
```

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

**Error Responses:**
- `400 Bad Request`: Invalid payload, missing required fields
- `401 Unauthorized`: Missing or invalid API key
- `500 Internal Server Error`: Server error

**Implementation Details:**
- Generate unique `event_id` using `uuid.uuid4()` (Python's uuid module)
  - Convert to string: `str(uuid.uuid4())` (lowercase UUID format)
- Record server timestamp as `created_at` in ISO 8601 format (UTC)
  - Format: `YYYY-MM-DDTHH:MM:SS.ffffffZ` (e.g., "2024-01-01T12:00:00.123456Z")
  - Use: `datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')`
- Set initial `status` to "pending"
- Calculate TTL: `int(time.time()) + (7 * 24 * 60 * 60)` (7 days in seconds, UTC)
- Store event in DynamoDB Events table
- Accept `idempotency_key` in metadata but ignore it (store in metadata map, no duplicate prevention)
- Validate payload size: reject if > 400KB (return 413 Payload Too Large)
- Generate or use provided request ID from `X-Request-ID` header
  - Use `uuid.uuid4()` if header not provided
  - Store as lowercase string
- Include request ID in response
- Return acknowledgment immediately (async processing not required)

### 3.3 GET /v1/inbox - Retrieve Undelivered Events

**Purpose:** List events that are pending delivery (not yet acknowledged).

**Request:**
```
GET /v1/inbox?limit=50&cursor=<base64>&source=<source>&event_type=<type>
Headers:
  X-API-Key: <api_key> (required)
  X-Request-ID: <request_id> (optional, for request tracking)

Query Parameters:
  limit: integer (optional, default: 50, max: 100)
  cursor: string (optional, base64-encoded DynamoDB LastEvaluatedKey)
  source: string (optional, filter by source)
  event_type: string (optional, filter by event type)
```

**Response (200 OK):**
```json
{
  "events": [
    {
      "event_id": "uuid-v4",
      "created_at": "ISO 8601",
      "source": "string",
      "event_type": "string",
      "payload": {},
      "status": "pending",
      "metadata": {}
    }
  ],
  "pagination": {
    "next_cursor": "string (optional, base64-encoded)",
    "limit": 50
  },
  "request_id": "uuid-v4"
}
```

**Implementation Details:**
- Query DynamoDB using GSI `status-created_at-index`
- Filter by `status = "pending"` in query key condition
- Order by `created_at` (oldest first, ascending)
- Support pagination using DynamoDB `LastEvaluatedKey` as cursor
  - Encode cursor: `base64.b64encode(json.dumps(last_evaluated_key).encode()).decode()`
  - Decode cursor: `json.loads(base64.b64decode(cursor).decode())`
- Filter by `source` and `event_type` using FilterExpression (applied after query)
  - **Note:** FilterExpression filters results AFTER DynamoDB query
  - This means you may query 100 items but return fewer after filtering
  - Pagination cursor includes all queried items, not just filtered results
  - Client should continue pagination even if filtered results are fewer than limit
- Limit results to max 100 per request
- **Pagination Note:** Total count is not provided (DynamoDB doesn't efficiently support this)
- Generate or use provided request ID from `X-Request-ID` header
- Include request ID in response

### 3.4 POST /v1/events/{event_id}/ack - Acknowledge Event

**Purpose:** Mark an event as acknowledged/delivered after processing.

**Request:**
```
POST /v1/events/{event_id}/ack
Headers:
  X-API-Key: <api_key> (required)
  X-Request-ID: <request_id> (optional, for request tracking)

Path Parameters:
  event_id: string (required, UUID v4)
```

**Response (200 OK):**
```json
{
  "event_id": "uuid-v4",
  "status": "acknowledged",
  "acknowledged_at": "ISO 8601",
  "message": "Event acknowledged successfully",
  "request_id": "uuid-v4"
}
```

**Error Responses:**
- `404 Not Found`: Event not found
- `409 Conflict`: Event already acknowledged
- `401 Unauthorized`: Invalid API key

**Implementation Details:**
- Update event `status` to "acknowledged"
- Record `acknowledged_at` timestamp (UTC, ISO 8601 format: `YYYY-MM-DDTHH:MM:SS.ffffffZ`)
- Use DynamoDB conditional update to prevent race conditions and double-acknowledgment:
  ```python
  UpdateExpression = "SET #status = :status, acknowledged_at = :ack_at"
  ConditionExpression = "#status = :pending"
  ExpressionAttributeNames = {"#status": "status"}
  ExpressionAttributeValues = {
      ":status": "acknowledged",
      ":pending": "pending",
      ":ack_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
  }
  ```
- If condition fails (already acknowledged), return 409 Conflict
- Event remains in database but excluded from inbox queries
- Idempotent operation (multiple acks return same result if already acknowledged)
- Generate or use provided request ID from `X-Request-ID` header
- Include request ID in response

### 3.5 DELETE /v1/events/{event_id} - Delete Event

**Purpose:** Permanently delete an event from the system.

**Request:**
```
DELETE /v1/events/{event_id}
Headers:
  X-API-Key: <api_key> (required)
  X-Request-ID: <request_id> (optional, for request tracking)

Path Parameters:
  event_id: string (required, UUID v4)
```

**Response (200 OK):**
```json
{
  "event_id": "uuid-v4",
  "message": "Event deleted successfully",
  "request_id": "uuid-v4"
}
```

**Implementation Details:**
- Permanently remove event from DynamoDB
- Idempotent (deleting non-existent event returns 200)
- No soft delete required for MVP
- Generate or use provided request ID from `X-Request-ID` header
- Include request ID in response

---

## 4. Technical Requirements

### 4.1 Project Structure

```
triggers-api/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # Pydantic models
│   ├── database.py          # DynamoDB client wrapper
│   ├── auth.py              # API key validation
│   └── endpoints/
│       ├── __init__.py
│       ├── events.py        # Event endpoints
│       └── inbox.py         # Inbox endpoints
├── scripts/
│   ├── seed_api_keys.py     # Create test API keys
│   └── local_setup.sh       # Local development setup
├── docker-compose.yml       # DynamoDB Local
├── requirements.txt
├── .env.example
└── README.md
```

### 4.2 Dependencies

**Python Packages:**
- `fastapi>=0.104.0`
- `uvicorn[standard]>=0.24.0`
- `pydantic>=2.0.0`
- `boto3>=1.28.0`
- `python-dotenv>=1.0.0`

**Development Tools:**
- Docker & Docker Compose (for DynamoDB Local)
- Python 3.11+

### 4.3 DynamoDB Schema (Local)

**Events Table:** `triggers-api-events`
- Partition Key: `event_id` (String, UUID v4)
- Sort Key: `created_at` (String, ISO 8601)
- Attributes:
  - `source` (String, required)
  - `event_type` (String, required)
  - `payload` (Map, required, any JSON)
  - `status` (String, required: "pending" | "acknowledged")
  - `metadata` (Map, optional)
  - `acknowledged_at` (String, ISO 8601, optional)
  - `ttl` (Number, Unix timestamp, 7 days from creation)
- **Note:** For MVP, no scaling concerns. This schema is sufficient for low-to-moderate volume.

**Inbox GSI:** `status-created_at-index`
- Partition Key: `status` (String)
- Sort Key: `created_at` (String)
- Projection: All attributes
- **Note:** For MVP scale, this GSI design is sufficient. No sharding needed.

**API Keys Table:** `triggers-api-keys`
- Partition Key: `api_key` (String)
- Attributes:
  - `source` (String, optional)
  - `created_at` (String, ISO 8601)
  - `is_active` (Boolean, default: true)

### 4.4 API Key Authentication

**For MVP (Phase 1):**
- Use hardcoded test API key: `test-api-key-12345`
- Validate `X-API-Key` header on all endpoints (except /v1/health)
- Return `401 Unauthorized` if missing or invalid
- Store API keys in DynamoDB for Phase 2 (migration path documented)

**Implementation:**
- Create `src/auth.py` with `validate_api_key()` function
- Use FastAPI dependency injection for authentication
- Apply to all endpoints via dependency (except health check)
- Support environment variable `AUTH_MODE=local` for hardcoded key mode
- When `AUTH_MODE=local`, validate against hardcoded key `test-api-key-12345`
- Return `401 Unauthorized` with request_id if invalid or missing

### 4.5 Error Handling

**Basic Error Response Format:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {},
    "request_id": "uuid-v4"
  }
}
```

**Request ID Tracking:**
- All requests generate a unique request ID (UUID v4)
- If client provides `X-Request-ID` header, use that; otherwise generate one using `uuid.uuid4()`
- Request ID is included in all responses (success and error)
- Request ID is logged for debugging
- **Implementation:** Use FastAPI middleware to extract/generate request ID:
  ```python
  @app.middleware("http")
  async def add_request_id(request: Request, call_next):
      request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
      request.state.request_id = request_id
      response = await call_next(request)
      # Add request_id to response headers and body
      response.headers["X-Request-ID"] = request_id
      return response
  ```
- In endpoints, access via: `request.state.request_id`

**Error Codes & HTTP Status Mapping:**
- `VALIDATION_ERROR` → 400 Bad Request (Invalid request payload)
- `UNAUTHORIZED` → 401 Unauthorized (Missing or invalid API key)
- `NOT_FOUND` → 404 Not Found (Resource not found)
- `CONFLICT` → 409 Conflict (Resource conflict, e.g., already acknowledged)
- `PAYLOAD_TOO_LARGE` → 413 Payload Too Large (Payload exceeds 400KB)
- `INTERNAL_ERROR` → 500 Internal Server Error (Server error)

**Error Handler Implementation:**
- Create custom exception classes in `src/exceptions.py`
- Register exception handlers in `src/main.py`:
  ```python
  @app.exception_handler(ValidationError)  # Pydantic validation errors
  @app.exception_handler(HTTPException)    # HTTP exceptions
  @app.exception_handler(Exception)         # Unexpected errors
  ```
- All handlers must include `request_id` in error response
- Log full stack traces when `LOG_LEVEL=DEBUG`, sanitized messages when `LOG_LEVEL=INFO`

### 4.6 Local Development Setup

**DynamoDB Local:**
- Use Docker Compose to run DynamoDB Local
- Endpoint: `http://localhost:8000` (DynamoDB Local default)
- **Table Creation:** Tables are created automatically on application startup
  - Create `scripts/create_tables.py` to initialize tables
  - Tables should be idempotent (check if exists before creating)
  - Run automatically when FastAPI app starts (via startup event)
  - Tables: `triggers-api-events`, `triggers-api-keys`

**Environment Variables:**
- `DYNAMODB_ENDPOINT_URL`: `http://localhost:8000` (for local, required)
- `AWS_REGION`: `us-east-1` (default, required)
- `AWS_ACCESS_KEY_ID`: `test` (for local, required)
- `AWS_SECRET_ACCESS_KEY`: `test` (for local, required)
- `AUTH_MODE`: `local` (default for Phase 1, uses hardcoded key)
- `LOG_LEVEL`: `INFO` (default, use `DEBUG` for full stack traces in development)

**FastAPI Server:**
- Run with `uvicorn src.main:app --reload`
- Default port: `8000`
- Auto-reload on code changes

---

## 5. Implementation Steps

1. **Project Setup**
   - Create project structure
   - Initialize virtual environment
   - Install dependencies
   - Create `requirements.txt`

2. **DynamoDB Local Setup**
   - Create `docker-compose.yml` for DynamoDB Local:
     ```yaml
     version: '3.8'
     services:
       dynamodb-local:
         image: amazon/dynamodb-local:latest
         ports:
           - "8000:8000"
         command: "-jar DynamoDBLocal.jar -sharedDb"
     ```
   - Create `scripts/create_tables.py` to initialize tables (idempotent)
   - Tables created automatically on FastAPI startup (via startup event)
   - Test DynamoDB connection

3. **Core Models**
   - Create Pydantic models in `src/models.py`
   - Define Event, EventCreate, EventResponse models
   - Define error response models
   - Use Pydantic v2 with strict validation:
     ```python
     from pydantic import BaseModel, ConfigDict
     
     class EventCreate(BaseModel):
         model_config = ConfigDict(extra='forbid')  # Reject unknown fields
         source: str
         event_type: str
         payload: dict
         metadata: dict | None = None
     ```
   - Validate UUID format in path parameters using FastAPI's UUID type

4. **Database Layer**
   - Create `src/database.py` with DynamoDB client
   - Implement table creation functions (idempotent - check if exists)
   - Implement CRUD operations for events
   - Handle DynamoDB errors gracefully (ConditionalCheckFailedException → 409 Conflict)
   - Use boto3's DynamoDB resource or client (resource recommended for simplicity)

5. **Authentication**
   - Create `src/auth.py` with API key validation
   - Implement hardcoded test key for MVP
   - Create FastAPI dependency

6. **Endpoints**
   - Create `src/endpoints/events.py` with POST /v1/events
   - Create `src/endpoints/inbox.py` with GET /v1/inbox
   - Add GET /v1/health endpoint
   - Add POST /v1/events/{id}/ack endpoint
   - Add DELETE /v1/events/{id} endpoint
   - Implement request ID tracking middleware

7. **FastAPI App**
   - Create `src/main.py` with FastAPI app
   - Use APIRouter with `/v1` prefix:
     ```python
     from fastapi import APIRouter
     v1_router = APIRouter(prefix="/v1")
     app.include_router(v1_router)
     ```
   - Add request ID middleware (extract/generate, attach to request.state)
   - Add error handlers (with request ID in responses)
   - Add startup event to create DynamoDB tables automatically
   - **Note:** CORS middleware not needed for Phase 1 (local development only)

8. **Scripts**
   - Create `scripts/seed_api_keys.py` for test keys
   - Create `scripts/local_setup.sh` for setup

9. **Testing**
   - Test with cURL commands
   - Verify all endpoints work
   - Test error cases

10. **Documentation**
    - Create basic README.md
    - Document local setup steps
    - Include example cURL commands

---

## 6. Success Criteria

- [ ] All 4 P0 endpoints implemented and functional (with /v1 prefix)
- [ ] Health check endpoint (GET /v1/health) implemented
- [ ] Events stored in DynamoDB Local successfully
- [ ] API key authentication works on all endpoints (except health)
- [ ] Request ID tracking implemented and included in all responses
- [ ] Can test all endpoints with cURL/Postman locally
- [ ] Basic project structure complete
- [ ] Error handling returns appropriate status codes with request IDs
- [ ] Pagination works for GET /v1/inbox (cursor-based, no total count)
- [ ] Filtering by source and event_type works
- [ ] Acknowledgment flow works end-to-end
- [ ] Delete operation works correctly

---

## 7. Testing Strategy

### Manual Testing
- Use cURL or Postman to test all endpoints
- Test happy paths for all operations
- Test error cases (invalid API key, missing fields, etc.)
- Test pagination with multiple events
- Test filtering functionality

### Test Scenarios
1. **GET /v1/health:**
   - Health check → 200 OK with status "healthy"
   - No authentication required

2. **POST /v1/events:**
   - Valid event → 201 Created with request_id
   - Missing required field → 400 Bad Request with request_id
   - Invalid API key → 401 Unauthorized with request_id
   - Request ID in response matches X-Request-ID header if provided

3. **GET /v1/inbox:**
   - Empty inbox → 200 OK with empty array and request_id
   - Multiple events → 200 OK with events and pagination object
   - With pagination → 200 OK with cursor
   - With filters → 200 OK with filtered results
   - Request ID in response

4. **POST /v1/events/{id}/ack:**
   - Valid event → 200 OK, status updated, request_id included
   - Already acknowledged → 409 Conflict with request_id
   - Non-existent event → 404 Not Found with request_id

5. **DELETE /v1/events/{id}:**
   - Valid event → 200 OK, event deleted, request_id included
   - Non-existent event → 200 OK (idempotent), request_id included

---

## 8. Known Limitations (Phase 1)

- No comprehensive unit tests (Phase 3)
- Hardcoded API key (will be migrated to DynamoDB in Phase 2)
- No AWS deployment (Phase 2)
- Basic error handling (enhanced in Phase 3)
- No rate limiting (out of scope for MVP)
- DynamoDB Local only (AWS in Phase 2)
- Idempotency key accepted but ignored (stored in metadata, no duplicate prevention until Phase 4)
- Request ID tracking is basic (no distributed tracing)
- No CORS middleware (not needed for local development, added in Phase 2)
- Pagination doesn't include total count (DynamoDB limitation, removed for simplicity)

---

## 9. Next Steps

After Phase 1 completion:
- Proceed to Phase 2: AWS Infrastructure & Deployment
- Deploy API to AWS Lambda
- Set up production DynamoDB tables
- Configure API Gateway

---

**Phase Status:** Not Started  
**Completion Date:** TBD

