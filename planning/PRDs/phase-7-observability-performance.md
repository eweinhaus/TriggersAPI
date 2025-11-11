# Phase 7: Observability & Performance - PRD

**Phase:** 7 of 10  
**Priority:** P1 (Should Have)  
**Estimated Duration:** 2-3 weeks  
**Dependencies:** Phase 1-6 (Core API complete)  
**Can be implemented in parallel with:** Phase 8, Phase 9, Phase 10

---

## 1. Executive Summary

Phase 7 enhances the API with observability and performance improvements. This includes structured logging, CloudWatch metrics, event lookup optimization, and load testing infrastructure. These improvements enable better monitoring, debugging, and performance optimization.

**Goal:** Production-ready observability and performance optimizations.

---

## 2. Scope

### In Scope
- Structured JSON logging with request context
- CloudWatch metrics (latency, success rate, error rate)
- Event lookup optimization (GSI for O(1) lookup)
- Load testing suite with performance benchmarks
- CloudWatch dashboard configuration
- Performance monitoring and alerting

### Out of Scope
- Rate limiting (Phase 8)
- API enhancements (Phase 8)
- Documentation (Phase 9)
- Advanced features (Phase 10)

---

## 3. Functional Requirements

### 3.1 Structured Logging Enhancement

**Purpose:** Convert logging to structured JSON format for better parsing and correlation.

**Requirements:**
- JSON-structured log format
- Request context in all logs (request_id, api_key, endpoint, method)
- Correlation ID tracking across services
- CloudWatch Log Insights compatibility
- Backward compatible (still readable as text)

**Implementation:**
- Create JSON formatter for Python logging
- Add request context middleware
- Update all log statements to use structured format
- Add CloudWatch Log Insights queries

**Success Criteria:**
- All logs are structured JSON
- Request IDs correlate across all log entries
- CloudWatch Log Insights queries work correctly

---

### 3.2 CloudWatch Metrics

**Purpose:** Track API performance and reliability metrics.

**Required Metrics:**
- **Latency:** p50, p95, p99 per endpoint
- **Success Rate:** Percentage of successful requests per endpoint
- **Error Rate:** Percentage of errors by error type
- **Request Count:** Total requests per endpoint
- **Event Ingestion Rate:** Events per second

**Dashboard:**
- Real-time metrics visualization
- Historical trends
- Alert thresholds visualization

**Alarms:**
- p95 latency > 100ms
- Success rate < 99.9%
- Error rate > 0.1%

**Implementation:**
- Create metrics helper functions
- Add metric calls to all endpoints
- Create CloudWatch dashboard
- Set up CloudWatch alarms

**Success Criteria:**
- All metrics are emitted correctly
- Dashboard displays all metrics
- Alarms trigger at thresholds

---

### 3.3 Event Lookup Optimization (GSI)

**Purpose:** Optimize event lookup from O(n) scan to O(1) query.

**Current Implementation:**
- Uses DynamoDB scan with pagination
- Scans entire table to find event by ID
- Slow for large tables

**New Implementation:**
- Create GSI on `event_id` (partition key only)
- Update `get_event()` to query GSI
- Maintain backward compatibility

**Migration:**
- Create migration script for existing tables
- Handle tables without GSI gracefully
- Update table creation scripts

**Implementation:**
- Add GSI definition to table creation
- Update `get_event()` function
- Create migration script
- Add tests for GSI lookup

**Success Criteria:**
- Event lookup uses GSI (verified in CloudWatch)
- Lookup time < 50ms (p95)
- Migration script works for existing tables

---

### 3.4 Load Testing Suite

**Purpose:** Automated load testing to validate performance targets.

**Test Scenarios:**
1. **Event Ingestion:** High volume event creation
2. **Inbox Polling:** Concurrent inbox queries
3. **Mixed Workload:** Realistic traffic patterns
4. **Stress Test:** Beyond normal capacity

**Performance Targets:**
- Event ingestion: < 100ms p95 latency
- Inbox query: < 200ms p95 latency
- Success rate: > 99.9%
- Throughput: 1000+ events/second

**Tools:**
- k6 (recommended) or Locust
- CI/CD integration
- Performance regression detection

**Implementation:**
- Set up k6 load testing framework
- Create load test scenarios
- Add performance benchmarks
- Integrate with CI/CD
- Create load test runner script

**Success Criteria:**
- Load tests run automatically
- Performance targets are met
- Regression detection works

---

## 4. Technical Requirements

### 4.1 Structured Logging

**Format:**
```json
{
  "timestamp": "2025-11-11T12:00:00.000Z",
  "level": "INFO",
  "message": "Event created",
  "request_id": "uuid-v4",
  "api_key": "key-prefix...",
  "endpoint": "/v1/events",
  "method": "POST",
  "status_code": 201,
  "duration_ms": 45,
  "event_id": "uuid-v4"
}
```

**Implementation Files:**
- `src/utils/logging.py` - JSON formatter and helpers
- `src/main.py` - Logging configuration
- All endpoint files - Enhanced log statements

---

### 4.2 CloudWatch Metrics

