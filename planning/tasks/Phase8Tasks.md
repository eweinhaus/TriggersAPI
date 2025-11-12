# Phase 8: API Enhancements & Developer Experience - Task List

**Phase:** 8 of 10  
**Priority:** P1 (Should Have)  
**Status:** 🔄 Not Started  
**Created:** 2025-11-11  
**Estimated Duration:** 2-3 weeks  
**Dependencies:** Phase 1-6 (Core API complete)

---

## Overview

This task list covers the implementation of Phase 8: API Enhancements & Developer Experience. The goal is to enhance the API with production-ready features including rate limiting, bulk operations, advanced filtering, and IP allowlisting.

**Key Deliverables:**
- Rate limiting with configurable limits per API key
- Bulk operations (create, acknowledge, delete multiple events)
- Advanced event filtering (date range, metadata, priority)
- IP allowlisting for API keys with CIDR support
- Comprehensive test coverage for all new features
- Updated documentation

---

## Task Breakdown

### 1. Rate Limiting Implementation

#### 1.1 Rate Limit Table Setup
- [ ] Create rate limit table definition in `scripts/create_tables.py`
  - Table name: `triggers-api-rate-limits-{stage}`
  - Partition Key: `api_key` (String)
  - Sort Key: `window_start` (Number, Unix timestamp)
  - TTL attribute: `ttl` (1 hour from window_start)
  - Billing mode: On-demand
- [ ] Add table creation to auto-create on startup (if not exists)
- [ ] Update `scripts/create_tables.py` to include rate limit table
- [ ] Test table creation locally and in AWS

#### 1.2 Rate Limit Database Functions
- [ ] Add rate limit tracking functions to `src/database.py`
  - `check_rate_limit(api_key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]`
    - Returns: (allowed, remaining, reset_timestamp)
    - Implement token bucket algorithm (recommended) or sliding window
  - `increment_rate_limit(api_key: str, window_start: int, limit: int) -> dict`
    - Update or create rate limit record
    - Use conditional writes to prevent race conditions
- [ ] Add helper function to calculate window start timestamp
- [ ] Handle DynamoDB conditional write failures gracefully
- [ ] Add unit tests for rate limit functions (moto mocking)

#### 1.3 Rate Limit Middleware
- [ ] Create `src/middleware/` directory with `__init__.py`
- [ ] Create `src/middleware/rate_limit.py` with rate limit middleware
  - Extract API key from request (after auth middleware)
  - Get rate limit config from API key (default: 1000/min)
  - Check rate limit using database functions
  - Add rate limit headers to response:
    - `X-RateLimit-Limit`: Maximum requests allowed
    - `X-RateLimit-Remaining`: Remaining requests in window
    - `X-RateLimit-Reset`: Unix timestamp when limit resets
  - Return 429 with `Retry-After` header if limit exceeded
  - Raise `RateLimitExceededError` exception
- [ ] Ensure middleware runs after authentication but before endpoint handlers
- [ ] Add request ID to rate limit error responses
- [ ] Log rate limit violations with request ID

#### 1.4 API Key Model Updates
- [ ] Update API Keys table schema to include `rate_limit` field (optional)
  - Default: 1000 requests per minute
  - Stored as integer (requests per minute)
- [ ] Update `src/models.py` with API key model including rate limit
- [ ] Update `src/database.py` functions to read rate limit from API key
- [ ] Update `scripts/seed_api_keys.py` to accept `--rate-limit` parameter
- [ ] Ensure backward compatibility (existing keys use default limit)

#### 1.5 Rate Limiting Integration
- [ ] Add rate limit middleware to `src/main.py`
  - Import rate limit middleware
  - Add middleware after auth middleware, before endpoints
  - Ensure proper middleware ordering
- [ ] Update exception handler for `RateLimitExceededError` (if not exists)
  - Return 429 status code
  - Include `Retry-After` header (seconds until reset)
  - Include rate limit headers in error response
