# CloudWatch Metrics

The Triggers API emits custom CloudWatch metrics for monitoring performance and reliability.

## Metric Namespace

All metrics are published under: `TriggersAPI/Production`

## Available Metrics

### ApiLatency
**Unit:** Milliseconds  
**Dimensions:**
- `Endpoint`: API endpoint path (e.g., "/v1/events")
- `Method`: HTTP method (GET, POST, DELETE)

**Description:** Request latency in milliseconds. Used to calculate p50, p95, p99 percentiles.

**Example Query:**
```
Namespace: TriggersAPI/Production
Metric: ApiLatency
Dimensions: Endpoint=/v1/events, Method=POST
Statistic: p95
```

### ApiRequestCount
**Unit:** Count  
**Dimensions:**
- `Endpoint`: API endpoint path
- `Method`: HTTP method
- `Status`: Request status (success, error)

**Description:** Total number of requests per endpoint. Can be filtered by status to get success/error counts.

**Example Query:**
```
Namespace: TriggersAPI/Production
Metric: ApiRequestCount
Dimensions: Endpoint=/v1/events, Method=POST, Status=success
Statistic: Sum
```

### ApiErrorRate
**Unit:** Count  
**Dimensions:**
- `Endpoint`: API endpoint path
- `Method`: HTTP method
- `ErrorType`: Error type (e.g., VALIDATION_ERROR, NOT_FOUND, INTERNAL_ERROR)

**Description:** Number of errors by error type. Helps identify common error patterns.

**Example Query:**
```
Namespace: TriggersAPI/Production
Metric: ApiErrorRate
Dimensions: ErrorType=VALIDATION_ERROR
Statistic: Sum
```

### EventIngestionRate
**Unit:** Count/Second  
**Dimensions:** None

**Description:** Event ingestion rate in events per second. Measures throughput.

**Example Query:**
```
Namespace: TriggersAPI/Production
Metric: EventIngestionRate
Statistic: Average
```

## Metric Dimensions

Dimensions allow filtering and grouping metrics:

- **Endpoint**: `/v1/events`, `/v1/inbox`, `/v1/health`, etc.
- **Method**: `GET`, `POST`, `DELETE`
- **Status**: `success`, `error`
- **ErrorType**: `VALIDATION_ERROR`, `NOT_FOUND`, `UNAUTHORIZED`, `CONFLICT`, `INTERNAL_ERROR`

## CloudWatch Dashboard

A pre-configured dashboard is available with widgets for:
- API Latency (p50, p95, p99)
- Request Count by Endpoint
- Success vs Error Rate
- Error Rate by Type
- Event Ingestion Rate

**Setup:**
```bash
./scripts/setup_cloudwatch_dashboard.sh
```

## CloudWatch Alarms

Pre-configured alarms monitor:
- **High Latency**: p95 latency > 100ms per endpoint
- **Low Success Rate**: Success rate < 99.9%
- **High Error Rate**: Error rate > 0.1%

**Setup:**
```bash
./scripts/setup_cloudwatch_alarms.sh
```

## Metric Batching

Metrics are automatically batched to reduce CloudWatch API calls:
- Metrics are collected during request processing
- Batched metrics are flushed after each request
- Maximum batch size: 20 metrics (CloudWatch limit)

## Cost Considerations

CloudWatch custom metrics have costs:
- **First 10,000 metrics**: Free
- **Additional metrics**: $0.30 per metric per month
- **API requests**: $0.01 per 1,000 PutMetricData requests

**Optimization:**
- Metrics are batched to minimize API calls
- Only essential metrics are emitted
- Consider using CloudWatch Embedded Metrics Format for better efficiency

## Example Queries

### Average Latency by Endpoint (Last Hour)
```
Namespace: TriggersAPI/Production
Metric: ApiLatency
Dimensions: Endpoint=/v1/events, Method=POST
Statistic: Average
Period: 5 minutes
Time Range: Last 1 hour
```

### Error Rate Trend
```
Namespace: TriggersAPI/Production
Metric: ApiErrorRate
Statistic: Sum
Period: 5 minutes
Time Range: Last 24 hours
```

### Throughput (Events/Second)
```
Namespace: TriggersAPI/Production
Metric: EventIngestionRate
Statistic: Average
Period: 1 minute
Time Range: Last 1 hour
```

## Integration with Alarms

Alarms can be configured to trigger SNS notifications:

```bash
export SNS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:alerts"
./scripts/setup_cloudwatch_alarms.sh
```

## Best Practices

1. **Monitor Key Metrics**: Focus on latency, success rate, and error rate
2. **Set Appropriate Thresholds**: Balance alert sensitivity vs noise
3. **Use Percentiles**: p95 and p99 provide better insight than averages
4. **Dimension Filtering**: Use dimensions to drill down into specific issues
5. **Cost Management**: Monitor metric usage and optimize if needed


