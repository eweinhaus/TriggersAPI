# API Reference

Complete reference documentation for the Zapier Triggers API.

## Base URL

- **Local Development**: `http://localhost:8080`
- **Production**: Your production API URL

## Authentication

Most endpoints require API key authentication via the `X-API-Key` header.

**Local Development**: Use `test-api-key-12345`  
**Production**: Use your actual API key from account settings

## Request Headers

- `Content-Type: application/json` - Required for POST requests
- `X-API-Key: your-api-key` - Required for authenticated endpoints
- `X-Request-ID: optional-request-id` - Optional request tracking ID

## Response Format

All responses include a `request_id` field for request tracking.

### Success Response

```json
{
  "data": { ... },
  "request_id": "uuid-v4"
}
```

### Error Response

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { ... },
    "request_id": "uuid-v4"
  }
}
```

## Endpoints

### Health Check

#### GET /v1/health

Check API availability and status. No authentication required.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T12:00:00.000000Z",
  "version": "1.0.0"
}
```

### Events

#### POST /v1/events

Create a new event.

**Request Body:**
```json
{
  "source": "string (required, 1-100 chars)",
  "event_type": "string (required, 1-100 chars)",
  "payload": {} (required, non-empty JSON object),
  "metadata": {
    "idempotency_key": "string (optional)",
    "priority": "low|normal|high (optional, default: normal)",
    "correlation_id": "string (optional)"
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
- `400` - Validation error
- `401` - Unauthorized
- `413` - Payload too large (>400KB)

#### GET /v1/events/{event_id}

Get detailed information about a specific event.

**Path Parameters:**
- `event_id` (UUID v4) - Event identifier

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
  "acknowledged_at": "ISO 8601 (optional)",
  "request_id": "uuid-v4"
}
```

**Error Responses:**
- `401` - Unauthorized
- `404` - Event not found

#### POST /v1/events/{event_id}/ack

Acknowledge an event.

**Path Parameters:**
- `event_id` (UUID v4) - Event identifier

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
- `401` - Unauthorized
- `404` - Event not found
- `409` - Event already acknowledged

#### DELETE /v1/events/{event_id}

Delete an event. Idempotent operation.

**Path Parameters:**
- `event_id` (UUID v4) - Event identifier

**Response (200 OK):**
```json
{
  "event_id": "uuid-v4",
  "message": "Event deleted successfully",
  "request_id": "uuid-v4"
}
```

**Error Responses:**
- `401` - Unauthorized

### Inbox

#### GET /v1/inbox

Retrieve pending events with pagination and filtering.

**Query Parameters:**
- `limit` (integer, 1-100, default: 50) - Number of events to return
- `cursor` (string, optional) - Pagination cursor from previous response
- `source` (string, optional) - Filter by source identifier
- `event_type` (string, optional) - Filter by event type

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
    "limit": 50,
    "next_cursor": "base64-encoded-cursor (optional)"
  },
  "request_id": "uuid-v4"
}
```

**Error Responses:**
- `401` - Unauthorized

## Pagination

The inbox endpoint uses cursor-based pagination:

1. Make initial request with `limit` parameter
2. If response includes `next_cursor` in pagination, use it for next page
3. Continue until no `next_cursor` is returned

**Example:**
```bash
# First page
GET /v1/inbox?limit=10

# Next page
GET /v1/inbox?limit=10&cursor=eyJldmVudF9pZCI6...
```

## Filtering

Filter events by `source` and/or `event_type`:

```bash
# Filter by source
GET /v1/inbox?source=my-app

# Filter by event type
GET /v1/inbox?event_type=user.created

# Combined filtering
GET /v1/inbox?source=my-app&event_type=user.created
```

## Idempotency

Prevent duplicate events using idempotency keys:

```json
{
  "source": "my-app",
  "event_type": "user.created",
  "payload": { ... },
  "metadata": {
    "idempotency_key": "unique-key-123"
  }
}
```

If an event with the same idempotency key exists within 24 hours, the existing event is returned instead of creating a new one.

## Rate Limiting

API requests are subject to rate limiting. When rate limit is exceeded, you'll receive a `429 Rate Limit Exceeded` error.

## Best Practices

1. **Always include Request ID**: Use `X-Request-ID` header for request tracking
2. **Use Idempotency Keys**: Prevent duplicate events in retry scenarios
3. **Handle Errors Gracefully**: Check error codes and details
4. **Implement Retry Logic**: For transient errors (network, 500, 429)
5. **Monitor Event Status**: Use GET /v1/events/{id} to verify event state
6. **Acknowledge Events**: Mark events as processed after handling
7. **Clean Up**: Delete processed events to maintain data hygiene

## See Also

- [Usage Examples](EXAMPLES.md) - Common use cases
- [Error Handling Guide](ERRORS.md) - Error codes and handling
- [cURL Examples](CURL_EXAMPLES.md) - Command-line examples