- [ ] Test middleware with various rate limit configurations

#### 1.6 Rate Limiting Tests
- [ ] Create `tests/unit/test_rate_limit.py`
  - Test rate limit middleware logic
  - Test token bucket algorithm correctness
  - Test rate limit header generation
  - Test 429 error response format
  - Test `Retry-After` header calculation
- [ ] Create `tests/integration/test_rate_limit_integration.py`
  - Test rate limiting in full request flow
  - Test rate limit state persistence
  - Test rate limit reset behavior
  - Test concurrent requests (rate limit accuracy)
- [ ] Add rate limit tests to existing test suites
- [ ] Verify test coverage >80% for rate limiting code

---

### 2. Bulk Operations Implementation

#### 2.1 Bulk Request/Response Models
- [ ] Update `src/models.py` with bulk operation models
  - `BulkEventCreate` model:
    - `items: List[EventCreate]` with `Field(max_length=25)`
    - Validation: Ensure items list is not empty
  - `BulkEventAcknowledge` model:
    - `event_ids: List[str]` with `Field(max_length=25)`
    - Validation: Ensure event_ids list is not empty
  - `BulkEventDelete` model:
    - `event_ids: List[str]` with `Field(max_length=25)`
    - Validation: Ensure event_ids list is not empty
  - `BulkItemError` model:
    - `index: int` - Index of failed item in request
    - `error: dict` - Error details (code, message)
  - `BulkEventResponse` model:
    - `successful: List[EventResponse]` - Successfully processed items
    - `failed: List[BulkItemError]` - Failed items with errors
    - `request_id: str` - Request ID for correlation
- [ ] Add validation for bulk request models
- [ ] Add unit tests for bulk models

#### 2.2 Bulk Create Endpoint
- [ ] Add `POST /v1/events/bulk` endpoint to `src/endpoints/events.py`
  - Accept `BulkEventCreate` request body
  - Validate batch size (max 25 items)
  - Process items in batches (DynamoDB batch_write_item, max 25 per batch)
  - Handle idempotency keys for each item (if provided)
  - Collect successful and failed items
  - Return `BulkEventResponse` with partial success
- [ ] Implement batch processing logic in `src/database.py`
  - `bulk_create_events(events: List[dict], api_key: str) -> tuple[List[dict], List[dict]]`
  - Use DynamoDB `batch_write_item` with proper error handling
  - Handle unprocessed items (retry logic if needed)
  - Return tuple: (successful_events, failed_events)
- [ ] Handle idempotency for bulk create
  - Check idempotency key for each item before creation
  - Return existing event if idempotency key found
  - Store idempotency key mapping for new events
- [ ] Add proper error handling and logging
- [ ] Include request ID in response

#### 2.3 Bulk Acknowledge Endpoint
- [ ] Add `POST /v1/events/bulk/ack` endpoint to `src/endpoints/events.py`
  - Accept `BulkEventAcknowledge` request body
  - Validate batch size (max 25 event IDs)
  - Process acknowledgments in batches
  - Handle partial failures (some events may not exist or already acknowledged)
  - Return `BulkEventResponse` with partial success
- [ ] Implement batch acknowledgment logic in `src/database.py`
  - `bulk_acknowledge_events(event_ids: List[str], api_key: str) -> tuple[List[dict], List[dict]]`
  - Use DynamoDB `batch_get_item` to fetch events
  - Use conditional updates to prevent double-acknowledgment
  - Handle events that don't exist or are already acknowledged
  - Return tuple: (successful_acknowledgments, failed_acknowledgments)
- [ ] Add proper error handling for each failed item
- [ ] Include request ID in response

#### 2.4 Bulk Delete Endpoint
- [ ] Add `DELETE /v1/events/bulk` endpoint to `src/endpoints/events.py`
  - Accept `BulkEventDelete` request body
  - Validate batch size (max 25 event IDs)
  - Process deletions in batches
  - Handle partial failures (some events may not exist)
  - Return `BulkEventResponse` with partial success
