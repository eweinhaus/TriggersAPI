# Phase 4: Developer Experience (P1) - Task List

**Phase:** 4 of 6  
**Priority:** P1 (Should Have)  
**Status:** Not Started  
**Created:** 2025-11-10  
**Estimated Duration:** 1-2 hours  
**Dependencies:** Phase 1, Phase 2, Phase 3

---

## Overview

This task list covers the implementation of Phase 4: Developer Experience enhancements. The goal is to improve the API with P1 features that enhance developer experience, including a new GET endpoint, enhanced error messages, response standardization, and idempotency support.

**Key Deliverables:**
- GET /v1/events/{event_id} endpoint for retrieving individual events
- Enhanced error messages with actionable context and suggestions
- Standardized response formats across all endpoints
- Enhanced status tracking with timestamps in all responses
- Idempotency key support to prevent duplicate event creation
- Updated test suite covering all new features

---

## Task Breakdown

### 1. GET /v1/events/{event_id} Endpoint

#### 1.1 Create Event Detail Response Model
- [ ] Add `EventDetailResponse` model to `src/models.py`
  - Include all event fields: `event_id`, `created_at`, `source`, `event_type`, `payload`, `status`, `metadata`
  - Include `acknowledged_at` (optional, only if acknowledged)
  - Include `request_id` for request tracking
  - Ensure all fields match PRD specification

#### 1.2 Optimize Database Query for Event Retrieval
- [ ] Review current `get_event()` implementation in `src/database.py`
- [ ] Optimize query to use `GetItem` directly when possible
  - Note: Current implementation uses scan due to composite key (event_id + created_at)
  - For MVP, scan is acceptable, but document the limitation
  - Consider if we can query by event_id alone (may require table structure change)
- [ ] Ensure `get_event()` returns full event with all fields including `status` and `acknowledged_at`
- [ ] Handle case where event doesn't exist (return None)

#### 1.3 Implement GET /v1/events/{event_id} Endpoint
- [ ] Add endpoint to `src/endpoints/events.py`
  - Route: `GET /events/{event_id}`
  - Path parameter: `event_id` (UUID, validated by FastAPI)
  - Authentication: Require API key via `Depends(get_api_key)`
  - Request ID: Extract from `request.state.request_id`
- [ ] Implement endpoint logic:
  - Call `get_event(event_id_str)` from database
  - If event not found, raise `NotFoundError` with enhanced error message
  - If found, return `EventDetailResponse` with all event fields
- [ ] Register route in FastAPI app (already included via router)
- [ ] Ensure route is prefixed with `/v1` in main app

#### 1.4 Add Tests for GET /v1/events/{event_id}
- [ ] Add unit tests in `tests/unit/test_events.py`:
  - Test successful event retrieval
  - Test 404 for non-existent event
  - Test 401 for invalid API key
  - Test response format matches `EventDetailResponse` model
  - Test that all fields are present (including `status`, `acknowledged_at`)
- [ ] Add integration tests in `tests/integration/test_integration.py`:
  - Test full flow: create event, retrieve by ID
  - Test retrieving acknowledged event (includes `acknowledged_at`)
  - Test retrieving pending event (no `acknowledged_at`)
- [ ] Add E2E tests in `tests/e2e/test_e2e_events.py`:
  - Test against real server with DynamoDB Local
- [ ] Add Playwright MCP tests in `tests/playwright/test_api_playwright.py`:
  - HTTP-based tests for GET endpoint

---

### 2. Enhanced Error Messages

#### 2.1 Create Error Message Utility Functions
- [ ] Create or update `src/utils.py` with error message helpers:
  - `format_validation_error(field, issue, value=None)` - Format validation errors with context
  - `format_not_found_error(resource_type, resource_id)` - Format not found errors
  - `format_conflict_error(resource_type, resource_id, context)` - Format conflict errors
  - Each function should return a `details` dict with:
    - Relevant field/resource information
    - Clear issue description
    - Actionable suggestion when possible
- [ ] Ensure error messages follow PRD examples:
  - Include field names and values when relevant
  - Provide suggestions for fixes
  - Avoid technical jargon

#### 2.2 Update Exception Classes to Support Enhanced Details
- [ ] Review `src/exceptions.py` - exception classes already support `details` parameter
- [ ] Ensure all exception constructors accept and store `details` dict
- [ ] Verify exception handlers in `src/main.py` properly format error responses with details

#### 2.3 Update Error Handlers to Use Enhanced Messages
- [ ] Update `ValidationError` usage in endpoints:
  - `src/endpoints/events.py` - Use enhanced validation error messages
  - `src/endpoints/inbox.py` - Use enhanced validation error messages
