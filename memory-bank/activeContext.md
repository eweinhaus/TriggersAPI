# Active Context: Zapier Triggers API

## Current Work Focus

**Status:** Phase 10 Completed - Advanced Features & Security  
**Phase:** Phase 10 Complete - Webhooks, Analytics, SDKs, Key Rotation, Request Signing, Chaos Engineering  
**Last Updated:** 2025-11-11 (Phase 10: Advanced Features & Security completed)

## Recent Changes

### Phase 1 & 2 (Completed)
- ✅ Phase 1 implementation completed
- ✅ All 5 endpoints implemented and tested
- ✅ DynamoDB Local integration working
- ✅ API key authentication functional (dual-mode: local/AWS)
- ✅ Request ID tracking implemented
- ✅ Error handling with standardized error responses
- ✅ Fixed DynamoDB reserved keyword issues (status, source, event_type)
- ✅ Added RequestValidationError handler for path parameter validation
- ✅ GitHub repository created: `https://github.com/eweinhaus/TriggersAPI`
- ✅ AWS infrastructure deployed and working
- ✅ API Gateway URL: `https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod`

### Phase 3 (Completed)
- ✅ Testing infrastructure setup complete
- ✅ Testing dependencies installed (pytest, pytest-cov, moto, httpx, faker)
- ✅ Test directory structure created (unit, integration, e2e, playwright, utils)
- ✅ pytest configuration with >80% coverage requirement
- ✅ Test fixtures created (base, integration, e2e, playwright)
- ✅ Test utilities and helpers created
- ✅ Error handling standardization complete
  - Added RateLimitExceededError exception
  - Verified all error handlers working correctly
  - Updated endpoints to use InternalError
- ✅ Enhanced input validation
  - Added field validators to EventCreate model
  - Source/event_type: required, non-empty, max 100 chars
  - Payload: required, valid JSON object, not empty
  - Metadata priority enum validation
  - Query parameter validation for inbox endpoint
- ✅ Comprehensive test suite created
  - Unit tests: 74 tests covering events, inbox, auth, database, models
  - Integration tests: Full event lifecycle, pagination, filtering
  - E2E tests: Tests against real server
  - Playwright MCP tests: HTTP-based API tests using httpx
- ✅ Test automation scripts created
  - `scripts/run_tests.sh` - Shell script for test automation
  - `scripts/run_tests.py` - Python alternative (cross-platform)
- ✅ Test coverage: 92% (exceeds 80% requirement)
- ✅ All unit tests passing (100+ tests)
- ✅ Additional test coverage added:
  - AWS mode authentication tests (test_auth_aws.py)
  - Exception class tests (test_exceptions.py)
  - Exception handler tests (test_main.py)
- ✅ README updated with comprehensive testing documentation

### Phase 6 (Completed)
- ✅ React frontend dashboard created
- ✅ Material-UI components implemented
- ✅ All pages functional (Send Event, Inbox, Event Details, Statistics)
- ✅ API integration complete
- ✅ API key management with validation
- ✅ Responsive design implemented
- ✅ Error handling and notifications
- ✅ Production build working
- ✅ Deployment scripts and documentation created
- ✅ Browser testing completed (Cursor browser extension)
- ✅ All core features tested and working
- ✅ **Production Deployment Fixes (2025-11-11):**
  - ✅ Fixed CORS issue: Frontend API URL corrected (added `/v1` prefix)
  - ✅ Fixed event lookup: DynamoDB scan pagination implemented for `get_event()`
  - ✅ Fixed Lambda permissions: Added `dynamodb:Scan` permission to IAM role
  - ✅ Fixed API key validation: Improved error handling and logging
  - ✅ Fixed SPA routing: S3 error document and CloudFront custom error responses configured
  - ✅ Frontend deployed and working: S3 + CloudFront deployment functional

### Phase 7 (Completed)
- ✅ Structured JSON logging implemented
  - ✅ Created `src/utils/logging.py` with JSONFormatter class
  - ✅ Request context middleware with automatic context injection
  - ✅ All logs include: request_id, api_key (masked), endpoint, method, duration_ms
  - ✅ CloudWatch Log Insights compatible format
  - ✅ Updated all endpoints to use structured logging
