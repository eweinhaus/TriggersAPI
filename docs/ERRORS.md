# Error Handling Guide

Complete guide to error codes, error handling, and troubleshooting.

## Error Response Format

All errors follow a standardized format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "field_name (for validation errors)",
      "issue": "Description of the issue",
      "suggestion": "Actionable suggestion to fix",
      "event_id": "uuid (for not found/conflict errors)",
      "current_status": "status (for conflict errors)"
    },
    "request_id": "uuid-v4"
  }
}
```

## Error Codes

**Complete List:**
- `VALIDATION_ERROR` (400) - Invalid request payload or parameters
- `UNAUTHORIZED` (401) - Missing or invalid API key
- `FORBIDDEN` (403) - IP address not allowed (Phase 8)
- `NOT_FOUND` (404) - Resource not found
- `CONFLICT` (409) - Resource conflict (e.g., already acknowledged)
- `PAYLOAD_TOO_LARGE` (413) - Payload exceeds 400KB limit
- `RATE_LIMIT_EXCEEDED` (429) - Rate limit exceeded (Phase 8)
- `INTERNAL_ERROR` (500) - Server error

### VALIDATION_ERROR (400)

Request validation failed. Check the `details` field for specific issues.

**Common Causes:**
- Missing required fields
- Invalid field values
- Field length violations
- Invalid JSON structure

**Example:**
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

**How to Fix:**
- Review the `details.field` to identify the problematic field
- Check the `details.issue` for specific validation rules
- Follow the `details.suggestion` to resolve the issue

### FORBIDDEN (403) - Phase 8

IP address not allowed. Your API key has IP allowlisting configured and your current IP is not in the allowed list.

**Common Causes:**
- API key configured with IP allowlist
- Current IP address not in allowed list
- IP address changed (dynamic IP)
- Proxy/VPN IP not whitelisted

**Example:**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "IP address not allowed",
    "details": {
      "client_ip": "10.0.0.1",
      "allowed_ips": ["192.168.1.0/24", "203.0.113.0/24"]
    },
    "request_id": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

**How to Fix:**
- Contact API administrator to add your IP to the allowlist
- If using dynamic IP, request CIDR range be added
- If behind proxy/VPN, ensure proxy IP is whitelisted
- Verify your current IP address matches expected value

### UNAUTHORIZED (401)

Authentication failed. Invalid or missing API key.

**Common Causes:**
- Missing `X-API-Key` header
- Invalid API key
- API key not active
- Wrong API key for environment (local vs production)

**Example:**
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

**How to Fix:**
- Verify `X-API-Key` header is included
- Check API key is correct
- For local: use `test-api-key-12345`
- For production: use your actual API key
- Verify API key is active in your account

### NOT_FOUND (404)

Resource not found.

**Common Causes:**
- Invalid event ID
- Event doesn't exist
- Event was deleted
- Typo in resource identifier

**Example:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Event with ID '550e8400-e29b-41d4-a716-446655440000' was not found",
    "details": {
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "suggestion": "Verify the event ID is correct and the event exists"
    },
    "request_id": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

**How to Fix:**
- Verify the event ID is correct (UUID v4 format)
- Check if event exists using GET /v1/events/{id}
- Check if event was deleted
- Verify you're using the correct API/environment

### CONFLICT (409)

Resource conflict. Operation cannot be completed due to current state.

**Common Causes:**
- Event already acknowledged
- Duplicate operation
- State mismatch

**Example:**
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

**How to Fix:**
- Check `details.current_status` to see current state
- Verify if operation was already completed
- Use GET /v1/events/{id} to check current state
- For idempotent operations, this may be expected (operation already done)

### PAYLOAD_TOO_LARGE (413)

Request payload exceeds size limit (400KB).

**Common Causes:**
- Payload too large
- Attachments or large data in payload
- Nested structures with excessive data

**Example:**
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

**How to Fix:**
- Reduce payload size to under 400KB
- Remove unnecessary data
- Use references instead of full data
- Split into multiple events if needed

### RATE_LIMIT_EXCEEDED (429) - Phase 8

Rate limit exceeded. Too many requests in the time window.

**Common Causes:**
- Exceeded requests per minute limit for your API key
- Burst of requests in short time period
- Default limit: 1000 requests per minute
- Custom limits may be lower

**Example:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 1000,
      "retry_after": 45
    },
    "request_id": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

**Response Headers:**
- `Retry-After`: Number of seconds to wait before retrying

**How to Fix:**
1. Wait for the duration specified in `Retry-After` header
2. Implement exponential backoff for retries
3. Use bulk operations to reduce request count
4. Monitor `X-RateLimit-Remaining` header to track usage
5. Contact API administrator to increase rate limit if needed
6. Consider implementing request queuing/throttling on client side

**Best Practices:**
- Check `X-RateLimit-Remaining` header before making requests
- Implement client-side rate limiting to stay under limit
- Use bulk endpoints when processing multiple events
- Cache responses when possible to reduce API calls

### INTERNAL_ERROR (500)

Internal server error. Something went wrong on the server.

**Common Causes:**
- Server-side bug
- Database issues
- Infrastructure problems
- Temporary service disruption

**Example:**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error",
    "details": {},
    "request_id": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

**How to Fix:**
- Retry the request (may be transient)
- Check service status
- Report to support with `request_id`
- Implement retry logic with exponential backoff

## Error Handling Patterns

### Python

```python
from triggers_api import (
    TriggersAPIClient,
    ValidationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    InternalError,
)