- [ ] Update `NotFoundError` usage:
  - `src/endpoints/events.py` - GET endpoint, ack endpoint, delete endpoint
  - Include event_id in error details
  - Add suggestion: "Verify the event ID is correct and the event exists"
- [ ] Update `ConflictError` usage:
  - `src/endpoints/events.py` - Acknowledge endpoint
  - Include event_id, current_status, acknowledged_at in details
  - Add suggestion: "This event has already been processed"
- [ ] Update Pydantic validation error handler in `src/main.py`:
  - Extract field name and issue from validation error
  - Format using error message utility
  - Include suggestion based on error type

#### 2.4 Add Tests for Enhanced Error Messages
- [ ] Add unit tests in `tests/unit/test_events.py`:
  - Test validation error format (field, issue, suggestion)
  - Test not found error format (event_id, suggestion)
  - Test conflict error format (event_id, status, suggestion)
- [ ] Add integration tests:
  - Test error message format in real scenarios
  - Verify suggestions are helpful and actionable

---

### 3. Response Standardization

#### 3.1 Review Current Response Models
- [ ] Review all response models in `src/models.py`:
  - `EventResponse` - Event creation response
  - `InboxResponse` - Inbox query response
  - `AckResponse` - Acknowledgment response
  - `DeleteResponse` - Deletion response
  - `EventDetailResponse` - New GET endpoint response (from task 1.1)
- [ ] Ensure all responses include `request_id`
- [ ] Ensure all event-related responses include `status` field
- [ ] Ensure all timestamps are in ISO 8601 format (already handled by `get_iso_timestamp()`)

#### 3.2 Standardize Event Responses
- [ ] Update `EventResponse` model:
  - Ensure it includes all standard fields
  - Verify `status` is included (currently included)
  - Consider if `source`, `event_type` should be included (check PRD)
- [ ] Update `AckResponse` model:
  - Ensure `acknowledged_at` is included (already included)
  - Verify format matches PRD specification
- [ ] Update inbox events in `InboxResponse`:
  - Ensure each event in the list includes `status` field
  - Ensure each event includes `created_at` timestamp
  - Ensure acknowledged events include `acknowledged_at`
- [ ] Update `EventDetailResponse` (from task 1.1):
  - Ensure it matches PRD specification exactly
  - Include all required fields

#### 3.3 Standardize Pagination Response Format
- [ ] Review `InboxResponse.pagination` format:
  - Current: `{"limit": int, "next_cursor": str (optional)}`
  - PRD specifies: `{"next_cursor": str (optional), "total": int, "limit": int}`
  - Note: DynamoDB doesn't support efficient total count
  - Decision: Keep current format (no total), document limitation
  - OR: Add total field with note that it's approximate/expensive

#### 3.4 Update Endpoint Responses to Use Standardized Format
- [ ] Update `create_event_endpoint` in `src/endpoints/events.py`:
  - Ensure response includes all standard fields
  - Verify `status` is included in response
- [ ] Update `acknowledge_event_endpoint`:
  - Ensure response format matches PRD (event_id, status, message, acknowledged_at)
  - Verify all fields are present
- [ ] Update `get_inbox` in `src/endpoints/inbox.py`:
  - Ensure each event in response includes `status` and `created_at`
  - Ensure acknowledged events include `acknowledged_at`
  - Verify pagination format is consistent

#### 3.5 Add Tests for Response Standardization
- [ ] Add unit tests:
  - Test all response models match expected format
  - Test that all responses include `request_id`
  - Test that all event responses include `status`
  - Test timestamp format (ISO 8601)
- [ ] Add integration tests:
  - Test response format consistency across endpoints
  - Test that inbox events include all required fields

---

### 4. Enhanced Status Tracking

#### 4.1 Review Current Status Tracking Implementation
- [ ] Review `acknowledge_event()` in `src/database.py`:
  - Verify `acknowledged_at` timestamp is being set (already implemented)
  - Verify status is updated atomically (conditional update already implemented)
- [ ] Review `create_event()` in `src/database.py`:
  - Verify `status` is set to "pending" (already implemented)
  - Verify `created_at` timestamp is set (already implemented)

#### 4.2 Ensure Status in All Event Responses
- [ ] Verify `EventResponse` includes `status` (already included)
- [ ] Verify `AckResponse` includes `status` (already included)
- [ ] Verify `EventDetailResponse` includes `status` (from task 1.1)
- [ ] Verify inbox events include `status` field (check `query_pending_events()`)
- [ ] Update `query_pending_events()` if needed to ensure status is in results