- [ ] Implement batch deletion logic in `src/database.py`
  - `bulk_delete_events(event_ids: List[str], api_key: str) -> tuple[List[str], List[dict]]`
  - Use DynamoDB `batch_write_item` with DeleteRequest
  - Handle events that don't exist gracefully
  - Return tuple: (successful_deletions, failed_deletions)
- [ ] Add proper error handling for each failed item
- [ ] Include request ID in response

#### 2.5 Bulk Operations Error Handling
- [ ] Implement detailed error reporting for failed items
  - Include index of failed item in request
  - Include error code and message for each failure
  - Preserve original error context
- [ ] Handle DynamoDB batch operation limitations
  - Process in chunks of 25 (DynamoDB limit)
  - Handle unprocessed items (retry if needed)
  - Log batch operation failures
- [ ] Ensure request ID is included in all bulk responses
- [ ] Add logging for bulk operation metrics (success rate, failure rate)

#### 2.6 Bulk Operations Tests
- [ ] Create `tests/unit/test_bulk_operations.py`
  - Test bulk create endpoint
  - Test bulk acknowledge endpoint
  - Test bulk delete endpoint
  - Test batch size validation (max 25)
  - Test partial success handling
  - Test idempotency for bulk create
  - Test error reporting for failed items
- [ ] Create `tests/integration/test_bulk_operations_integration.py`
  - Test bulk operations end-to-end
  - Test bulk operations with mixed success/failure
  - Test bulk operations with large batches (chunking)
  - Test bulk operations with idempotency keys
- [ ] Add bulk operation tests to existing test suites
- [ ] Verify test coverage >80% for bulk operations code

---

### 3. Advanced Event Filtering Implementation

#### 3.1 Filter Models
- [ ] Update `src/models.py` with filter models
  - `EventFilter` model (optional query parameters):
    - `created_after: Optional[datetime]` - ISO 8601 timestamp
    - `created_before: Optional[datetime]` - ISO 8601 timestamp
    - `priority: Optional[Literal["low", "normal", "high"]]` - Priority level
    - `metadata: Optional[dict]` - Metadata field filters (key-value pairs)
  - Add validation for date ranges (created_after < created_before)
  - Add validation for metadata filter format
- [ ] Add unit tests for filter models

#### 3.2 Inbox Endpoint Query Parameters
- [ ] Update `GET /v1/inbox` endpoint in `src/endpoints/inbox.py`
  - Add new query parameters:
    - `created_after: Optional[str]` - ISO 8601 timestamp string
    - `created_before: Optional[str]` - ISO 8601 timestamp string
    - `priority: Optional[str]` - Priority level (low, normal, high)
    - `metadata.{key}: Optional[str]` - Metadata field value (exact match)
  - Parse and validate query parameters
  - Convert to `EventFilter` model
  - Pass filters to database query function
- [ ] Update endpoint documentation (OpenAPI/Swagger)
  - Add parameter descriptions
  - Add example values
  - Document filter combination behavior

#### 3.3 Database Filter Logic
- [ ] Enhance `query_pending_events()` in `src/database.py`
  - Accept `EventFilter` parameter
  - Build DynamoDB FilterExpression dynamically based on filters
  - Support multiple filter conditions (AND logic)
  - Handle date range filters (created_after, created_before)
  - Handle priority filter (metadata.priority = value)
  - Handle metadata field filters (metadata.{key} = value)
  - Optimize filter expressions for performance
- [ ] Implement filter expression builder function
  - `build_filter_expression(filters: EventFilter) -> dict`
  - Returns FilterExpression, ExpressionAttributeNames, ExpressionAttributeValues
  - Handle empty filters (no filter expression)
  - Handle complex filter combinations
