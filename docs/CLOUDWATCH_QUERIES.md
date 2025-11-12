# CloudWatch Log Insights Queries

Useful CloudWatch Log Insights queries for monitoring and debugging the Triggers API.

## Error Analysis

### Error Rate by Endpoint
```
fields @timestamp, endpoint, method, status_code, error
| filter level = "ERROR" or level = "WARNING"
| stats count() by endpoint, method
| sort count desc
```

### Recent Errors
```
fields @timestamp, endpoint, method, error, error_type, request_id
| filter level = "ERROR"
| sort @timestamp desc
| limit 100
```

### Failed Authentication Attempts
```
fields @timestamp, api_key, endpoint, error, request_id
| filter operation = "validate_api_key" and level = "WARNING"
| stats count() by api_key
| sort count desc
```

## Performance Analysis

### Request Latency by Endpoint
```
fields @timestamp, endpoint, method, duration_ms
| filter duration_ms > 0
| stats avg(duration_ms), max(duration_ms), pct(duration_ms, 50), pct(duration_ms, 95), pct(duration_ms, 99) by endpoint, method
```

### High Latency Requests
```
fields @timestamp, endpoint, method, duration_ms, request_id
| filter duration_ms > 100
| sort duration_ms desc
| limit 50
```

### Slowest Operations
```
fields @timestamp, operation, duration_ms, endpoint, request_id
| filter duration_ms > 0
| stats max(duration_ms), avg(duration_ms), pct(duration_ms, 95) by operation
| sort max(duration_ms) desc
```

## Request Correlation

### Full Request Trace (by request_id)
```
fields @timestamp, request_id, endpoint, method, operation, status_code, duration_ms, error
| filter request_id = "550e8400-e29b-41d4-a716-446655440000"
| sort @timestamp asc
```

### Request Flow for Specific Event
```
fields @timestamp, request_id, endpoint, method, operation, event_id, status_code
| filter event_id = "660e8400-e29b-41d4-a716-446655440001"
| sort @timestamp asc
```

## Traffic Analysis

### Event Creation Rate
```
fields @timestamp, operation
| filter operation = "create_event" and status_code = 201
| stats count() by bin(5m)
```

### Request Count by Endpoint
```
fields @timestamp, endpoint, method
| stats count() by endpoint, method, bin(5m)
```

### API Key Usage
```
fields @timestamp, api_key, endpoint, method
| filter api_key != ""
| stats count() by api_key, endpoint
| sort count desc
```

## Database Operations

### DynamoDB Operation Performance
```
fields @timestamp, operation, duration_ms, error
| filter operation = "get_event" or operation = "create_event" or operation = "query_pending_events"
| stats avg(duration_ms), max(duration_ms), pct(duration_ms, 95) by operation
```

### GSI vs Scan Usage
```
fields @timestamp, operation, method
| filter operation = "get_event"
| stats count() by method
```

## Error Patterns

### Most Common Errors
```
fields @timestamp, error_type, error, endpoint
| filter level = "ERROR"
| stats count() by error_type, endpoint
| sort count desc
```

### Validation Errors
```
fields @timestamp, endpoint, method, error, request_id
| filter error_type = "ValidationError" or error_type = "VALIDATION_ERROR"
| sort @timestamp desc
| limit 50
```

## Time Range Queries

### Last Hour Errors
```
fields @timestamp, endpoint, method, error, request_id
| filter @timestamp > date_sub(now(), 1h) and level = "ERROR"
| sort @timestamp desc
```

### Last 24 Hours Performance
```
fields @timestamp, endpoint, method, duration_ms
| filter @timestamp > date_sub(now(), 24h) and duration_ms > 0
| stats avg(duration_ms), pct(duration_ms, 95), pct(duration_ms, 99) by endpoint, method, bin(1h)
```

## Custom Queries

### Events Created by Source
```
fields @timestamp, source, event_id
| filter operation = "create_event" and status_code = 201
| stats count() by source
| sort count desc
```

### Inbox Query Patterns
```
fields @timestamp, source_filter, event_type_filter, result_count
| filter operation = "get_inbox"
| stats avg(result_count), max(result_count) by source_filter, event_type_filter
```

## Tips

1. **Time Range**: Always specify a time range for better performance
2. **Field Selection**: Use `fields` to limit returned data
3. **Filtering**: Use `filter` to narrow down results
4. **Sorting**: Use `sort` to order results meaningfully
5. **Limits**: Use `limit` to cap result sets

## Saving Queries

Save frequently used queries in CloudWatch Log Insights:
1. Run your query
2. Click "Save" button
3. Give it a descriptive name
4. Access saved queries from the "Saved queries" tab


