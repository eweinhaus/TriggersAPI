# Phase 4: Developer Experience (P1) - PRD

**Phase:** 4 of 6  
**Priority:** P1 (Should Have)  
**Estimated Duration:** 1-2 hours  
**Dependencies:** Phase 1, Phase 2, Phase 3

---

## 1. Executive Summary

Phase 4 enhances the API with P1 features focused on developer experience. This includes adding GET /events/{event_id} endpoint, improving error messages, standardizing responses, and enhancing status tracking.

**Goal:** Enhanced API with P1 features for better developer experience.

---

## 2. Scope

### In Scope
- GET /v1/events/{event_id} endpoint for event details
- Enhanced event status tracking
- Improved error messages with actionable details
- Response standardization across all endpoints
- Status transition tracking with timestamps
- Enhanced metadata in responses
- Optional idempotency key support (via metadata.idempotency_key)

### Out of Scope
- Retry logic (deferred to post-MVP)
- Rate limiting UI (deferred to post-MVP)
- Documentation (Phase 5)
- Frontend (Phase 6)
- Webhook delivery (out of scope)

---

## 3. Functional Requirements

### 3.1 GET /v1/events/{event_id} - Get Event Details

**Purpose:** Retrieve detailed information about a specific event, including its current status and metadata.

**Request:**
```
GET /v1/events/{event_id}
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
  "created_at": "ISO 8601",
  "source": "string",
  "event_type": "string",
  "payload": {},
  "status": "pending|acknowledged",
  "metadata": {},
  "acknowledged_at": "ISO 8601 (optional, if acknowledged)",
  "request_id": "uuid-v4"
}
```

**Error Responses:**
- `404 Not Found`: Event not found
- `401 Unauthorized`: Invalid API key

**Implementation Details:**
- Query DynamoDB by event_id (partition key)
- Return full event details including status
- Include timestamps for status transitions
- Return 404 if event doesn't exist

### 3.2 Enhanced Status Tracking

**Status Values:**
- `pending`: Event created but not yet acknowledged
- `acknowledged`: Event has been acknowledged/delivered

**Status Transitions:**
- `pending` → `acknowledged` (via POST /events/{id}/ack)
- Status transitions are tracked with timestamps
- `acknowledged_at` timestamp recorded on acknowledgment

**Status in Responses:**
- All event responses include `status` field
- Status is consistent across all endpoints
- Status changes are atomic (DynamoDB conditional updates)

### 3.3 Enhanced Error Messages

**Error Message Requirements:**
- Clear, actionable error messages
- Include relevant context (field names, values)
- Suggest fixes when possible
- Avoid technical jargon when possible

**Error Message Examples:**

**Validation Error:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The 'source' field is required but was not provided",
    "details": {
      "field": "source",
      "issue": "Field is required",
      "suggestion": "Include 'source' in your request body"
    }
  }
}
```

**Not Found Error:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Event with ID 'abc-123' was not found",
    "details": {
      "event_id": "abc-123",
      "suggestion": "Verify the event ID is correct and the event exists"
    }
  }
}
```

**Conflict Error:**
```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Event 'abc-123' has already been acknowledged",
    "details": {
      "event_id": "abc-123",
      "current_status": "acknowledged",
      "acknowledged_at": "2024-01-01T12:00:00Z",
      "suggestion": "This event has already been processed"
    }
  }
}
```

### 3.4 Response Standardization

**Standard Response Format:**
All successful responses follow consistent structure:

**Single Resource:**
```json
{
  "event_id": "uuid-v4",
  "timestamp": "ISO 8601",
  // ... resource-specific fields
}
```

**List Response:**
```json
{
  "events": [...],
  "pagination": {
    "next_cursor": "string (optional)",
    "total": 123,
    "limit": 50
  }
}
```

**Action Response:**
```json
{
  "event_id": "uuid-v4",
  "status": "acknowledged",
  "message": "Event acknowledged successfully",
  "acknowledged_at": "ISO 8601"
}
```

**Consistent Fields:**
- All timestamps in ISO 8601 format
- All UUIDs in standard format
- Consistent field naming (snake_case)
- Consistent status values

---

## 4. Technical Requirements

### 4.1 New Endpoint Implementation

**Endpoint Location:**
- Add to `src/endpoints/events.py`
- Route: `GET /events/{event_id}`
- Use FastAPI path parameter validation

