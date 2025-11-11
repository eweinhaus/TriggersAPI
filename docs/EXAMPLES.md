# Usage Examples

Common use cases and code examples for the Zapier Triggers API.

## Table of Contents

- [Event Lifecycle](#event-lifecycle)
- [Polling for Events](#polling-for-events)
- [Idempotency](#idempotency)
- [Error Handling](#error-handling)
- [Retry Patterns](#retry-patterns)
- [Pagination](#pagination)
- [Filtering](#filtering)

## Event Lifecycle

Complete workflow: Create → Process → Acknowledge → Delete

### Python

```python
from triggers_api import TriggersAPIClient

client = TriggersAPIClient(
    api_key="your-api-key",
    base_url="http://localhost:8080"
)

# 1. Create event
event = client.create_event(
    source="workflow-app",
    event_type="task.completed",
    payload={"task_id": "123", "status": "done"}
)

# 2. Get event details
details = client.get_event(event.event_id)

# 3. Process event (your business logic)
process_task(details.payload)

# 4. Acknowledge event
client.acknowledge_event(event.event_id)

# 5. Clean up
client.delete_event(event.event_id)
```

### JavaScript

```javascript
const TriggersAPIClient = require('./src/client');

const client = new TriggersAPIClient({
    apiKey: 'your-api-key',
    baseUrl: 'http://localhost:8080'
});

async function processEvent() {
    // 1. Create event
    const event = await client.createEvent({
        source: 'workflow-app',
        eventType: 'task.completed',
        payload: { taskId: '123', status: 'done' }
    });

    // 2. Get event details
    const details = await client.getEvent(event.event_id);

    // 3. Process event
    await processTask(details.payload);

    // 4. Acknowledge event
    await client.acknowledgeEvent(event.event_id);

    // 5. Clean up
    await client.deleteEvent(event.event_id);
}
```

## Polling for Events

Poll the inbox for new events to process.

### Python

```python
import time
from triggers_api import TriggersAPIClient

client = TriggersAPIClient(
    api_key="your-api-key",
    base_url="http://localhost:8080"
)

def poll_events():
    cursor = None
    while True:
        inbox = client.get_inbox(limit=50, cursor=cursor)
        
        for event in inbox.events:
            # Process event
            process_event(event)
            # Acknowledge
            client.acknowledge_event(event['event_id'])
        
        # Check for more events
        if 'next_cursor' in inbox.pagination:
            cursor = inbox.pagination['next_cursor']
        else:
            cursor = None
            time.sleep(5)  # Wait before next poll
```

### JavaScript

```javascript
const TriggersAPIClient = require('./src/client');

const client = new TriggersAPIClient({
    apiKey: 'your-api-key',
    baseUrl: 'http://localhost:8080'
});

async function pollEvents() {
    let cursor = null;
    
    while (true) {
        const inbox = await client.getInbox({ limit: 50, cursor });
        
        for (const event of inbox.events) {
            // Process event
            await processEvent(event);
            // Acknowledge
            await client.acknowledgeEvent(event.event_id);
        }
        
        // Check for more events
        if (inbox.pagination.next_cursor) {
            cursor = inbox.pagination.next_cursor;
        } else {
            cursor = null;
            await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5s
        }
    }
}
```

## Idempotency

Prevent duplicate events using idempotency keys.

### Python

```python
# First request
event1 = client.create_event(
    source="my-app",
    event_type="payment.processed",
    payload={"payment_id": "pay-123", "amount": 100},
    metadata={"idempotency_key": "payment-pay-123"}
)

# Retry with same idempotency key (returns existing event)
event2 = client.create_event(
    source="my-app",
    event_type="payment.processed",
    payload={"payment_id": "pay-123", "amount": 100},
    metadata={"idempotency_key": "payment-pay-123"}
)

# event1.event_id == event2.event_id (same event returned)
```

### JavaScript

```javascript
// First request
const event1 = await client.createEvent({
    source: 'my-app',
    eventType: 'payment.processed',
    payload: { paymentId: 'pay-123', amount: 100 },
    metadata: { idempotency_key: 'payment-pay-123' }
});

// Retry with same idempotency key
const event2 = await client.createEvent({
    source: 'my-app',
    eventType: 'payment.processed',
    payload: { paymentId: 'pay-123', amount: 100 },
    metadata: { idempotency_key: 'payment-pay-123' }
});

// event1.event_id === event2.event_id (same event)
```

## Error Handling

Comprehensive error handling patterns.

### Python

```python
from triggers_api import (
    TriggersAPIClient,
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
)

client = TriggersAPIClient(
    api_key="your-api-key",
    base_url="http://localhost:8080"
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
    # Handle re-authentication
except TriggersAPIError as e:
    print(f"API error: {e.message}")
    print(f"Request ID: {e.request_id}")
    # Log for support
```

### JavaScript

```javascript
const TriggersAPIClient = require('./src/client');
const {
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
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
        console.log(`Validation error: ${error.message}`);
        console.log('Details:', error.details);
    } else if (error instanceof UnauthorizedError) {
        console.log(`Authentication failed: ${error.message}`);
        // Handle re-authentication
    } else if (error instanceof TriggersAPIError) {
        console.log(`API error: ${error.message}`);
        console.log(`Request ID: ${error.requestId}`);
        // Log for support
    }
}
```

## Pagination

Handle paginated results efficiently.

### Python

```python
def get_all_events(client, source=None):
    """Get all events, handling pagination."""
    all_events = []
    cursor = None
    
    while True:
        inbox = client.get_inbox(limit=100, cursor=cursor, source=source)
        all_events.extend(inbox.events)
        
        if 'next_cursor' in inbox.pagination:
            cursor = inbox.pagination['next_cursor']
        else:
            break
    
    return all_events
```

### JavaScript

```javascript
async function getAllEvents(client, source = null) {
    const allEvents = [];
    let cursor = null;
    
    while (true) {
        const inbox = await client.getInbox({ limit: 100, cursor, source });
        allEvents.push(...inbox.events);
        
        if (inbox.pagination.next_cursor) {
            cursor = inbox.pagination.next_cursor;
        } else {
            break;
        }
    }
    
    return allEvents;
}
```

## Filtering

### Basic Filtering

Filter events by source and event type.

### Python

```python
# Get events from specific source
inbox = client.get_inbox(source="payment-service", limit=50)

# Get specific event types
inbox = client.get_inbox(event_type="payment.completed", limit=50)

# Combined filtering
inbox = client.get_inbox(
    source="payment-service",
    event_type="payment.completed",
    limit=50
)
```

### JavaScript

```javascript
// Get events from specific source
const inbox = await client.getInbox({ source: 'payment-service', limit: 50 });

// Get specific event types
const inbox = await client.getInbox({ eventType: 'payment.completed', limit: 50 });

// Combined filtering
const inbox = await client.getInbox({
    source: 'payment-service',
    eventType: 'payment.completed',
    limit: 50
});
```

### Advanced Filtering (Phase 8)

Filter events by date range, priority, and metadata fields.

### Python

```python
from datetime import datetime, timezone

# Filter by date range
created_after = datetime(2025, 11, 10, tzinfo=timezone.utc).isoformat()
created_before = datetime(2025, 11, 11, tzinfo=timezone.utc).isoformat()
inbox = client.get_inbox(
    created_after=created_after,
    created_before=created_before,
    limit=50
)

# Filter by priority
inbox = client.get_inbox(priority="high", limit=50)

# Filter by metadata field
inbox = client.get_inbox(
    metadata_key="user_id",
    metadata_value="12345",
    limit=50
)

# Combined advanced filtering
inbox = client.get_inbox(
    source="payment-service",
    priority="high",
    created_after=created_after,
    limit=50
)
```

### JavaScript

```javascript
// Filter by date range
const createdAfter = '2025-11-10T00:00:00Z';
const createdBefore = '2025-11-11T00:00:00Z';
const inbox = await client.getInbox({
    createdAfter,
    createdBefore,
    limit: 50
});

// Filter by priority
const inbox = await client.getInbox({ priority: 'high', limit: 50 });

// Filter by metadata field
const inbox = await client.getInbox({
    metadataKey: 'user_id',
    metadataValue: '12345',
    limit: 50
});

// Combined advanced filtering
const inbox = await client.getInbox({
    source: 'payment-service',
    priority: 'high',
    createdAfter,
    limit: 50
});
```

## Bulk Operations (Phase 8)

Process multiple events in a single request for better performance.

### Python

```python
# Bulk create events
events_to_create = [
    {
        "source": "batch-processor",
        "event_type": "task.completed",
        "payload": {"task_id": f"task-{i}"}
    }
    for i in range(10)
]

response = client.bulk_create_events(events_to_create)
print(f"Created {len(response.successful)} events")
if response.failed:
    print(f"Failed: {len(response.failed)} events")
    for failure in response.failed:
        print(f"  Index {failure.index}: {failure.error.message}")

# Bulk acknowledge events
event_ids = [event['event_id'] for event in response.successful]
ack_response = client.bulk_acknowledge_events(event_ids)
print(f"Acknowledged {len(ack_response.successful)} events")

# Bulk delete events
delete_response = client.bulk_delete_events(event_ids)
print(f"Deleted {len(delete_response.successful)} events")
```

### JavaScript

```javascript
// Bulk create events
const eventsToCreate = Array.from({ length: 10 }, (_, i) => ({
    source: 'batch-processor',
    eventType: 'task.completed',
    payload: { taskId: `task-${i}` }
}));

const response = await client.bulkCreateEvents(eventsToCreate);
console.log(`Created ${response.successful.length} events`);
if (response.failed.length > 0) {
    console.log(`Failed: ${response.failed.length} events`);
    response.failed.forEach(failure => {
        console.log(`  Index ${failure.index}: ${failure.error.message}`);
    });
}

// Bulk acknowledge events
const eventIds = response.successful.map(e => e.event_id);
const ackResponse = await client.bulkAcknowledgeEvents(eventIds);
console.log(`Acknowledged ${ackResponse.successful.length} events`);

// Bulk delete events
const deleteResponse = await client.bulkDeleteEvents(eventIds);
console.log(`Deleted ${deleteResponse.successful.length} events`);
```

### cURL

```bash
# Bulk create events
curl -X POST http://localhost:8080/v1/events/bulk \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-12345" \
  -d '{
    "items": [
      {
        "source": "batch-processor",
        "event_type": "task.completed",
        "payload": {"task_id": "task-1"}
      },
      {
        "source": "batch-processor",
        "event_type": "task.completed",
        "payload": {"task_id": "task-2"}
      }
    ]
  }'

# Bulk acknowledge events
curl -X POST http://localhost:8080/v1/events/bulk/ack \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-12345" \
  -d '{
    "event_ids": ["event-id-1", "event-id-2"]
  }'

# Bulk delete events
curl -X DELETE http://localhost:8080/v1/events/bulk \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-12345" \
  -d '{
    "event_ids": ["event-id-1", "event-id-2"]
  }'
```

## Rate Limiting (Phase 8)

Handle rate limits gracefully by monitoring headers and implementing backoff.

### Python

```python
import time
from triggers_api import RateLimitExceededError

def make_request_with_retry(client, max_retries=3):
    """Make request with rate limit handling."""
    for attempt in range(max_retries):
        try:
            response = client.get_inbox(limit=50)
            
            # Check rate limit headers
            remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
            limit = response.headers.get('X-RateLimit-Limit', 'unknown')
            print(f"Rate limit: {remaining}/{limit} remaining")
            
            return response
            
        except RateLimitExceededError as e:
            retry_after = e.details.get('retry_after', 60)
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            
            if attempt == max_retries - 1:
                raise
```

### JavaScript

```javascript
const { RateLimitExceededError } = require('./src/errors');

async function makeRequestWithRetry(client, maxRetries = 3) {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            const response = await client.getInbox({ limit: 50 });
            
            // Check rate limit headers
            const remaining = response.headers['x-ratelimit-remaining'];
            const limit = response.headers['x-ratelimit-limit'];
            console.log(`Rate limit: ${remaining}/${limit} remaining`);
            
            return response;
            
        } catch (error) {
            if (error instanceof RateLimitExceededError) {
                const retryAfter = error.details.retry_after || 60;
                console.log(`Rate limit exceeded. Retrying after ${retryAfter} seconds...`);
                await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
                
                if (attempt === maxRetries - 1) {
                    throw error;
                }
            } else {
                throw error;
            }
        }
    }
}
```

### Monitoring Rate Limits

```python
def monitor_rate_limits(client):
    """Monitor rate limit usage."""
    response = client.get_inbox(limit=1)
    
    limit = int(response.headers.get('X-RateLimit-Limit', 0))
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    reset = int(response.headers.get('X-RateLimit-Reset', 0))
    
    usage_percent = ((limit - remaining) / limit) * 100
    
    print(f"Rate Limit Usage: {usage_percent:.1f}%")
    print(f"Remaining: {remaining}/{limit}")
    print(f"Resets at: {datetime.fromtimestamp(reset)}")
    
    if usage_percent > 80:
        print("Warning: Approaching rate limit!")
```

## Integration Patterns

### Webhook Receiver Pattern

Receive webhooks and forward as events:

```python
from flask import Flask, request
from triggers_api import TriggersAPIClient

app = Flask(__name__)
client = TriggersAPIClient(api_key="your-api-key", base_url="http://localhost:8080")

@app.route('/webhook', methods=['POST'])
def webhook():
    webhook_data = request.json
    
    # Forward as event
    event = client.create_event(
        source="webhook-receiver",
        event_type=f"{webhook_data['type']}",
        payload=webhook_data,
        metadata={"idempotency_key": webhook_data.get('id')}
    )
    
    return {"event_id": event.event_id}, 201
```

### Batch Processing Pattern

Process events in batches:

```python
def process_batch(client, batch_size=10):
    inbox = client.get_inbox(limit=batch_size)
    
    for event in inbox.events:
        try:
            # Process event
            process_event(event)
            # Acknowledge on success
            client.acknowledge_event(event['event_id'])
        except Exception as e:
            # Log error but don't acknowledge
            log_error(event['event_id'], e)
            # Event remains in inbox for retry
```

## Retry Patterns

Implement retry logic for transient errors to improve reliability.

### When to Retry

**Retry on:**
- Network errors (connection timeouts, DNS failures)
- `429 Rate Limit Exceeded` errors
- `500 Internal Server Error` errors
- Transient service disruptions

**Don't Retry on:**
- `400 Validation Error` - Fix request first
- `401 Unauthorized` - Check API key
- `404 Not Found` - Resource doesn't exist
- `409 Conflict` - State conflict (may be expected)

### Exponential Backoff

Retry with increasing delays between attempts.

**Python Example (with tenacity):**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from triggers_api import TriggersAPIClient, RateLimitExceededError, InternalError

client = TriggersAPIClient(
    api_key="your-api-key",
    base_url="http://localhost:8080"
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((RateLimitExceededError, InternalError))
)
def create_event_with_retry(event_data):
    """Create event with automatic retry on transient errors."""
    return client.create_event(**event_data)

# Usage
event = create_event_with_retry({
    "source": "my-app",
    "event_type": "user.created",
    "payload": {"user_id": "123"}
})
```

**Python Example (manual retry):**
```python
import time
import random
from triggers_api import TriggersAPIClient, RateLimitExceededError, InternalError

client = TriggersAPIClient(
    api_key="your-api-key",
    base_url="http://localhost:8080"
)

def create_event_with_retry(event_data, max_retries=3):
    """Manual retry implementation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return client.create_event(**event_data)
        except (RateLimitExceededError, InternalError) as e:
            if attempt == max_retries - 1:
                raise  # Last attempt failed
            # Exponential backoff with jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
        except Exception as e:
            # Don't retry on client errors
            raise

# Usage
event = create_event_with_retry({
    "source": "my-app",
    "event_type": "user.created",
    "payload": {"user_id": "123"}
})
```

**JavaScript Example:**
```javascript
const TriggersAPIClient = require('./src/client');
const { RateLimitExceededError, InternalError } = require('./src/errors');

const client = new TriggersAPIClient({
    apiKey: 'your-api-key',
    baseUrl: 'http://localhost:8080'
});

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function isRetryableError(error) {
    return error instanceof RateLimitExceededError || 
           error instanceof InternalError;
}

async function createEventWithRetry(eventData, maxRetries = 3) {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            return await client.createEvent(eventData);
        } catch (error) {
            if (attempt === maxRetries - 1 || !isRetryableError(error)) {
                throw error;
            }
            // Exponential backoff with jitter
            const waitTime = Math.pow(2, attempt) * 1000 + Math.random() * 1000;
            await sleep(waitTime);
        }
    }
}

// Usage
const event = await createEventWithRetry({
    source: 'my-app',
    eventType: 'user.created',
    payload: { userId: '123' }
});
```

### Retry with Idempotency

Always use idempotency keys when retrying to prevent duplicate events.

**Python Example:**
```python
import uuid
from triggers_api import TriggersAPIClient

client = TriggersAPIClient(
    api_key="your-api-key",
    base_url="http://localhost:8080"
)

def create_event_with_retry_and_idempotency(event_data, max_retries=3):
    """Retry with idempotency key to prevent duplicates."""
    # Generate idempotency key
    idempotency_key = str(uuid.uuid4())
    
    # Add to metadata
    event_data.setdefault("metadata", {})["idempotency_key"] = idempotency_key
    
    for attempt in range(max_retries):
        try:
            return client.create_event(**event_data)
        except (RateLimitExceededError, InternalError) as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    
    # If all retries fail, same idempotency key ensures no duplicate on manual retry
    return None
```

**JavaScript Example:**
```javascript
const { v4: uuidv4 } = require('uuid');

async function createEventWithRetryAndIdempotency(eventData, maxRetries = 3) {
    // Generate idempotency key
    const idempotencyKey = uuidv4();
    
    // Add to metadata
    eventData.metadata = eventData.metadata || {};
    eventData.metadata.idempotency_key = idempotencyKey;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            return await client.createEvent(eventData);
        } catch (error) {
            if (attempt === maxRetries - 1 || !isRetryableError(error)) {
                throw error;
            }
            await sleep(Math.pow(2, attempt) * 1000);
        }
    }
}
```

### Retry Best Practices

1. **Use Exponential Backoff:**
   - Start with short delays (1-2 seconds)
   - Increase exponentially (2, 4, 8 seconds)
   - Add jitter to avoid thundering herd

2. **Set Maximum Retries:**
   - Recommended: 3-5 retries
   - Don't retry indefinitely
   - Fail fast for non-retryable errors

3. **Always Use Idempotency Keys:**
   - Prevent duplicate events on retry
   - Safe to retry with same key
   - Key valid for 24 hours

4. **Log Retry Attempts:**
   - Track retry attempts for monitoring
   - Include request ID in logs
   - Monitor retry rates

5. **Handle Timeouts:**
   - Set appropriate request timeouts
   - Don't retry on timeout if operation is long-running
   - Consider operation idempotency

## Best Practices

1. **Always use idempotency keys** for critical operations
2. **Acknowledge events** only after successful processing
3. **Handle errors gracefully** with appropriate retry logic
4. **Use request IDs** for request tracking and debugging
5. **Implement pagination** for large result sets
6. **Filter efficiently** to reduce data transfer
7. **Monitor event status** before processing
8. **Clean up** processed events regularly
9. **Implement retry logic** for transient errors
10. **Use exponential backoff** with jitter

## See Also

- [API Reference](API.md) - Complete endpoint documentation
- [Error Handling Guide](ERRORS.md) - Error codes and troubleshooting
- [Performance Tuning](PERFORMANCE.md) - Optimization best practices
- [cURL Examples](CURL_EXAMPLES.md) - Command-line examples

