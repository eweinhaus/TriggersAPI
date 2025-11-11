# Chaos Engineering Guide

## Overview

Chaos engineering features allow you to inject controlled failures into the API for resilience testing. This helps ensure your application handles failures gracefully.

## Features

- **Random Delays**: Inject random delays to simulate network latency
- **Random Errors**: Inject random HTTP errors (500, 503, 504)
- **Configurable Rates**: Control failure injection rates (0.0 to 1.0)
- **Per-Endpoint**: Configure chaos per endpoint (future feature)

## Configuration

Chaos engineering is **disabled by default** and must be explicitly enabled via environment variables.

### Environment Variables

- `CHAOS_ENABLED`: Enable chaos engineering (`true`/`false`, default: `false`)
- `CHAOS_ERROR_RATE`: Probability of injecting an error (0.0 to 1.0, default: `0.0`)
- `CHAOS_DELAY_RATE`: Probability of injecting a delay (0.0 to 1.0, default: `0.0`)
- `CHAOS_MAX_DELAY_MS`: Maximum delay in milliseconds (default: `1000`)

### Example Configuration

```bash
# Enable chaos with 10% error rate and 20% delay rate
export CHAOS_ENABLED=true
export CHAOS_ERROR_RATE=0.1
export CHAOS_DELAY_RATE=0.2
export CHAOS_MAX_DELAY_MS=500
```

## Usage

### Testing Resilience

1. **Enable Chaos**: Set `CHAOS_ENABLED=true`
2. **Configure Rates**: Set error and delay rates
3. **Run Tests**: Execute your test suite
4. **Verify Handling**: Ensure your application handles failures gracefully

### Example Test

```python
import os
import pytest
from fastapi.testclient import TestClient

# Enable chaos for testing
os.environ['CHAOS_ENABLED'] = 'true'
os.environ['CHAOS_ERROR_RATE'] = '0.1'  # 10% error rate
os.environ['CHAOS_DELAY_RATE'] = '0.2'  # 20% delay rate

def test_resilience():
    client = TestClient(app)
    
    # Make multiple requests
    for _ in range(100):
        try:
            response = client.post('/v1/events', json={
                'source': 'test',
                'event_type': 'test.event',
                'payload': {}
            })
            # Handle both success and error cases
            assert response.status_code in [201, 500, 503, 504]
        except Exception as e:
            # Verify error handling
            assert 'CHAOS_ERROR' in str(e) or 'Network' in str(e)
```

## Injected Errors

When chaos is enabled, the following HTTP status codes may be injected:

- **500 Internal Server Error**: General server error
- **503 Service Unavailable**: Service temporarily unavailable
- **504 Gateway Timeout**: Gateway timeout

Error responses follow the standard API error format:

```json
{
  "error": {
    "code": "CHAOS_ERROR",
    "message": "Chaos: Injected 500 error",
    "details": {},
    "request_id": null
  }
}
```

## Best Practices

1. **Use in Testing Only**: Never enable chaos in production
2. **Gradual Increase**: Start with low rates (0.01) and increase gradually
3. **Monitor Impact**: Monitor error rates and latency when chaos is enabled
4. **Test Retry Logic**: Verify that retry logic works correctly
5. **Test Timeouts**: Ensure timeouts are configured appropriately

## Safety

- **Disabled by Default**: Chaos is disabled unless explicitly enabled
- **No Production Risk**: Never enable in production environments
- **Configurable**: All rates and behaviors are configurable
- **Logging**: All chaos injections are logged for debugging

## Advanced Usage

### Decorators

You can use chaos decorators in your tests:

```python
from src.middleware.chaos import inject_chaos_delay, inject_chaos_error

# Inject fixed delay
@inject_chaos_delay(500)  # 500ms delay
async def test_with_delay():
    # Test code
    pass

# Inject fixed error
@inject_chaos_error(503)  # 503 error
async def test_with_error():
    # Test code
    pass
```

## Troubleshooting

### Chaos Not Working

- **Check Environment**: Verify `CHAOS_ENABLED=true`
- **Check Rates**: Ensure rates are > 0.0
- **Check Logs**: Look for chaos injection logs

### Too Many Errors

- **Reduce Rate**: Lower `CHAOS_ERROR_RATE`
- **Check Configuration**: Verify environment variables

### Too Many Delays

- **Reduce Rate**: Lower `CHAOS_DELAY_RATE`
- **Reduce Max Delay**: Lower `CHAOS_MAX_DELAY_MS`

## Additional Resources

- [Testing Guide](../tests/chaos/test_chaos.py) - Example chaos tests
- [Middleware Source](../src/middleware/chaos.py) - Implementation details

