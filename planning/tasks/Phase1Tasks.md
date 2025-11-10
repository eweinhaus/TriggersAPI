# Phase 1: Core API Backend - Task List

**Phase:** 1 of 6  
**Priority:** P0 (Must Have)  
**Status:** ✅ Completed  
**Created:** 2024-01-XX  
**Completed:** 2025-11-10

---

## Overview

This task list covers the implementation of Phase 1: Core API Backend. The goal is to deliver a working FastAPI application with all P0 endpoints, testable locally using DynamoDB Local.

**Key Deliverables:**
- FastAPI application with 5 endpoints (health + 4 P0 endpoints)
- DynamoDB Local integration with auto-created tables
- API key authentication (hardcoded for MVP)
- Request ID tracking middleware
- Standardized error handling
- Local development environment setup

---

## Task Breakdown

### 1. Project Setup & Structure

#### 1.1 Create Project Structure
- [ ] Create `src/` directory with `__init__.py`
- [ ] Create `src/endpoints/` directory with `__init__.py`
- [ ] Create `scripts/` directory
- [ ] Create `tests/` directory structure (for future use)

#### 1.2 Initialize Python Environment
- [ ] Create virtual environment (venv or similar)
- [ ] Create `requirements.txt` with dependencies:
  - `fastapi>=0.104.0`
  - `uvicorn[standard]>=0.24.0`
  - `pydantic>=2.0.0`
  - `boto3>=1.28.0`
  - `python-dotenv>=1.0.0`
- [ ] Install dependencies
- [ ] Create `.env.example` with required environment variables

#### 1.3 Create Basic Configuration Files
- [ ] Create `README.md` with project overview
- [ ] Create `.gitignore` (if not exists)
- [ ] Document local setup steps in README

---

### 2. DynamoDB Local Setup

#### 2.1 Docker Compose Configuration
- [ ] Create `docker-compose.yml` for DynamoDB Local
  - Use image: `amazon/dynamodb-local:latest`
  - Expose port: `8000`
  - Command: `-jar DynamoDBLocal.jar -sharedDb`
- [ ] Test DynamoDB Local starts correctly: `docker-compose up -d`
- [ ] Verify DynamoDB Local accessible at `http://localhost:8000`

#### 2.2 Table Creation Script
- [ ] Create `scripts/create_tables.py`
- [ ] Implement function to create `triggers-api-events` table:
  - Partition Key: `event_id` (String)
  - Sort Key: `created_at` (String)
  - GSI: `status-created_at-index` (Partition: `status`, Sort: `created_at`, Projection: ALL)
  - TTL attribute: `ttl`
- [ ] Implement function to create `triggers-api-keys` table:
  - Partition Key: `api_key` (String)
- [ ] Make table creation idempotent (check if exists before creating)
- [ ] Handle `ResourceInUseException` gracefully
- [ ] Test script runs successfully

