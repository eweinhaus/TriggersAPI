# Triggers API TypeScript Client

TypeScript client library for the Zapier Triggers API.

## Installation

```bash
npm install @zapier/triggers-api-client
```

## Usage

```typescript
import TriggersAPIClient from '@zapier/triggers-api-client';

const client = new TriggersAPIClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.example.com',
  signingSecret: 'your-signing-secret', // Optional
});

// Create an event
const event = await client.createEvent({
  source: 'my-app',
  eventType: 'user.created',
  payload: {
    userId: '123',
    name: 'John Doe',
  },
});

console.log(`Created event: ${event.event_id}`);
```

## Features

- Full TypeScript support
- Request signing (HMAC) support
- Type-safe request/response types
- Error handling

## Documentation

See [API Documentation](../../docs/API.md) for complete API reference.

