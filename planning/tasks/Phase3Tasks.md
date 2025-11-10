# Phase 3: Testing & Error Handling - Task List

**Phase:** 3 of 6  
**Priority:** P0 (Must Have)  
**Status:** Not Started  
**Created:** 2024-01-XX  
**Dependencies:** Phase 1 (Core API), Phase 2 (AWS Infrastructure)

---

## Overview

This task list covers the implementation of Phase 3: Testing & Error Handling. The goal is to make the API production-ready with comprehensive testing (>80% coverage) and standardized error handling.

**Key Deliverables:**
- Unit tests with >80% code coverage
- Integration tests with mocked AWS services
- End-to-end (E2E) tests against real running API server
- Playwright MCP tests for API endpoints
- Standardized error response format
- Enhanced input validation
- Test automation script (single command)
- Test fixtures and utilities

---

## Task Breakdown

### 1. Testing Infrastructure Setup

#### 1.1 Install Testing Dependencies
- [ ] Update `requirements.txt` or create `requirements-dev.txt` with:
  - `pytest>=7.4.0`
  - `pytest-cov>=4.1.0` (coverage reporting)
  - `pytest-asyncio>=0.21.0` (if using async)
  - `moto>=4.2.0` (AWS service mocking)
  - `httpx>=0.25.0` (HTTP client for testing)
  - `faker>=19.0.0` (test data generation)
  - `pytest-xdist>=3.0.0` (parallel test execution, optional)
  - `pytest-timeout>=2.1.0` (test timeout management, optional)
- [ ] Install testing dependencies
- [ ] Verify all packages install correctly

#### 1.2 Create Test Directory Structure
- [ ] Create `tests/` directory with `__init__.py`
- [ ] Create `tests/unit/` directory with `__init__.py`
- [ ] Create `tests/integration/` directory with `__init__.py`
- [ ] Create `tests/e2e/` directory with `__init__.py`
- [ ] Create `tests/playwright/` directory with `__init__.py`
- [ ] Create `tests/utils/` directory with `__init__.py`
- [ ] Verify directory structure matches PRD specification

#### 1.3 Configure pytest
- [ ] Create `pytest.ini` in project root:
  - Set `testpaths = tests`
  - Set `python_files = test_*.py`
  - Set `python_classes = Test*`
  - Set `python_functions = test_*`
  - Configure coverage options:
    - `--cov=src`
    - `--cov-report=html`
    - `--cov-report=term-missing`
    - `--cov-fail-under=80`
  - Set `-v` for verbose output
- [ ] Create `.coveragerc` (optional, for advanced coverage config):
  - Exclude migrations, config files, test files
  - Include all source code in `src/`
- [ ] Test pytest configuration: `pytest --collect-only`

---

### 2. Test Fixtures & Utilities

#### 2.1 Create Base Test Fixtures (`tests/conftest.py`)
- [ ] Create `app` fixture:
  - Returns FastAPI app instance
  - Use test configuration
  - Ensure clean state
- [ ] Create `client` fixture:
  - Returns `httpx.TestClient` for FastAPI app
  - Use `app` fixture as dependency
- [ ] Create `dynamodb_table` fixture:
  - Use `moto` to create mock DynamoDB table
  - Create `triggers-api-events` table with correct schema
  - Create GSI `status-created_at-index`
  - Return table resource
  - Clean up after test
- [ ] Create `api_key` fixture:
  - Return test API key string
  - Use hardcoded key for Phase 1 compatibility
- [ ] Create `sample_event` fixture:
  - Return sample event data dict
  - Use `faker` for realistic test data
  - Include all required fields (source, event_type, payload)
- [ ] Create `request_id` fixture:
  - Generate UUID v4 for request ID
  - Use in tests that need request ID

#### 2.2 Create Test Utilities (`tests/utils/`)
- [ ] Create `tests/utils/fixtures.py`:
  - `generate_event_data()` - Generate random event data
  - `generate_multiple_events()` - Generate N events for pagination tests
  - `create_test_event_in_db()` - Helper to create event in database
  - `create_test_api_key()` - Helper to create test API key
- [ ] Create `tests/utils/test_helpers.py`:
  - `assert_error_response()` - Verify error response format
  - `assert_success_response()` - Verify success response format
  - `assert_request_id_present()` - Verify request ID in response
  - `encode_cursor()` - Helper for cursor encoding
  - `decode_cursor()` - Helper for cursor decoding
  - `calculate_payload_size()` - Helper for payload size validation

