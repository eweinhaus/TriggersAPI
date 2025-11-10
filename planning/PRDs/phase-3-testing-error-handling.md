# Phase 3: Testing & Error Handling - PRD

**Phase:** 3 of 6  
**Priority:** P0 (Must Have)  
**Estimated Duration:** 2-3 hours  
**Dependencies:** Phase 1 (Core API), Phase 2 (AWS Infrastructure)

---

## 1. Executive Summary

Phase 3 adds comprehensive testing and standardized error handling to make the API production-ready. This phase includes unit tests, integration tests, error response standardization, and input validation improvements.

**Goal:** Production-ready API with >80% test coverage and consistent error handling.

---

## 2. Scope

### In Scope
- Unit tests for all endpoints (>80% coverage)
- Integration tests for all endpoints (with mocks)
- **End-to-end (E2E) tests against running API server**
- **Playwright MCP tests for API endpoints** (automated HTTP testing)
- Standardized error responses
- Enhanced input validation with Pydantic
- Error handling middleware
- Test fixtures and utilities
- Mock DynamoDB for unit tests
- Integration test setup
- **Automated test scripts** (AI-runnable)
- **Test automation documentation**

### Out of Scope
- P1 features (Phase 4)
- Documentation (Phase 5)
- Frontend browser tests (Phase 6)
- Performance testing (out of scope for MVP)
- Load testing (out of scope for MVP)

---

## 3. Functional Requirements

### 3.1 Unit Testing

**Coverage Requirements:**
- >80% code coverage overall
- 100% coverage for critical paths (endpoints, auth, database)
- Test all error cases
- Test all validation scenarios

**Test Structure:**
```
tests/
├── __init__.py
├── conftest.py              # pytest fixtures
├── unit/
│   ├── test_events.py       # Unit tests for events
│   ├── test_inbox.py        # Unit tests for inbox
│   ├── test_auth.py         # Unit tests for auth
│   ├── test_database.py     # Unit tests for database
│   └── test_models.py       # Unit tests for models
├── integration/
│   ├── test_integration.py  # Integration tests (mocks)
│   └── conftest.py          # Integration fixtures
├── e2e/
│   ├── conftest.py          # E2E fixtures (real server)
│   ├── test_e2e_events.py  # E2E event tests
│   ├── test_e2e_inbox.py   # E2E inbox tests
│   └── test_e2e_flow.py    # Full workflow E2E tests
├── playwright/
│   ├── conftest.py          # Playwright fixtures
│   ├── test_api_playwright.py  # Playwright MCP tests
│   └── api_test_scenarios.py   # Test scenarios
└── utils/
    ├── __init__.py
    ├── fixtures.py          # Test data fixtures
    └── test_helpers.py      # Test helper functions
```

**Test Categories:**
1. **Endpoint Tests:**
   - Happy path scenarios
   - Error scenarios (400, 401, 404, 409, 500)
   - Edge cases (empty payloads, large payloads, etc.)
   - Validation errors

2. **Authentication Tests:**
   - Valid API key
   - Invalid API key
   - Missing API key
   - Expired/inactive API key

3. **Database Tests:**
   - CRUD operations
   - Query operations
   - Pagination
   - Filtering
   - Error handling (DynamoDB errors)

4. **Model Tests:**
   - Pydantic validation
   - Field requirements
   - Type validation
   - Default values

### 3.2 Integration Testing

**Integration Test Setup:**
- Use moto library to mock AWS services
- Test full request/response cycle
- Test DynamoDB operations end-to-end
- Test API Gateway integration (optional, can use local FastAPI)

**Integration Test Scenarios:**
1. **Full Event Flow:**
   - POST /v1/events → GET /v1/inbox → POST /v1/events/{id}/ack
   - Verify event appears in inbox
   - Verify acknowledgment removes from inbox
   - Verify request IDs are included in all responses

2. **Error Scenarios:**
   - Invalid requests return proper errors
   - Database errors are handled gracefully
   - Authentication failures return 401

3. **Pagination:**
   - Test cursor-based pagination
   - Test with multiple pages
   - Test edge cases (empty, single page)

4. **Filtering:**
   - Test source filter
   - Test event_type filter
   - Test combined filters

### 3.3 End-to-End (E2E) Testing