#### 4.3 Ensure Timestamps in All Event Responses
- [ ] Verify `created_at` is included in:
  - `EventResponse` (already included)
  - `EventDetailResponse` (from task 1.1)
  - Inbox events (verify database query returns it)
- [ ] Verify `acknowledged_at` is included when applicable:
  - `AckResponse` (already included)
  - `EventDetailResponse` (optional, only if acknowledged)
  - Inbox events (only if acknowledged)

#### 4.4 Add Tests for Status Tracking
- [ ] Add unit tests:
  - Test that created events have status "pending"
  - Test that acknowledged events have status "acknowledged"
  - Test that `acknowledged_at` is set on acknowledgment
  - Test that status transitions are atomic (conditional update)
- [ ] Add integration tests:
  - Test full status transition flow: create → acknowledge
  - Test that status is consistent across all endpoints
  - Test that timestamps are properly formatted

---

### 5. Idempotency Key Support

#### 5.1 Review Current Idempotency Implementation
- [ ] Review `EventCreate` model in `src/models.py`:
  - Verify `metadata.idempotency_key` field exists (already exists as optional)
  - Verify it's accepted in event creation requests
- [ ] Review `create_event()` in `src/database.py`:
  - Currently idempotency_key is stored in metadata but not used
  - Need to implement idempotency check

#### 5.2 Design Idempotency Implementation
- [ ] Decide on idempotency approach:
  - Option A: Use separate DynamoDB table for idempotency keys
  - Option B: Use GSI on events table (idempotency_key → event_id)
  - Option C: Query events table by idempotency_key (scan/query)
  - Recommendation: Option A (separate table) for MVP simplicity
- [ ] Design idempotency table structure:
  - Partition key: `idempotency_key` (string)
  - Attributes: `event_id` (string), `created_at` (ISO 8601)
  - TTL: 24 hours (Unix timestamp)
