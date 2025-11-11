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

## Response Headers (Phase 8)

All authenticated endpoints include rate limit information:

- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when window resets

## IP Allowlisting (Phase 8)

API keys can be configured with IP allowlists for additional security.

**Behavior:**
- If an API key has an IP allowlist configured, only requests from allowed IPs are accepted
- Supports exact IP matches and CIDR notation (e.g., `192.168.1.0/24`)
- Supports both IPv4 and IPv6 addresses
- Empty allowlist = allow all IPs (backward compatible)
- IP is extracted from `X-Forwarded-For`, `X-Real-IP`, or `request.client.host`

**Error Response (403 Forbidden):**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "IP address not allowed",
    "details": {
      "client_ip": "10.0.0.1",
      "allowed_ips": ["192.168.1.0/24"]
    },
    "request_id": "uuid-v4"
  }
}
```

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
- `created_after` (string, optional, Phase 8) - ISO 8601 timestamp - filter events created after this time
- `created_before` (string, optional, Phase 8) - ISO 8601 timestamp - filter events created before this time
- `priority` (string, optional, Phase 8) - Filter by priority: `low`, `normal`, or `high`
- `metadata_key` (string, optional, Phase 8) - Metadata field name to filter by (must be used with `metadata_value`)
- `metadata_value` (string, optional, Phase 8) - Metadata field value to match (must be used with `metadata_key`)

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

**Response Headers (Phase 8):**
- `X-RateLimit-Limit`: Maximum requests per minute for your API key
- `X-RateLimit-Remaining`: Remaining requests in current rate limit window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit window resets

**Error Responses:**
- `401` - Unauthorized
- `403` - Forbidden (IP address not allowed) (Phase 8)
- `429` - Rate limit exceeded (Phase 8)

### Bulk Operations (Phase 8)

#### POST /v1/events/bulk

Create multiple events in a single request (up to 25 events).

**Request Body:**
```json
{
  "items": [
    {
      "source": "string (required)",
      "event_type": "string (required)",
      "payload": {} (required),
      "metadata": {} (optional)
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "successful": [
    {
      "event_id": "uuid-v4",
      "created_at": "ISO 8601",
      "status": "pending",
      "message": "Event ingested successfully"
    }
  ],
  "failed": [
    {
      "index": 0,
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "Error message",
        "details": {}
      }
    }
  ],
  "request_id": "uuid-v4"
}
```

**Error Responses:**
- `400` - Validation error (invalid request body)
- `401` - Unauthorized
- `403` - Forbidden (IP address not allowed)
- `429` - Rate limit exceeded

#### POST /v1/events/bulk/ack

Acknowledge multiple events in a single request (up to 25 events).

**Request Body:**
```json
{
  "event_ids": ["uuid-1", "uuid-2", ...]
}
```

**Response (200 OK):**
```json
{
  "successful": [
    {
      "event_id": "uuid-v4",
      "status": "acknowledged",
      "acknowledged_at": "ISO 8601"
    }
  ],
  "failed": [
    {
      "index": 0,
      "error": {
        "code": "NOT_FOUND",
        "message": "Event not found",
        "details": {}
      }
    }
  ],
  "request_id": "uuid-v4"
}
```

**Error Responses:**
- `400` - Validation error
- `401` - Unauthorized
- `403` - Forbidden (IP address not allowed)
- `429` - Rate limit exceeded

#### DELETE /v1/events/bulk

Delete multiple events in a single request (up to 25 events).

**Request Body:**
```json
{
  "event_ids": ["uuid-1", "uuid-2", ...]
}
```

**Response (200 OK):**
```json
{
  "successful": ["uuid-1", "uuid-2"],
  "failed": [
    {
      "index": 0,
      "error": {
        "code": "NOT_FOUND",
        "message": "Event not found",
        "details": {}
      }
    }
  ],
  "request_id": "uuid-v4"
}
```

**Error Responses:**
- `400` - Validation error
- `401` - Unauthorized
- `403` - Forbidden (IP address not allowed)
- `429` - Rate limit exceeded

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

### Basic Filtering

Filter events by `source` and/or `event_type`:

```bash
# Filter by source
GET /v1/inbox?source=my-app

# Filter by event type
GET /v1/inbox?event_type=user.created

# Combined filtering
GET /v1/inbox?source=my-app&event_type=user.created
```

### Advanced Filtering (Phase 8)

Filter events by date range, priority, and metadata fields:

```bash
# Filter by date range
GET /v1/inbox?created_after=2025-11-10T00:00:00Z&created_before=2025-11-11T00:00:00Z

# Filter by priority
GET /v1/inbox?priority=high

# Filter by metadata field
GET /v1/inbox?metadata_key=user_id&metadata_value=12345

# Combined filtering
GET /v1/inbox?source=my-app&priority=high&created_after=2025-11-10T00:00:00Z
```

**Filter Parameters:**
- `created_after`: ISO 8601 timestamp - events created after this time
- `created_before`: ISO 8601 timestamp - events created before this time
- `priority`: `low`, `normal`, or `high` (matches `metadata.priority`)
- `metadata_key` + `metadata_value`: Exact match on metadata field (both required)

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

## Rate Limiting (Phase 8)

API requests are subject to rate limiting with configurable limits per API key.

### Rate Limit Headers

All responses include rate limit information in headers:

- `X-RateLimit-Limit`: Maximum requests per minute for your API key (default: 1000)
- `X-RateLimit-Remaining`: Remaining requests in current rate limit window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit window resets

### Rate Limit Behavior

- **Algorithm**: Token bucket with 60-second windows
- **Default Limit**: 1000 requests per minute per API key
- **Configurable**: Limits can be customized per API key
- **Window**: Rolling 60-second windows

### Rate Limit Exceeded

When rate limit is exceeded, you'll receive:

**Status Code:** `429 Too Many Requests`

**Response Headers:**
- `Retry-After`: Number of seconds to wait before retrying

**Response Body:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 1000,
      "retry_after": 45
    },
    "request_id": "uuid-v4"
  }
}
```

**Handling Rate Limits:**
1. Check `X-RateLimit-Remaining` header to monitor usage
2. When `429` is received, wait for the duration specified in `Retry-After` header
3. Implement exponential backoff for retries
4. Consider using bulk operations to reduce request count

## API Versioning

The API uses URL-based versioning. All endpoints are prefixed with `/v1`.

### Current Version

**Version:** v1  
**Base URL:** `/v1/...`

### Versioning Policy

**Breaking Changes:**
- Removing endpoints
- Changing request/response structure
- Removing required fields
- Changing field types or formats
- Changing authentication requirements

**Non-Breaking Changes:**
- Adding new endpoints
- Adding optional fields to requests/responses
- Adding new error codes
- Performance improvements
- Documentation updates

### Version Support

- **Current Version:** v1 (fully supported)
- **Previous Versions:** None (v1 is the first version)
- **Support Lifecycle:** Previous versions supported for 6-12 months after new version release

### Version Negotiation

Version is specified in the URL path:

```bash
# v1 endpoints
GET /v1/health
POST /v1/events
GET /v1/inbox
```

**Client Configuration:**
```python
# Python
client = TriggersAPIClient(
    api_key="your-api-key",
    base_url="https://api.example.com/v1"  # Version in URL
)
```

```javascript
// JavaScript
const client = new TriggersAPIClient({
    apiKey: 'your-api-key',
    baseUrl: 'https://api.example.com/v1'  // Version in URL
});
```

### Migration Guide

When a new version is released:

1. **Announcement:** 6 months before deprecation
2. **Deprecation Period:** 6 months with warnings
3. **Migration Support:** Documentation and examples provided
4. **Removal:** Previous version removed after deprecation period

**Migration Steps:**
1. Review breaking changes documentation
2. Update client code to use new version
3. Test thoroughly in development
4. Deploy to production
5. Monitor for issues

### Deprecation Timeline

**Process:**
1. **Announcement:** New version announced, deprecation timeline published
2. **Warning Period (3 months):** Deprecation warnings in API responses
3. **Deprecation Period (6 months):** Version marked as deprecated
4. **Removal:** Version removed after deprecation period

**Communication Channels:**
- GitHub releases and announcements
- API documentation updates
- Email notifications (if subscribed)
- Deprecation warnings in API responses

## Best Practices

1. **Always include Request ID**: Use `X-Request-ID` header for request tracking
2. **Use Idempotency Keys**: Prevent duplicate events in retry scenarios
3. **Handle Errors Gracefully**: Check error codes and details
4. **Implement Retry Logic**: For transient errors (network, 500, 429)
5. **Monitor Event Status**: Use GET /v1/events/{id} to verify event state
6. **Acknowledge Events**: Mark events as processed after handling
7. **Clean Up**: Delete processed events to maintain data hygiene
8. **Version Your Integration**: Specify API version in base URL
9. **Monitor Deprecation Warnings**: Check for version deprecation notices

## See Also

- [Usage Examples](EXAMPLES.md) - Common use cases
- [Error Handling Guide](ERRORS.md) - Error codes and handling
- [cURL Examples](CURL_EXAMPLES.md) - Command-line examples
- [Architecture Documentation](ARCHITECTURE.md) - System architecture