- ✅ CloudWatch metrics implemented
  - ✅ Created `src/utils/metrics.py` with CloudWatchMetrics class
  - ✅ Metrics batching (up to 20 metrics per call)
  - ✅ Metrics added to all endpoints: latency, success, error, request count
  - ✅ Error metrics recorded in exception handlers
  - ✅ Metrics flushed after each request
  - ✅ IAM permissions updated in template.yaml
- ✅ CloudWatch dashboard and alarms
  - ✅ Created `scripts/cloudwatch_dashboard.json` with dashboard widgets
  - ✅ Created `scripts/setup_cloudwatch_dashboard.sh` for dashboard setup
  - ✅ Created `scripts/setup_cloudwatch_alarms.sh` for alarm configuration
  - ✅ Alarms monitor: latency (p95 > 100ms), success rate (< 99.9%), error rate (> 0.1%)
- ✅ Event lookup optimization (GSI)
  - ✅ Added `event-id-index` GSI to table creation script
  - ✅ Updated `get_event()` to use GSI query (O(1) lookup) with scan fallback
  - ✅ Updated SAM template with GSI definition and permissions
  - ✅ Created `scripts/migrate_add_event_id_gsi.py` for existing tables
  - ✅ Backward compatibility maintained (fallback to scan)
- ✅ Load testing suite
  - ✅ Created k6 load testing framework
  - ✅ 4 test scenarios: event_ingestion, inbox_polling, mixed_workload, stress_test
  - ✅ Created `scripts/run_load_tests.sh` test runner
  - ✅ Created `tests/load/config.yaml` for configuration
  - ✅ Created `tests/load/benchmarks.md` for baseline tracking
- ✅ Documentation
  - ✅ Created `docs/LOGGING.md` - Structured logging format and queries
  - ✅ Created `docs/METRICS.md` - CloudWatch metrics reference
  - ✅ Created `docs/CLOUDWATCH_QUERIES.md` - Useful Log Insights queries
  - ✅ Updated `README.md` with observability section
  - ✅ Created `tests/load/README.md` - Load testing guide

### Phase 4 (Completed)
- ✅ GET /v1/events/{event_id} endpoint implemented
  - Added EventDetailResponse model
  - Implemented GET endpoint with full event details
  - Added 7 unit tests for GET endpoint
- ✅ Enhanced error messages implemented
  - Created error message utility functions (format_validation_error, format_not_found_error, format_conflict_error)
  - Updated Pydantic validation handler with actionable suggestions
  - Updated error handlers in endpoints to use enhanced messages
  - Error responses now include field names, issues, and suggestions
- ✅ Response standardization verified
  - All responses include request_id
  - All event responses include status field
  - Timestamps consistently ISO 8601 format
- ✅ Status tracking enhancements verified
  - Status and acknowledged_at included in all relevant responses
  - Status transitions tracked with timestamps
- ✅ Idempotency key support implemented
  - Created idempotency DynamoDB table (triggers-api-idempotency)
  - Implemented check_idempotency_key() and store_idempotency_key() functions
  - Updated create_event() to support idempotency
  - Updated event creation endpoint to extract and use idempotency keys
  - Added 2 unit tests for idempotency
- ✅ Testing and validation complete
  - All 117 unit tests passing
  - Code coverage: 87.25% (exceeds 80% requirement)
  - Fixed failing tests in test_main.py
- ✅ Documentation updated
  - README updated with GET endpoint documentation
  - Added idempotency key documentation
  - Added error handling section with examples
  - Updated test statistics (117 tests, 87% coverage)

### Phase 5 (Completed)
- ✅ Enhanced OpenAPI/Swagger documentation
  - Added comprehensive API metadata and descriptions
  - Enhanced all endpoint descriptions with use cases
  - Added request/response examples for all endpoints
  - Configured Swagger UI authentication (API key header)
  - Added error response examples (400, 401, 404, 409, 413)
  - Enhanced query and path parameter descriptions
  - Custom OpenAPI schema with security schemes
- ✅ Python example client created
  - Full-featured client with type hints and Pydantic models
  - Comprehensive error handling with specific exception classes
  - Three example scripts: basic_usage.py, event_flow.py, error_handling.py
  - Complete README with installation and usage instructions
  - All files compile successfully
- ✅ JavaScript/Node.js example client created
  - Promise-based client using axios
  - Error classes matching Python client patterns
  - Three example scripts: basic-usage.js, event-flow.js, error-handling.js
  - package.json with npm scripts
  - Complete README with installation and usage instructions
  - All files have valid syntax
