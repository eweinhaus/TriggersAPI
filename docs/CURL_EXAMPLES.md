# cURL Examples for Zapier Triggers API

This document provides comprehensive cURL examples for all API endpoints.

## Table of Contents

- [Authentication](#authentication)
- [Health Check](#health-check)
- [Create Event](#create-event)
- [Get Event](#get-event)
- [Get Inbox](#get-inbox)
- [Acknowledge Event](#acknowledge-event)
- [Delete Event](#delete-event)
- [Error Examples](#error-examples)

## Authentication

All authenticated endpoints require the `X-API-Key` header. For local development, use `test-api-key-12345`. For production, use your actual API key.

```bash
# Local development
API_KEY="test-api-key-12345"
BASE_URL="http://localhost:8080"

# Production (replace with your actual values)
# API_KEY="your-production-api-key"
# BASE_URL="https://your-api-url.com"
```

## Health Check

### GET /v1/health

Check API availability and status. No authentication required.

**Local:**
```bash
curl -X GET http://localhost:8080/v1/health
```

**Production:**
```bash
curl -X GET https://your-api-url.com/v1/health
```

**Expected Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T12:00:00.000000Z",
  "version": "1.0.0"
}
```

## Create Event

### POST /v1/events

Create a new event. Requires authentication.

**Minimal Request:**
```bash
curl -X POST http://localhost:8080/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-123" \
  -d '{
    "source": "my-app",
    "event_type": "user.created",
    "payload": {
      "user_id": "123",
      "name": "John Doe"
    }
  }'
```

**With Metadata:**
```bash
curl -X POST http://localhost:8080/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-124" \
  -d '{
    "source": "my-app",
    "event_type": "user.created",
    "payload": {
      "user_id": "123",
      "name": "John Doe",
      "email": "john@example.com"
    },
    "metadata": {
      "priority": "high",
      "correlation_id": "corr-456"
    }
  }'
```

**With Idempotency Key:**
```bash
curl -X POST http://localhost:8080/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-125" \
  -d '{
    "source": "my-app",
    "event_type": "user.created",
    "payload": {
      "user_id": "123",
      "name": "John Doe"
    },
    "metadata": {
      "idempotency_key": "unique-key-123",
      "priority": "normal"
    }
  }'
```

**Expected Response (201 Created):**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-11-10T12:00:00.000000Z",
  "status": "pending",
  "message": "Event ingested successfully",
  "request_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

## Get Event

### GET /v1/events/{event_id}

Retrieve detailed information about a specific event. Requires authentication.

**Local:**
```bash
curl -X GET "http://localhost:8080/v1/events/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-126"
```

**Production:**
```bash
curl -X GET "https://your-api-url.com/v1/events/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your-api-key" \
  -H "X-Request-ID: my-request-126"
```

**Expected Response (200 OK):**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-11-10T12:00:00.000000Z",
  "source": "my-app",
  "event_type": "user.created",
  "payload": {
    "user_id": "123",
    "name": "John Doe"
  },
  "status": "pending",
  "metadata": {
    "priority": "normal"
  },
  "acknowledged_at": null,
  "request_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

## Get Inbox

### GET /v1/inbox

Retrieve pending events with pagination and filtering. Requires authentication.

**Basic Query:**
```bash
curl -X GET "http://localhost:8080/v1/inbox?limit=50" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-127"
```

**With Pagination:**
```bash
# First page
curl -X GET "http://localhost:8080/v1/inbox?limit=10" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-128"

# Next page (use cursor from previous response)
curl -X GET "http://localhost:8080/v1/inbox?limit=10&cursor=eyJldmVudF9pZCI6ICI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJjcmVhdGVkX2F0IjogIjIwMjUtMTEtMTBUMTI6MDA6MDAuMDAwMDAwWiJ9" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-129"
```

**Filter by Source:**
```bash
curl -X GET "http://localhost:8080/v1/inbox?limit=50&source=my-app" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-130"
```

**Filter by Event Type:**
```bash
curl -X GET "http://localhost:8080/v1/inbox?limit=50&event_type=user.created" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-131"
```

**Combined Filtering:**
```bash
curl -X GET "http://localhost:8080/v1/inbox?limit=50&source=my-app&event_type=user.created" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-132"
```

**Expected Response (200 OK):**
```json
{
  "events": [
    {
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-11-10T12:00:00.000000Z",
      "source": "my-app",
      "event_type": "user.created",
      "payload": {
        "user_id": "123",
        "name": "John Doe"
      },
      "status": "pending",
      "metadata": {
        "priority": "normal"
      }
    }
  ],
  "pagination": {
    "limit": 50,
    "next_cursor": "eyJldmVudF9pZCI6ICI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJjcmVhdGVkX2F0IjogIjIwMjUtMTEtMTBUMTI6MDA6MDAuMDAwMDAwWiJ9"
  },
  "request_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

## Acknowledge Event

### POST /v1/events/{event_id}/ack

Mark an event as acknowledged. Requires authentication.

**Local:**
```bash
curl -X POST "http://localhost:8080/v1/events/550e8400-e29b-41d4-a716-446655440000/ack" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-133"
```

**Production:**
```bash
curl -X POST "https://your-api-url.com/v1/events/550e8400-e29b-41d4-a716-446655440000/ack" \
  -H "X-API-Key: your-api-key" \
  -H "X-Request-ID: my-request-133"
```

**Expected Response (200 OK):**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "acknowledged",
  "acknowledged_at": "2025-11-10T12:05:00.000000Z",
  "message": "Event acknowledged successfully",
  "request_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

## Delete Event

### DELETE /v1/events/{event_id}

Delete an event. Requires authentication. Idempotent operation.

**Local:**
```bash
curl -X DELETE "http://localhost:8080/v1/events/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: test-api-key-12345" \
  -H "X-Request-ID: my-request-134"
```

**Production:**
```bash
curl -X DELETE "https://your-api-url.com/v1/events/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your-api-key" \
  -H "X-Request-ID: my-request-134"
```

**Expected Response (200 OK):**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Event deleted successfully",
  "request_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

## Error Examples

### Validation Error (400)

**Request with Invalid Payload:**
```bash
curl -X POST http://localhost:8080/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-12345" \
  -d '{
    "source": "",
    "event_type": "test.event",
    "payload": {}
  }'
```

**Error Response:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The 'source' field is required and cannot be empty",
    "details": {
      "field": "source",
      "issue": "source field is required and cannot be empty",
      "suggestion": "Provide a non-empty source value"
    },
    "request_id": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

### Unauthorized Error (401)

**Request with Missing API Key:**
```bash
curl -X GET "http://localhost:8080/v1/inbox?limit=10"
```

**Request with Invalid API Key:**
```bash
curl -X GET "http://localhost:8080/v1/inbox?limit=10" \
  -H "X-API-Key: invalid-key"
```

**Error Response:**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing API key",
    "details": {},
    "request_id": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

### Not Found Error (404)

**Request with Non-existent Event ID:**
```bash
curl -X GET "http://localhost:8080/v1/events/00000000-0000-0000-0000-000000000000" \
  -H "X-API-Key: test-api-key-12345"
```

**Error Response:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Event with ID '00000000-0000-0000-0000-000000000000' was not found",
    "details": {
      "event_id": "00000000-0000-0000-0000-000000000000",
      "suggestion": "Verify the event ID is correct and the event exists"
    },
    "request_id": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

### Conflict Error (409)

**Request to Acknowledge Already Acknowledged Event:**
```bash
# First, acknowledge an event
curl -X POST "http://localhost:8080/v1/events/550e8400-e29b-41d4-a716-446655440000/ack" \
  -H "X-API-Key: test-api-key-12345"

# Then try to acknowledge again (will cause conflict)
curl -X POST "http://localhost:8080/v1/events/550e8400-e29b-41d4-a716-446655440000/ack" \
  -H "X-API-Key: test-api-key-12345"
```

**Error Response:**
```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Event '550e8400-e29b-41d4-a716-446655440000' has already been acknowledged",
    "details": {
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "current_status": "acknowledged",
      "acknowledged_at": "2025-11-10T12:05:00.000000Z"
    },
    "request_id": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

### Payload Too Large Error (413)

**Request with Payload Exceeding 400KB:**
```bash
# Create a large payload (this is just an example - actual payload would need to be >400KB)
curl -X POST http://localhost:8080/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-12345" \
  -d '{
    "source": "my-app",
    "event_type": "large.event",
    "payload": {
      "data": "'$(python3 -c "print('x' * 410000)")'"
    }
  }'
```

**Error Response:**
```json
{
  "error": {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "Payload size exceeds 400KB limit",
    "details": {},
    "request_id": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

## Tips

1. **Request ID**: Always include `X-Request-ID` header for request tracking and debugging
2. **JSON Formatting**: Use `jq` to format JSON responses: `curl ... | jq`
3. **Error Handling**: Check HTTP status codes and error response format
4. **Pagination**: Use `next_cursor` from pagination object to get next page
5. **Idempotency**: Use `idempotency_key` in metadata to prevent duplicate events

## Environment Variables

For easier testing, you can set environment variables:

```bash
export API_KEY="test-api-key-12345"
export BASE_URL="http://localhost:8080"

# Then use in commands:
curl -X GET "$BASE_URL/v1/inbox?limit=10" \
  -H "X-API-Key: $API_KEY"
```