#### 2.3 Database Client Setup
- [ ] Create `src/database.py`
- [ ] Implement DynamoDB client initialization:
  - Read `DYNAMODB_ENDPOINT_URL` from environment (default: `http://localhost:8000`)
  - Read `AWS_REGION` from environment (default: `us-east-1`)
  - Read `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (use `test` for local)
  - Create boto3 DynamoDB resource/client
- [ ] Implement `create_tables()` function that calls table creation script
- [ ] Test database connection

---

### 3. Core Models (Pydantic)

#### 3.1 Create Pydantic Models
- [ ] Create `src/models.py`
- [ ] Implement `EventCreate` model:
  - `source: str` (required)
  - `event_type: str` (required)
  - `payload: dict` (required, any JSON)
  - `metadata: dict | None = None` (optional)
  - Use `ConfigDict(extra='forbid')` to reject unknown fields
- [ ] Implement `EventMetadata` model (optional, for nested validation):
  - `correlation_id: str | None = None`
  - `priority: Literal["low", "normal", "high"] = "normal"`
  - `idempotency_key: str | None = None`
- [ ] Implement `EventResponse` model:
  - `event_id: str`
  - `created_at: str` (ISO 8601)
  - `status: str`
  - `message: str`
  - `request_id: str`
- [ ] Implement `InboxResponse` model:
  - `events: list[dict]`
  - `pagination: dict` (with `next_cursor` and `limit`)
  - `request_id: str`
- [ ] Implement `AckResponse` model:
  - `event_id: str`
  - `status: str`
  - `acknowledged_at: str`
  - `message: str`
  - `request_id: str`
- [ ] Implement `DeleteResponse` model:
  - `event_id: str`
  - `message: str`
  - `request_id: str`
- [ ] Implement `ErrorResponse` model:
  - `error: dict` with `code`, `message`, `details`, `request_id`
- [ ] Implement `HealthResponse` model:
  - `status: str`
  - `timestamp: str`
  - `version: str`

---

### 4. Database Layer

#### 4.1 Event CRUD Operations
- [ ] Implement `create_event()` function in `src/database.py`:
  - Accept event data (source, event_type, payload, metadata)
  - Generate `event_id` using `uuid.uuid4()` (lowercase string)
  - Generate `created_at` timestamp (ISO 8601 UTC with Z suffix)
  - Set `status` to "pending"
  - Calculate `ttl` (7 days from now, Unix timestamp)
  - Store in DynamoDB Events table
  - Return event data
- [ ] Implement `get_event()` function:
  - Query by `event_id` (partition key)
  - Return event data or None
- [ ] Implement `query_pending_events()` function:
  - Query GSI `status-created_at-index` with `status = "pending"`
  - Order by `created_at` (ascending, oldest first)
  - Support pagination with `LastEvaluatedKey` (cursor)
  - Support filtering by `source` and `event_type` using FilterExpression
  - Limit results (max 100)
  - Return events and pagination info
- [ ] Implement `acknowledge_event()` function:
  - Use DynamoDB conditional update:
    - `UpdateExpression`: `SET #status = :status, acknowledged_at = :ack_at`
    - `ConditionExpression`: `#status = :pending`
  - Set `acknowledged_at` timestamp (ISO 8601 UTC with Z)
  - Handle `ConditionalCheckFailedException` (return None or raise)
  - Return updated event data
