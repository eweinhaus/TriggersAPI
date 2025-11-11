# Zapier Triggers API - Python Client

A Python client library for the Zapier Triggers API.

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from triggers_api import TriggersAPIClient

# Initialize client
client = TriggersAPIClient(
    api_key="your-api-key",
    base_url="http://localhost:8080"  # or your production URL
)

# Create an event
event = client.create_event(
    source="my-app",
    event_type="user.created",
    payload={"user_id": "123", "name": "John Doe"}
)

print(f"Event created: {event.event_id}")
```

## Configuration

### Local Development

```python
client = TriggersAPIClient(
    api_key="test-api-key-12345",
    base_url="http://localhost:8080"
)
```

### Production

```python
client = TriggersAPIClient(
    api_key="your-production-api-key",
    base_url="https://your-api-url.com"
)
```

## API Methods

### Create Event

```python
event = client.create_event(
    source="my-app",
    event_type="user.created",
    payload={"user_id": "123"},
    metadata={
        "idempotency_key": "unique-key-123",
        "priority": "high",
        "correlation_id": "corr-456"
    }
)
```

### Get Event

```python
event = client.get_event("550e8400-e29b-41d4-a716-446655440000")
print(event.payload)
print(event.status)
```

### Get Inbox

```python
# Get all pending events
inbox = client.get_inbox(limit=50)

# Filter by source
inbox = client.get_inbox(limit=50, source="my-app")

# Filter by event type
inbox = client.get_inbox(limit=50, event_type="user.created")

# Pagination
inbox = client.get_inbox(limit=10)
if "next_cursor" in inbox.pagination:
    next_page = client.get_inbox(
        limit=10,
        cursor=inbox.pagination["next_cursor"]
    )
```

### Acknowledge Event

```python
ack = client.acknowledge_event("550e8400-e29b-41d4-a716-446655440000")
print(f"Acknowledged at: {ack.acknowledged_at}")
```

### Delete Event

```python
result = client.delete_event("550e8400-e29b-41d4-a716-446655440000")
print(result.message)
```

## Error Handling

```python
from triggers_api import (
    TriggersAPIClient,
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
)

try:
    event = client.create_event(
        source="my-app",
        event_type="user.created",
        payload={"user_id": "123"}
    )
except ValidationError as e:
    print(f"Validation error: {e.message}")
    print(f"Details: {e.details}")
except UnauthorizedError as e:
    print(f"Authentication failed: {e.message}")
except TriggersAPIError as e:
    print(f"API error: {e.message}")
    print(f"Request ID: {e.request_id}")
```

## Request ID Tracking

You can optionally provide a request ID for tracking:

```python
event = client.create_event(
    source="my-app",
    event_type="user.created",
    payload={"user_id": "123"},
    request_id="my-custom-request-id"
)
```

Or set a default request ID when initializing the client:

```python
client = TriggersAPIClient(
    api_key="your-api-key",
    base_url="http://localhost:8080",
    request_id="default-request-id"
)
```

## Examples

See the `examples/` directory for complete examples:

- `basic_usage.py` - Basic API usage
- `event_flow.py` - Complete event lifecycle
- `error_handling.py` - Error handling patterns

Run examples:

```bash
cd examples
python basic_usage.py
python event_flow.py
python error_handling.py
```

## Response Models

All methods return Pydantic models with type hints:

- `EventResponse` - Event creation response
- `EventDetailResponse` - Event details response
- `InboxResponse` - Inbox query response
- `AckResponse` - Acknowledgment response
- `DeleteResponse` - Deletion response

## Error Classes

- `TriggersAPIError` - Base exception class
- `ValidationError` - Request validation failed (400)
- `UnauthorizedError` - Authentication failed (401)
- `NotFoundError` - Resource not found (404)
- `ConflictError` - Resource conflict (409)
- `PayloadTooLargeError` - Payload too large (413)
- `RateLimitError` - Rate limit exceeded (429)
- `InternalError` - Server error (500)

## Troubleshooting

### Connection Errors

If you get connection errors, verify:
- The API server is running
- The `base_url` is correct
- Network connectivity is available

### Authentication Errors

If you get `UnauthorizedError`:
- Verify your API key is correct
- Check that the API key is active
- Ensure you're using the correct API key for the environment (local vs production)

### Validation Errors

If you get `ValidationError`:
- Check the error details for specific field issues
- Verify required fields are provided
- Ensure field values meet requirements (e.g., non-empty, within length limits)

## License

Internal project for Zapier.