- ✅ Comprehensive cURL examples
  - Complete examples for all endpoints (docs/CURL_EXAMPLES.md)
  - Local and production URL examples
  - Error case examples with expected responses
  - Tips and best practices section
- ✅ Enhanced README documentation
  - Quick Start section with 3 options (Python, JavaScript, cURL)
  - Links to all documentation files
  - Example clients section with code samples
  - Updated project status to Phase 5
- ✅ Additional documentation files created
  - docs/README.md - Documentation index
  - docs/QUICKSTART.md - Step-by-step getting started guide
  - docs/API.md - Complete API reference
  - docs/EXAMPLES.md - Usage examples and patterns
  - docs/ERRORS.md - Error handling guide with troubleshooting
  - All documentation files verified and complete

### Phase 8 (Completed)
- ✅ Rate limiting implementation
  - Rate limit table created (`triggers-api-rate-limits-{stage}`)
  - Database functions: `check_rate_limit()`, `increment_rate_limit()`, `get_rate_limit_for_api_key()`
  - Rate limit middleware with token bucket algorithm
  - Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
  - 429 error responses with `Retry-After` header
  - Configurable per API key (default: 1000 requests/min)
  - Seed script updated with `--rate-limit` parameter
- ✅ Bulk operations implementation
  - Bulk operation models: `BulkEventCreate`, `BulkEventAcknowledge`, `BulkEventDelete`, `BulkEventResponse`, `BulkItemError`
  - Database functions: `bulk_create_events()`, `bulk_acknowledge_events()`, `bulk_delete_events()`
  - Three bulk endpoints: `POST /v1/events/bulk`, `POST /v1/events/bulk/ack`, `DELETE /v1/events/bulk`
  - Partial success handling with detailed error reporting
  - Idempotency support for bulk create
  - Batch size limit: 25 items per request
- ✅ Advanced filtering implementation
  - New query parameters: `created_after`, `created_before`, `priority`, `metadata_key`, `metadata_value`
  - Enhanced `query_pending_events()` with filter expression building
  - Date range filtering (ISO 8601 timestamps)
  - Priority filtering (low, normal, high)
  - Metadata field filtering (exact match)
  - Filter validation and error handling
- ✅ IP allowlisting implementation
  - IP validation utilities: `validate_ip_format()`, `validate_cidr_format()`, `ip_matches_allowlist()`, `extract_client_ip()`
  - IP validation middleware with proxy header handling
  - CIDR notation support for IP ranges
  - Backward compatible (empty list = allow all IPs)
  - Seed script updated with `--allowed-ips` parameter
  - `ForbiddenError` exception (403) for blocked IPs
- ✅ Middleware integration
  - IP validation middleware (after auth, before rate limit)
  - Rate limit middleware (after IP validation, before endpoints)
  - Proper middleware ordering maintained
- ✅ Testing
  - Unit tests created for rate limiting, bulk operations, and IP validation
  - Test coverage for new features
  - All existing tests still passing (123+ tests)

### Phase 10 (Completed)
- ✅ Webhook Support
  - DynamoDB webhooks table with GSI for active webhook queries
  - SQS queues (main queue + DLQ) for async webhook delivery
  - Lambda handler for webhook delivery with retry logic (max 3 retries, exponential backoff)
  - CRUD endpoints: POST /v1/webhooks, GET /v1/webhooks, GET /v1/webhooks/{id}, PUT /v1/webhooks/{id}, DELETE /v1/webhooks/{id}
  - Test endpoint: POST /v1/webhooks/{id}/test
  - Event creation integration: Automatic webhook triggering on event creation
  - Frontend UI: WebhookList and WebhookForm components with full CRUD operations
  - HMAC signature generation and verification
  - Documentation: docs/WEBHOOKS.md with examples and best practices
- ✅ Analytics Dashboard
  - DynamoDB Analytics table with TTL (30 days retention)
  - DynamoDB Streams integration for real-time event processing
  - Lambda function for analytics aggregation (hourly and daily metrics)
  - Analytics endpoints: GET /v1/analytics, GET /v1/analytics/summary, GET /v1/analytics/export
  - Metrics: Event volume, source distribution, event type distribution
  - Frontend API integration ready for UI updates
- ✅ Additional SDKs
  - TypeScript SDK: Full type support, HMAC signing, error handling
  - Go SDK: Complete client implementation with HMAC signing support
  - Both SDKs support all API endpoints and request signing
  - Documentation: README files for both SDKs
