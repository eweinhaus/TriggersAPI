# Phase 7: Observability & Performance - Task List

**Phase:** 7 of 10  
**Priority:** P1 (Should Have)  
**Status:** 🔄 Pending  
**Created:** 2025-11-11  
**Estimated Duration:** 2-3 weeks  
**Dependencies:** Phase 1-6 (Core API complete)

---

## Overview

This task list covers the implementation of Phase 7: Observability & Performance. The goal is to enhance the API with production-ready observability (structured logging, CloudWatch metrics) and performance optimizations (GSI for event lookup, load testing infrastructure).

**Key Deliverables:**
- Structured JSON logging with request context
- CloudWatch metrics (latency, success rate, error rate)
- Event lookup optimization (GSI for O(1) lookup)
- Load testing suite with k6
- CloudWatch dashboard and alarms
- Performance monitoring and alerting

---

## Task Breakdown

### 1. Structured Logging Enhancement

#### 1.1 Create JSON Logging Formatter
- [ ] Create `src/utils/logging.py` module
- [ ] Implement `JSONFormatter` class extending `logging.Formatter`:
  - Format logs as JSON objects
  - Include standard fields: `timestamp`, `level`, `message`
  - Support request context injection (request_id, api_key, endpoint, method)
  - Handle nested objects and exceptions
  - Ensure CloudWatch Log Insights compatibility
- [ ] Add helper function `get_logger(name: str)` that returns configured logger
- [ ] Add context manager for request context (store in thread-local or contextvars)
- [ ] Test JSON formatter with various log levels and message types

#### 1.2 Update Logging Configuration
- [ ] Update `src/main.py` to use structured JSON logging:
  - Replace basic logging config with JSON formatter
  - Configure root logger with JSON formatter
  - Set log level from environment variable (`LOG_LEVEL`)
  - Ensure backward compatibility (logs still readable as text)
- [ ] Test logging output format in local environment
- [ ] Verify JSON logs are valid and parseable

#### 1.3 Add Request Context Middleware
- [ ] Create request context middleware in `src/main.py`:
  - Extract request context: `request_id`, `api_key` (masked), `endpoint`, `method`
  - Store context in request state or contextvars
  - Make context available to all loggers during request processing
  - Clear context after request completes
- [ ] Update existing request ID middleware to also set logging context
- [ ] Test context propagation across all endpoints

#### 1.4 Update Log Statements in Endpoints
- [ ] Update `src/endpoints/events.py`:
  - Replace all `logger.info()`, `logger.error()` calls with structured logging
  - Include relevant context: `event_id`, `status_code`, `duration_ms`
  - Add structured fields for event creation, acknowledgment, deletion
- [ ] Update `src/endpoints/inbox.py`:
  - Add structured logging for inbox queries
  - Include pagination context (limit, cursor, result_count)
  - Log filtering parameters (source, event_type)
- [ ] Update `src/endpoints/health.py`:
  - Add structured logging for health checks
- [ ] Update `src/database.py`:
  - Add structured logging for DynamoDB operations
  - Log operation type, table name, duration
  - Include error context for failed operations
- [ ] Update `src/auth.py`:
  - Add structured logging for authentication attempts
  - Log success/failure (without exposing API keys)
- [ ] Test all log statements produce valid JSON

#### 1.5 Add CloudWatch Log Insights Queries
- [ ] Create `docs/CLOUDWATCH_QUERIES.md`:
  - Document useful CloudWatch Log Insights queries
  - Include queries for:
    - Error rate by endpoint
    - Request latency by endpoint
    - Failed authentication attempts
    - Event creation rate
    - Request correlation (by request_id)
- [ ] Test queries against sample log data
- [ ] Document query syntax and usage

**Success Criteria:**
- ✅ All logs are structured JSON format
- ✅ Request IDs correlate across all log entries
- ✅ CloudWatch Log Insights queries work correctly
- ✅ Logs are backward compatible (readable as text)

---

### 2. CloudWatch Metrics