**E2E Test Setup:**
- Start actual FastAPI server with DynamoDB Local
- Test against real running API (not mocks)
- Use pytest fixtures to manage server lifecycle
- Clean up test data after each test

**E2E Test Structure:**
```
tests/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py          # E2E fixtures (server, client)
│   ├── test_e2e_events.py  # E2E event tests
│   ├── test_e2e_inbox.py   # E2E inbox tests
│   └── test_e2e_flow.py    # Full workflow tests
```

**E2E Test Scenarios:**
1. **Full API Workflow:**
   - Start server with DynamoDB Local
   - Create event via POST /v1/events
   - Verify event in GET /v1/inbox
   - Acknowledge event via POST /v1/events/{id}/ack
   - Verify event removed from inbox
   - Delete event via DELETE /v1/events/{id}

2. **Error Handling:**
   - Test 400, 401, 404, 409, 500 responses
   - Verify error response format
   - Verify request IDs in errors

3. **Edge Cases:**
   - Large payloads (up to 400KB limit)
   - Invalid UUIDs
   - Missing required fields
   - Invalid API keys

### 3.4 Playwright MCP Tests

**Playwright MCP Test Setup:**
- Use Playwright MCP server for automated HTTP testing
- Test actual HTTP requests to running API
- Can test both local and deployed APIs
- Fully automated, no manual intervention

**Playwright MCP Test Structure:**
```
tests/
├── playwright/
│   ├── conftest.py              # Playwright fixtures
│   ├── test_api_playwright.py  # Playwright MCP API tests
│   └── api_test_scenarios.py    # Test scenarios
```

**Playwright MCP Test Scenarios:**
1. **API Endpoint Tests:**
   - Test all endpoints via HTTP requests
   - Verify response status codes
   - Verify response body structure
   - Verify headers (X-Request-ID, etc.)

2. **Full Workflow Tests:**
   - Create event → Get inbox → Acknowledge → Delete
   - Test with real HTTP requests
   - Verify data persistence

3. **Error Scenario Tests:**
   - Test error responses
   - Verify error format
   - Test authentication failures

**Playwright MCP Implementation:**
- Use `mcp_cursor-browser-extension` tools for HTTP testing
- Can test both local (http://localhost:8000) and deployed APIs
- Fully automated - AI can run these tests
- No browser needed (HTTP testing only)

### 3.5 Error Handling Standardization

**Error Response Format:**
All errors must follow this structure:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "field_name",
      "issue": "specific issue description"
    },
    "request_id": "uuid-v4"
  }
}
```

**Request ID Tracking:**
- All error responses must include `request_id` field
- Request ID comes from `X-Request-ID` header (if provided) or is generated
- Request ID is logged in CloudWatch for correlation
- Request ID helps with debugging and support

**Error Codes:**
- `VALIDATION_ERROR`: Invalid request payload (400)
- `UNAUTHORIZED`: Missing or invalid API key (401)
- `NOT_FOUND`: Resource not found (404)
- `CONFLICT`: Resource conflict, e.g., already acknowledged (409)
- `RATE_LIMIT_EXCEEDED`: Too many requests (429)
- `INTERNAL_ERROR`: Server error (500)

**Error Handling Middleware:**
- Global exception handler
- Pydantic validation error handler
- HTTP exception handler
- Custom exception classes

### 3.6 Input Validation

**Pydantic Models:**
- Strict validation on all inputs
- Type checking
- Required field validation
- Custom validators for business rules
- Clear error messages

**Validation Rules:**
1. **Event Creation:**
   - `source`: Required, non-empty string, max 100 chars
   - `event_type`: Required, non-empty string, max 100 chars
   - `payload`: Required, valid JSON object
   - `metadata`: Optional, valid JSON object
   - `metadata.priority`: Optional, enum: "low", "normal", "high"

2. **Inbox Query:**
   - `limit`: Optional, integer, 1-100, default 50
   - `cursor`: Optional, base64 string
   - `source`: Optional, non-empty string
   - `event_type`: Optional, non-empty string

3. **Event ID:**
   - Must be valid UUID v4 format
   - Validation in path parameters

---

## 4. Technical Requirements

### 4.1 Testing Dependencies

**Python Packages:**
- `pytest>=7.4.0`
- `pytest-cov>=4.1.0` (coverage reporting)
- `pytest-asyncio>=0.21.0` (if using async)
- `moto>=4.2.0` (AWS service mocking)
- `httpx>=0.25.0` (HTTP client for testing)
- `faker>=19.0.0` (test data generation)
- `pytest-xdist>=3.0.0` (parallel test execution)
- `pytest-timeout>=2.1.0` (test timeout management)

**Test Automation:**
- All tests must be runnable via single command
- Tests should be idempotent (can run multiple times)
- Tests should clean up after themselves
- No manual intervention required

### 4.2 Test Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -v
```