- [ ] Consider additional GSI for common filter combinations (if needed)
  - Evaluate performance impact
  - Add GSI if filter performance < 200ms p95 requirement not met

#### 3.4 Filter Validation and Error Handling
- [ ] Add validation for filter parameters
  - Validate date format (ISO 8601)
  - Validate date range (created_after < created_before)
  - Validate priority enum values
  - Validate metadata key format
- [ ] Add error handling for invalid filters
  - Return 400 Bad Request with clear error message
  - Include field names and validation errors
  - Include request ID in error response
- [ ] Add logging for filter usage (for analytics)

#### 3.5 Advanced Filtering Tests
- [ ] Create `tests/unit/test_filtering.py`
  - Test filter expression building
  - Test date range filters
  - Test priority filters
  - Test metadata field filters
  - Test filter combinations
  - Test filter validation
- [ ] Create `tests/integration/test_filtering_integration.py`
  - Test filtering in inbox endpoint
  - Test filter combinations end-to-end
  - Test filter performance (< 200ms p95)
  - Test filter with pagination
  - Test filter with existing source/event_type filters
- [ ] Add filtering tests to existing test suites
- [ ] Verify test coverage >80% for filtering code

---

### 4. IP Allowlisting Implementation

#### 4.1 API Keys Table Schema Update
- [ ] Update API Keys table schema to include `allowed_ips` field
  - Field type: List of strings (optional)
  - Default: Empty list (allows all IPs - backward compatible)
  - Support IPv4 and IPv6 addresses
  - Support CIDR notation (e.g., "192.168.1.0/24")
- [ ] Update `src/models.py` with API key model including `allowed_ips`
  - `allowed_ips: Optional[List[str]]` - List of allowed IPs/CIDR ranges
  - Add validation for IP/CIDR format
- [ ] Update `src/database.py` functions to read `allowed_ips` from API key
- [ ] Ensure backward compatibility (existing keys without field allow all IPs)

#### 4.2 IP Validation Utilities
- [ ] Create IP validation utility functions
  - `validate_ip_format(ip: str) -> bool` - Validate IP address format
  - `validate_cidr_format(cidr: str) -> bool` - Validate CIDR notation format
  - `ip_matches_allowlist(client_ip: str, allowed_ips: List[str]) -> bool`
    - Check if client IP matches any allowed IP or CIDR range
    - Support IPv4 and IPv6
    - Handle CIDR notation (use ipaddress library)
- [ ] Add unit tests for IP validation utilities
- [ ] Handle edge cases (invalid IPs, malformed CIDR, etc.)

#### 4.3 IP Extraction from Request
- [ ] Create IP extraction utility function
  - `extract_client_ip(request: Request) -> str`
  - Check `X-Forwarded-For` header (first IP in chain)
  - Check `X-Real-IP` header
  - Fall back to `request.client.host` if headers not present
  - Handle proxy chains correctly (take first IP)
  - Handle IPv6 addresses
- [ ] Add unit tests for IP extraction
- [ ] Test with various proxy scenarios (API Gateway, CloudFront, etc.)

#### 4.4 IP Validation Middleware
- [ ] Create `src/middleware/ip_validation.py` with IP validation middleware
  - Extract client IP from request
  - Get API key from request (after auth middleware)
  - Get `allowed_ips` from API key (empty list = allow all)
  - Validate client IP against allowlist
  - Return 403 Forbidden if IP not allowed
  - Raise `ForbiddenError` exception (or create new exception)
  - Log blocked IP attempts with request ID
- [ ] Ensure middleware runs after authentication but before endpoint handlers
- [ ] Add request ID to IP validation error responses

#### 4.5 IP Validation Integration
- [ ] Add IP validation middleware to `src/main.py`
  - Import IP validation middleware
  - Add middleware after auth middleware, before rate limit middleware
  - Ensure proper middleware ordering
