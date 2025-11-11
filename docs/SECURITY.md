# Security Features Guide

## Overview

The Triggers API includes several security features to protect your data and ensure secure communication:

- **API Key Authentication**: Required for all authenticated endpoints
- **API Key Rotation**: Rotate keys without service interruption
- **Request Signing (HMAC)**: Optional HMAC signature verification for enhanced security
- **Webhook Signatures**: HMAC signatures for webhook payload verification

## API Key Authentication

All authenticated endpoints require an API key in the `X-API-Key` header.

### Usage

```bash
curl -X GET https://api.example.com/v1/inbox \
  -H "X-API-Key: your-api-key"
```

### Security Best Practices

1. **Store Securely**: Never commit API keys to version control
2. **Rotate Regularly**: Use API key rotation to update keys periodically
3. **Use Environment Variables**: Store keys in environment variables, not code
4. **Limit Access**: Only share keys with authorized personnel

## API Key Rotation

Rotate API keys without service interruption using the rotation endpoint.

### Rotate a Key

```bash
curl -X POST https://api.example.com/v1/api-keys/{key_id}/rotate?transition_days=7 \
  -H "X-API-Key: your-api-key"
```

### Response

```json
{
  "api_key": "tr_new-key-here",
  "version": 2,
  "previous_version": "tr_old-key-here",
  "expires_at": "2025-11-18T12:00:00.000000Z",
  "rotated_at": "2025-11-11T12:00:00.000000Z",
  "request_id": "..."
}
```

### Rotation Process

1. **Create New Key**: A new API key version is created
2. **Transition Period**: Both old and new keys work during transition (default: 7 days)
3. **Update Clients**: Use transition period to update all clients with new key
4. **Expiration**: Old key expires after transition period

### Important Notes

- **New Key Only Returned Once**: The new API key is only returned in the rotation response
- **Store Immediately**: Save the new key securely immediately after rotation
- **Transition Period**: Both keys work during transition - use this time to update clients
- **Automatic Expiration**: Old keys are automatically expired after transition period

### View Key Versions

```bash
curl -X GET https://api.example.com/v1/api-keys/{key_id}/versions \
  -H "X-API-Key: your-api-key"
```

## Request Signing (HMAC)

Optional HMAC request signing provides additional security by verifying request authenticity.

### How It Works

1. Client generates HMAC signature using secret key
2. Server validates signature before processing request
3. Invalid signatures are rejected with 401 Unauthorized

### Signature Format

```
HMAC-SHA256(
  method + "\n" +
  path + "\n" +
  query_string + "\n" +
  timestamp + "\n" +
  body_hash,
  secret_key
)
```

### Headers

- `X-Signature-Timestamp`: Unix timestamp (seconds since epoch)
- `X-Signature`: Base64-encoded HMAC-SHA256 signature
- `X-Signature-Version`: Signature version (currently "v1")

### Python Example

```python
from triggers_api import TriggersAPIClient

client = TriggersAPIClient(
    api_key="your-api-key",
    base_url="https://api.example.com",
    signing_secret="your-signing-secret"
)

# All requests are automatically signed
event = client.create_event(
    source="my-app",
    event_type="user.created",
    payload={"user_id": "123"}
)
```

### JavaScript Example

```javascript
const TriggersAPIClient = require('@zapier/triggers-api-client');

const client = new TriggersAPIClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.example.com',
  signingSecret: 'your-signing-secret'
});

// All requests are automatically signed
const event = await client.createEvent({
  source: 'my-app',
  eventType: 'user.created',
  payload: { userId: '123' }
});
```

### Manual Signing

If not using an SDK, you can manually sign requests:

```python
import hmac
import hashlib
import base64
import time
import json
import requests

def sign_request(method, path, query_string, body, secret):
    timestamp = str(int(time.time()))
    body_hash = hashlib.sha256(json.dumps(body).encode()).hexdigest()
    signature_string = f"{method}\n{path}\n{query_string}\n{timestamp}\n{body_hash}"
    signature = base64.b64encode(
        hmac.new(secret.encode(), signature_string.encode(), hashlib.sha256).digest()
    ).decode()
    return {
        'X-Signature-Timestamp': timestamp,
        'X-Signature': signature,
        'X-Signature-Version': 'v1'
    }

# Usage
headers = sign_request('POST', '/v1/events', '', {'source': 'test'}, 'your-secret')
headers['X-API-Key'] = 'your-api-key'
response = requests.post('https://api.example.com/v1/events', json={'source': 'test'}, headers=headers)
```

### Enabling Request Signing

Request signing is **optional** and **backward compatible**:

- **Disabled by default**: Unsigned requests work normally
- **Enable on server**: Set `ENABLE_REQUEST_SIGNING=true` environment variable
- **Client-side**: Provide `signing_secret` to SDK or add signature headers manually
- **Backward compatible**: Clients without signing still work (if server allows)

### Security Considerations

- **Timestamp Validation**: Signatures older than 5 minutes are rejected (prevents replay attacks)
- **Constant-Time Comparison**: Uses constant-time comparison to prevent timing attacks
- **Secret Management**: Store signing secrets securely, never expose in logs
- **HTTPS Required**: Always use HTTPS when signing is enabled

## Webhook Signatures

All webhook payloads include HMAC signatures for verification. See [Webhooks Guide](./WEBHOOKS.md) for details.

## Best Practices

1. **Use HTTPS**: Always use HTTPS in production
2. **Rotate Keys**: Rotate API keys regularly (every 90 days recommended)
3. **Enable Signing**: Use request signing for enhanced security
4. **Verify Webhooks**: Always verify webhook signatures
5. **Monitor Access**: Monitor API key usage and rotate if compromised
6. **Least Privilege**: Use separate API keys for different applications
7. **Secure Storage**: Store secrets in secure vaults, not in code

## Troubleshooting

### Invalid Signature Error

- **Check Secret**: Ensure you're using the correct signing secret
- **Check Timestamp**: Ensure system clock is synchronized (within 5 minutes)
- **Check Format**: Ensure signature format matches exactly (method, path, query, timestamp, body_hash)
- **Check Body**: Ensure request body matches exactly (JSON serialization must be consistent)

### Key Rotation Issues

- **Transition Period**: Both keys work during transition - update clients gradually
- **Expiration**: Old keys expire after transition period - ensure all clients updated
- **Version History**: Use versions endpoint to track rotation history

## Additional Resources

- [Webhooks Guide](./WEBHOOKS.md) - Webhook signature verification
- [API Documentation](./API.md) - Complete API reference
- [Examples](./EXAMPLES.md) - Code examples with security features