#### 2.3 Create Integration Test Fixtures (`tests/integration/conftest.py`)
- [ ] Create `mock_dynamodb` fixture:
  - Use `moto` to mock DynamoDB
  - Set up mock tables
  - Return mock DynamoDB resource
- [ ] Create `integration_client` fixture:
  - Use mocked DynamoDB
  - Return test client for integration tests

#### 2.4 Create E2E Test Fixtures (`tests/e2e/conftest.py`)
- [ ] Create `dynamodb_local` fixture:
  - Start DynamoDB Local (Docker) if not running
  - Create tables in DynamoDB Local
  - Clean up after test
  - Handle Docker connection errors
- [ ] Create `api_server` fixture:
  - Start FastAPI server on test port (e.g., 8081)
  - Use DynamoDB Local endpoint
  - Wait for server to be ready
  - Stop server after test
  - Handle port conflicts
- [ ] Create `e2e_client` fixture:
  - Return `httpx.AsyncClient` or `httpx.Client` for real server
  - Use `api_server` fixture as dependency
  - Point to test server URL
- [ ] Create `cleanup_events` fixture:
  - Clean up test events after each test
  - Query and delete all test events
  - Run in `yield` pattern for cleanup

#### 2.5 Create Playwright MCP Test Fixtures (`tests/playwright/conftest.py`)
- [ ] Create `api_base_url` fixture:
  - Return base URL for API (local or deployed)
  - Read from environment variable or default to `http://localhost:8000`
- [ ] Create `playwright_api_key` fixture:
  - Return test API key for Playwright tests
- [ ] Create `playwright_client` fixture (if needed):
  - Set up HTTP client for Playwright MCP tests
  - Configure base URL and headers

---

### 3. Error Handling Standardization

#### 3.1 Create Custom Exception Classes (`src/exceptions.py`)
- [ ] Create base exception class `TriggersAPIError`:
  - Base class for all custom exceptions
  - Include error code and message attributes
- [ ] Create `ValidationError(TriggersAPIError)`:
  - Status code: 400
  - Error code: `VALIDATION_ERROR`
  - Include field details
- [ ] Create `UnauthorizedError(TriggersAPIError)`:
  - Status code: 401
  - Error code: `UNAUTHORIZED`
- [ ] Create `NotFoundError(TriggersAPIError)`:
  - Status code: 404
  - Error code: `NOT_FOUND`
- [ ] Create `ConflictError(TriggersAPIError)`:
  - Status code: 409
  - Error code: `CONFLICT`
  - Include conflict details
- [ ] Create `RateLimitExceededError(TriggersAPIError)`:
  - Status code: 429
  - Error code: `RATE_LIMIT_EXCEEDED`
- [ ] Create `PayloadTooLargeError(TriggersAPIError)`:
  - Status code: 413
  - Error code: `PAYLOAD_TOO_LARGE`
- [ ] Create `InternalError(TriggersAPIError)`:
  - Status code: 500
  - Error code: `INTERNAL_ERROR`

#### 3.2 Implement Error Handlers (`src/main.py`)
- [ ] Create `triggers_api_error_handler()`:
  - Handle `TriggersAPIError` exceptions
  - Extract request ID from `request.state.request_id`
  - Format error response with standardized format
  - Include request ID in error response
  - Return appropriate HTTP status code
- [ ] Create `validation_error_handler()`:
  - Handle Pydantic `ValidationError` exceptions
  - Extract field errors from Pydantic
  - Format as `VALIDATION_ERROR` with field details
  - Include request ID
  - Return 400 status code
- [ ] Create `http_exception_handler()`:
  - Handle FastAPI `HTTPException`
  - Convert to standardized error format
  - Include request ID
  - Preserve status code
- [ ] Create `generic_exception_handler()`:
  - Handle unexpected exceptions
  - Log full stack trace (if `LOG_LEVEL=DEBUG`)
  - Return sanitized error message
  - Return 500 status code
  - Include request ID
- [ ] Register all exception handlers in FastAPI app:
  - Use `@app.exception_handler()` decorator
  - Register in correct order (specific to generic)

#### 3.3 Update Existing Endpoints to Use Custom Exceptions
- [ ] Update `POST /v1/events`:
  - Raise `ValidationError` for invalid payload
  - Raise `PayloadTooLargeError` for payload > 400KB
  - Raise `UnauthorizedError` for invalid API key
  - Raise `InternalError` for database errors