- [ ] Design idempotency logic:
  - On event creation, if idempotency_key provided:
    1. Check if idempotency_key exists in idempotency table
    2. If exists, return existing event (don't create new one)
    3. If not exists, create event and store idempotency_key mapping
  - Use conditional writes to prevent race conditions

#### 5.3 Create Idempotency Table
- [ ] Update `scripts/create_tables.py`:
  - Add idempotency table creation:
    - Table name: `triggers-api-idempotency` (or from env var)
    - Partition key: `idempotency_key` (String)
    - TTL attribute: `ttl` (Number)
    - Billing mode: On-demand
- [ ] Update table creation to be idempotent (handle existing table)
- [ ] Test table creation locally and in AWS

#### 5.4 Implement Idempotency Check in Database Layer
- [ ] Add `check_idempotency_key()` function to `src/database.py`:
  - Query idempotency table by idempotency_key
  - Return event_id if found, None otherwise
- [ ] Add `store_idempotency_key()` function to `src/database.py`:
  - Store idempotency_key → event_id mapping
  - Set TTL to 24 hours from now
  - Use conditional write (idempotency_key doesn't exist)
- [ ] Update `create_event()` function:
  - Accept optional `idempotency_key` parameter
  - If provided, check for existing event
  - If existing event found, return it (don't create new)
  - If not found, create event and store idempotency mapping
  - Handle race conditions with conditional writes

#### 5.5 Update Event Creation Endpoint
- [ ] Update `create_event_endpoint` in `src/endpoints/events.py`:
  - Extract `idempotency_key` from `event_data.metadata` if present
  - Pass `idempotency_key` to `create_event()` function
  - If existing event returned (idempotency), return it with appropriate message
  - Ensure response indicates if event was created or retrieved

#### 5.6 Add Tests for Idempotency
- [ ] Add unit tests in `tests/unit/test_events.py`:
  - Test creating event with idempotency_key (first time - creates new)
  - Test creating event with same idempotency_key (second time - returns existing)
  - Test idempotency_key with different payload (should return existing event)
  - Test idempotency_key expiration (after 24 hours, new event created)
  - Test race condition handling (concurrent requests with same key)
- [ ] Add integration tests:
  - Test full idempotency flow
  - Test idempotency across multiple requests
- [ ] Add E2E tests:
  - Test idempotency with real server

---

### 6. Testing & Validation

#### 6.1 Run Full Test Suite
- [ ] Run unit tests: `pytest tests/unit/ -v`
  - Verify all new tests pass
  - Verify existing tests still pass (no regressions)
  - Target: Maintain >80% code coverage (currently 84%)
- [ ] Run integration tests: `pytest tests/integration/ -v`
  - Verify all integration tests pass
- [ ] Run E2E tests: `pytest tests/e2e/ -v`
  - Requires DynamoDB Local running
  - Verify all E2E tests pass
- [ ] Run Playwright MCP tests: `pytest tests/playwright/ -v`
  - Requires API server running
  - Verify all Playwright tests pass

#### 6.2 Test Coverage Validation
- [ ] Run coverage report: `pytest --cov=src --cov-report=html`
  - Verify coverage is maintained above 80%
  - Identify any uncovered code paths
  - Add tests for uncovered paths if critical

#### 6.3 Manual Testing
- [ ] Test GET /v1/events/{event_id} endpoint:
  - Create event, retrieve by ID
  - Test with non-existent event ID (404)
  - Test with invalid API key (401)
  - Test with acknowledged event (includes acknowledged_at)
- [ ] Test enhanced error messages:
  - Validation errors (check field, issue, suggestion)
  - Not found errors (check event_id, suggestion)
  - Conflict errors (check event_id, status, suggestion)
- [ ] Test response standardization:
  - Verify all responses include request_id
  - Verify all event responses include status
  - Verify timestamps are ISO 8601 format
- [ ] Test idempotency:
  - Create event with idempotency_key
  - Create same event again (should return existing)
  - Verify response indicates existing event

---

### 7. Documentation Updates

#### 7.1 Update README
- [ ] Document new GET /v1/events/{event_id} endpoint:
  - Request format
  - Response format
  - Error responses
  - Example cURL commands
- [ ] Document enhanced error messages:
  - Error response format
  - Error codes and meanings
  - Examples of enhanced error messages
- [ ] Document idempotency key support:
  - How to use idempotency_key
  - Behavior and guarantees
  - Examples

#### 7.2 Update API Documentation
- [ ] Update endpoint documentation in code (docstrings):
  - GET /v1/events/{event_id} endpoint docstring
  - Enhanced error message examples in docstrings
- [ ] Ensure all endpoint docstrings are up to date

#### 7.3 Update Test Documentation
- [ ] Update test documentation if needed:
  - Document new test cases
  - Update test execution instructions if needed

---

### 8. Code Quality & Cleanup

#### 8.1 Code Review
- [ ] Review all new code for:
  - Type hints (Python type hints throughout)
  - Docstrings (document all functions and classes)
  - Error handling (comprehensive error handling)
  - Code organization (follow project structure)
- [ ] Ensure code follows project patterns:
  - Request ID tracking
  - Error response format
  - Database operation patterns

#### 8.2 Linting & Formatting
- [ ] Run linter (if configured): Ensure no linting errors
- [ ] Format code (if formatter configured): Ensure consistent formatting

#### 8.3 Remove Temporary Code
- [ ] Remove any temporary debugging code
- [ ] Remove commented-out code
- [ ] Clean up unused imports

---

## Success Criteria Checklist

- [ ] GET /v1/events/{event_id} endpoint implemented and tested
- [ ] Enhanced error messages with context and suggestions implemented
- [ ] All responses follow standardized format
- [ ] Status tracking functional with timestamps in all responses
- [ ] Idempotency key support implemented and tested
- [ ] All tests updated and passing (>80% coverage maintained)
- [ ] Documentation updated (README, code docstrings)
- [ ] No regressions in existing functionality
- [ ] Code quality maintained (type hints, docstrings, error handling)

---

## Implementation Notes

### Database Query Optimization
- Current `get_event()` uses scan operation which is acceptable for MVP
- For production scale, consider optimizing to use GetItem directly
- May require table structure change (event_id as partition key only)

### Idempotency Implementation
- Using separate DynamoDB table for idempotency keys
- TTL of 24 hours for automatic cleanup
- Conditional writes prevent race conditions
- Idempotency key stored in metadata and also in separate table

### Error Message Enhancement
- Error messages include field names, values, and suggestions
- Suggestions are actionable and help developers fix issues
- Error format remains backward compatible (details field is additive)

### Response Standardization
- All responses include `request_id` for request tracking
- All event responses include `status` field
- Timestamps are consistently ISO 8601 format
- Pagination format is consistent (no total count due to DynamoDB limitation)

---

## Dependencies

- Phase 1: Core API Backend (completed)
- Phase 2: AWS Infrastructure (completed)
- Phase 3: Testing & Error Handling (completed)

---

## Estimated Time

- Task 1: GET Endpoint - 30 minutes
- Task 2: Enhanced Error Messages - 20 minutes
- Task 3: Response Standardization - 15 minutes
- Task 4: Status Tracking - 10 minutes
- Task 5: Idempotency - 25 minutes
- Task 6: Testing - 20 minutes
- Task 7: Documentation - 10 minutes
- Task 8: Code Quality - 10 minutes

**Total: ~2 hours**

---

**Task List Status:** Ready for Implementation  
**Last Updated:** 2025-11-10