client = TriggersAPIClient(api_key="your-api-key", base_url="http://localhost:8080")

try:
    event = client.create_event(
        source="my-app",
        event_type="user.created",
        payload={"user_id": "123"}
    )
except ValidationError as e:
    # Handle validation errors - fix request and retry
    print(f"Validation error: {e.message}")
    print(f"Field: {e.details.get('field')}")
    print(f"Suggestion: {e.details.get('suggestion')}")
except NotFoundError as e:
    # Handle not found - check if resource exists
    print(f"Not found: {e.message}")
except ConflictError as e:
    # Handle conflict - check current state
    print(f"Conflict: {e.message}")
    print(f"Current status: {e.details.get('current_status')}")
except RateLimitError as e:
    # Handle rate limit - implement backoff
    print(f"Rate limited: {e.message}")
    time.sleep(60)  # Wait before retry
except InternalError as e:
    # Handle server errors - retry with backoff
    print(f"Server error: {e.message}")
    print(f"Request ID: {e.request_id}")
    # Retry with exponential backoff
except TriggersAPIError as e:
    # Generic error handling
    print(f"API error: {e.message}")
    print(f"Request ID: {e.request_id}")
```

### JavaScript

```javascript
const TriggersAPIClient = require('./src/client');
const {
    ValidationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    InternalError,
} = require('./src/errors');

const client = new TriggersAPIClient({
    apiKey: 'your-api-key',
    baseUrl: 'http://localhost:8080'
});

try {
    const event = await client.createEvent({
        source: 'my-app',
        eventType: 'user.created',
        payload: { userId: '123' }
    });
} catch (error) {
    if (error instanceof ValidationError) {
        // Handle validation errors
        console.log(`Validation error: ${error.message}`);
        console.log(`Field: ${error.details.field}`);
        console.log(`Suggestion: ${error.details.suggestion}`);
    } else if (error instanceof NotFoundError) {
        // Handle not found
        console.log(`Not found: ${error.message}`);
    } else if (error instanceof ConflictError) {
        // Handle conflict
        console.log(`Conflict: ${error.message}`);
        console.log(`Current status: ${error.details.current_status}`);
    } else if (error instanceof RateLimitError) {
        // Handle rate limit
        console.log(`Rate limited: ${error.message}`);
        await new Promise(resolve => setTimeout(resolve, 60000)); // Wait 60s
    } else if (error instanceof InternalError) {
        // Handle server errors
        console.log(`Server error: ${error.message}`);
        console.log(`Request ID: ${error.requestId}`);
        // Retry with exponential backoff
    } else {
        // Generic error handling
        console.log(`API error: ${error.message}`);
        console.log(`Request ID: ${error.requestId}`);
    }
}
```

## Retry Strategies

### Exponential Backoff

```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except (RateLimitError, InternalError) as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
    return None
```

### Retry on Specific Errors

```python
def create_event_with_retry(client, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.create_event(
                source="my-app",
                event_type="user.created",
                payload={"user_id": "123"}
            )
        except (RateLimitError, InternalError) as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except (ValidationError, UnauthorizedError) as e:
            # Don't retry - fix the issue first
            raise
```

## Troubleshooting

### Common Issues

1. **"Invalid or missing API key"**
   - Check `X-API-Key` header is included
   - Verify API key is correct
   - For local: use `test-api-key-12345`

2. **"Event not found"**
   - Verify event ID is correct (UUID v4)
   - Check if event exists
   - Verify correct environment (local vs production)

3. **"Event already acknowledged"**
   - This is expected if event was already processed
   - Check event status before acknowledging
   - May indicate duplicate processing attempt

4. **"Payload too large"**
   - Reduce payload size
   - Remove unnecessary data
   - Split into multiple events

5. **"Rate limit exceeded"**
   - Reduce request frequency
   - Implement exponential backoff
   - Batch requests when possible

### Getting Help

When reporting issues, include:
- Error code and message
- Request ID (from error response)
- Request details (endpoint, payload)
- Environment (local vs production)
- Steps to reproduce

## See Also

- [API Reference](API.md) - Complete endpoint documentation
- [Usage Examples](EXAMPLES.md) - Code examples
- [cURL Examples](CURL_EXAMPLES.md) - Command-line examples

