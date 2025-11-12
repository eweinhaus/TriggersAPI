# Structured Logging

The Triggers API uses structured JSON logging for better observability and CloudWatch Log Insights compatibility.

## Log Format

All logs are emitted as JSON objects with the following structure:

```json
{
  "timestamp": "2025-11-11T12:00:00.000000Z",
  "level": "INFO",
  "message": "Event created successfully",
  "logger": "src.endpoints.events",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "api_key": "test-api...",
  "endpoint": "/v1/events",
  "method": "POST",
  "operation": "create_event",
  "event_id": "660e8400-e29b-41d4-a716-446655440001",
  "status_code": 201,
  "duration_ms": 45.2
}
```

## Log Fields

### Standard Fields
- `timestamp`: ISO 8601 UTC timestamp with microseconds
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `message`: Human-readable log message
- `logger`: Logger name (typically module path)

### Request Context Fields
These fields are automatically added to all logs during request processing:
- `request_id`: Unique request identifier (UUID v4)
- `api_key`: Masked API key (first 8 characters + "...")
- `endpoint`: Request endpoint path
- `method`: HTTP method (GET, POST, DELETE, etc.)

### Operation-Specific Fields
Additional fields are added based on the operation:
- `operation`: Operation name (e.g., "create_event", "get_inbox")
- `event_id`: Event identifier (when applicable)
- `status_code`: HTTP status code
- `duration_ms`: Request duration in milliseconds
- `error`: Error message (for error logs)
- `error_type`: Error type/class name

## CloudWatch Log Insights Queries

### Error Rate by Endpoint
```
fields @timestamp, endpoint, method, status_code, error
| filter level = "ERROR" or level = "WARNING"
| stats count() by endpoint, method
```

### Request Latency by Endpoint
```
fields @timestamp, endpoint, method, duration_ms
| filter duration_ms > 0
| stats avg(duration_ms), max(duration_ms), pct(duration_ms, 95) by endpoint, method
```

### Failed Authentication Attempts
```
fields @timestamp, api_key, endpoint, error
| filter operation = "validate_api_key" and level = "WARNING"
| stats count() by api_key
```

### Event Creation Rate
```
fields @timestamp, operation
| filter operation = "create_event" and status_code = 201
| stats count() by bin(5m)
```

### Request Correlation (by request_id)
```
fields @timestamp, request_id, endpoint, method, status_code, duration_ms
| filter request_id = "550e8400-e29b-41d4-a716-446655440000"
| sort @timestamp asc
```

### High Latency Requests
```
fields @timestamp, endpoint, method, duration_ms, request_id
| filter duration_ms > 100
| sort duration_ms desc
```

## Log Levels

- **DEBUG**: Detailed diagnostic information (only when `LOG_LEVEL=DEBUG`)
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages (e.g., event not found, already acknowledged)
- **ERROR**: Error messages (e.g., failed operations, exceptions)
- **CRITICAL**: Critical errors requiring immediate attention

## Configuration

Set log level via environment variable:
```bash
export LOG_LEVEL=INFO  # or DEBUG, WARNING, ERROR, CRITICAL
```

## Best Practices

1. **Request Correlation**: Use `request_id` to correlate all logs for a single request
2. **Structured Fields**: Always use structured fields in `extra` parameter
3. **Error Context**: Include full error context in error logs
4. **Performance**: Log duration_ms for all endpoint operations
5. **Security**: Never log full API keys or sensitive data

## Example Usage

```python
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Info log with structured fields
logger.info(
    "Event created successfully",
    extra={
        'operation': 'create_event',
        'event_id': event_id,
        'status_code': 201,
        'duration_ms': duration_ms,
    }
)

# Error log with context
logger.error(
    "Failed to create event",
    extra={
        'operation': 'create_event',
        'error': str(e),
        'error_type': type(e).__name__,
        'status_code': 500,
    }
)
```