**Database Query:**
- Use `GetItem` operation on Events table
- Query by `event_id` (partition key)
- Return 404 if item not found

**Response Model:**
- Use Pydantic model for response
- Include all event fields
- Include status and timestamps

### 4.2 Status Tracking Enhancement

**Database Updates:**
- Add `acknowledged_at` field to events
- Update status atomically using conditional updates
- Track status transitions in metadata (optional)

**Status Validation:**
- Validate status transitions
- Prevent invalid transitions
- Return appropriate errors

### 4.3 Error Message Enhancement

**Error Message Factory:**
- Create utility function for error messages
- Include context in error details
- Add suggestions where helpful

**Error Context:**
- Include request details in errors
- Include relevant field values
- Include suggestions for fixes

### 4.4 Response Standardization

**Response Models:**
- Create base response models
- Use Pydantic for validation
- Ensure consistent structure

**Response Utilities:**
- Create utility functions for responses
- Standardize timestamp formatting
- Standardize UUID formatting

---

## 5. Implementation Steps

1. **Add GET /v1/events/{event_id} Endpoint**
   - Create endpoint in `src/endpoints/events.py`
   - Implement database query
   - Create response model
   - Add route to FastAPI app with /v1 prefix
   - Include request ID in response

2. **Enhance Status Tracking**
   - Update database operations to track status
   - Add `acknowledged_at` field
   - Update acknowledgment endpoint
   - Add status validation

3. **Improve Error Messages**
   - Create error message utility
   - Update error handlers
   - Add context to error responses
   - Add suggestions to errors

4. **Standardize Responses**
   - Create base response models
   - Update all endpoints to use standard format
   - Standardize timestamp formatting
   - Standardize UUID formatting

5. **Update Tests**
   - Add tests for GET /events/{id}
   - Update existing tests for new formats
   - Test error message improvements
   - Test response standardization

6. **Documentation**
   - Update API documentation
   - Document new endpoint
   - Document enhanced error messages
   - Document response formats

---

## 6. Success Criteria

- [ ] GET /v1/events/{event_id} endpoint implemented
- [ ] Optional idempotency key support implemented
- [ ] Status tracking functional with timestamps
- [ ] Enhanced error messages with context
- [ ] All responses follow standard format
- [ ] Status transitions are atomic
- [ ] Tests updated and passing
- [ ] Documentation updated

---

## 7. API Changes

### New Endpoint

**GET /v1/events/{event_id}**
- Returns full event details
- Includes status and timestamps (created_at, acknowledged_at)
- Includes request_id in response
- Returns 404 if not found

### Enhanced Responses

**All Event Responses Now Include:**
- `status`: Current event status
- `created_at`: Event creation timestamp
- `acknowledged_at`: Acknowledgment timestamp (if acknowledged)

**Error Responses Enhanced:**
- More descriptive messages
- Context and suggestions
- Field-level details

### Response Format Changes

**Inbox Response:**
```json
{
  "events": [...],
  "pagination": {
    "next_cursor": "string",
    "total": 123,
    "limit": 50
  }
}
```

**Acknowledgment Response:**
```json
{
  "event_id": "uuid-v4",
  "status": "acknowledged",
  "message": "Event acknowledged successfully",
  "acknowledged_at": "ISO 8601"
}
```

---

## 8. Testing Requirements

### New Tests

**GET /events/{event_id} Tests:**
- Test successful retrieval
- Test 404 for non-existent event
- Test 401 for invalid API key
- Test response format

**Status Tracking Tests:**
- Test status transitions
- Test timestamp recording
- Test atomic updates
- Test conflict handling

**Error Message Tests:**
- Test error message format
- Test error context
- Test suggestions

**Response Standardization Tests:**
- Test consistent format
- Test timestamp formatting
- Test UUID formatting

---

## 9. Known Limitations (Phase 4)

- No retry logic (deferred to post-MVP)
- No webhook delivery (out of scope)
- Status tracking is basic (no history)
- No status webhooks (out of scope)

---

## 10. Next Steps

After Phase 4 completion:
- Proceed to Phase 5: Documentation & Example Clients
- Create OpenAPI documentation
- Create example clients
- Add cURL examples

---

**Phase Status:** Not Started  
**Completion Date:** TBD