- ✅ API Key Rotation
  - Database schema updates: version, status, previous_version, expires_at, rotated_at fields
  - Rotation logic: create_webhook(), generate_api_key(), get_api_key_versions() functions
  - Rotation endpoint: POST /v1/api-keys/{key_id}/rotate
  - Versions endpoint: GET /v1/api-keys/{key_id}/versions
  - Lambda function for automatic key expiration (daily cleanup)
  - Migration script: scripts/migrate_api_keys.py
  - Auth updates: Support for "rotating" status and expiration date checking
- ✅ Request Signing (HMAC)
  - Middleware: Optional signature validation (ENABLE_REQUEST_SIGNING env var)
  - Signature format: HMAC-SHA256 of method, path, query, timestamp, body_hash
  - SDK support: Python, JavaScript, TypeScript, Go clients all support signing
  - Backward compatible: Unsigned requests still work (fail-open)
  - Documentation: docs/SECURITY.md with examples
- ✅ Chaos Engineering
  - Middleware: Random delay and error injection
  - Configuration: Environment variables (CHAOS_ENABLED, CHAOS_ERROR_RATE, CHAOS_DELAY_RATE)
  - Error codes: 500, 503, 504 injection
  - Decorators: inject_chaos_delay(), inject_chaos_error() for testing
  - Tests: tests/chaos/test_chaos.py
  - Documentation: docs/CHAOS_ENGINEERING.md
  - Safety: Disabled by default, never enabled in production

### Phase 9 (Completed)
- ✅ Architecture documentation created (docs/ARCHITECTURE.md)
  - System architecture diagram (Mermaid)
  - Component architecture diagram
  - Data flow diagram
  - Deployment architecture diagram
  - Request flow diagram
  - Component descriptions with code references
  - Design patterns documentation
- ✅ Troubleshooting guide created (docs/TROUBLESHOOTING.md)
  - Common error messages with solutions
  - API key issues troubleshooting
  - DynamoDB connection issues
  - CORS issues
  - Rate limiting issues
  - Performance issues
  - Debugging tips and workflows
- ✅ Performance tuning guide created (docs/PERFORMANCE.md)
  - Performance best practices
  - Batch operations usage
  - Filtering optimization
  - Pagination best practices
  - Connection pooling
  - Caching strategies
  - Performance benchmarks
- ✅ Retry logic documentation added
  - Added retry patterns section to docs/EXAMPLES.md
  - Python retry examples (with tenacity and manual)
  - JavaScript retry examples
  - Retry with idempotency key examples
  - Updated examples/python/examples/error_handling.py
  - Updated examples/javascript/examples/error-handling.js
- ✅ API versioning strategy documented
  - Added versioning section to docs/API.md
  - Added versioning section to README.md
  - Versioning policy, migration guide, and deprecation timeline
- ✅ Lambda provisioned concurrency configured
  - Added ProvisionedConcurrency parameter to template.yaml
  - Configured AutoPublishAlias: live
  - Added ProvisionedConcurrencyConfig
  - Documented cost implications in README
  - SAM template validated successfully
- ✅ Documentation review and testing
  - All files created and updated
  - Code examples syntax validated
  - Documentation links verified
  - Documentation index updated

## Next Steps

### Future Phases Planning (Completed 2025-11-11)

**PRD Planning Completed:**
- ✅ Phase 7: Observability & Performance PRD created
- ✅ Phase 8: API Enhancements & Developer Experience PRD created
- ✅ Phase 9: Documentation & Quick Wins PRD created
- ✅ Phase 10: Advanced Features & Security PRD created
- ✅ Feature complexity ranking document created
- ✅ Feature implementation guide created
- ✅ PRD implementation strategy document created

**All PRDs can be implemented in parallel:**
- PRD 7: Observability & Performance (2-3 weeks) - Backend infrastructure
- PRD 8: API Enhancements (2-3 weeks) - API features
- PRD 9: Documentation & Quick Wins (1 week) - Documentation and config
- PRD 10: Advanced Features & Security (6-8 weeks) - Strategic features

**Key Features Planned:**
- Rate limiting, bulk operations, advanced filtering, IP allowlisting
- Structured logging, CloudWatch metrics, GSI optimization, load testing
- Architecture docs, troubleshooting guide, retry logic docs, Lambda concurrency
- Webhooks, analytics dashboard, additional SDKs, API key rotation, request signing, chaos engineering