**Coverage Configuration:**
- Minimum coverage: 80%
- Exclude migrations, config files
- Include all source code

### 4.3 Test Fixtures

**conftest.py Fixtures:**
```python
@pytest.fixture
def app():
    """FastAPI app instance"""
    
@pytest.fixture
def client(app):
    """Test client"""
    
@pytest.fixture
def dynamodb_table():
    """Mock DynamoDB table"""
    
@pytest.fixture
def api_key():
    """Test API key"""
    
@pytest.fixture
def sample_event():
    """Sample event data"""
```

### 4.4 Error Handling Implementation

**Custom Exceptions:**
```python
class TriggersAPIError(Exception):
    """Base exception"""
    
class ValidationError(TriggersAPIError):
    """Validation error"""
    
class UnauthorizedError(TriggersAPIError):
    """Authentication error"""
    
class NotFoundError(TriggersAPIError):
    """Resource not found"""
    
class ConflictError(TriggersAPIError):
    """Resource conflict"""
```

**Error Handler:**
```python
@app.exception_handler(TriggersAPIError)
async def triggers_api_error_handler(request, exc):
    """Handle custom exceptions"""
    
@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    """Handle validation errors"""
    
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
```

---

## 5. Implementation Steps

1. **Set Up Testing Infrastructure**
   - Install testing dependencies
   - Create test directory structure
   - Configure pytest
   - Set up coverage reporting

2. **Create Test Fixtures**
   - Create conftest.py with common fixtures
   - Set up mock DynamoDB with moto
   - Create test data generators
   - Create utility functions

3. **Implement Error Handling**
   - Create custom exception classes
   - Implement error handlers
   - Standardize error response format
   - Update existing endpoints

4. **Enhance Input Validation**
   - Update Pydantic models with strict validation
   - Add custom validators
   - Improve error messages
   - Test validation edge cases

5. **Write Unit Tests**
   - Test all endpoints (test_events.py)
   - Test authentication (test_auth.py)
   - Test database layer (test_database.py)
   - Test models (test_models.py)

6. **Write Integration Tests**
   - Test full event flow
   - Test error scenarios
   - Test pagination
   - Test filtering

7. **Write E2E Tests**
   - Create E2E test fixtures (start/stop server)
   - Test against real running API
   - Test full workflows
   - Test error scenarios with real server

8. **Write Playwright MCP Tests**
   - Set up Playwright MCP test structure
   - Create API test scenarios
   - Test all endpoints via HTTP
   - Test both local and deployed APIs

9. **Create Test Automation Scripts**
   - Create `scripts/run_tests.sh` (or `run_tests.py`)
   - Script should:
     - Start DynamoDB Local (if not running)
     - Start FastAPI server for E2E tests
     - Run all test suites (unit, integration, e2e, playwright)
     - Generate coverage report
     - Clean up test resources
   - Make script AI-runnable (single command)

10. **Run Tests and Fix Issues**
    - Run complete test suite
    - Fix failing tests
    - Improve coverage
    - Refactor as needed
    - Verify all tests pass

11. **Documentation**
    - Document test structure
    - Document how to run tests (single command)
    - Document coverage requirements
    - Document Playwright MCP test usage
    - Document E2E test setup

---

## 6. Success Criteria

- [ ] Unit tests with >80% coverage
- [ ] Integration tests for all endpoints (with mocks)
- [ ] E2E tests for all endpoints (against real server)
- [ ] Playwright MCP tests for all endpoints
- [ ] All tests passing (unit, integration, e2e, playwright)
- [ ] Test automation script works (single command)
- [ ] Tests are fully automated (no manual intervention)
- [ ] Standardized error responses
- [ ] Input validation working correctly
- [ ] Error handlers catch all exceptions
- [ ] Test fixtures and utilities created
- [ ] Coverage report generated
- [ ] Test documentation complete

---

## 7. Testing Strategy

### Unit Test Examples