- [ ] Update `GET /v1/inbox`:
  - Raise `UnauthorizedError` for invalid API key
  - Raise `ValidationError` for invalid query parameters
  - Raise `InternalError` for database errors
- [ ] Update `POST /v1/events/{id}/ack`:
  - Raise `NotFoundError` for non-existent event
  - Raise `ConflictError` for already acknowledged event
  - Raise `UnauthorizedError` for invalid API key
  - Raise `InternalError` for database errors
- [ ] Update `DELETE /v1/events/{id}`:
  - Raise `UnauthorizedError` for invalid API key
  - Raise `InternalError` for database errors
  - Note: Delete is idempotent, no NotFoundError needed

#### 3.4 Verify Error Response Format
- [ ] All error responses include `request_id` field
- [ ] All error responses follow standardized format:
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
- [ ] Error codes map to correct HTTP status codes
- [ ] Error messages are user-friendly (not stack traces)

---

### 4. Enhanced Input Validation

#### 4.1 Update Pydantic Models with Strict Validation
- [ ] Update `EventCreate` model:
  - Add field validators for `source`:
    - Required, non-empty string
    - Max 100 characters
    - Custom error messages
  - Add field validators for `event_type`:
    - Required, non-empty string
    - Max 100 characters
    - Custom error messages
  - Add field validators for `payload`:
    - Required, valid JSON object
    - Not empty dict
    - Custom error messages
  - Add field validators for `metadata`:
    - Optional, valid JSON object if provided
    - Validate `metadata.priority` enum: "low", "normal", "high"
    - Custom error messages
  - Ensure `ConfigDict(extra='forbid')` is set
- [ ] Update query parameter models:
  - `limit`: Integer, 1-100, default 50
  - `cursor`: Optional string, base64 format validation
  - `source`: Optional string, non-empty if provided
  - `event_type`: Optional string, non-empty if provided
- [ ] Add custom validators for business rules:
  - Payload size validation (400KB limit)
  - UUID format validation for event IDs
  - Timestamp format validation

#### 4.2 Improve Error Messages
- [ ] Update Pydantic error messages:
  - Field-specific error messages
  - Clear validation failure reasons
  - Examples of valid values
- [ ] Add validation error details:
  - Include field name in error details
  - Include specific issue description
  - Include expected format/values

#### 4.3 Test Validation Edge Cases
- [ ] Test empty strings for required fields
- [ ] Test strings exceeding max length
- [ ] Test invalid JSON in payload
- [ ] Test invalid enum values
- [ ] Test missing required fields
- [ ] Test unknown fields (should be rejected)
- [ ] Test payload size > 400KB
- [ ] Test invalid UUID formats

---

### 5. Unit Tests

#### 5.1 Event Endpoint Unit Tests (`tests/unit/test_events.py`)
- [ ] Test `POST /v1/events` - Success cases:
  - Valid event creation → 201 Created
  - Verify `event_id` in response
  - Verify `request_id` in response
  - Verify `status` is "pending"
  - Verify event stored in database
- [ ] Test `POST /v1/events` - Error cases:
  - Missing `source` → 400 Validation Error
  - Missing `event_type` → 400 Validation Error
  - Missing `payload` → 400 Validation Error
  - Empty `source` → 400 Validation Error
  - Empty `event_type` → 400 Validation Error
  - Invalid `payload` (not JSON object) → 400 Validation Error
  - Payload > 400KB → 413 Payload Too Large
  - Unknown fields → 400 Validation Error
  - Missing API key → 401 Unauthorized
  - Invalid API key → 401 Unauthorized
  - Database error → 500 Internal Error
- [ ] Test `POST /v1/events/{id}/ack` - Success cases:
  - Valid acknowledgment → 200 OK
  - Verify `status` updated to "acknowledged"
  - Verify `acknowledged_at` timestamp set
  - Verify `request_id` in response
- [ ] Test `POST /v1/events/{id}/ack` - Error cases:
  - Non-existent event → 404 Not Found
  - Already acknowledged event → 409 Conflict
  - Invalid UUID format → 422 Validation Error
  - Missing API key → 401 Unauthorized
  - Invalid API key → 401 Unauthorized
  - Database error → 500 Internal Error
- [ ] Test `DELETE /v1/events/{id}` - Success cases:
  - Valid deletion → 200 OK
  - Verify event deleted from database
  - Verify `request_id` in response
  - Idempotent deletion (non-existent event) → 200 OK
