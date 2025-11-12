# Troubleshooting Guide

Comprehensive troubleshooting guide for common issues with the Zapier Triggers API.

## Table of Contents

- [Common Error Messages](#common-error-messages)
- [API Key Issues](#api-key-issues)
- [DynamoDB Connection Issues](#dynamodb-connection-issues)
- [CORS Issues](#cors-issues)
- [Rate Limiting Issues](#rate-limiting-issues)
- [Performance Issues](#performance-issues)
- [Debugging Tips](#debugging-tips)

---

## Common Error Messages

### VALIDATION_ERROR (400)

**Symptoms:**
- HTTP 400 status code
- Error code: `VALIDATION_ERROR`
- Error message describing validation failure

**Common Causes:**
1. Missing required fields (`source`, `event_type`, `payload`)
2. Empty string values for required fields
3. Field length violations (source/event_type > 100 characters)
4. Invalid JSON structure in payload
5. Empty payload object `{}`
6. Invalid metadata values (e.g., priority not in enum)

**Solutions:**

1. **Check Required Fields:**
   ```python
   # ❌ Missing source
   client.create_event(
       event_type="test.event",
       payload={"data": "test"}
   )
   
   # ✅ Include all required fields
   client.create_event(
       source="my-app",
       event_type="test.event",
       payload={"data": "test"}
   )
   ```

2. **Verify Field Values:**
   ```python
   # ❌ Empty source
   client.create_event(
       source="",  # Invalid: empty string
       event_type="test.event",
       payload={"data": "test"}
   )
   
   # ✅ Non-empty source
   client.create_event(
       source="my-app",  # Valid
       event_type="test.event",
       payload={"data": "test"}
   )
   ```

3. **Check Payload Structure:**
   ```python
   # ❌ Empty payload
   client.create_event(
       source="my-app",
       event_type="test.event",
       payload={}  # Invalid: empty object
   )
   
   # ✅ Valid payload
   client.create_event(
       source="my-app",
       event_type="test.event",
       payload={"data": "test"}  # Valid: non-empty object
   )
   ```

4. **Review Error Details:**
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
   - Check `details.field` to identify the problematic field
   - Review `details.issue` for specific validation rules
   - Follow `details.suggestion` to resolve

**Debugging Steps:**
1. Review the error response `details` field
2. Verify all required fields are present
3. Check field values meet constraints (length, format, enum)
4. Validate JSON structure is correct
5. Test with minimal payload first

---

### UNAUTHORIZED (401)

**Symptoms:**
- HTTP 401 status code
- Error code: `UNAUTHORIZED`
- Error message: "Invalid or missing API key"

**Common Causes:**
1. Missing `X-API-Key` header
2. Invalid API key value
3. API key not found in DynamoDB (AWS mode)
4. Using wrong API key for environment (local vs production)
5. API key inactive or revoked

**Solutions:**

1. **Check Header Name:**
   ```bash
   # ❌ Wrong header name
   curl -H "API-Key: test-api-key-12345" http://localhost:8080/v1/health
   
   # ✅ Correct header name
   curl -H "X-API-Key: test-api-key-12345" http://localhost:8080/v1/health
   ```

2. **Verify API Key for Environment:**
   ```python
   # Local development
   client = TriggersAPIClient(
       api_key="test-api-key-12345",  # Local test key
       base_url="http://localhost:8080"
   )
   
   # Production (AWS)
   client = TriggersAPIClient(
       api_key="your-production-api-key",  # From DynamoDB
       base_url="https://your-api.execute-api.us-east-1.amazonaws.com/prod"
   )
   ```

3. **Check API Key in DynamoDB (AWS Mode):**
   ```bash
   # List API keys in DynamoDB
   aws dynamodb scan \
     --table-name triggers-api-keys-prod \
     --region us-east-1
   
   # Check specific API key
   aws dynamodb get-item \
     --table-name triggers-api-keys-prod \
     --key '{"api_key": {"S": "your-api-key"}}' \
     --region us-east-1
   ```

4. **Create/Seed API Key:**
   ```bash
   # Seed API key for production
   python scripts/seed_api_keys.py \
     --api-key "your-api-key" \
     --stage prod \
     --region us-east-1
   ```

5. **Verify AUTH_MODE:**
   ```bash
   # Local mode (hardcoded key)
   export AUTH_MODE=local
   
   # AWS mode (DynamoDB validation)
   export AUTH_MODE=aws
   ```

**Debugging Steps:**
1. Verify `X-API-Key` header is included in request
2. Check API key value is correct (no extra spaces, correct format)
3. Verify environment matches API key (local vs production)
4. Check `AUTH_MODE` environment variable
5. For AWS mode, verify API key exists in DynamoDB
6. Check CloudWatch logs for authentication failures

---

### NOT_FOUND (404)

**Symptoms:**
- HTTP 404 status code
- Error code: `NOT_FOUND`
- Error message: "Event with ID '...' was not found"

**Common Causes:**
1. Invalid event ID format (not UUID v4)
2. Event doesn't exist
3. Event was deleted
4. Event expired (TTL removed it)
5. Wrong environment (checking local vs production)

**Solutions:**

1. **Verify Event ID Format:**
   ```python
   # ❌ Invalid format
   event_id = "123"  # Not UUID v4
   
   # ✅ Valid UUID v4
   event_id = "550e8400-e29b-41d4-a716-446655440000"
   ```

2. **Check Event Exists:**
   ```python
   # Check event before operations
   try:
       event = client.get_event(event_id)
       print(f"Event found: {event.status}")
   except NotFoundError:
       print("Event does not exist")
   ```

3. **Verify Environment:**
   ```python
   # Make sure you're using the correct API URL
   # Local
   client = TriggersAPIClient(
       api_key="test-api-key-12345",
       base_url="http://localhost:8080"
   )
   
   # Production
   client = TriggersAPIClient(
       api_key="your-api-key",
       base_url="https://your-api.execute-api.us-east-1.amazonaws.com/prod"
   )
   ```

4. **Check Event TTL:**
   - Events have 7-day TTL
   - Expired events are automatically deleted
   - Check `created_at` timestamp to verify event age

**Debugging Steps:**
1. Verify event ID is valid UUID v4 format
2. Check event exists using `GET /v1/events/{id}`
3. Verify correct environment (local vs production)
4. Check event `created_at` timestamp (TTL is 7 days)
5. Review CloudWatch logs for event lookup operations

---

### CONFLICT (409)

**Symptoms:**
- HTTP 409 status code
- Error code: `CONFLICT`
- Error message: "Event '...' has already been acknowledged"

**Common Causes:**
1. Attempting to acknowledge an already-acknowledged event
2. Race condition (multiple acknowledgments)
3. Event status mismatch

**Solutions:**

1. **Check Event Status Before Acknowledging:**
   ```python
   # Check status first
   event = client.get_event(event_id)
   
   if event.status == "pending":
       client.acknowledge_event(event_id)
   else:
       print(f"Event already {event.status}")
   ```

2. **Handle Conflict Gracefully:**
   ```python
   try:
       client.acknowledge_event(event_id)
   except ConflictError as e:
       # Event already acknowledged - this may be expected
       print(f"Event already acknowledged: {e.details.get('current_status')}")
   ```

3. **Use Idempotency:**
   - Acknowledgment operations are idempotent
   - If event is already acknowledged, this is expected behavior
   - Check `details.current_status` in error response

**Debugging Steps:**
1. Check event status using `GET /v1/events/{id}`
2. Review `details.current_status` in error response
3. Verify if acknowledgment was already successful
4. Check for race conditions (multiple concurrent requests)

---

### PAYLOAD_TOO_LARGE (413)

**Symptoms:**
- HTTP 413 status code
- Error code: `PAYLOAD_TOO_LARGE`
- Error message: "Payload size exceeds 400KB limit"

**Common Causes:**
1. Payload exceeds 400KB limit
2. Large nested objects
3. Base64-encoded data in payload
4. Attachments or binary data

**Solutions:**

1. **Reduce Payload Size:**
   ```python
   # ❌ Large payload
   large_data = {"data": "x" * 500000}  # 500KB
   
   # ✅ Smaller payload with reference
   client.create_event(
       source="my-app",
       event_type="file.uploaded",
       payload={
           "file_id": "file-123",
           "file_url": "https://storage.example.com/file-123"
       }
   )
   ```

2. **Split Large Data:**
   ```python
   # Split into multiple events
   for chunk in split_large_data(data, chunk_size=300000):
       client.create_event(
           source="my-app",
           event_type="data.chunk",
           payload={"chunk": chunk, "chunk_index": i}
       )
   ```

3. **Use References:**
   ```python
   # Store large data elsewhere, reference it
   storage_url = upload_to_storage(large_data)
   
   client.create_event(
       source="my-app",
       event_type="data.uploaded",
       payload={"storage_url": storage_url}
   )
   ```

**Debugging Steps:**
1. Measure payload size before sending
2. Remove unnecessary data from payload
3. Use references instead of full data
4. Split into multiple events if needed

---

### RATE_LIMIT_EXCEEDED (429)

**Symptoms:**
- HTTP 429 status code
- Error code: `RATE_LIMIT_EXCEEDED`
- Error message: "Rate limit exceeded"

**Common Causes:**
1. Too many requests per second
2. Burst of requests
3. API Gateway default throttling limits

**Solutions:**

1. **Implement Exponential Backoff:**
   ```python
   import time
   import random
   
   def create_event_with_retry(client, event_data, max_retries=3):
       for attempt in range(max_retries):
           try:
               return client.create_event(event_data)
           except RateLimitExceededError:
               if attempt == max_retries - 1:
                   raise
               wait_time = (2 ** attempt) + random.uniform(0, 1)
               time.sleep(wait_time)
   ```

2. **Reduce Request Frequency:**
   ```python
   # ❌ Rapid requests
   for item in items:
       client.create_event(item)  # No delay
   
   # ✅ Rate-limited requests
   import time
   for item in items:
       client.create_event(item)
       time.sleep(0.1)  # 100ms delay between requests
   ```

3. **Batch Operations:**
   - Process multiple events in batches
   - Add delays between batches
   - Use appropriate batch sizes

**Debugging Steps:**
1. Monitor request rate
2. Implement exponential backoff
3. Reduce request frequency
4. Check API Gateway throttling settings

---

### INTERNAL_ERROR (500)

**Symptoms:**
- HTTP 500 status code
- Error code: `INTERNAL_ERROR`
- Error message: "Internal server error"

**Common Causes:**
1. Server-side bug
2. DynamoDB connection issues
3. Lambda timeout or memory issues
4. Temporary service disruption

**Solutions:**

1. **Retry with Exponential Backoff:**
   ```python
   import time
   
   def create_event_with_retry(client, event_data, max_retries=3):
       for attempt in range(max_retries):
           try:
               return client.create_event(event_data)
           except InternalError as e:
               if attempt == max_retries - 1:
                   raise
               wait_time = 2 ** attempt
               time.sleep(wait_time)
   ```

2. **Check Service Status:**
   - Verify API health: `GET /v1/health`
   - Check CloudWatch logs for errors
   - Review AWS service status

3. **Report with Request ID:**
   ```python
   try:
       event = client.create_event(event_data)
   except InternalError as e:
       print(f"Request ID: {e.request_id}")
       # Report to support with request ID
   ```

**Debugging Steps:**
1. Retry the request (may be transient)
2. Check service health endpoint
3. Review CloudWatch logs using request ID
4. Report to support with request ID

---

## API Key Issues

### "Invalid API key" Error

**Problem:** API key validation fails.

**Solutions:**

1. **Verify Header Format:**
   ```bash
   # Correct header
   curl -H "X-API-Key: your-api-key" http://localhost:8080/v1/health
   ```

2. **Check API Key Value:**
   - No extra spaces or newlines
   - Correct case (if applicable)
   - Full key value (not truncated)

3. **Verify Environment:**
   ```bash
   # Local development
   export AUTH_MODE=local
   # Use: test-api-key-12345
   
   # Production
   export AUTH_MODE=aws
   # Use: API key from DynamoDB
   ```

4. **Check API Key in DynamoDB:**
   ```bash
   aws dynamodb get-item \
     --table-name triggers-api-keys-prod \
     --key '{"api_key": {"S": "your-api-key"}}' \
     --region us-east-1
   ```

### "Missing API key" Error

**Problem:** `X-API-Key` header is not included in request.

**Solutions:**

1. **Add Header to Request:**
   ```python
   # Python
   headers = {"X-API-Key": "your-api-key"}
   response = requests.post(url, json=data, headers=headers)
   ```

2. **Configure Client:**
   ```python
   # TriggersAPIClient automatically adds header
   client = TriggersAPIClient(
       api_key="your-api-key",
       base_url="http://localhost:8080"
   )
   ```

### Local vs AWS Mode Differences

**Local Mode (`AUTH_MODE=local`):**
- Uses hardcoded test key: `test-api-key-12345`
- No DynamoDB lookup required
- Faster for development

**AWS Mode (`AUTH_MODE=aws`):**
- Validates against DynamoDB `triggers-api-keys-{stage}` table
- Requires API key to exist in DynamoDB
- Production-ready authentication

**Troubleshooting:**
1. Check `AUTH_MODE` environment variable
2. Verify API key matches mode (local test key vs DynamoDB key)
3. For AWS mode, ensure API key is seeded in DynamoDB

---

## DynamoDB Connection Issues

### Local DynamoDB Connection Issues

**Problem:** Cannot connect to DynamoDB Local.

**Solutions:**

1. **Verify Docker is Running:**
   ```bash
   docker ps
   # Should show dynamodb-local container
   ```

2. **Start DynamoDB Local:**
   ```bash
   docker-compose up -d
   ```

3. **Check Environment Variables:**
   ```bash
   export DYNAMODB_ENDPOINT_URL=http://localhost:8000
   export AWS_REGION=us-east-1
   export AWS_ACCESS_KEY_ID=test
   export AWS_SECRET_ACCESS_KEY=test
   ```

4. **Test Connection:**
   ```bash
   aws dynamodb list-tables \
     --endpoint-url http://localhost:8000 \
     --region us-east-1
   ```

### AWS DynamoDB Connection Issues

**Problem:** Cannot connect to AWS DynamoDB.

**Solutions:**

1. **Check IAM Permissions:**
   - Lambda execution role needs DynamoDB permissions
   - Verify role has: `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem`, `dynamodb:DeleteItem`, `dynamodb:Query`, `dynamodb:Scan`

2. **Verify Table Exists:**
   ```bash
   aws dynamodb list-tables --region us-east-1
   ```

3. **Check Region:**
   ```bash
   export AWS_REGION=us-east-1
   ```

4. **Verify Table Names:**
   - Events: `triggers-api-events-{stage}`
   - API Keys: `triggers-api-keys-{stage}`
   - Idempotency: `triggers-api-idempotency-{stage}`

### Table Creation Issues

**Problem:** Tables not created automatically.

**Solutions:**

1. **Tables Auto-Create on Startup:**
   - FastAPI application creates tables on startup
   - Check application logs for table creation messages

2. **Manual Table Creation:**
   ```bash
   python scripts/create_tables.py
   ```

3. **Verify Table Structure:**
   ```bash
   aws dynamodb describe-table \
     --table-name triggers-api-events-prod \
     --region us-east-1
   ```

---

## CORS Issues

### CORS Error Symptoms

**Problem:** Browser shows CORS errors in console.

**Common Errors:**
- `Access-Control-Allow-Origin` header missing
- Preflight request fails
- CORS policy blocks request

**Solutions:**

1. **Verify API URL:**
   ```javascript
   // ❌ Missing /v1 prefix
   const apiUrl = "https://api.execute-api.us-east-1.amazonaws.com/prod";
   
   // ✅ Correct URL with /v1
   const apiUrl = "https://api.execute-api.us-east-1.amazonaws.com/prod/v1";
   ```

2. **Check API Gateway CORS:**
   - CORS is configured in `template.yaml`
   - Allowed methods: `GET, POST, DELETE, OPTIONS`
   - Allowed headers: `Content-Type, X-API-Key, X-Request-ID`
   - Allowed origin: `*` (all origins)

3. **Verify Frontend Configuration:**
   ```javascript
   // Frontend API client
   const client = axios.create({
       baseURL: 'https://api.execute-api.us-east-1.amazonaws.com/prod/v1',
       headers: {
           'Content-Type': 'application/json',
           'X-API-Key': apiKey
       }
   });
   ```

4. **Test Preflight Request:**
   ```bash
   curl -X OPTIONS \
     -H "Origin: https://your-frontend.com" \
     -H "Access-Control-Request-Method: POST" \
     https://api.execute-api.us-east-1.amazonaws.com/prod/v1/events
   ```

**Debugging Steps:**
1. Check browser console for CORS errors
2. Verify API URL includes `/v1` prefix
3. Test preflight OPTIONS request
4. Check API Gateway CORS configuration
5. Verify frontend is sending correct headers

---

## Rate Limiting Issues

### Rate Limit Error Handling

**Problem:** Receiving `429 Rate Limit Exceeded` errors.

**Solutions:**

1. **Implement Exponential Backoff:**
   ```python
   import time
   import random
   
   def retry_with_backoff(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except RateLimitExceededError:
               if attempt == max_retries - 1:
                   raise
               wait_time = (2 ** attempt) + random.uniform(0, 1)
               time.sleep(wait_time)
   ```

2. **Reduce Request Frequency:**
   - Add delays between requests
   - Batch operations when possible
   - Use appropriate request rates

3. **Monitor Request Rate:**
   - Track requests per second
   - Implement rate limiting on client side
   - Use request queuing

---

## Performance Issues

### Slow Response Times

**Problem:** API responses are slow.

**Solutions:**

1. **Check Lambda Cold Starts:**
   - Cold starts can take 1-2 seconds
   - Use provisioned concurrency to reduce cold starts
   - Monitor CloudWatch metrics

2. **Optimize DynamoDB Queries:**
   - Use GSI for inbox queries (`status-created_at-index`)
   - Minimize filter expressions
   - Use appropriate page sizes (50-100)

3. **Check Network Latency:**
   - Use regional API Gateway (closest to users)
   - Monitor API Gateway latency metrics
   - Check CloudFront for frontend assets

### Lambda Cold Start Issues

**Problem:** First request after idle period is slow.

**Solutions:**

1. **Use Provisioned Concurrency:**
   - Configure in `template.yaml`
   - Reduces cold start latency
   - See [Lambda Provisioned Concurrency](#lambda-provisioned-concurrency) section

2. **Monitor Cold Start Metrics:**
   - Check CloudWatch Lambda metrics
   - Track `Duration` and `InitDuration`
   - Optimize package size

### DynamoDB Query Performance

**Problem:** Inbox queries are slow.

**Solutions:**

1. **Use GSI for Queries:**
   - Use `status-created_at-index` for inbox queries
   - Avoid full table scans
   - Use appropriate query filters

2. **Optimize Pagination:**
   - Use appropriate page sizes (50-100)
   - Use cursor-based pagination efficiently
   - Avoid fetching unnecessary data

---

## Debugging Tips

### Request ID Usage

**Purpose:** Request ID enables request correlation across logs and debugging.

**Usage:**

1. **Include Request ID in Requests:**
   ```python
   import uuid
   
   request_id = str(uuid.uuid4())
   headers = {
       "X-API-Key": "your-api-key",
       "X-Request-ID": request_id
   }
   ```

2. **Extract Request ID from Responses:**
   ```python
   response = client.create_event(event_data)
   request_id = response.request_id
   print(f"Request ID: {request_id}")
   ```

3. **Use Request ID for Support:**
   - Include request ID when reporting issues
   - Search CloudWatch logs by request ID
   - Correlate requests across services

### CloudWatch Logs Access

**Access Logs:**

1. **AWS Console:**
   - Navigate to CloudWatch → Log groups
   - Find: `/aws/lambda/triggers-api-{stage}`
   - Search by request ID or error message

2. **AWS CLI:**
   ```bash
   aws logs tail /aws/lambda/triggers-api-prod \
     --follow \
     --region us-east-1
   ```

3. **Search by Request ID:**
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/triggers-api-prod \
     --filter-pattern "request_id" \
     --region us-east-1
   ```

### Local Logging Setup

**Configure Logging:**

1. **Set Log Level:**
   ```bash
   export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
   ```

2. **View Logs:**
   ```bash
   # Local development
   uvicorn src.main:app --reload
   # Logs appear in console
   ```

3. **Structured Logging:**
   - Logs are in JSON format
   - Include request ID in all log entries
   - Use structured logging for easier parsing

### API Testing Tools

**cURL Examples:**

```bash
# Health check
curl http://localhost:8080/v1/health

# Create event
curl -X POST http://localhost:8080/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-12345" \
  -d '{
    "source": "my-app",
    "event_type": "test.event",
    "payload": {"data": "test"}
  }'
```

**Postman Setup:**

1. Create new collection
2. Set base URL: `http://localhost:8080/v1`
3. Add header: `X-API-Key: test-api-key-12345`
4. Create requests for each endpoint

### Debugging Workflow

**Step-by-Step Process:**

1. **Reproduce Issue:**
   - Capture request details (endpoint, payload, headers)
   - Note error response (code, message, request_id)

2. **Check Logs:**
   - Search CloudWatch logs by request ID
   - Review error stack traces
   - Check for related errors

3. **Verify Configuration:**
   - Check environment variables
   - Verify API key and authentication
   - Confirm table names and permissions

4. **Test Locally:**
   - Reproduce issue in local environment
   - Use DynamoDB Local for testing
   - Debug with local logging

5. **Isolate Problem:**
   - Test individual components
   - Verify database operations
   - Check network connectivity

6. **Fix and Verify:**
   - Apply fix
   - Test fix locally
   - Deploy and verify in production

---

## Getting Help

When reporting issues, include:

- **Error Details:**
  - Error code and message
  - HTTP status code
  - Request ID (from error response)

- **Request Details:**
  - Endpoint and HTTP method
  - Request payload (sanitized)
  - Headers (sanitize API key)

- **Environment:**
  - Local vs production
  - API URL
  - Environment variables (sanitized)

- **Steps to Reproduce:**
  - Clear steps to reproduce
  - Expected vs actual behavior
  - Frequency of issue

- **Additional Context:**
  - CloudWatch log snippets
  - Related error messages
  - Recent changes or deployments

---

## See Also

- [API Reference](API.md) - Complete endpoint documentation
- [Error Handling Guide](ERRORS.md) - Detailed error codes
- [Performance Tuning](PERFORMANCE.md) - Optimization best practices
- [Usage Examples](EXAMPLES.md) - Code examples and patterns