**Event Creation Test:**
```python
def test_create_event_success(client, api_key, sample_event):
    response = client.post(
        "/v1/events",
        json=sample_event,
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 201
    assert "event_id" in response.json()
    assert "request_id" in response.json()
    assert response.json()["status"] == "pending"

def test_create_event_missing_source(client, api_key):
    response = client.post(
        "/v1/events",
        json={"event_type": "test", "payload": {}},
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in response.json()["error"]
```

**Authentication Test:**
```python
def test_invalid_api_key(client, sample_event):
    response = client.post(
        "/v1/events",
        json=sample_event,
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in response.json()["error"]
```

### Integration Test Examples

**Full Event Flow:**
```python
def test_event_lifecycle(client, api_key, sample_event):
    # Create event
    create_response = client.post(
        "/v1/events",
        json=sample_event,
        headers={"X-API-Key": api_key}
    )
    event_id = create_response.json()["event_id"]
    assert "request_id" in create_response.json()
    
    # Get from inbox
    inbox_response = client.get(
        "/v1/inbox",
        headers={"X-API-Key": api_key}
    )
    assert len(inbox_response.json()["events"]) == 1
    assert inbox_response.json()["events"][0]["event_id"] == event_id
    assert "request_id" in inbox_response.json()
    
    # Acknowledge
    ack_response = client.post(
        f"/v1/events/{event_id}/ack",
        headers={"X-API-Key": api_key}
    )
    assert ack_response.status_code == 200
    assert "request_id" in ack_response.json()
    
    # Verify removed from inbox
    inbox_response = client.get(
        "/v1/inbox",
        headers={"X-API-Key": api_key}
    )
    assert len(inbox_response.json()["events"]) == 0
```

---

## 8. Error Handling Examples

### Validation Error
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request payload",
    "details": {
      "field": "source",
      "issue": "Field is required"
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Unauthorized Error
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing API key",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Conflict Error
```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Event already acknowledged",
    "details": {
      "event_id": "uuid-v4",
      "current_status": "acknowledged"
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## 9. Test Automation

### Running Tests

**Single Command (AI-Friendly):**
```bash
# Run all tests (unit, integration, e2e, playwright)
./scripts/run_tests.sh

# Or using Python
python scripts/run_tests.py
```

**Individual Test Suites:**
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v

# Playwright MCP tests only
pytest tests/playwright/ -v

# With coverage
pytest --cov=src --cov-report=html
```

**Test Script Requirements:**
- Automatically start DynamoDB Local if not running
- Start FastAPI server for E2E tests
- Run all test suites in sequence
- Generate coverage report
- Clean up test resources
- Exit with proper status code (0 = success, 1 = failure)
- AI can run with single command

### Playwright MCP Test Example

```python
# tests/playwright/test_api_playwright.py
import pytest
from mcp_cursor_browser_extension import browser_navigate, browser_snapshot

@pytest.mark.playwright
def test_create_event_playwright(api_base_url, api_key):
    """Test event creation via Playwright MCP"""
    # Navigate to API endpoint
    browser_navigate(url=f"{api_base_url}/v1/events")
    
    # Make POST request (using Playwright MCP HTTP capabilities)
    # Verify response
    # This is a placeholder - actual implementation uses Playwright MCP HTTP tools
    pass
```

**Note:** Playwright MCP tests use HTTP testing capabilities, not browser automation for API tests.

**Playwright MCP Test Implementation Details:**
- Use `mcp_cursor-browser-extension` MCP server
- Tests make actual HTTP requests to API
- Can test local API (http://localhost:8000) or deployed API
- Verify response status, body, headers
- Fully automated - AI can execute via MCP tools
- Example test structure:
  ```python
  # Use MCP tools to make HTTP requests
  # Verify responses
  # Test all endpoints
  # No manual steps required
  ```

## 10. Known Limitations (Phase 3)

- No performance testing (out of scope)
- No load testing (out of scope)
- Mock DynamoDB may not match all AWS behaviors
- Integration tests use mocks (not real AWS)
- E2E tests require DynamoDB Local running
- Playwright MCP tests require MCP server configured

---

## 11. Next Steps

After Phase 3 completion:
- Proceed to Phase 4: Developer Experience (P1)
- Add GET /events/{id} endpoint
- Enhance error messages
- Add status tracking

---

**Phase Status:** Not Started  
**Completion Date:** TBD