- [ ] Update exception handler for IP validation errors
  - Return 403 Forbidden status code
  - Include clear error message
  - Include request ID in error response
- [ ] Update `src/auth.py` if needed (integrate IP check into auth flow)
- [ ] Test middleware with various IP configurations

#### 4.6 Seed Script Updates
- [ ] Update `scripts/seed_api_keys.py` to accept IP allowlist
  - Add `--allowed-ips` parameter (comma-separated list)
  - Parse IP/CIDR list from parameter
  - Validate IP/CIDR formats
  - Store in API Keys table
- [ ] Update seed script documentation
- [ ] Test seed script with IP allowlist

#### 4.7 IP Allowlisting Tests
- [ ] Create `tests/unit/test_ip_validation.py`
  - Test IP extraction from request headers
  - Test IP validation logic
  - Test CIDR notation matching
  - Test IPv4 and IPv6 support
  - Test empty allowlist (allow all)
  - Test IP validation middleware
- [ ] Create `tests/integration/test_ip_validation_integration.py`
  - Test IP allowlisting in full request flow
  - Test various IP configurations
  - Test CIDR ranges
  - Test blocked IP attempts (403 response)
  - Test allowed IP requests (200 response)
  - Test backward compatibility (no allowlist = allow all)
- [ ] Add IP validation tests to existing test suites
- [ ] Verify test coverage >80% for IP validation code

---

### 5. Testing & Validation

#### 5.1 Comprehensive Test Suite
- [ ] Run full test suite to ensure no regressions
  - Unit tests: All passing
  - Integration tests: All passing
  - E2E tests: All passing
- [ ] Verify test coverage >80% for all new code
- [ ] Add tests for edge cases and error scenarios
- [ ] Test backward compatibility (existing API keys, existing endpoints)

#### 5.2 Performance Testing
- [ ] Test rate limiting performance (overhead < 10ms per request)
- [ ] Test bulk operations performance (25 items < 500ms)
- [ ] Test advanced filtering performance (< 200ms p95)
- [ ] Test IP validation performance (overhead < 5ms per request)
- [ ] Document performance benchmarks

#### 5.3 Integration Testing
- [ ] Test all features together (rate limiting + bulk ops + filtering + IP allowlisting)
- [ ] Test middleware ordering (auth → IP → rate limit → endpoints)
- [ ] Test error handling across all features
- [ ] Test with real DynamoDB (local and AWS)

---

### 6. Documentation Updates

#### 6.1 API Documentation
- [ ] Update `docs/API.md` with new endpoints and parameters
  - Rate limiting headers documentation
  - Bulk operations endpoints (POST /v1/events/bulk, POST /v1/events/bulk/ack, DELETE /v1/events/bulk)
  - Advanced filtering query parameters
  - IP allowlisting documentation
- [ ] Update OpenAPI/Swagger documentation in `src/main.py`
  - Add rate limit headers to all endpoint responses
  - Add bulk operation endpoints with examples
  - Add filter query parameters with descriptions
  - Add IP allowlisting information

#### 6.2 Examples Documentation
- [ ] Update `docs/EXAMPLES.md` with bulk operation examples
  - Bulk create example
  - Bulk acknowledge example
  - Bulk delete example
  - Partial success handling example
- [ ] Add advanced filtering examples
  - Date range filtering
  - Priority filtering
  - Metadata filtering
  - Combined filters
- [ ] Add rate limiting examples
  - Rate limit header interpretation
  - Handling 429 errors
  - Retry logic with Retry-After header
- [ ] Add IP allowlisting examples
  - CIDR notation examples
  - IP configuration examples

#### 6.3 README Updates
- [ ] Update `README.md` with new features
  - Rate limiting section
  - Bulk operations section
  - Advanced filtering section
  - IP allowlisting section
- [ ] Update feature list
- [ ] Update quick start examples if needed