### Immediate Next Steps (Optional)

1. **Implement Future Phases**
   - Choose which PRD to implement first (recommend PRD 9 for quick wins)
   - PRDs can be implemented in parallel by different teams
   - See `planning/PRD_IMPLEMENTATION_STRATEGY.md` for details

2. **CI/CD Setup**
   - Automated testing pipeline
   - Deployment automation
   - Test reporting

3. **Documentation Maintenance**
   - Keep documentation up to date with code changes
   - Add more integration examples as needed

## Active Decisions and Considerations

### Implementation Decisions Made

1. **Pagination Total Field:** Removed from response (DynamoDB limitation)
2. **Idempotency Key:** ✅ Implemented in Phase 4 - Uses separate DynamoDB table with 24-hour TTL
3. **Table Creation:** Auto-create on application startup (idempotent)
4. **Request ID:** Use UUID v4, lowercase string format
5. **Timestamps:** ISO 8601 UTC with Z suffix, include microseconds
6. **Error Handling:** Standardized format with request ID always included
7. **CORS:** Not needed for Phase 1 (local development only)

### Open Questions / Pending Decisions

- None at this time (all critical decisions documented in PRDs)

### Critical Implementation Notes

From `IMPLEMENTATION_NOTES.md`, key areas to watch:

1. **Pagination:** No total count, cursor-based only
2. **Filtering:** FilterExpression applied after query (affects pagination)
3. **Idempotency:** ✅ Implemented in Phase 4 - Separate DynamoDB table with conditional writes
4. **Table Creation:** Auto-create on startup, idempotent (includes idempotency table)
5. **Request ID:** Middleware pattern for tracking
6. **Error Handlers:** Custom exception classes with standardized format
7. **Pydantic Validation:** Strict mode, reject unknown fields

## Current Phase Details

### Phase 1: Core API Backend (P0)

**Goal:** Working API with all P0 endpoints, testable locally

**Endpoints to Implement:**
- GET /v1/health
- POST /v1/events
- GET /v1/inbox
- POST /v1/events/{id}/ack
- DELETE /v1/events/{id}

**Key Features:**
- FastAPI application
- DynamoDB Local integration
- API key authentication (hardcoded for MVP)
- Request ID tracking
- Basic error handling

**Success Criteria:** ✅ All Met
- ✅ All 4 P0 endpoints implemented and functional
- ✅ Health check endpoint working
- ✅ Events stored in DynamoDB Local
- ✅ API key authentication functional
- ✅ Request ID tracking implemented
- ✅ Testable with cURL/Postman locally
- ✅ Pagination and filtering working
- ✅ Error handling with proper status codes
- ✅ Conditional updates preventing double-acknowledgment

## Workflow Context

### Development Workflow

1. **Local Development:**
   - Use DynamoDB Local (Docker)
   - FastAPI with auto-reload
   - Test with cURL/Postman

2. **Testing:**
   - Manual testing in Phase 1
   - Automated testing in Phase 3

3. **Deployment:**
   - Local only in Phase 1
   - AWS deployment in Phase 2

### Testing Approach

**Phase 1:** Manual testing with cURL/Postman  
**Phase 3:** ✅ Comprehensive automated testing complete
- ✅ Unit tests: 74 tests, 84% coverage (exceeds 80% requirement)
- ✅ Integration tests: Full event lifecycle, pagination, filtering
- ✅ E2E tests: Tests against real server (require DynamoDB Local)
- ✅ Playwright MCP tests: HTTP-based API tests using httpx
- ✅ Test automation: Single-command test execution scripts

## Important Reminders

### For Implementation

1. **Follow PRD Specifications:** All endpoints must match PRD exactly
2. **Request ID:** Always include in responses (success and error)
3. **Error Format:** Use standardized error response format
4. **Validation:** Strict Pydantic validation, reject unknown fields
5. **Pagination:** No total count, cursor-based only
6. **Idempotency:** ✅ Implemented in Phase 4 - Extract from metadata.idempotency_key, uses separate DynamoDB table

### For Code Quality

1. **Type Hints:** Use Python type hints throughout
2. **Docstrings:** Document all functions and classes
3. **Error Handling:** Comprehensive error handling with proper status codes
4. **Logging:** Structured logging with request IDs
5. **Code Organization:** Follow project structure in PRD