**Custom Metrics:**
- `ApiLatency` (Milliseconds, p50/p95/p99)
- `ApiSuccessRate` (Percent)
- `ApiErrorRate` (Count, by error type)
- `ApiRequestCount` (Count)
- `EventIngestionRate` (Count/Second)

**Namespace:** `TriggersAPI/Production`

**Implementation Files:**
- `src/utils/metrics.py` - Metric helpers
- All endpoint files - Metric calls
- `scripts/setup_cloudwatch_dashboard.sh` - Dashboard setup
- `template.yaml` - CloudWatch permissions

---

### 4.3 Event Lookup GSI

**GSI Definition:**
- Name: `event-id-index`
- Partition Key: `event_id` (String)
- Projection: All attributes
- Billing: On-demand

**Implementation Files:**
- `scripts/create_tables.py` - GSI definition
- `src/database.py` - Updated `get_event()` function
- `scripts/migrate_add_event_id_gsi.py` - Migration script
- `template.yaml` - GSI in SAM template

---

### 4.4 Load Testing

**Framework:** k6 (JavaScript-based)

**Test Structure:**
```
tests/load/
├── scenarios/
│   ├── event_ingestion.js
│   ├── inbox_polling.js
│   ├── mixed_workload.js
│   └── stress_test.js
├── config.yaml
└── README.md
```

**Implementation Files:**
- `tests/load/` - Load test directory
- `scripts/run_load_tests.sh` - Test runner
- `.github/workflows/load-tests.yml` - CI/CD integration (optional)

---

## 5. Implementation Steps

### Step 1: Structured Logging (Week 1, Days 1-2)
1. Create `src/utils/logging.py` with JSON formatter
2. Update `src/main.py` to use structured logging
3. Add request context middleware
4. Update all log statements in endpoints
5. Test structured logging output
6. Add CloudWatch Log Insights queries

### Step 2: CloudWatch Metrics (Week 1, Days 3-5)
1. Create `src/utils/metrics.py` with metric helpers
2. Add metric calls to all endpoints (start/end timing)
3. Create CloudWatch dashboard configuration
4. Set up CloudWatch alarms
5. Test metrics emission
6. Verify dashboard and alarms

### Step 3: Event Lookup Optimization (Week 2, Days 1-3)
1. Add GSI definition to `scripts/create_tables.py`
2. Update `src/database.py` `get_event()` to use GSI
3. Create migration script for existing tables
4. Update `template.yaml` with GSI
5. Test GSI lookup performance
6. Run migration on test environment

### Step 4: Load Testing Suite (Week 2, Days 4-5)
1. Set up k6 framework
2. Create load test scenarios
3. Define performance benchmarks
4. Create load test runner script
5. Run initial load tests
6. Document load testing process

---

## 6. Success Metrics

### Observability
- ✅ All logs are structured JSON
- ✅ Request correlation works (request_id in all logs)
- ✅ CloudWatch Log Insights queries return results
- ✅ Metrics are emitted for all endpoints
- ✅ Dashboard displays all metrics correctly
- ✅ Alarms trigger at configured thresholds

### Performance
- ✅ Event lookup < 50ms (p95) with GSI
- ✅ Event ingestion < 100ms (p95) under load
- ✅ Inbox query < 200ms (p95) under load
- ✅ Success rate > 99.9% under load
- ✅ Throughput > 1000 events/second

### Testing
- ✅ Load tests run automatically
- ✅ Performance benchmarks are met
- ✅ Regression detection works

---

## 7. Testing Requirements

### Unit Tests
- Structured logging formatter
- Metrics helper functions
- GSI lookup function
- Migration script logic

### Integration Tests
- Structured logging in request flow
- Metrics emission in endpoints
- GSI lookup with test data
- Load test scenarios

### Manual Testing
- CloudWatch dashboard verification
- Alarm triggering verification
- Load test execution
- Performance benchmark validation

---

## 8. Documentation

### Required Documentation
- Structured logging format specification
- CloudWatch metrics reference
- Load testing guide
- Performance tuning guide (if created)

### Files to Update
- `docs/PERFORMANCE.md` - Performance tuning guide
- `README.md` - Add observability section
- `docs/ARCHITECTURE.md` - Update with observability components

---

## 9. Out of Scope

- Rate limiting (Phase 8)
- API feature enhancements (Phase 8)
- Documentation improvements (Phase 9)
- Advanced features (Phase 10)
- Real-time alerting (can use CloudWatch alarms)
- Custom analytics (Phase 10)

---

## 10. Dependencies

### Required
- Phase 1-6 complete (core API)
- AWS account with CloudWatch access
- DynamoDB tables (existing)

### Optional
- CI/CD pipeline (for automated load tests)
- CloudWatch Log Insights (for log queries)

---

## 11. Risks & Mitigation

### Risk 1: GSI Migration Complexity
**Mitigation:** Test migration script thoroughly on staging, support rollback

### Risk 2: Metrics Overhead
**Mitigation:** Use CloudWatch PutMetricData batching, monitor Lambda costs

### Risk 3: Load Test Costs
**Mitigation:** Run load tests on staging environment, limit test duration

### Risk 4: Structured Logging Performance
**Mitigation:** Use efficient JSON serialization, benchmark logging overhead

---

**Document Status:** Draft  
**Last Updated:** 2025-11-11