#### 6.4 Error Documentation
- [ ] Update `docs/ERRORS.md` with new error scenarios
  - Rate limit exceeded (429)
  - IP not allowed (403)
  - Bulk operation partial failures
  - Filter validation errors

---

### 7. Deployment & Migration

#### 7.1 Database Migration
- [ ] Create rate limit table in production
  - Use `scripts/create_tables.py` or manual creation
  - Verify table creation in AWS
- [ ] Update API Keys table schema (add `allowed_ips` field)
  - Ensure backward compatibility (existing keys work without field)
  - No migration needed (DynamoDB is schema-less)
- [ ] Update API Keys table schema (add `rate_limit` field)
  - Ensure backward compatibility (existing keys use default limit)
  - No migration needed (DynamoDB is schema-less)

#### 7.2 Lambda Deployment
- [ ] Update Lambda function code with all Phase 8 changes
- [ ] Update Lambda IAM permissions if needed
  - Verify DynamoDB permissions for rate limit table
- [ ] Deploy Lambda function to AWS
- [ ] Verify deployment success

#### 7.3 Testing in Production
- [ ] Test rate limiting in production environment
- [ ] Test bulk operations in production environment
- [ ] Test advanced filtering in production environment
- [ ] Test IP allowlisting in production environment
- [ ] Monitor CloudWatch logs for errors
- [ ] Verify all features work correctly

---

## Success Criteria

### Rate Limiting
- ✅ Rate limiting works correctly with configurable limits
- ✅ Rate limit headers included in all responses
- ✅ 429 errors returned when limit exceeded with Retry-After header
- ✅ Rate limit state tracked accurately in DynamoDB
- ✅ Performance overhead < 10ms per request

### Bulk Operations
- ✅ Bulk create endpoint works correctly
- ✅ Bulk acknowledge endpoint works correctly
- ✅ Bulk delete endpoint works correctly
- ✅ Partial success handled properly (successful + failed items)
- ✅ Batch size limits enforced (max 25 items)
- ✅ Idempotency works for bulk create

### Advanced Filtering
- ✅ All filter options work correctly (date range, metadata, priority)
- ✅ Filters can be combined
- ✅ Filter performance < 200ms p95
- ✅ Filter validation works correctly

### IP Allowlisting
- ✅ IP allowlisting works correctly
- ✅ CIDR notation supported
- ✅ Empty list allows all IPs (backward compatible)
- ✅ 403 Forbidden returned for blocked IPs
- ✅ IP extraction handles proxy headers correctly

### Overall
- ✅ All tests passing (>80% coverage)
- ✅ No regressions in existing functionality
- ✅ Documentation updated
- ✅ Production deployment successful
- ✅ All features working in production

---

## Notes

### Implementation Order
1. Rate Limiting (Week 1, Days 1-3) - Foundation for other features
2. Bulk Operations (Week 1, Days 4-5) - Independent feature
3. Advanced Filtering (Week 2, Days 1-3) - Enhances existing endpoint
4. IP Allowlisting (Week 2, Days 4-5) - Security feature

### Key Considerations
- **Backward Compatibility:** All changes must be backward compatible with existing API keys and endpoints
- **Performance:** Monitor performance impact of each feature, especially rate limiting
- **Error Handling:** Comprehensive error handling for all new features
- **Testing:** Thorough testing including edge cases and error scenarios
- **Documentation:** Complete documentation for all new features

### Dependencies
- Phase 1-6 must be complete (core API, authentication, database)
- DynamoDB tables must exist
- API key authentication must be working

### Risks & Mitigation
- **Rate Limit Performance:** Use efficient algorithm, cache state, monitor performance
- **Bulk Operation Complexity:** Start simple, add partial success handling incrementally
- **Filter Performance:** Optimize expressions, consider GSIs for common filters
- **IP Validation Accuracy:** Handle proxy headers correctly, test with various IP formats

---

**Document Status:** Draft  
**Last Updated:** 2025-11-11