## Blockers / Issues

**Current Blockers:**
- None - Phase 3 completed successfully

**Issues Resolved During Phase 1:**
1. ✅ DynamoDB reserved keywords (status, source, event_type) - resolved by using ExpressionAttributeNames
2. ✅ Request validation error formatting - resolved by adding RequestValidationError handler
3. ✅ FastAPI Request dependency injection - resolved by removing Depends() wrapper

**Issues Resolved During Phase 2:**
1. ✅ SAM CLI handler validation issue - bypassed by using AWS CLI directly
2. ✅ Python packages installed in repo root - cleaned up and added to .gitignore
3. ✅ CORS configuration - added FastAPI CORS middleware
4. ✅ Dual-mode authentication - implemented local/AWS mode switching
5. ✅ Lambda deployment package - fixed x86_64 binary compatibility using Docker
6. ✅ Lambda package size - deployed via S3 due to >50MB size limit
7. ✅ DynamoDB credentials - fixed to use IAM role in Lambda (not hardcoded)

**Issues Resolved During Phase 3:**
1. ✅ Moto import syntax - Updated to use `mock_aws` instead of deprecated `mock_dynamodb`
2. ✅ Test fixture dependencies - Fixed integration test fixtures to properly patch database
3. ✅ Pydantic validation status codes - Updated tests to handle both 400 and 422 status codes
4. ✅ Database test mocking - Fixed monkeypatch usage for module-level table references

**Issues Resolved During Phase 4:**
1. ✅ Test failures in test_main.py - Fixed asyncio usage (changed pytest.asyncio.run to asyncio.run)
2. ✅ Error handler tests - Updated to work with enhanced error message format

**Issues Resolved During Production Deployment (2025-11-11):**
1. ✅ **CORS Error:** Frontend was calling wrong API URL (missing `/v1` prefix)
   - **Fix:** Updated `frontend/scripts/deploy.sh` to use correct URL: `https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod/v1`
   - **Result:** CORS errors resolved, frontend successfully communicates with API
2. ✅ **Event Not Found Error:** DynamoDB scan with `Limit=1` only checked first item
   - **Fix:** Implemented pagination in `get_event()` to scan through all items until event found
   - **Files Modified:** `src/database.py` - Added pagination loop with `ConsistentRead=True`
   - **Result:** Events can now be found and acknowledged correctly
3. ✅ **Missing Scan Permission:** Lambda IAM role lacked `dynamodb:Scan` permission
   - **Fix:** Added inline IAM policy `AllowDynamoDBScan` to Lambda execution role
   - **Result:** Lambda can now perform scan operations on Events table
4. ✅ **API Key Validation Errors:** Generic exception handler catching UnauthorizedError
   - **Fix:** Improved error handling in `src/auth.py` - explicitly re-raise UnauthorizedError, added logging
   - **Result:** Better error messages and proper exception propagation
5. ✅ **SPA Routing 404:** Direct access to routes like `/inbox` returned 404
   - **Fix:** Configured S3 error document and verified CloudFront custom error responses (403/404 → 200 → `/index.html`)
   - **Result:** All client-side routes work correctly, no more 404 errors

**Known Issues:**
- Integration tests require proper table setup (some tests may need DynamoDB Local)
- Playwright/E2E tests require running API server (expected behavior)
- `get_event()` uses scan operation with pagination (acceptable for MVP, could be optimized with GSI for production scale)

## Resources

### Documentation
- Main PRD: `PRD.md`
- Phase 1-6 PRDs: `planning/PRDs/phase-1-core-api.md` through `phase-6-frontend-dashboard.md`
- **Future Phases PRDs:** `planning/PRDs/phase-7-observability-performance.md` through `phase-10-advanced-features-security.md`
- Feature Planning: `planning/FEATURE_COMPLEXITY_RANKING.md`, `planning/FEATURE_IMPLEMENTATION_GUIDE.md`
- Implementation Strategy: `planning/PRD_IMPLEMENTATION_STRATEGY.md`
- Architecture: `planning/architecture.mmd`

### External Resources
- FastAPI Documentation
- DynamoDB Local Documentation
- AWS SAM Documentation
- Pydantic Documentation

---

**Document Status:** Active  
**Last Updated:** 2025-11-11 (Phase 10: Advanced Features & Security completed)

