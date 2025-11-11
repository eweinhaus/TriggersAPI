# Usage Examples

Common use cases and code examples for the Zapier Triggers API.

## Table of Contents

- [Event Lifecycle](#event-lifecycle)
- [Polling for Events](#polling-for-events)
- [Idempotency](#idempotency)
- [Error Handling](#error-handling)
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

## Best Practices

1. **Always use idempotency keys** for critical operations
2. **Acknowledge events** only after successful processing
3. **Handle errors gracefully** with appropriate retry logic
4. **Use request IDs** for request tracking and debugging
5. **Implement pagination** for large result sets
6. **Filter efficiently** to reduce data transfer
7. **Monitor event status** before processing
8. **Clean up** processed events regularly

## See Also

- [API Reference](API.md) - Complete endpoint documentation
- [Error Handling Guide](ERRORS.md) - Error codes and troubleshooting
- [cURL Examples](CURL_EXAMPLES.md) - Command-line examples