- [ ] Test `DELETE /v1/events/{id}` - Error cases:
  - Invalid UUID format → 422 Validation Error
  - Missing API key → 401 Unauthorized
  - Invalid API key → 401 Unauthorized
  - Database error → 500 Internal Error

#### 5.2 Inbox Endpoint Unit Tests (`tests/unit/test_inbox.py`)
- [ ] Test `GET /v1/inbox` - Success cases:
  - Empty inbox → 200 OK with empty array
  - Single event → 200 OK with one event
  - Multiple events → 200 OK with events
  - Verify `request_id` in response
  - Verify pagination structure
- [ ] Test `GET /v1/inbox` - Pagination:
  - First page with `limit=10` → Returns 10 events + cursor
  - Next page with cursor → Returns next 10 events
  - Last page → Returns remaining events, no cursor
  - Invalid cursor → 400 Validation Error
  - Cursor decoding errors → 400 Validation Error
- [ ] Test `GET /v1/inbox` - Filtering:
  - Filter by `source` → Returns filtered events
  - Filter by `event_type` → Returns filtered events
  - Filter by both → Returns filtered events
  - Filter with no matches → Returns empty array
  - Invalid filter values → 400 Validation Error
- [ ] Test `GET /v1/inbox` - Error cases:
  - Invalid `limit` (< 1) → 400 Validation Error
  - Invalid `limit` (> 100) → 400 Validation Error
  - Missing API key → 401 Unauthorized
  - Invalid API key → 401 Unauthorized
  - Database error → 500 Internal Error

#### 5.3 Authentication Unit Tests (`tests/unit/test_auth.py`)
- [ ] Test valid API key:
  - Valid key → Authentication succeeds
  - Request proceeds to endpoint
- [ ] Test invalid API key:
  - Invalid key → 401 Unauthorized
  - Error response includes request ID
- [ ] Test missing API key:
  - No `X-API-Key` header → 401 Unauthorized
  - Error response includes request ID
- [ ] Test expired/inactive API key (if applicable):
  - Inactive key → 401 Unauthorized
  - Error response includes request ID

#### 5.4 Database Layer Unit Tests (`tests/unit/test_database.py`)
- [ ] Test `create_event()`:
  - Creates event with correct structure
  - Generates UUID for `event_id`
  - Sets `created_at` timestamp correctly
  - Sets `status` to "pending"
  - Calculates TTL correctly (7 days)
  - Stores in DynamoDB correctly
- [ ] Test `get_event()`:
  - Retrieves existing event
  - Returns None for non-existent event
- [ ] Test `query_pending_events()`:
  - Queries GSI correctly
  - Orders by `created_at` ascending
  - Handles pagination with cursor
  - Applies filters correctly
  - Respects limit
- [ ] Test `acknowledge_event()`:
  - Updates status to "acknowledged"
  - Sets `acknowledged_at` timestamp
  - Conditional update prevents double-ack
  - Returns None if already acknowledged
  - Returns None if event not found
