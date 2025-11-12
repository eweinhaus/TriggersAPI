# Load Testing Suite

This directory contains k6 load testing scenarios for the Triggers API.

## Prerequisites

Install k6:
- macOS: `brew install k6`
- Linux: Follow [k6 installation guide](https://k6.io/docs/getting-started/installation/)
- Windows: Download from [k6.io](https://k6.io/docs/getting-started/installation/)

## Test Scenarios

### 1. Event Ingestion (`event_ingestion.js`)
High volume event creation test.
- **Ramp up:** 2 minutes to 1000 virtual users
- **Sustain:** 5 minutes at 1000 users
- **Thresholds:**
  - p95 latency < 100ms
  - Success rate > 99.9%
  - Throughput > 1000 events/second

### 2. Inbox Polling (`inbox_polling.js`)
Concurrent inbox query test.
- **Ramp up:** 2 minutes to 500 virtual users
- **Sustain:** 5 minutes at 500 users
- **Thresholds:**
  - p95 latency < 200ms
  - Success rate > 99.9%

### 3. Mixed Workload (`mixed_workload.js`)
Realistic traffic pattern test.
- **Distribution:**
  - 70% event creation
  - 20% inbox queries
  - 5% event acknowledgment
  - 5% event deletion
- **Ramp up:** 2 minutes to 1000 virtual users
- **Sustain:** 10 minutes at 1000 users
- **Thresholds:**
  - p95 latency < 150ms (weighted average)
  - Success rate > 99.9%

### 4. Stress Test (`stress_test.js`)
Beyond normal capacity testing.
- **Ramp up:** 3 minutes to 2000+ virtual users
- **Sustain:** 5 minutes at 2000 users
- **Thresholds:** (More lenient)
  - p95 latency < 500ms
  - Success rate > 95%

## Running Tests

### Quick Start (Local)

```bash
# Run event ingestion test against local server
./scripts/run_load_tests.sh event_ingestion local
```

### Against Staging

```bash
export STAGING_API_URL="https://api-staging.example.com"
export STAGING_API_KEY="your-staging-api-key"
./scripts/run_load_tests.sh event_ingestion staging
```

### Against Production (with confirmation)

```bash
export PRODUCTION_API_URL="https://api.example.com"
export PRODUCTION_API_KEY="your-production-api-key"
./scripts/run_load_tests.sh event_ingestion production
```

## Available Scenarios

- `event_ingestion` - High volume event creation
- `inbox_polling` - Concurrent inbox queries
- `mixed_workload` - Realistic traffic patterns
- `stress_test` - Beyond normal capacity

## Configuration

Edit `tests/load/config.yaml` to adjust:
- Test durations
- User counts
- Performance thresholds
- Environment URLs and API keys

## Interpreting Results

k6 outputs:
- **Request rate:** Requests per second
- **Latency percentiles:** p50, p95, p99
- **Error rate:** Percentage of failed requests
- **Throughput:** Successful requests per second

### Success Criteria

- ✅ All thresholds met
- ✅ No significant performance degradation
- ✅ Error rate within acceptable limits

## Performance Baselines

See `tests/load/benchmarks.md` for baseline performance metrics.

## CI/CD Integration

Load tests can be integrated into CI/CD pipelines:

```yaml
# .github/workflows/load-tests.yml
- name: Run Load Tests
  run: ./scripts/run_load_tests.sh event_ingestion staging
```

## Safety

- Production tests require explicit confirmation
- Production test duration is limited to 5 minutes
- Always test on staging first


