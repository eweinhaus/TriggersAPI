# Performance Benchmarks

This document tracks baseline performance metrics for the Triggers API.

## Baseline Metrics (Pre-Optimization)

*To be established after initial load test runs*

### Event Ingestion
- **p50 Latency:** TBD ms
- **p95 Latency:** TBD ms
- **p99 Latency:** TBD ms
- **Throughput:** TBD events/second
- **Success Rate:** TBD %

### Inbox Query
- **p50 Latency:** TBD ms
- **p95 Latency:** TBD ms
- **p99 Latency:** TBD ms
- **Success Rate:** TBD %

## Performance Targets

### Event Ingestion
- **p95 Latency:** < 100ms
- **Success Rate:** > 99.9%
- **Throughput:** > 1000 events/second

### Inbox Query
- **p95 Latency:** < 200ms
- **Success Rate:** > 99.9%

### Mixed Workload
- **p95 Latency:** < 150ms (weighted average)
- **Success Rate:** > 99.9%

## Regression Detection

Performance regressions are detected when:
- Latency increases by > 20% from baseline
- Success rate drops below target thresholds
- Throughput decreases by > 10% from baseline

## How to Update Baselines

1. Run load tests against stable environment
2. Record metrics from k6 output
3. Update this document with new baseline values
4. Commit baseline updates with test results

## Test Date: TBD

*Run initial load tests and update this section with actual baseline metrics.*

