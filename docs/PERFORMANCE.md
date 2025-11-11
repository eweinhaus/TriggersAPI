# Performance Tuning Guide

Best practices and optimization strategies for the Zapier Triggers API.

## Table of Contents

- [Performance Goals](#performance-goals)
- [Best Practices](#best-practices)
- [Batch Operations](#batch-operations)
- [Filtering Optimization](#filtering-optimization)
- [Pagination Best Practices](#pagination-best-practices)
- [Connection Pooling](#connection-pooling)
- [Caching Strategies](#caching-strategies)
- [Performance Benchmarks](#performance-benchmarks)

---

## Performance Goals

**Target Metrics:**
- **Event Ingestion Latency:** < 100ms (p95)
- **Inbox Query Latency:** < 200ms (p95)
- **Cold Start:** < 2 seconds (acceptable for MVP)
- **Warm Start:** < 100ms

**Current Performance:**
- Lambda cold starts: ~1-2 seconds
- Warm invocations: < 100ms
- DynamoDB operations: < 50ms (p95)

---

## Best Practices

### Event Payload Size Optimization

**Recommendation:** Keep payloads under 100KB for optimal performance.

**Strategies:**

1. **Minimize Payload Size:**
   ```python
   # ❌ Large payload with redundant data
   payload = {
       "user": {
           "id": "123",
           "name": "John Doe",
           "email": "john@example.com",
           "profile": {
               "bio": "Very long bio text...",
               "avatar": "base64-encoded-image-data..."
           }
       }
   }
   
   # ✅ Optimized payload with references
   payload = {
       "user_id": "123",
       "user_url": "https://api.example.com/users/123"
   }
   ```

2. **Use References Instead of Full Data:**
   ```python
   # Store large data elsewhere, reference it
   storage_url = upload_to_storage(large_data)
   
   client.create_event(
       source="my-app",
       event_type="data.uploaded",
       payload={
           "storage_url": storage_url,
           "metadata": {"size": len(large_data)}
       }
   )
   ```

3. **Remove Unnecessary Data:**
   - Only include data needed for processing
   - Remove computed fields that can be regenerated
   - Exclude debug or development data

### Batch Operations Usage

**When to Use:** Processing multiple events efficiently.

**Best Practices:**

1. **Appropriate Batch Sizes:**
   - Recommended: 10-25 events per batch
   - Maximum: 50 events per batch
   - Balance between throughput and error handling

2. **Error Handling:**
   ```python
   def create_events_batch(client, events, batch_size=20):
       results = []
       errors = []
       
       for i in range(0, len(events), batch_size):
           batch = events[i:i+batch_size]
           for event_data in batch:
               try:
                   result = client.create_event(**event_data)
                   results.append(result)
               except Exception as e:
                   errors.append({"event": event_data, "error": str(e)})
       
       return results, errors
   ```

3. **Parallel Processing:**
   ```python
   import asyncio
   from concurrent.futures import ThreadPoolExecutor
   
   def create_events_parallel(client, events, max_workers=5):
       with ThreadPoolExecutor(max_workers=max_workers) as executor:
           futures = [
               executor.submit(client.create_event, **event_data)
               for event_data in events
           ]
           results = [f.result() for f in futures]
       return results
   ```

### Filtering Optimization

**Recommendation:** Use GSI for efficient queries, minimize filter expressions.

**Strategies:**

1. **Use GSI for Status-Based Queries:**
   ```python
   # ✅ Efficient: Uses GSI
   inbox = client.get_inbox(
       limit=50,
       source="my-app"  # Filter applied after query
   )
   
   # ❌ Inefficient: Would require full table scan
   # (Not supported - always uses GSI for inbox)
   ```

2. **Minimize Filter Expressions:**
   - Filter expressions are applied after query
   - Use query filters when possible
   - Combine filters efficiently

3. **Optimize Source/Event Type Filtering:**
   ```python
   # ✅ Efficient filtering
   inbox = client.get_inbox(
       source="my-app",
       event_type="user.created",
       limit=50
   )
   
   # Filtering is applied after GSI query
   # Still efficient for most use cases
   ```

### Pagination Best Practices

**Recommendation:** Use appropriate page sizes and efficient cursor handling.

**Strategies:**

1. **Optimal Page Sizes:**
   - Recommended: 50-100 events per page
   - Maximum: 100 events per page
   - Balance between response size and number of requests

2. **Efficient Cursor Handling:**
   ```python
   def get_all_events(client, source=None):
       """Efficiently paginate through all events."""
       all_events = []
       cursor = None
       
       while True:
           inbox = client.get_inbox(
               limit=100,  # Optimal page size
               cursor=cursor,
               source=source
           )
           all_events.extend(inbox.events)
           
           if inbox.pagination.next_cursor:
               cursor = inbox.pagination.next_cursor
           else:
               break
       
       return all_events
   ```

3. **Avoid Unnecessary Pagination:**
   ```python
   # ❌ Fetching all events when only few needed
   all_events = get_all_events(client)
   recent_events = all_events[:10]
   
   # ✅ Fetch only what's needed
   inbox = client.get_inbox(limit=10)
   recent_events = inbox.events
   ```

### Connection Pooling

**Automatic in Lambda:** boto3 handles connection pooling automatically.

**Best Practices:**

1. **Lambda Connection Reuse:**
   - Connections persist between warm invocations
   - No manual connection pool configuration needed
   - boto3 manages connections efficiently

2. **Connection Pool Benefits:**
   - Reduced latency for warm starts
   - Automatic connection management
   - No configuration required

3. **Performance Impact:**
   - Cold start: New connections established (~100ms overhead)
   - Warm start: Connections reused (< 10ms overhead)

### Caching Strategies

**Client-Side Caching:** Implement caching in your application.

**Strategies:**

1. **Cache Event Details:**
   ```python
   from functools import lru_cache
   from datetime import datetime, timedelta
   
   class CachedTriggersClient:
       def __init__(self, client, ttl_seconds=300):
           self.client = client
           self.cache = {}
           self.ttl = timedelta(seconds=ttl_seconds)
       
       def get_event(self, event_id):
           now = datetime.utcnow()
           
           # Check cache
           if event_id in self.cache:
               cached_data, cached_time = self.cache[event_id]
               if now - cached_time < self.ttl:
                   return cached_data
           
           # Fetch from API
           event = self.client.get_event(event_id)
           
           # Cache result
           self.cache[event_id] = (event, now)
           return event
   ```

2. **Cache Inbox Results:**
   ```python
   def get_inbox_cached(client, cache_key, ttl=60):
       # Check cache
       cached = cache.get(cache_key)
       if cached:
           return cached
       
       # Fetch from API
       inbox = client.get_inbox(limit=50)
       
       # Cache result
       cache.set(cache_key, inbox, ttl)
       return inbox
   ```

3. **Cache Invalidation:**
   - Invalidate cache on event updates
   - Use TTL-based expiration
   - Invalidate on acknowledgment or deletion

---

## Batch Operations

### When to Use Batch Operations

**Use Cases:**
- Processing multiple events from a queue
- Bulk event ingestion
- Event replay scenarios
- Data migration

**Benefits:**
- Reduced API call overhead
- Better error handling per event
- Improved throughput

### Batch Size Recommendations

**Optimal Sizes:**
- **Small batches (10-20 events):** Better error isolation
- **Medium batches (20-50 events):** Balanced throughput and error handling
- **Large batches (50+ events):** Maximum throughput (higher error risk)

**Python Example:**
```python
def create_events_batch(client, events, batch_size=25):
    """Create events in batches with error handling."""
    results = []
    errors = []
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i+batch_size]
        
        for event_data in batch:
            try:
                result = client.create_event(
                    source=event_data["source"],
                    event_type=event_data["event_type"],
                    payload=event_data["payload"],
                    metadata=event_data.get("metadata")
                )
                results.append(result)
            except Exception as e:
                errors.append({
                    "event": event_data,
                    "error": str(e),
                    "request_id": getattr(e, "request_id", None)
                })
        
        # Small delay between batches
        if i + batch_size < len(events):
            time.sleep(0.1)
    
    return results, errors
```

**JavaScript Example:**
```javascript
async function createEventsBatch(client, events, batchSize = 25) {
    const results = [];
    const errors = [];
    
    for (let i = 0; i < events.length; i += batchSize) {
        const batch = events.slice(i, i + batchSize);
        
        for (const eventData of batch) {
            try {
                const result = await client.createEvent({
                    source: eventData.source,
                    eventType: eventData.eventType,
                    payload: eventData.payload,
                    metadata: eventData.metadata
                });
                results.push(result);
            } catch (error) {
                errors.push({
                    event: eventData,
                    error: error.message,
                    requestId: error.requestId
                });
            }
        }
        
        // Small delay between batches
        if (i + batchSize < events.length) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }
    
    return { results, errors };
}
```

### Error Handling for Batches

**Best Practices:**

1. **Continue on Error:**
   - Don't stop batch on single error
   - Collect errors for later processing
   - Return both successes and errors

2. **Idempotency in Batches:**
   ```python
   def create_events_batch_with_idempotency(client, events):
       """Use idempotency keys to prevent duplicates."""
       results = []
       
       for event_data in events:
           # Generate idempotency key
           idempotency_key = f"{event_data['source']}-{event_data['event_type']}-{event_data.get('id')}"
           
           result = client.create_event(
               source=event_data["source"],
               event_type=event_data["event_type"],
               payload=event_data["payload"],
               metadata={
                   **event_data.get("metadata", {}),
                   "idempotency_key": idempotency_key
               }
           )
           results.append(result)
       
       return results
   ```

3. **Retry Failed Events:**
   ```python
   def create_events_with_retry(client, events, max_retries=3):
       """Retry failed events with exponential backoff."""
       results = []
       failed = []
       
       for event_data in events:
           for attempt in range(max_retries):
               try:
                   result = client.create_event(**event_data)
                   results.append(result)
                   break
               except (RateLimitExceededError, InternalError) as e:
                   if attempt == max_retries - 1:
                       failed.append(event_data)
                   else:
                       time.sleep(2 ** attempt)
               except Exception as e:
                   failed.append(event_data)
                   break
       
       return results, failed
   ```

---

## Filtering Optimization

### Efficient Filtering Strategies

**Use GSI for Status-Based Queries:**
- Inbox queries automatically use `status-created_at-index` GSI
- Efficient for querying pending events
- Filter expressions applied after query

**Optimize Filter Combinations:**
```python
# ✅ Efficient: Single source filter
inbox = client.get_inbox(source="my-app", limit=50)

# ✅ Efficient: Source + event_type filter
inbox = client.get_inbox(
    source="my-app",
    event_type="user.created",
    limit=50
)

# Filtering is applied after GSI query
# Still efficient for most use cases
```

### GSI Usage for Filtering

**How It Works:**
1. Query GSI by status (partition key)
2. Sort by created_at (sort key)
3. Apply source/event_type filters after query
4. Return filtered results

**Performance Impact:**
- GSI query: < 50ms (p95)
- Filter application: < 10ms
- Total: < 60ms for filtered queries

### Filter Expression Best Practices

**Limitations:**
- Filter expressions are applied after query
- May affect pagination (filtered items don't count toward limit)
- Use query filters when possible

**Best Practices:**
1. Use specific source/event_type values
2. Combine filters efficiently
3. Use appropriate page sizes
4. Handle pagination with filtered results

---

## Pagination Best Practices

### Cursor-Based Pagination Usage

**How It Works:**
1. Initial request: `GET /v1/inbox?limit=50`
2. Response includes `next_cursor` if more results available
3. Next request: `GET /v1/inbox?limit=50&cursor=...`
4. Continue until no `next_cursor`

**Python Example:**
```python
def get_all_events_paginated(client, source=None):
    """Efficiently paginate through all events."""
    all_events = []
    cursor = None
    
    while True:
        inbox = client.get_inbox(
            limit=100,  # Optimal page size
            cursor=cursor,
            source=source
        )
        
        all_events.extend(inbox.events)
        
        # Check for more results
        if inbox.pagination.next_cursor:
            cursor = inbox.pagination.next_cursor
        else:
            break
    
    return all_events
```

**JavaScript Example:**
```javascript
async function getAllEventsPaginated(client, source = null) {
    const allEvents = [];
    let cursor = null;
    
    while (true) {
        const inbox = await client.getInbox({
            limit: 100,
            cursor,
            source
        });
        
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

### Page Size Recommendations

**Optimal Sizes:**
- **Small (10-25):** Faster responses, more requests
- **Medium (50-100):** Balanced (recommended)
- **Large (100):** Maximum per request, slower responses

**Considerations:**
- Response size (larger pages = larger responses)
- Number of requests (smaller pages = more requests)
- Processing time (larger pages = more processing)

### Pagination Performance Tips

1. **Use Appropriate Page Sizes:**
   - Default: 50 events per page
   - Maximum: 100 events per page
   - Adjust based on use case

2. **Handle Cursors Efficiently:**
   - Store cursor for resuming pagination
   - Don't decode/modify cursor values
   - Use cursor as-is from API response

3. **Avoid Unnecessary Pagination:**
   - Fetch only what you need
   - Don't paginate through all events if only recent ones needed
   - Use filtering to reduce result set

### Pagination Limitations

**No Total Count:**
- DynamoDB doesn't efficiently support total count
- Pagination is cursor-based only
- No way to know total number of events

**Filtering Impact:**
- Filter expressions applied after query
- Filtered items don't count toward limit
- May need to paginate through more pages to get desired results

---

## Connection Pooling

### boto3 Connection Pooling

**Automatic Management:**
- boto3 handles connection pooling automatically
- No manual configuration required
- Connections persist between Lambda invocations

**Benefits:**
- Reduced latency for warm starts
- Automatic connection reuse
- Efficient resource management

### Lambda Connection Reuse

**How It Works:**
1. **Cold Start:** New connections established (~100ms overhead)
2. **Warm Start:** Connections reused (< 10ms overhead)
3. **Connection Pool:** Managed by boto3 automatically

**Performance Impact:**
- Cold start: ~100ms connection overhead
- Warm start: < 10ms connection overhead
- Significant improvement for high-traffic scenarios

### Connection Pool Configuration

**Default Settings:**
- No configuration needed
- boto3 uses optimal defaults
- Automatic connection management

**Best Practices:**
- Let boto3 manage connections
- No manual connection pool configuration
- Connections automatically reused in warm Lambda invocations

---

## Caching Strategies

### Client-Side Caching

**Event Details Caching:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedTriggersClient:
    def __init__(self, client, ttl_seconds=300):
        self.client = client
        self.cache = {}
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def get_event(self, event_id):
        now = datetime.utcnow()
        
        # Check cache
        if event_id in self.cache:
            cached_data, cached_time = self.cache[event_id]
            if now - cached_time < self.ttl:
                return cached_data
        
        # Fetch from API
        event = self.client.get_event(event_id)
        
        # Cache result
        self.cache[event_id] = (event, now)
        return event
```

### Cache Invalidation Patterns

**TTL-Based Expiration:**
- Set appropriate TTL based on data freshness needs
- Shorter TTL for frequently changing data
- Longer TTL for stable data

**Event-Based Invalidation:**
- Invalidate cache on event updates
- Invalidate on acknowledgment
- Invalidate on deletion

**Cache Hit/Miss Considerations:**
- Monitor cache hit rates
- Adjust TTL based on hit rates
- Balance freshness vs performance

---

## Performance Benchmarks

### Expected Latency Targets

**Target Metrics:**
- Event ingestion: < 100ms (p95)
- Inbox query: < 200ms (p95)
- Event retrieval: < 50ms (p95)
- Acknowledgment: < 50ms (p95)

### Actual Performance Measurements

**Lambda Performance:**
- Cold start: ~1-2 seconds
- Warm start: < 100ms
- Memory: 512MB (configurable)

**DynamoDB Performance:**
- PutItem: < 50ms (p95)
- GetItem: < 20ms (p95)
- Query (GSI): < 50ms (p95)
- Scan: < 100ms (p95, limited use)

### Cold Start Times

**Current Performance:**
- First invocation: ~1-2 seconds
- Includes: Lambda initialization, package loading, connection setup

**Optimization:**
- Use provisioned concurrency to reduce cold starts
- Optimize package size
- Minimize initialization code

### Warm Start Times

**Current Performance:**
- Subsequent invocations: < 100ms
- Includes: Request processing, DynamoDB operations

**Factors:**
- Connection reuse
- Lambda container reuse
- Optimized code paths

### Benchmark Methodology

**How to Measure:**
1. Use CloudWatch metrics for Lambda duration
2. Monitor API Gateway latency
3. Track DynamoDB operation times
4. Measure end-to-end latency from client

**Tools:**
- CloudWatch Metrics
- API Gateway metrics
- Custom logging with timestamps
- Performance testing tools

---

## Performance Comparison Tables

### Operation Latency (p95)

| Operation | Cold Start | Warm Start | Target |
|-----------|------------|------------|--------|
| Create Event | ~1.5s | < 100ms | < 100ms |
| Get Event | ~1.5s | < 50ms | < 50ms |
| Get Inbox | ~1.5s | < 200ms | < 200ms |
| Acknowledge | ~1.5s | < 50ms | < 50ms |

### Throughput

| Scenario | Events/Second | Notes |
|----------|---------------|-------|
| Single Request | 1 | Sequential processing |
| Batch (10 events) | ~5-10 | With delays |
| Parallel (5 workers) | ~20-30 | Concurrent requests |
| Optimal | 50+ | With provisioned concurrency |

---

## See Also

- [API Reference](API.md) - Complete endpoint documentation
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- [Usage Examples](EXAMPLES.md) - Code examples and patterns
- [Architecture Documentation](ARCHITECTURE.md) - System architecture