- [ ] Implement `delete_event()` function:
  - Delete by `event_id`
  - Idempotent (no error if doesn't exist)
  - Return success boolean

#### 4.2 Error Handling
- [ ] Map DynamoDB `ConditionalCheckFailedException` to conflict errors
- [ ] Map DynamoDB `ResourceNotFoundException` to not found errors
- [ ] Handle other DynamoDB exceptions gracefully

---

### 5. Authentication

#### 5.1 API Key Validation
- [ ] Create `src/auth.py`
- [ ] Implement `validate_api_key()` function:
  - Read `AUTH_MODE` from environment (default: `local`)
  - If `AUTH_MODE=local`, validate against hardcoded key `test-api-key-12345`
  - Extract `X-API-Key` header from request
  - Return API key if valid, raise exception if invalid
- [ ] Create FastAPI dependency `get_api_key()`:
  - Use `Depends()` to inject request
  - Call `validate_api_key()`
  - Raise `HTTPException(401)` if invalid
  - Return API key if valid

---

### 6. Exception Handling

#### 6.1 Custom Exceptions
- [ ] Create `src/exceptions.py`
- [ ] Implement custom exception classes:
  - `ValidationError` (400 Bad Request)
  - `UnauthorizedError` (401 Unauthorized)
  - `NotFoundError` (404 Not Found)
  - `ConflictError` (409 Conflict)
  - `PayloadTooLargeError` (413 Payload Too Large)
  - `InternalError` (500 Internal Server Error)
- [ ] Each exception should include error code and message

#### 6.2 Exception Handlers
- [ ] In `src/main.py`, register exception handlers:
  - Pydantic `ValidationError` → 400 with standardized format
  - Custom exceptions → appropriate status codes
  - `HTTPException` → standardized format
  - Generic `Exception` → 500 with sanitized message
- [ ] All handlers must:
  - Extract `request_id` from `request.state.request_id`
  - Return standardized error response format
  - Include `request_id` in error response
  - Log errors (full stack trace if `LOG_LEVEL=DEBUG`)

---

### 7. Request ID Middleware

#### 7.1 Middleware Implementation
- [ ] In `src/main.py`, create request ID middleware:
  - Extract `X-Request-ID` header from request
  - If not provided, generate UUID v4 (lowercase string)
  - Store in `request.state.request_id`
  - Add `X-Request-ID` header to response
  - Ensure request ID is accessible in all endpoints and error handlers

---

### 8. Endpoints Implementation

#### 8.1 Health Check Endpoint
- [ ] Create `src/endpoints/health.py` (or add to main.py)
- [ ] Implement `GET /v1/health`:
  - No authentication required
  - Return `{"status": "healthy", "timestamp": "ISO 8601", "version": "1.0.0"}`
  - Fast response (< 10ms target)

#### 8.2 Event Ingestion Endpoint
- [ ] Create `src/endpoints/events.py`
- [ ] Implement `POST /v1/events`:
  - Require API key authentication (use dependency)
  - Accept `EventCreate` model in request body
  - Validate payload size (reject if > 400KB, return 413)
  - Generate `event_id` (UUID v4, lowercase)
  - Generate `created_at` timestamp (ISO 8601 UTC with Z)
  - Set `status` to "pending"
  - Calculate TTL (7 days from now)
  - Store event in DynamoDB
  - Accept `idempotency_key` in metadata (store but ignore)
  - Return `EventResponse` with `request_id` from middleware
  - Handle errors with appropriate status codes

#### 8.3 Inbox Endpoint
- [ ] Create `src/endpoints/inbox.py`
- [ ] Implement `GET /v1/inbox`:
  - Require API key authentication
  - Accept query parameters:
    - `limit: int = 50` (max 100)
    - `cursor: str | None = None` (base64-encoded)
    - `source: str | None = None`
    - `event_type: str | None = None`
  - Decode cursor if provided (base64 → JSON → LastEvaluatedKey)
  - Query DynamoDB using GSI `status-created_at-index`
  - Filter by `status = "pending"` in key condition
  - Order by `created_at` (ascending)
  - Apply FilterExpression for `source` and `event_type` if provided
  - Encode `LastEvaluatedKey` as cursor if more results exist
  - Return `InboxResponse` with events, pagination, and `request_id`
  - Handle errors appropriately

#### 8.4 Acknowledge Endpoint
- [ ] Add to `src/endpoints/events.py`
- [ ] Implement `POST /v1/events/{event_id}/ack`:
  - Require API key authentication
  - Validate `event_id` is valid UUID (use FastAPI UUID type)
  - Call `acknowledge_event()` from database layer
  - If event not found, return 404
  - If already acknowledged (ConditionalCheckFailedException), return 409 Conflict
  - Return `AckResponse` with `request_id`
  - Handle errors appropriately

#### 8.5 Delete Endpoint
- [ ] Add to `src/endpoints/events.py`
- [ ] Implement `DELETE /v1/events/{event_id}`:
  - Require API key authentication
  - Validate `event_id` is valid UUID
  - Call `delete_event()` from database layer
  - Idempotent (return 200 even if event doesn't exist)
  - Return `DeleteResponse` with `request_id`
  - Handle errors appropriately

---

### 9. FastAPI Application Setup

#### 9.1 Main Application
- [ ] Create `src/main.py`
- [ ] Initialize FastAPI app
- [ ] Create `APIRouter` with `/v1` prefix
- [ ] Include routers:
  - Health endpoint
  - Events endpoints
  - Inbox endpoint
- [ ] Register exception handlers (from step 6.2)
- [ ] Add request ID middleware (from step 7.1)

#### 9.2 Startup Event
- [ ] Add startup event handler to `src/main.py`:
  - Call `create_tables()` from database layer
  - Handle errors gracefully (log but don't crash)
  - Ensure tables are created before API accepts requests

---

### 10. Utility Functions

#### 10.1 Timestamp Utilities
- [ ] Create utility function for ISO 8601 UTC timestamps:
  - Format: `YYYY-MM-DDTHH:MM:SS.ffffffZ`
  - Use: `datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')`
  - Use consistently across all endpoints

#### 10.2 UUID Utilities
- [ ] Ensure UUID generation uses `uuid.uuid4()` and converts to lowercase string
- [ ] Use consistently for `event_id` and `request_id`

#### 10.3 Cursor Encoding/Decoding
- [ ] Create utility functions for cursor encoding:
  - Encode: `base64.b64encode(json.dumps(last_evaluated_key).encode()).decode()`
  - Decode: `json.loads(base64.b64decode(cursor).decode())`
- [ ] Handle encoding/decoding errors gracefully

#### 10.4 Payload Size Validation
- [ ] Create utility function to validate payload size:
  - Calculate JSON payload size
  - Reject if > 400KB
  - Return appropriate error

---

### 11. Scripts

#### 11.1 Local Setup Script
- [ ] Create `scripts/local_setup.sh`:
  - Start DynamoDB Local (docker-compose up)
  - Wait for DynamoDB to be ready
  - Create tables (optional, since auto-created on startup)
  - Print setup instructions

#### 11.2 Seed API Keys Script (Optional for Phase 1)
- [ ] Create `scripts/seed_api_keys.py`:
  - For Phase 1, this is optional (using hardcoded key)
  - Can create placeholder for Phase 2 migration

---

### 12. Testing & Verification

#### 12.1 Manual Testing with cURL
- [ ] Test `GET /v1/health`:
  - Verify 200 OK response
  - Verify no authentication required
  - Verify response format matches spec

- [ ] Test `POST /v1/events`:
  - Valid event → 201 Created with `request_id`
  - Missing API key → 401 Unauthorized with `request_id`
  - Invalid API key → 401 Unauthorized with `request_id`
  - Missing required field → 400 Bad Request with `request_id`
  - Payload > 400KB → 413 Payload Too Large with `request_id`
  - Unknown fields → 400 Bad Request (Pydantic strict validation)
  - Verify `X-Request-ID` header works (if provided, use it; otherwise generate)

- [ ] Test `GET /v1/inbox`:
  - Empty inbox → 200 OK with empty array and `request_id`
  - Multiple events → 200 OK with events and pagination
  - With pagination cursor → 200 OK with next page
  - With `source` filter → 200 OK with filtered results
  - With `event_type` filter → 200 OK with filtered results
  - With both filters → 200 OK with filtered results
  - Missing API key → 401 Unauthorized
  - Verify `request_id` in response

- [ ] Test `POST /v1/events/{id}/ack`:
  - Valid pending event → 200 OK, status updated to "acknowledged"
  - Already acknowledged event → 409 Conflict with `request_id`
  - Non-existent event → 404 Not Found with `request_id`
  - Invalid UUID format → 422 Validation Error
  - Missing API key → 401 Unauthorized
  - Verify `acknowledged_at` timestamp set
  - Verify `request_id` in response

- [ ] Test `DELETE /v1/events/{id}`:
  - Valid event → 200 OK, event deleted
  - Non-existent event → 200 OK (idempotent)
  - Invalid UUID format → 422 Validation Error
  - Missing API key → 401 Unauthorized
  - Verify `request_id` in response

#### 12.2 End-to-End Flow Testing
- [ ] Test complete workflow:
  1. Create event via `POST /v1/events`
  2. Verify event appears in `GET /v1/inbox`
  3. Acknowledge event via `POST /v1/events/{id}/ack`
  4. Verify event no longer appears in `GET /v1/inbox`
  5. Delete event via `DELETE /v1/events/{id}`
  6. Verify event deleted (404 on get)

- [ ] Test pagination flow:
  1. Create multiple events (more than limit)
  2. Query first page with `limit=10`
  3. Use `next_cursor` to query next page
  4. Verify all events retrieved across pages

- [ ] Test filtering flow:
  1. Create events with different sources and event types
  2. Filter by `source`
  3. Filter by `event_type`
  4. Filter by both
  5. Verify correct events returned

#### 12.3 Error Handling Verification
- [ ] Verify all error responses include `request_id`
- [ ] Verify error format matches specification
- [ ] Verify appropriate HTTP status codes
- [ ] Test error cases for each endpoint

---

### 13. Documentation

#### 13.1 README Updates
- [ ] Update `README.md` with:
  - Project overview
  - Local setup instructions
  - Environment variables documentation
  - How to start DynamoDB Local
  - How to start FastAPI server
  - Example cURL commands for all endpoints
  - Testing instructions

#### 13.2 Code Documentation
- [ ] Add docstrings to all functions and classes
- [ ] Document complex logic (pagination, filtering, conditional updates)
- [ ] Add inline comments where necessary

---

## Success Criteria Checklist

- [x] All 4 P0 endpoints implemented and functional (with /v1 prefix)
- [x] Health check endpoint (GET /v1/health) implemented
- [x] Events stored in DynamoDB Local successfully
- [x] API key authentication works on all endpoints (except health)
- [x] Request ID tracking implemented and included in all responses
- [x] Can test all endpoints with cURL/Postman locally
- [x] Basic project structure complete
- [x] Error handling returns appropriate status codes with request IDs
- [x] Pagination works for GET /v1/inbox (cursor-based, no total count)
- [x] Filtering by source and event_type works
- [x] Acknowledgment flow works end-to-end
- [x] Delete operation works correctly
- [x] Payload size validation works (400KB limit)
- [x] Pydantic strict validation rejects unknown fields
- [x] Conditional updates prevent double-acknowledgment
- [x] Tables auto-created on application startup

---

## Notes & Considerations

### Port Configuration
- DynamoDB Local: `http://localhost:8000`
- FastAPI Server: Consider using port `8080` to avoid conflict, or configure accordingly
- Update documentation with correct ports

### Testing Approach
- Manual testing with cURL/Postman for Phase 1
- Comprehensive automated testing in Phase 3
- Focus on happy paths and critical error cases

### Known Limitations (Phase 1)
- Hardcoded API key (migrated to DynamoDB in Phase 2)
- Basic error handling (enhanced in Phase 3)
- No comprehensive unit tests (Phase 3)
- No CORS middleware (not needed for local development)
- Idempotency key accepted but ignored (implemented in Phase 4)

### Critical Implementation Details
- UUID format: lowercase string (e.g., "550e8400-e29b-41d4-a716-446655440000")
- Timestamp format: ISO 8601 UTC with Z suffix and microseconds (e.g., "2024-01-01T12:00:00.123456Z")
- TTL calculation: `int(time.time()) + (7 * 24 * 60 * 60)` (7 days in seconds)
- Cursor encoding: Base64-encoded JSON of DynamoDB LastEvaluatedKey
- FilterExpression applied after query (affects pagination behavior)

---

## Next Steps After Completion

After Phase 1 completion:
1. Proceed to Phase 2: AWS Infrastructure & Deployment
2. Deploy API to AWS Lambda
3. Set up production DynamoDB tables
4. Configure API Gateway
5. Migrate API key authentication to DynamoDB

---

**Task List Status:** ✅ Completed  
**Last Updated:** 2025-11-10  
**Completion Notes:** All tasks completed and tested. All endpoints functional. Issues with DynamoDB reserved keywords resolved. Request validation error handling added.

