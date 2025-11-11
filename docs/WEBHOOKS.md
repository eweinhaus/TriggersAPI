# Webhooks Guide

## Overview

Webhooks enable push-based event delivery to your endpoints. When events are created in the Triggers API, registered webhooks automatically receive HTTP POST requests with the event data.

## Features

- **Automatic Delivery**: Events are automatically delivered to registered webhooks
- **Event Filtering**: Subscribe to specific event types or all events using `["*"]`
- **HMAC Signatures**: All webhook payloads include HMAC signatures for verification
- **Retry Logic**: Automatic retry with exponential backoff (max 3 retries)
- **Dead Letter Queue**: Failed deliveries after max retries are sent to DLQ
- **Test Endpoint**: Test webhook delivery before going live

## Creating a Webhook

### Request

```bash
curl -X POST https://api.example.com/v1/webhooks \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-endpoint.com/webhook",
    "events": ["*"],
    "secret": "your-webhook-secret-min-16-chars"
  }'
```

### Response

```json
{
  "webhook_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://your-endpoint.com/webhook",
  "events": ["*"],
  "is_active": true,
  "created_at": "2025-11-11T12:00:00.000000Z",
  "request_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

### Parameters

- **url** (required): Webhook URL to receive events (must be HTTP/HTTPS)
- **events** (required): List of event types to subscribe to
  - Use `["*"]` to receive all events
  - Use specific types like `["user.created", "order.completed"]`
- **secret** (required): Secret for HMAC signature verification (minimum 16 characters)

## Event Filtering

### All Events

Subscribe to all events using the wildcard:

```json
{
  "events": ["*"]
}
```

### Specific Event Types

Subscribe to specific event types:

```json
{
  "events": ["user.created", "user.updated", "order.completed"]
}
```

## Webhook Payload

When an event is created, webhooks receive a POST request with the following payload:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-11-11T12:00:00.000000Z",
  "source": "my-app",
  "event_type": "user.created",
  "payload": {
    "user_id": "123",
    "email": "user@example.com"
  },
  "status": "pending",
  "metadata": {
    "correlation_id": "corr-123",
    "priority": "normal"
  }
}
```

### Headers

- `X-Webhook-Signature`: HMAC-SHA256 signature of the payload
- `X-Webhook-Id`: Webhook ID that triggered this delivery
- `X-Webhook-Timestamp`: ISO 8601 timestamp of the delivery
- `Content-Type`: `application/json`

## Signature Verification

Verify webhook signatures to ensure authenticity:

### Python Example

```python
import hmac
import hashlib
import json

def verify_webhook_signature(payload: dict, signature: str, secret: str) -> bool:
    """Verify webhook HMAC signature."""
    payload_json = json.dumps(payload, sort_keys=True)
    expected_signature = hmac.new(
        secret.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

# In your webhook handler
payload = request.json
signature = request.headers.get('X-Webhook-Signature')
secret = 'your-webhook-secret'

if verify_webhook_signature(payload, signature, secret):
    # Process webhook
    pass
else:
    # Reject webhook
    return 401
```

### JavaScript Example

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, signature, secret) {
  const payloadJson = JSON.stringify(payload);
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payloadJson)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

// In your webhook handler
const payload = req.body;
const signature = req.headers['x-webhook-signature'];
const secret = 'your-webhook-secret';

if (verifyWebhookSignature(payload, signature, secret)) {
  // Process webhook
} else {
  // Reject webhook
  res.status(401).send('Invalid signature');
}
```

## Retry Logic

Webhooks are automatically retried on failure:

- **Max Retries**: 3 attempts
- **Backoff**: Exponential (1s, 2s, 4s)
- **Retry Conditions**: 5xx server errors, timeouts, network errors
- **No Retry**: 4xx client errors (bad request, unauthorized, etc.)
- **Dead Letter Queue**: Messages that fail after max retries are sent to DLQ

## Managing Webhooks

### List Webhooks

```bash
curl -X GET https://api.example.com/v1/webhooks \
  -H "X-API-Key: your-api-key"
```

### Get Webhook Details

```bash
curl -X GET https://api.example.com/v1/webhooks/{webhook_id} \
  -H "X-API-Key: your-api-key"
```

### Update Webhook

```bash
curl -X PUT https://api.example.com/v1/webhooks/{webhook_id} \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://new-url.com/webhook",
    "is_active": false
  }'
```

### Delete Webhook

```bash
curl -X DELETE https://api.example.com/v1/webhooks/{webhook_id} \
  -H "X-API-Key: your-api-key"
```

### Test Webhook

Test webhook delivery without creating an event:

```bash
curl -X POST https://api.example.com/v1/webhooks/{webhook_id}/test \
  -H "X-API-Key: your-api-key"
```

## Best Practices

1. **Use HTTPS**: Always use HTTPS for webhook URLs to ensure secure delivery
2. **Verify Signatures**: Always verify HMAC signatures to ensure authenticity
3. **Idempotency**: Make webhook handlers idempotent to handle duplicate deliveries
4. **Quick Response**: Respond quickly (within 10 seconds) to avoid timeouts
5. **Error Handling**: Return appropriate HTTP status codes:
   - `200-299`: Success (webhook processed)
   - `400-499`: Client error (don't retry)
   - `500-599`: Server error (will retry)
6. **Secret Management**: Store webhook secrets securely, never expose in logs
7. **Event Filtering**: Use specific event types instead of `["*"]` when possible

## Troubleshooting

### Webhook Not Receiving Events

1. **Check Webhook Status**: Ensure webhook is active (`is_active: true`)
2. **Verify Event Type**: Check that event type matches webhook subscription
3. **Check API Key**: Ensure webhook belongs to the correct API key
4. **Test Webhook**: Use the test endpoint to verify webhook URL is accessible

### Signature Verification Fails

1. **Check Secret**: Ensure you're using the correct webhook secret
2. **Payload Format**: Ensure payload JSON matches exactly (no extra whitespace)
3. **Header Name**: Verify you're reading `X-Webhook-Signature` header

### Webhook Delivery Failures

1. **Check DLQ**: Failed webhooks after max retries are in the dead letter queue
2. **Review Logs**: Check CloudWatch logs for delivery errors
3. **Test Endpoint**: Use test endpoint to verify webhook URL accessibility
4. **Timeout Issues**: Ensure webhook endpoint responds within 10 seconds

## Security Considerations

- **Secrets**: Webhook secrets are never returned in API responses
- **HTTPS Only**: Use HTTPS for webhook URLs in production
- **Signature Verification**: Always verify signatures to prevent spoofing
- **Rate Limiting**: Implement rate limiting on webhook endpoints
- **IP Allowlisting**: Consider IP allowlisting for additional security

## API Reference

See [API Documentation](./API.md) for complete endpoint reference.

