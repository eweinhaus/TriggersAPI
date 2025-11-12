# Zapier Triggers API - JavaScript Client

A JavaScript/Node.js client library for the Zapier Triggers API.

## Installation

```bash
npm install
```

## Quick Start

```javascript
const TriggersAPIClient = require('./src/client');

// Initialize client
const client = new TriggersAPIClient({
    apiKey: 'your-api-key',
    baseUrl: 'http://localhost:8080'  // or your production URL
});

// Create an event
const event = await client.createEvent({
    source: 'my-app',
    eventType: 'user.created',
    payload: { userId: '123', name: 'John Doe' }
});

console.log(`Event created: ${event.event_id}`);
```

## Configuration

### Local Development

```javascript
const client = new TriggersAPIClient({
    apiKey: 'test-api-key-12345',
    baseUrl: 'http://localhost:8080'
});
```

### Production

```javascript
const client = new TriggersAPIClient({
    apiKey: 'your-production-api-key',
    baseUrl: 'https://your-api-url.com'
});
```

## API Methods

### Create Event

```javascript
const event = await client.createEvent({
    source: 'my-app',
    eventType: 'user.created',
    payload: { userId: '123' },
    metadata: {
        idempotency_key: 'unique-key-123',
        priority: 'high',
        correlation_id: 'corr-456'
    }
});
```

### Get Event

```javascript
const event = await client.getEvent('550e8400-e29b-41d4-a716-446655440000');
console.log(event.payload);
console.log(event.status);
```

### Get Inbox

```javascript
// Get all pending events
const inbox = await client.getInbox({ limit: 50 });

// Filter by source
const inbox = await client.getInbox({ limit: 50, source: 'my-app' });

// Filter by event type
const inbox = await client.getInbox({ limit: 50, eventType: 'user.created' });

// Pagination
const inbox = await client.getInbox({ limit: 10 });
if (inbox.pagination.next_cursor) {
    const nextPage = await client.getInbox({
        limit: 10,
        cursor: inbox.pagination.next_cursor
    });
}
```

### Acknowledge Event

```javascript
const ack = await client.acknowledgeEvent('550e8400-e29b-41d4-a716-446655440000');
console.log(`Acknowledged at: ${ack.acknowledged_at}`);
```

### Delete Event

```javascript
const result = await client.deleteEvent('550e8400-e29b-41d4-a716-446655440000');
console.log(result.message);
```

## Error Handling

```javascript
const {
    TriggersAPIError,
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
} = require('./src/errors');

try {
    const event = await client.createEvent({
        source: 'my-app',
        eventType: 'user.created',
        payload: { userId: '123' }
    });
} catch (error) {
    if (error instanceof ValidationError) {
        console.log(`Validation error: ${error.message}`);
        console.log(`Details:`, error.details);
    } else if (error instanceof UnauthorizedError) {
        console.log(`Authentication failed: ${error.message}`);
    } else if (error instanceof TriggersAPIError) {
        console.log(`API error: ${error.message}`);
        console.log(`Request ID: ${error.requestId}`);
    }
}
```

## Request ID Tracking

You can optionally provide a request ID for tracking:

```javascript
const event = await client.createEvent({
    source: 'my-app',
    eventType: 'user.created',
    payload: { userId: '123' },
    requestId: 'my-custom-request-id'
});
```

Or set a default request ID when initializing the client:

```javascript
const client = new TriggersAPIClient({
    apiKey: 'your-api-key',
    baseUrl: 'http://localhost:8080',
    requestId: 'default-request-id'
});
```

## Examples

See the `examples/` directory for complete examples:

- `basic-usage.js` - Basic API usage
- `event-flow.js` - Complete event lifecycle
- `error-handling.js` - Error handling patterns

Run examples:

```bash
npm run example:basic
npm run example:flow
npm run example:errors
```

Or directly:

```bash
node examples/basic-usage.js
node examples/event-flow.js
node examples/error-handling.js
```

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
- The `baseUrl` is correct
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