- [ ] Test `delete_event()`:
  - Deletes existing event
  - Idempotent (no error if doesn't exist)
  - Returns success boolean

#### 5.5 Model Unit Tests (`tests/unit/test_models.py`)
- [ ] Test `EventCreate` model:
  - Valid data → Model created successfully
  - Missing required fields → Validation error
  - Invalid types → Validation error
  - Unknown fields → Validation error (strict mode)
  - Field length validation
  - Enum validation for priority
- [ ] Test `EventResponse` model:
  - Valid data → Model created successfully
  - Required fields present
- [ ] Test `InboxResponse` model:
  - Valid data → Model created successfully
  - Pagination structure correct
- [ ] Test `ErrorResponse` model:
  - Valid error data → Model created successfully
  - All required fields present

---

### 6. Integration Tests

#### 6.1 Full Event Flow Integration Tests (`tests/integration/test_integration.py`)
- [ ] Test complete event lifecycle:
  1. Create event via `POST /v1/events`
  2. Verify event in `GET /v1/inbox`
  3. Acknowledge event via `POST /v1/events/{id}/ack`
  4. Verify event removed from inbox
  5. Delete event via `DELETE /v1/events/{id}`
  6. Verify event deleted
- [ ] Verify request IDs in all responses:
  - Request ID present in create response
  - Request ID present in inbox response
  - Request ID present in ack response
  - Request ID present in delete response
- [ ] Test error scenarios:
  - Invalid requests return proper errors
  - Database errors handled gracefully
  - Authentication failures return 401
  - Error responses include request IDs

#### 6.2 Pagination Integration Tests
- [ ] Test cursor-based pagination:
  - Create 25 events
  - Query with `limit=10` → Returns 10 events + cursor
  - Query next page with cursor → Returns next 10 events + cursor
  - Query last page → Returns remaining 5 events, no cursor
  - Verify all 25 events retrieved across pages
- [ ] Test pagination edge cases:
  - Empty result set → No cursor
  - Single page (results < limit) → No cursor
  - Invalid cursor → 400 Validation Error

#### 6.3 Filtering Integration Tests
- [ ] Test source filter:
  - Create events with different sources
  - Filter by `source` → Returns only matching events
  - Verify filter applied correctly
- [ ] Test event_type filter:
  - Create events with different event types
  - Filter by `event_type` → Returns only matching events
  - Verify filter applied correctly
- [ ] Test combined filters:
  - Filter by both `source` and `event_type`
  - Returns only events matching both filters
  - Verify filter logic correct

---

### 7. End-to-End (E2E) Tests

#### 7.1 E2E Test Setup (`tests/e2e/conftest.py`)
- [ ] Verify `dynamodb_local` fixture:
  - Starts DynamoDB Local if not running
  - Creates tables in DynamoDB Local
  - Cleans up after tests
- [ ] Verify `api_server` fixture:
  - Starts FastAPI server on test port
  - Connects to DynamoDB Local
  - Waits for server to be ready
  - Stops server after tests
- [ ] Verify `e2e_client` fixture:
  - Connects to running API server
  - Uses correct base URL
  - Handles connection errors

#### 7.2 E2E Event Tests (`tests/e2e/test_e2e_events.py`)
- [ ] Test `POST /v1/events` against real server:
  - Create event → 201 Created
  - Verify event stored in DynamoDB Local
  - Verify response format correct
  - Verify request ID present
- [ ] Test `POST /v1/events/{id}/ack` against real server:
  - Acknowledge event → 200 OK
  - Verify status updated in DynamoDB Local
  - Verify `acknowledged_at` timestamp set
  - Test already acknowledged → 409 Conflict
  - Test non-existent event → 404 Not Found
- [ ] Test `DELETE /v1/events/{id}` against real server:
  - Delete event → 200 OK
  - Verify event deleted from DynamoDB Local
  - Test idempotent deletion → 200 OK

#### 7.3 E2E Inbox Tests (`tests/e2e/test_e2e_inbox.py`)
- [ ] Test `GET /v1/inbox` against real server:
  - Query empty inbox → 200 OK with empty array
  - Create events and query → Returns events
  - Verify pagination works
  - Verify filtering works
  - Verify request ID present

#### 7.4 E2E Full Workflow Tests (`tests/e2e/test_e2e_flow.py`)
- [ ] Test complete workflow:
  1. Start server with DynamoDB Local
  2. Create event via `POST /v1/events`
  3. Verify event in `GET /v1/inbox`
  4. Acknowledge event via `POST /v1/events/{id}/ack`
  5. Verify event removed from inbox
  6. Delete event via `DELETE /v1/events/{id}`
  7. Verify event deleted
- [ ] Test error handling with real server:
  - Test 400, 401, 404, 409, 500 responses
  - Verify error response format
  - Verify request IDs in errors
- [ ] Test edge cases with real server:
  - Large payloads (up to 400KB limit)
  - Invalid UUIDs
  - Missing required fields
  - Invalid API keys

---

### 8. Playwright MCP Tests

#### 8.1 Playwright MCP Test Setup (`tests/playwright/conftest.py`)
- [ ] Verify `api_base_url` fixture:
  - Returns correct API base URL
  - Supports local and deployed APIs
- [ ] Verify `playwright_api_key` fixture:
  - Returns test API key
- [ ] Set up Playwright MCP test structure:
  - Import MCP tools for HTTP testing
  - Configure test client
  - Document MCP tool usage

#### 8.2 Playwright MCP API Tests (`tests/playwright/test_api_playwright.py`)
- [ ] Test `GET /v1/health` via Playwright MCP:
  - Make HTTP GET request
  - Verify 200 OK response
  - Verify response body structure
  - Verify no authentication required
- [ ] Test `POST /v1/events` via Playwright MCP:
  - Make HTTP POST request with valid event
  - Verify 201 Created response
  - Verify response body structure
  - Verify `X-Request-ID` header
  - Test error cases (400, 401, 413)
- [ ] Test `GET /v1/inbox` via Playwright MCP:
  - Make HTTP GET request
  - Verify 200 OK response
  - Verify response body structure
  - Verify pagination structure
  - Test with filters
  - Test with pagination cursor
- [ ] Test `POST /v1/events/{id}/ack` via Playwright MCP:
  - Make HTTP POST request
  - Verify 200 OK response
  - Verify response body structure
  - Test error cases (404, 409, 401)
- [ ] Test `DELETE /v1/events/{id}` via Playwright MCP:
  - Make HTTP DELETE request
  - Verify 200 OK response
  - Verify response body structure
  - Test error cases (401, 422)

#### 8.3 Playwright MCP Full Workflow Tests
- [ ] Test complete workflow via Playwright MCP:
  - Create event → Get inbox → Acknowledge → Delete
  - Test with real HTTP requests
  - Verify data persistence
  - Verify request IDs in all responses
- [ ] Test error scenarios via Playwright MCP:
  - Test error responses
  - Verify error format
  - Test authentication failures

#### 8.4 Playwright MCP Test Scenarios (`tests/playwright/api_test_scenarios.py`)
- [ ] Create test scenario functions:
  - `scenario_create_and_acknowledge_event()`
  - `scenario_pagination_flow()`
  - `scenario_filtering_flow()`
  - `scenario_error_handling()`
- [ ] Document Playwright MCP test usage:
  - How to run tests
  - How to configure for local vs deployed API
  - MCP tool requirements

---

### 9. Test Automation Script

#### 9.1 Create Test Automation Script (`scripts/run_tests.sh`)
- [ ] Create shell script that:
  - Checks if DynamoDB Local is running (start if not)
  - Starts FastAPI server for E2E tests (if needed)
  - Runs unit tests: `pytest tests/unit/ -v`
  - Runs integration tests: `pytest tests/integration/ -v`
  - Runs E2E tests: `pytest tests/e2e/ -v`
  - Runs Playwright MCP tests: `pytest tests/playwright/ -v`
  - Generates coverage report: `pytest --cov=src --cov-report=html`
  - Cleans up test resources
  - Exits with proper status code (0 = success, 1 = failure)
- [ ] Make script executable: `chmod +x scripts/run_tests.sh`
- [ ] Test script runs successfully

#### 9.2 Create Python Test Script (Alternative: `scripts/run_tests.py`)
- [ ] Create Python script as alternative:
  - Same functionality as shell script
  - Better cross-platform support
  - More robust error handling
  - Can be run with: `python scripts/run_tests.py`
- [ ] Test Python script runs successfully

#### 9.3 Test Script Requirements
- [ ] Script handles DynamoDB Local:
  - Checks if running (Docker container)
  - Starts if not running
  - Waits for DynamoDB to be ready
  - Handles Docker errors gracefully
- [ ] Script handles FastAPI server:
  - Starts server on test port for E2E tests
  - Waits for server to be ready
  - Stops server after tests
  - Handles port conflicts
- [ ] Script runs all test suites:
  - Unit tests
  - Integration tests
  - E2E tests
  - Playwright MCP tests
- [ ] Script generates coverage report:
  - HTML coverage report
  - Terminal coverage report
  - Fails if coverage < 80%
- [ ] Script cleans up:
  - Stops test server
  - Cleans up test data (optional)
  - Exits with correct status code

---

### 10. Test Execution & Coverage

#### 10.1 Run All Test Suites
- [ ] Run unit tests: `pytest tests/unit/ -v`
  - Verify all tests pass
  - Fix any failing tests
- [ ] Run integration tests: `pytest tests/integration/ -v`
  - Verify all tests pass
  - Fix any failing tests
- [ ] Run E2E tests: `pytest tests/e2e/ -v`
  - Verify all tests pass
  - Fix any failing tests
- [ ] Run Playwright MCP tests: `pytest tests/playwright/ -v`
  - Verify all tests pass
  - Fix any failing tests
- [ ] Run all tests together: `pytest tests/ -v`
  - Verify all tests pass
  - Check total test count

#### 10.2 Generate Coverage Report
- [ ] Run coverage: `pytest --cov=src --cov-report=html --cov-report=term-missing`
- [ ] Verify coverage > 80%:
  - Check terminal output
  - Check HTML report in `htmlcov/`
- [ ] Identify coverage gaps:
  - Review uncovered lines
  - Add tests for uncovered code
  - Aim for 100% coverage on critical paths
- [ ] Fix coverage issues:
  - Add missing tests
  - Remove dead code (if any)
  - Update coverage exclusions if needed

#### 10.3 Verify Test Automation
- [ ] Run test automation script: `./scripts/run_tests.sh`
  - Verify script runs successfully
  - Verify all test suites execute
  - Verify coverage report generated
  - Verify exit code is 0 (success)
- [ ] Test script error handling:
  - Test with DynamoDB Local not running
  - Test with port conflicts
  - Test with failing tests
  - Verify script handles errors gracefully

---

### 11. Documentation

#### 11.1 Test Documentation
- [ ] Document test structure in README:
  - Test directory structure
  - Test types (unit, integration, e2e, playwright)
  - How to run tests
  - Coverage requirements
- [ ] Document test fixtures:
  - Available fixtures
  - How to use fixtures
  - Fixture dependencies
- [ ] Document test utilities:
  - Available helper functions
  - How to use utilities
  - Examples

#### 11.2 Test Execution Documentation
- [ ] Document how to run tests:
  - Single command: `./scripts/run_tests.sh`
  - Individual test suites
  - With coverage
  - Playwright MCP tests
- [ ] Document test requirements:
  - DynamoDB Local setup
  - Environment variables
  - Dependencies
- [ ] Document Playwright MCP test usage:
  - MCP server setup
  - How to configure for local vs deployed API
  - MCP tool requirements

#### 11.3 Error Handling Documentation
- [ ] Document error response format:
  - Standardized error structure
  - Error codes
  - Request ID tracking
- [ ] Document error codes:
  - List all error codes
  - HTTP status code mapping
  - When each error occurs
- [ ] Document validation rules:
  - Field requirements
  - Validation rules
  - Error messages

---

## Success Criteria Checklist

- [ ] Unit tests with >80% coverage
- [ ] Integration tests for all endpoints (with mocks)
- [ ] E2E tests for all endpoints (against real server)
- [ ] Playwright MCP tests for all endpoints
- [ ] All tests passing (unit, integration, e2e, playwright)
- [ ] Test automation script works (single command)
- [ ] Tests are fully automated (no manual intervention)
- [ ] Standardized error responses with request IDs
- [ ] Input validation working correctly
- [ ] Error handlers catch all exceptions
- [ ] Test fixtures and utilities created
- [ ] Coverage report generated (>80%)
- [ ] Test documentation complete

---

## Notes & Considerations

### Test Execution Order
- Unit tests: Fast, isolated, run first
- Integration tests: Use mocks, run second
- E2E tests: Require real server, run third
- Playwright MCP tests: Require MCP server, run last

### Test Isolation
- Each test should be independent
- Use fixtures for clean state
- Clean up test data after each test
- Use unique test data to avoid conflicts

### Coverage Requirements
- Overall coverage: >80%
- Critical paths: 100% coverage (endpoints, auth, database)
- Error handling: 100% coverage
- Exclude: migrations, config files, test files

### DynamoDB Local Setup
- Use Docker Compose for DynamoDB Local
- Start DynamoDB Local before E2E tests
- Clean up tables between tests (optional)
- Handle Docker connection errors

### Playwright MCP Tests
- Use MCP tools for HTTP testing (not browser automation)
- Can test both local and deployed APIs
- Fully automated - AI can run these tests
- No browser needed (HTTP testing only)

### Error Handling Testing
- Test all error scenarios
- Verify error response format
- Verify request IDs in errors
- Test edge cases (invalid input, database errors)

### Known Limitations (Phase 3)
- No performance testing (out of scope)
- No load testing (out of scope)
- Mock DynamoDB may not match all AWS behaviors
- Integration tests use mocks (not real AWS)
- E2E tests require DynamoDB Local running
- Playwright MCP tests require MCP server configured

---

## Next Steps After Completion

After Phase 3 completion:
1. Proceed to Phase 4: Developer Experience (P1)
2. Add GET /events/{id} endpoint
3. Enhance error messages
4. Add status tracking
5. Implement idempotency key support

---

**Task List Status:** Ready for Implementation  
**Last Updated:** 2024-01-XX