#### 2.1 Create Metrics Helper Module
- [ ] Create `src/utils/metrics.py` module
- [ ] Implement `CloudWatchMetrics` class:
  - Initialize CloudWatch client (boto3)
  - Support metric batching (use `PutMetricData` with multiple metrics)
  - Handle metric namespace (`TriggersAPI/Production`)
  - Support custom dimensions (endpoint, method, error_type)
- [ ] Implement helper functions:
  - `record_latency(endpoint: str, method: str, duration_ms: float, percentiles: list = [50, 95, 99])`
  - `record_success(endpoint: str, method: str)`
  - `record_error(endpoint: str, method: str, error_type: str)`
  - `record_request_count(endpoint: str, method: str)`
  - `record_event_ingestion_rate(events_per_second: float)`
- [ ] Add metric batching to reduce API calls
- [ ] Handle errors gracefully (log but don't fail request)
- [ ] Add unit tests for metrics helper functions

#### 2.2 Add Metrics to Endpoints
- [ ] Create timing middleware in `src/main.py`:
  - Measure request duration (start time → end time)
  - Calculate duration in milliseconds
  - Store duration in request state
- [ ] Update `src/endpoints/events.py`:
  - Record latency metrics for POST /v1/events
  - Record success/error metrics
  - Record request count
  - Record event ingestion rate (calculate from request count)
- [ ] Update `src/endpoints/inbox.py`:
  - Record latency metrics for GET /v1/inbox
  - Record success/error metrics
  - Record request count
- [ ] Update `src/endpoints/health.py`:
  - Record latency metrics for GET /v1/health
  - Record request count
- [ ] Update `src/endpoints/events.py` (GET, ACK, DELETE):
  - Record latency metrics for all event operations
  - Record success/error metrics
  - Record request count
- [ ] Test metrics emission in local environment (verify CloudWatch calls)

#### 2.3 Update IAM Permissions
- [ ] Update `template.yaml`:
  - Add CloudWatch permissions to Lambda execution role:
    - `cloudwatch:PutMetricData`
    - `cloudwatch:GetMetricStatistics` (for dashboard)
    - `cloudwatch:ListMetrics` (for dashboard)
- [ ] Test permissions in AWS environment
- [ ] Verify metrics are emitted correctly

#### 2.4 Create CloudWatch Dashboard
- [ ] Create `scripts/setup_cloudwatch_dashboard.sh`:
  - Use AWS CLI to create CloudWatch dashboard
  - Define dashboard widgets:
    - Latency metrics (p50, p95, p99) per endpoint
    - Success rate per endpoint
    - Error rate by error type
    - Request count per endpoint
    - Event ingestion rate
  - Configure time ranges and refresh intervals
- [ ] Create dashboard JSON configuration file:
  - `scripts/cloudwatch_dashboard.json`
  - Define all widgets and metrics
- [ ] Test dashboard creation script
- [ ] Verify dashboard displays all metrics correctly

#### 2.5 Set Up CloudWatch Alarms
- [ ] Create `scripts/setup_cloudwatch_alarms.sh`:
  - Create alarm for p95 latency > 100ms (per endpoint)
  - Create alarm for success rate < 99.9% (per endpoint)
  - Create alarm for error rate > 0.1% (per endpoint)
  - Configure SNS topic for alarm notifications (optional)
  - Set alarm evaluation period and threshold
- [ ] Test alarm creation script
- [ ] Verify alarms trigger at configured thresholds
- [ ] Document alarm configuration

**Success Criteria:**
- ✅ All metrics are emitted correctly
- ✅ Dashboard displays all metrics
- ✅ Alarms trigger at configured thresholds
- ✅ Metrics have proper dimensions and namespaces

---

### 3. Event Lookup Optimization (GSI)

#### 3.1 Add GSI Definition to Table Creation
- [ ] Update `scripts/create_tables.py`:
  - Add GSI definition for `event-id-index`:
    - Name: `event-id-index`
    - Partition Key: `event_id` (String)
    - Projection: All attributes
    - Billing Mode: On-demand
  - Make GSI creation idempotent (check if exists)
  - Handle `ResourceInUseException` gracefully
- [ ] Test table creation with GSI in local environment
- [ ] Verify GSI is created correctly

#### 3.2 Update get_event() Function
- [ ] Update `src/database.py` `get_event()` function:
  - Check if GSI exists (try query first, fallback to scan)
  - Use GSI query when available:
    - Query `event-id-index` with `event_id` as partition key
    - Return first result (should be unique)
  - Fallback to scan if GSI doesn't exist (backward compatibility)
  - Log which method is used (for monitoring)
- [ ] Add error handling for GSI query failures
- [ ] Test GSI lookup with test data
- [ ] Verify lookup performance improvement

#### 3.3 Update SAM Template
- [ ] Update `template.yaml`:
  - Add GSI definition to Events table:
    - GSI name: `event-id-index`
    - Partition key: `event_id` (String)
    - Projection: All attributes
  - Ensure GSI is included in table definition
- [ ] Test SAM template validation
- [ ] Verify GSI is created in AWS environment

#### 3.4 Create Migration Script
- [ ] Create `scripts/migrate_add_event_id_gsi.py`:
  - Connect to existing DynamoDB table
  - Check if GSI already exists
  - Create GSI if it doesn't exist
  - Wait for GSI to become active
  - Handle errors gracefully
  - Support dry-run mode
  - Support rollback (delete GSI if needed)
- [ ] Add command-line arguments:
  - `--table-name`: Table name to migrate
  - `--region`: AWS region
  - `--dry-run`: Preview changes without applying
  - `--rollback`: Delete GSI if exists
- [ ] Test migration script on test environment
- [ ] Document migration process

#### 3.5 Update Tests
- [ ] Update `tests/unit/test_database.py`:
  - Add tests for GSI lookup
  - Test fallback to scan when GSI doesn't exist
  - Test GSI query performance
- [ ] Update integration tests:
  - Test GSI lookup in integration scenarios
  - Verify backward compatibility
- [ ] Add performance tests:
  - Compare scan vs GSI lookup times
  - Verify GSI lookup < 50ms (p95)

**Success Criteria:**
- ✅ Event lookup uses GSI (verified in CloudWatch)
- ✅ Lookup time < 50ms (p95)
- ✅ Migration script works for existing tables
- ✅ Backward compatibility maintained (fallback to scan)

---

### 4. Load Testing Suite

#### 4.1 Set Up k6 Framework
- [ ] Install k6 (check if already installed):
  - macOS: `brew install k6`
  - Linux: Follow k6 installation guide
  - Windows: Download from k6.io
- [ ] Create `tests/load/` directory structure:
  - `tests/load/scenarios/` - Test scenario files
  - `tests/load/config.yaml` - Load test configuration
  - `tests/load/README.md` - Load testing documentation
- [ ] Create base k6 configuration:
  - Define common options (thresholds, summary)
  - Set up environment variables
  - Configure output formats

#### 4.2 Create Load Test Scenarios

##### 4.2.1 Event Ingestion Scenario
- [ ] Create `tests/load/scenarios/event_ingestion.js`:
  - High volume event creation (POST /v1/events)
  - Ramp up from 10 to 1000 virtual users
  - Sustain load for 5 minutes
  - Measure latency (p50, p95, p99)
  - Measure success rate
  - Measure throughput (events/second)
- [ ] Define performance thresholds:
  - p95 latency < 100ms
  - Success rate > 99.9%
  - Throughput > 1000 events/second
- [ ] Test scenario locally

##### 4.2.2 Inbox Polling Scenario
- [ ] Create `tests/load/scenarios/inbox_polling.js`:
  - Concurrent inbox queries (GET /v1/inbox)
  - Ramp up from 10 to 500 virtual users
  - Sustain load for 5 minutes
  - Measure latency (p50, p95, p99)
  - Measure success rate
- [ ] Define performance thresholds:
  - p95 latency < 200ms
  - Success rate > 99.9%
- [ ] Test scenario locally

##### 4.2.3 Mixed Workload Scenario
- [ ] Create `tests/load/scenarios/mixed_workload.js`:
  - Realistic traffic patterns:
    - 70% event creation
    - 20% inbox queries
    - 5% event acknowledgment
    - 5% event deletion
  - Ramp up from 10 to 1000 virtual users
  - Sustain load for 10 minutes
  - Measure overall latency and success rate
- [ ] Define performance thresholds:
  - p95 latency < 150ms (weighted average)
  - Success rate > 99.9%
- [ ] Test scenario locally

##### 4.2.4 Stress Test Scenario
- [ ] Create `tests/load/scenarios/stress_test.js`:
  - Beyond normal capacity testing
  - Ramp up to 2000+ virtual users
  - Test system limits
  - Measure error rates and degradation
  - Document breaking points
- [ ] Define thresholds (may be lower than normal):
  - Document expected degradation
  - Measure recovery time
- [ ] Test scenario on staging environment only

#### 4.3 Create Load Test Configuration
- [ ] Create `tests/load/config.yaml`:
  - Define test environments (local, staging, production)
  - Configure API endpoints
  - Configure API keys (use environment variables)
  - Define test durations and user counts
  - Configure thresholds per scenario
- [ ] Document configuration options

#### 4.4 Create Load Test Runner Script
- [ ] Create `scripts/run_load_tests.sh`:
  - Accept scenario name as argument
  - Accept environment (local, staging, production)
  - Load configuration from `tests/load/config.yaml`
  - Run k6 with appropriate options
  - Generate test reports
  - Exit with error code if thresholds not met
- [ ] Add safety checks:
  - Warn before running against production
  - Require confirmation for production tests
  - Limit production test duration
- [ ] Test runner script

#### 4.5 Add Performance Benchmarks
- [ ] Create `tests/load/benchmarks.md`:
  - Document baseline performance metrics
  - Define performance targets
  - Document how to interpret results
  - Include regression detection guidelines
- [ ] Run initial load tests to establish baselines
- [ ] Document baseline metrics

#### 4.6 CI/CD Integration (Optional)
- [ ] Create `.github/workflows/load-tests.yml`:
  - Run load tests on staging environment
  - Run on schedule (e.g., nightly)
  - Run on pull requests (optional, may be too slow)
  - Fail build if performance regressions detected
  - Generate test reports
- [ ] Test CI/CD integration
- [ ] Document CI/CD usage

**Success Criteria:**
- ✅ Load tests run automatically
- ✅ Performance targets are met
- ✅ Regression detection works
- ✅ Test reports are generated

---

### 5. Testing & Validation

#### 5.1 Unit Tests
- [ ] Test structured logging formatter:
  - Test JSON output format
  - Test context injection
  - Test error handling
- [ ] Test metrics helper functions:
  - Test metric batching
  - Test metric dimensions
  - Test error handling
- [ ] Test GSI lookup function:
  - Test GSI query
  - Test fallback to scan
  - Test error handling
- [ ] Test migration script logic:
  - Test GSI creation
  - Test dry-run mode
  - Test rollback

#### 5.2 Integration Tests
- [ ] Test structured logging in request flow:
  - Verify logs are structured JSON
  - Verify request correlation works
  - Test across all endpoints
- [ ] Test metrics emission in endpoints:
  - Verify metrics are emitted
  - Verify metric values are correct
  - Test error scenarios
- [ ] Test GSI lookup with test data:
  - Create test events
  - Query via GSI
  - Verify results
- [ ] Test load test scenarios:
  - Run each scenario
  - Verify thresholds are met
  - Test error handling

#### 5.3 Manual Testing
- [ ] CloudWatch dashboard verification:
  - Verify all metrics display correctly
  - Test dashboard refresh
  - Verify historical data
- [ ] Alarm triggering verification:
  - Trigger alarms manually (if possible)
  - Verify alarm notifications
  - Test alarm recovery
- [ ] Load test execution:
  - Run all scenarios
  - Verify performance targets
  - Document results
- [ ] Performance benchmark validation:
  - Compare against baselines
  - Verify improvements
  - Document findings

---

### 6. Documentation

#### 6.1 Structured Logging Documentation
- [ ] Create `docs/LOGGING.md`:
  - Document structured logging format
  - Document log fields and their meanings
  - Provide examples of log entries
  - Document CloudWatch Log Insights queries
  - Document how to correlate logs by request_id
- [ ] Update `README.md`:
  - Add observability section
  - Link to logging documentation

#### 6.2 CloudWatch Metrics Documentation
- [ ] Create `docs/METRICS.md`:
  - Document all metrics and their meanings
  - Document metric dimensions
  - Document metric namespaces
  - Provide examples of metric queries
  - Document alarm configuration
- [ ] Update `README.md`:
  - Add metrics section
  - Link to metrics documentation

#### 6.3 Load Testing Documentation
- [ ] Update `tests/load/README.md`:
  - Document how to run load tests
  - Document test scenarios
  - Document performance targets
  - Document how to interpret results
  - Document CI/CD integration
- [ ] Update `README.md`:
  - Add load testing section
  - Link to load testing documentation

#### 6.4 Performance Tuning Guide
- [ ] Create `docs/PERFORMANCE.md`:
  - Document performance optimizations
  - Document GSI usage and benefits
  - Document performance tuning tips
  - Document monitoring best practices
- [ ] Update `docs/ARCHITECTURE.md`:
  - Add observability components
  - Document metrics and logging architecture
  - Document GSI design decisions

---

## Success Criteria Checklist

### Observability
- [ ] All logs are structured JSON
- [ ] Request correlation works (request_id in all logs)
- [ ] CloudWatch Log Insights queries return results
- [ ] Metrics are emitted for all endpoints
- [ ] Dashboard displays all metrics correctly
- [ ] Alarms trigger at configured thresholds

### Performance
- [ ] Event lookup < 50ms (p95) with GSI
- [ ] Event ingestion < 100ms (p95) under load
- [ ] Inbox query < 200ms (p95) under load
- [ ] Success rate > 99.9% under load
- [ ] Throughput > 1000 events/second

### Testing
- [ ] Load tests run automatically
- [ ] Performance benchmarks are met
- [ ] Regression detection works
- [ ] All unit tests pass
- [ ] All integration tests pass

---

## Notes & Considerations

### Implementation Order
1. **Week 1, Days 1-2:** Structured logging (foundation for observability)
2. **Week 1, Days 3-5:** CloudWatch metrics (builds on logging)
3. **Week 2, Days 1-3:** Event lookup optimization (performance improvement)
4. **Week 2, Days 4-5:** Load testing suite (validation)

### Critical Implementation Details

#### Structured Logging
- Use `contextvars` or thread-local storage for request context
- Ensure JSON serialization is efficient (use `json.dumps()` with appropriate options)
- Mask API keys in logs (show only prefix)
- Include duration_ms in all endpoint logs

#### CloudWatch Metrics
- Batch metrics to reduce API calls (use `PutMetricData` with multiple metrics)
- Use appropriate metric dimensions (endpoint, method, error_type)
- Monitor CloudWatch costs (metrics can be expensive at scale)
- Use percentiles for latency (p50, p95, p99)

#### GSI Migration
- Test migration script thoroughly on staging first
- Support rollback (delete GSI if needed)
- Handle tables without GSI gracefully (fallback to scan)
- Monitor GSI creation time (can take several minutes)

#### Load Testing
- Run load tests on staging environment (not production)
- Limit production test duration if needed
- Monitor AWS costs during load tests
- Document performance baselines before optimization

### Known Limitations
- Structured logging adds slight overhead (benchmark and optimize)
- CloudWatch metrics have costs (monitor usage)
- GSI migration requires table downtime (plan accordingly)
- Load tests can be resource-intensive (run during off-peak hours)

### Dependencies
- Phase 1-6 complete (core API)
- AWS account with CloudWatch access
- DynamoDB tables (existing)
- k6 installed locally (for load testing)

---

## Next Steps After Completion

After Phase 7 completion:
1. Proceed to Phase 8: API Enhancements (rate limiting, additional features)
2. Proceed to Phase 9: Documentation Improvements
3. Proceed to Phase 10: Advanced Features
4. Monitor observability metrics in production
5. Tune performance based on load test results

---

**Task List Status:** 🔄 Pending  
**Last Updated:** 2025-11-11  
**Created By:** AI Assistant

