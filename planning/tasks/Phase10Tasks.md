# Phase 10: Advanced Features & Security - Task List

**Phase:** 10 of 10  
**Priority:** P2 (Nice to Have) / Strategic  
**Status:** 🔄 Not Started  
**Created:** 2025-11-11  
**Estimated Duration:** 6-8 weeks  
**Dependencies:** Phase 1-6 (Core API complete)  
**Note:** Features can be implemented independently in any order

---

## Overview

This task list covers Phase 10: Advanced Features & Security. The phase includes six independent features that can be implemented based on business priorities:

1. **Webhook Support** - Push-based event delivery (2 weeks)
2. **Analytics Dashboard** - Event insights and metrics (2 weeks)
3. **Additional SDKs** - TypeScript and Go clients (1 week per SDK)
4. **API Key Rotation** - Security enhancement (1 week)
5. **Request Signing (HMAC)** - Enhanced security (1 week)
6. **Chaos Engineering** - Resilience testing (1 week)

**Key Deliverables:**
- Webhook delivery system with retry logic and DLQ
- Real-time analytics dashboard with DynamoDB Streams
- TypeScript and Go SDKs matching existing SDK patterns
- API key rotation with zero-downtime transitions
- Optional HMAC request signing (backward compatible)
- Chaos engineering framework for resilience testing

---

## Feature 1: Webhook Support (2 weeks)

### 1.1 Backend Infrastructure Setup

#### 1.1.1 DynamoDB Webhooks Table
- [ ] Create `src/database.py` function to create `triggers-api-webhooks` table
  - Partition Key: `webhook_id` (String, UUID v4)
  - Attributes: `url` (String), `secret` (String), `events` (List), `is_active` (Boolean), `created_at` (String), `api_key` (String)
  - GSI: `api-key-is-active-index` (Partition: `api_key`, Sort: `is_active`, Projection: ALL)
  - Billing Mode: On-demand
- [ ] Add table creation to application startup
- [ ] Test table creation locally and in AWS

#### 1.1.2 SQS Queue Setup
- [ ] Update `template.yaml` to include:
  - SQS Queue: `triggers-api-webhook-delivery`
  - Dead Letter Queue: `triggers-api-webhook-dlq`
  - Queue visibility timeout: 30 seconds
  - DLQ max receive count: 3
- [ ] Create SQS client utilities in `src/utils.py`
  - Function to send message to webhook delivery queue
  - Function to handle DLQ messages
- [ ] Test SQS queue creation and message sending

#### 1.1.3 Lambda Function for Webhook Delivery
- [ ] Create `src/lambda_handlers/webhook_delivery.py`
  - Handler function to process SQS messages
  - HTTP POST to webhook URL
  - HMAC signature generation (`X-Webhook-Signature` header)
  - Retry logic with exponential backoff
  - Error handling and DLQ routing
- [ ] Update `template.yaml` to include webhook delivery Lambda
  - Event source: SQS queue
  - IAM permissions: SQS, DynamoDB (read webhooks), CloudWatch Logs
- [ ] Test Lambda function locally and deploy

### 1.2 Webhook Management Endpoints

#### 1.2.1 Create Webhook Endpoint
- [ ] Create `src/endpoints/webhooks.py`
- [ ] Implement `POST /v1/webhooks` endpoint:
  - Request model: `WebhookCreate` (url, events, secret)
  - Validate URL format
  - Generate `webhook_id` (UUID v4)
  - Store webhook in DynamoDB
  - Return `WebhookResponse` with webhook details
- [ ] Add authentication (API key from request)
- [ ] Add request ID tracking
- [ ] Test endpoint with cURL/Postman

#### 1.2.2 List Webhooks Endpoint
- [ ] Implement `GET /v1/webhooks` endpoint:
  - Query by `api_key` using GSI
  - Filter by `is_active` (optional query parameter)
  - Pagination support (cursor-based)
  - Return list of webhooks
- [ ] Test pagination and filtering

#### 1.2.3 Get Webhook Endpoint
- [ ] Implement `GET /v1/webhooks/{webhook_id}` endpoint:
  - Validate webhook belongs to requesting API key
  - Return webhook details
  - Return 404 if not found
- [ ] Test endpoint

#### 1.2.4 Update Webhook Endpoint
- [ ] Implement `PUT /v1/webhooks/{webhook_id}` endpoint:
  - Request model: `WebhookUpdate` (url, events, secret, is_active)
  - Validate webhook belongs to requesting API key
  - Update webhook in DynamoDB
  - Return updated webhook details
- [ ] Test endpoint

#### 1.2.5 Delete Webhook Endpoint
- [ ] Implement `DELETE /v1/webhooks/{webhook_id}` endpoint:
  - Validate webhook belongs to requesting API key
  - Delete webhook from DynamoDB
  - Return 204 No Content
- [ ] Test endpoint

#### 1.2.6 Test Webhook Endpoint
- [ ] Implement `POST /v1/webhooks/{webhook_id}/test` endpoint:
  - Send test event to webhook URL
  - Return delivery status
  - Use synchronous HTTP request (not SQS)
- [ ] Test endpoint with real webhook URL

### 1.3 Webhook Delivery Integration

#### 1.3.1 Event Creation Integration
- [ ] Update `src/endpoints/events.py` `POST /v1/events`:
  - After successful event creation, query active webhooks for API key
  - Filter webhooks by event type (support `*` wildcard)
  - Send webhook delivery message to SQS queue
  - Include event data in SQS message
- [ ] Test webhook triggering on event creation

#### 1.3.2 Webhook Delivery Logic
- [ ] Implement webhook delivery in Lambda handler:
  - Extract webhook details from SQS message
  - Generate HMAC signature: `HMAC-SHA256(payload, secret)`
  - Send HTTP POST to webhook URL with:
    - Body: Event JSON
    - Headers: `X-Webhook-Signature`, `X-Webhook-Id`, `X-Webhook-Timestamp`
  - Handle HTTP errors (4xx, 5xx)
  - Implement exponential backoff retry (max 3 retries)
  - Send to DLQ after max retries
- [ ] Test delivery with various webhook endpoints
- [ ] Test retry logic
- [ ] Test DLQ routing

### 1.4 Frontend Webhook Management UI

#### 1.4.1 Webhook List Component
- [ ] Create `frontend/src/components/WebhookList.jsx`:
  - Display list of webhooks
  - Show webhook URL, events, status
  - Add "Create Webhook" button
  - Add edit/delete actions
- [ ] Integrate with API endpoints
- [ ] Add error handling and notifications

#### 1.4.2 Webhook Form Component
- [ ] Create `frontend/src/components/WebhookForm.jsx`:
  - Form fields: URL, events (multi-select or text input), secret
  - URL validation
  - Events validation (comma-separated or array)
  - Submit handler for create/update
- [ ] Add form validation
- [ ] Test form submission

#### 1.4.3 Webhook Details Page
- [ ] Create `frontend/src/pages/WebhookDetails.jsx`:
  - Display webhook details
  - Show delivery history (if implemented)
  - Test webhook button
  - Edit/Delete actions
- [ ] Add routing for webhook details
- [ ] Test page navigation

#### 1.4.4 Webhook Management Route
- [ ] Add `/webhooks` route to frontend router
- [ ] Add navigation link to main menu
- [ ] Test routing and navigation

### 1.5 Testing

#### 1.5.1 Unit Tests
- [ ] Test webhook CRUD operations
- [ ] Test webhook delivery logic
- [ ] Test HMAC signature generation
- [ ] Test retry logic
- [ ] Test DLQ routing
- [ ] Test webhook filtering by event type

#### 1.5.2 Integration Tests
- [ ] Test webhook creation and event delivery end-to-end
- [ ] Test webhook update and re-delivery
- [ ] Test webhook deletion stops delivery
- [ ] Test retry logic with failing webhook
- [ ] Test DLQ handling

#### 1.5.3 Manual Testing
- [ ] Create webhook with real URL (e.g., webhook.site)
- [ ] Create event and verify webhook delivery
- [ ] Test webhook signature verification
- [ ] Test retry logic with temporary failures
- [ ] Test webhook management UI

### 1.6 Documentation
- [ ] Create `docs/WEBHOOKS.md`:
  - Webhook registration guide
  - Event delivery format
  - Signature verification guide
  - Retry logic explanation
  - Troubleshooting section
- [ ] Update `docs/API.md` with webhook endpoints
- [ ] Add webhook examples to `docs/EXAMPLES.md`

---

## Feature 2: Analytics Dashboard (2 weeks)

### 2.1 Backend Infrastructure Setup

#### 2.1.1 DynamoDB Streams Configuration
- [ ] Enable DynamoDB Streams on `triggers-api-events` table
  - Stream view type: NEW_AND_OLD_IMAGES
  - Update `template.yaml` to enable streams
- [ ] Test stream configuration

#### 2.1.2 Analytics Storage Table
- [ ] Create `src/database.py` function to create `triggers-api-analytics` table
  - Partition Key: `metric_date` (String, format: YYYY-MM-DD)
  - Sort Key: `metric_type` (String, e.g., "hourly", "daily")
  - Attributes: `event_count`, `source_distribution`, `event_type_distribution`, `error_count`, `performance_metrics`
  - TTL attribute: `ttl` (30 days retention)
  - Billing Mode: On-demand
- [ ] Add table creation to application startup
- [ ] Test table creation

#### 2.1.3 Stream Processing Lambda
- [ ] Create `src/lambda_handlers/analytics_processor.py`
  - Handler function to process DynamoDB Stream records
  - Aggregate events by hour/day
  - Update analytics table with aggregated data
  - Handle batch processing
- [ ] Update `template.yaml` to include analytics processor Lambda
  - Event source: DynamoDB Stream
  - IAM permissions: DynamoDB (read streams, write analytics), CloudWatch Logs
- [ ] Test Lambda function locally and deploy

### 2.2 Analytics Aggregation Logic

#### 2.2.1 Event Volume Aggregation
- [ ] Implement hourly aggregation:
  - Count events per hour
  - Store in analytics table with `metric_type="hourly"`
- [ ] Implement daily aggregation:
  - Count events per day
  - Store in analytics table with `metric_type="daily"`
- [ ] Test aggregation logic

#### 2.2.2 Source Distribution
- [ ] Aggregate events by source:
  - Count events per source per time period
  - Store in `source_distribution` attribute (JSON map)
- [ ] Test source distribution calculation

#### 2.2.3 Event Type Distribution
- [ ] Aggregate events by event type:
  - Count events per event type per time period
  - Store in `event_type_distribution` attribute (JSON map)
- [ ] Test event type distribution calculation

#### 2.2.4 Error Rate Calculation
- [ ] Track error events (if error tracking implemented):
  - Count errors per time period
  - Calculate error rate percentage
  - Store in `error_count` and `error_rate` attributes
- [ ] Test error rate calculation

#### 2.2.5 Performance Metrics
- [ ] Track performance metrics (if available):
  - Average response time
  - P95/P99 latency
  - Store in `performance_metrics` attribute
- [ ] Test performance metric aggregation

### 2.3 Analytics API Endpoints

#### 2.3.1 Get Analytics Endpoint
- [ ] Create `src/endpoints/analytics.py`
- [ ] Implement `GET /v1/analytics` endpoint:
  - Query parameters: `start_date`, `end_date`, `metric_type` (hourly/daily)
  - Query analytics table by date range
  - Return aggregated analytics data
  - Support pagination if needed
- [ ] Add authentication (API key)
- [ ] Add request ID tracking
- [ ] Test endpoint

#### 2.3.2 Get Analytics Summary Endpoint
- [ ] Implement `GET /v1/analytics/summary` endpoint:
  - Return summary statistics:
    - Total events (date range)
    - Top sources
    - Top event types
    - Error rate
    - Performance metrics
  - Query multiple analytics records and aggregate
- [ ] Test endpoint

#### 2.3.3 Export Analytics Endpoint
- [ ] Implement `GET /v1/analytics/export` endpoint:
  - Query parameters: `start_date`, `end_date`, `format` (csv/json)
  - Query analytics table
  - Format data as CSV or JSON
  - Return file download response
- [ ] Test CSV export
- [ ] Test JSON export

### 2.4 Frontend Analytics Dashboard

#### 2.4.1 Analytics Dashboard Page
- [ ] Create `frontend/src/pages/Analytics.jsx`:
  - Date range picker
  - Metric type selector (hourly/daily)
  - Charts for event volume, source distribution, event type distribution
  - Summary statistics cards
  - Export button
- [ ] Integrate with analytics API endpoints
- [ ] Add error handling and loading states

#### 2.4.2 Event Volume Chart
- [ ] Create chart component using Recharts:
  - Line or area chart showing event volume over time
  - X-axis: time (hour/day)
  - Y-axis: event count
  - Tooltip with detailed information
- [ ] Test chart rendering

#### 2.4.3 Source Distribution Chart
- [ ] Create chart component:
  - Pie or bar chart showing source distribution
  - Display top N sources
  - Percentage labels
- [ ] Test chart rendering

#### 2.4.4 Event Type Distribution Chart
- [ ] Create chart component:
  - Bar chart showing event type distribution
  - Display top N event types
  - Count labels
- [ ] Test chart rendering

#### 2.4.5 Real-Time Updates
- [ ] Implement polling mechanism:
  - Poll analytics API every 30 seconds (configurable)
  - Update charts with new data
  - Show "Last updated" timestamp
- [ ] Add option to enable/disable auto-refresh
- [ ] Test real-time updates

#### 2.4.6 Export Functionality
- [ ] Implement export handler:
  - Call export API endpoint
  - Download file (CSV or JSON)
  - Show download notification
- [ ] Test export functionality

#### 2.4.7 Analytics Route
- [ ] Add `/analytics` route to frontend router
- [ ] Add navigation link to main menu
- [ ] Test routing and navigation

### 2.5 Testing

#### 2.5.1 Unit Tests
- [ ] Test analytics aggregation logic
- [ ] Test analytics API endpoints
- [ ] Test export formatting

#### 2.5.2 Integration Tests
- [ ] Test DynamoDB Stream processing
- [ ] Test analytics data flow end-to-end
- [ ] Test analytics querying

#### 2.5.3 Manual Testing
- [ ] Create events and verify analytics aggregation
- [ ] Test analytics dashboard UI
- [ ] Test real-time updates
- [ ] Test export functionality

### 2.6 Documentation
- [ ] Create `docs/ANALYTICS.md`:
  - Analytics overview
  - Available metrics
  - Dashboard usage guide
  - Export functionality
- [ ] Update `docs/API.md` with analytics endpoints

---

## Feature 3: Additional SDKs (1 week per SDK)

### 3.1 TypeScript SDK

#### 3.1.1 Project Setup
- [ ] Create `examples/typescript/` directory
- [ ] Initialize npm package:
  - Package name: `@zapier/triggers-api-client`
  - TypeScript configuration
  - Build configuration (tsc or esbuild)
- [ ] Create `package.json` with dependencies:
  - `axios` for HTTP client
  - `typescript` for compilation
  - `@types/node` for Node.js types
- [ ] Create `tsconfig.json`

#### 3.1.2 Type Definitions
- [ ] Create `src/types.ts`:
  - `EventCreate` interface
  - `EventResponse` interface
  - `EventDetailResponse` interface
  - `InboxResponse` interface
  - `PaginationResponse` interface
  - `ErrorResponse` interface
  - All other API types
- [ ] Match types with Python/JavaScript SDKs

#### 3.1.3 HTTP Client
- [ ] Create `src/client.ts`:
  - `TriggersAPIClient` class
  - Constructor: `apiKey`, `baseUrl`, `timeout`
  - Private method: `request<T>(method, path, data?)`
  - Error handling with custom error classes
- [ ] Implement request ID tracking
- [ ] Test HTTP client

#### 3.1.4 API Methods
- [ ] Implement `createEvent(event: EventCreate): Promise<EventResponse>`
- [ ] Implement `getEvent(eventId: string): Promise<EventDetailResponse>`
- [ ] Implement `getInbox(options?): Promise<InboxResponse>`
- [ ] Implement `acknowledgeEvent(eventId: string): Promise<EventResponse>`
- [ ] Implement `deleteEvent(eventId: string): Promise<void>`
- [ ] Test all methods

#### 3.1.5 Error Classes
- [ ] Create `src/errors.ts`:
  - `TriggersAPIError` base class
  - `ValidationError`, `UnauthorizedError`, `NotFoundError`, `ConflictError`, etc.
  - Match error classes with Python/JavaScript SDKs
- [ ] Test error handling

#### 3.1.6 Examples
- [ ] Create `examples/basic-usage.ts`:
  - Initialize client
  - Create event
  - Get inbox
  - Acknowledge event
- [ ] Create `examples/event-flow.ts`:
  - Complete event lifecycle
- [ ] Create `examples/error-handling.ts`:
  - Error handling examples
- [ ] Test all examples

#### 3.1.7 Documentation
- [ ] Create `README.md`:
  - Installation instructions
  - Usage examples
  - API reference
  - Error handling guide
- [ ] Add JSDoc comments to all public methods

#### 3.1.8 Build and Publish
- [ ] Configure build script
- [ ] Test build output
- [ ] Create `.npmignore`
- [ ] Test package installation locally

### 3.2 Go SDK

#### 3.2.1 Project Setup
- [ ] Create `examples/go/` directory
- [ ] Initialize Go module:
  - Module name: `github.com/zapier/triggers-api-go`
  - Create `go.mod`
- [ ] Create project structure:
  - `client/` - Client implementation
  - `models/` - Data models
  - `errors/` - Error types
  - `examples/` - Example code

#### 3.2.2 Data Models
- [ ] Create `models/events.go`:
  - `EventCreate` struct
  - `EventResponse` struct
  - `EventDetailResponse` struct
  - `InboxResponse` struct
  - JSON tags for serialization
- [ ] Match models with other SDKs

#### 3.2.3 HTTP Client
- [ ] Create `client/client.go`:
  - `Client` struct with `apiKey`, `baseURL`, `httpClient`
  - Constructor: `NewClient(apiKey, baseURL string) *Client`
  - Private method: `doRequest(method, path string, body interface{})`
  - Error handling
- [ ] Test HTTP client

#### 3.2.4 API Methods
- [ ] Implement `CreateEvent(event EventCreate) (*EventResponse, error)`
- [ ] Implement `GetEvent(eventID string) (*EventDetailResponse, error)`
- [ ] Implement `GetInbox(options InboxOptions) (*InboxResponse, error)`
- [ ] Implement `AcknowledgeEvent(eventID string) (*EventResponse, error)`
- [ ] Implement `DeleteEvent(eventID string) error`
- [ ] Test all methods

#### 3.2.5 Error Types
- [ ] Create `errors/errors.go`:
  - `APIError` interface
  - `ValidationError`, `UnauthorizedError`, `NotFoundError`, etc.
  - Error message parsing
- [ ] Test error handling

#### 3.2.6 Examples
- [ ] Create `examples/basic_usage.go`:
  - Initialize client
  - Create event
  - Get inbox
  - Acknowledge event
- [ ] Create `examples/event_flow.go`:
  - Complete event lifecycle
- [ ] Create `examples/error_handling.go`:
  - Error handling examples
- [ ] Test all examples

#### 3.2.7 Documentation
- [ ] Create `README.md`:
  - Installation instructions
  - Usage examples
  - API reference
  - Error handling guide
- [ ] Add Go doc comments to all public functions

#### 3.2.8 Build and Test
- [ ] Test Go module build
- [ ] Run `go fmt` and `go vet`
- [ ] Test package usage locally

### 3.3 SDK Testing
- [ ] Test TypeScript SDK against local API
- [ ] Test TypeScript SDK against production API
- [ ] Test Go SDK against local API
- [ ] Test Go SDK against production API
- [ ] Verify SDKs match API behavior

---

## Feature 4: API Key Rotation (1 week)

### 4.1 Database Schema Updates

#### 4.1.1 Update API Keys Table Schema
- [ ] Update `src/database.py` to modify API keys table:
  - Add `version` attribute (Number, default: 1)
  - Add `previous_version` attribute (String, nullable)
  - Add `rotated_at` attribute (String, ISO 8601, nullable)
  - Add `expires_at` attribute (String, ISO 8601, nullable)
  - Add `status` attribute (String: "active", "rotating", "expired")
- [ ] Create migration script for existing keys:
  - Set `version=1` for all existing keys
  - Set `status="active"`
- [ ] Test schema updates

#### 4.1.2 Key Versions Table (Optional)
- [ ] Consider creating separate `triggers-api-key-versions` table:
  - Partition Key: `key_id` (String)
  - Sort Key: `version` (Number)
  - Store all key versions for audit trail
- [ ] Or use single table with version tracking
- [ ] Test table structure

### 4.2 Rotation Logic

#### 4.2.1 Key Generation
- [ ] Create `src/utils.py` function `generate_api_key()`:
  - Generate secure random API key
  - Format: `tr_<random_string>` (or similar)
  - Return key string
- [ ] Test key generation

#### 4.2.2 Rotation Function
- [ ] Create `src/database.py` function `rotate_api_key(key_id, transition_days)`:
  - Generate new API key
  - Create new key record with `version=old_version+1`
  - Mark old key as `status="rotating"`
  - Set `expires_at` for old key (transition_days from now)
  - Set `rotated_at` timestamp
  - Link new key to old key via `previous_version`
  - Return new key details
- [ ] Test rotation logic

#### 4.2.3 Authentication Updates
- [ ] Update `src/auth.py` `validate_api_key()`:
  - Check key status: accept "active" and "rotating" keys
  - Reject "expired" keys
  - Check `expires_at` if present
- [ ] Test authentication with rotating keys

#### 4.2.4 Expiration Cleanup
- [ ] Create `src/lambda_handlers/key_expiration.py`:
  - Lambda function to check expired keys
  - Update `status="expired"` for keys past `expires_at`
  - Run on schedule (EventBridge rule, daily)
- [ ] Update `template.yaml` to include expiration Lambda
- [ ] Test expiration logic

### 4.3 Rotation API Endpoints

#### 4.3.1 Rotate Key Endpoint
- [ ] Create `src/endpoints/api_keys.py`
- [ ] Implement `POST /v1/api-keys/{key_id}/rotate` endpoint:
  - Request model: `KeyRotateRequest` (transition_days, optional)
  - Validate key exists and belongs to requester (if applicable)
  - Call rotation function
  - Return new key details (include new API key)
  - Return old key expiration date
- [ ] Add authentication (admin or key owner)
- [ ] Add request ID tracking
- [ ] Test endpoint

#### 4.3.2 List Key Versions Endpoint
- [ ] Implement `GET /v1/api-keys/{key_id}/versions` endpoint:
  - Query all versions of a key
  - Return version history with status and dates
  - Support pagination
- [ ] Test endpoint

#### 4.3.3 Get Key Details Endpoint (Optional)
- [ ] Implement `GET /v1/api-keys/{key_id}` endpoint:
  - Return key details (excluding actual key value for security)
  - Return status, version, rotation dates
- [ ] Test endpoint

### 4.4 Migration Script

#### 4.4.1 Migration Script
- [ ] Create `scripts/migrate_api_keys.py`:
  - Read all existing API keys
  - Add version and status attributes
  - Update keys in DynamoDB
  - Report migration results
- [ ] Test migration script on test data
- [ ] Document migration process

### 4.5 Frontend UI (Optional)

#### 4.5.1 Key Management UI
- [ ] Create `frontend/src/pages/ApiKeys.jsx`:
  - Display API keys list
  - Show key status, version, rotation dates
  - "Rotate Key" button
  - Key version history
- [ ] Integrate with rotation endpoints
- [ ] Add confirmation dialogs for rotation
- [ ] Test UI

### 4.6 Testing

#### 4.6.1 Unit Tests
- [ ] Test key generation
- [ ] Test rotation logic
- [ ] Test authentication with rotating keys
- [ ] Test expiration logic

#### 4.6.2 Integration Tests
- [ ] Test rotation process end-to-end
- [ ] Test transition period (both keys work)
- [ ] Test expiration after transition
- [ ] Test migration script

#### 4.6.3 Manual Testing
- [ ] Create API key
- [ ] Rotate key
- [ ] Verify both keys work during transition
- [ ] Verify old key expires after transition
- [ ] Test key version history

### 4.7 Documentation
- [ ] Update `docs/SECURITY.md`:
  - API key rotation guide
  - Best practices
  - Migration instructions
- [ ] Update `docs/API.md` with rotation endpoints

---

## Feature 5: Request Signing (HMAC) (1 week)

### 5.1 Signature Generation

#### 5.1.1 Signature Utilities
- [ ] Create `src/utils.py` function `generate_request_signature()`:
  - Parameters: `method`, `path`, `query_string`, `timestamp`, `body`, `secret_key`
  - Build signature string: `method + "\n" + path + "\n" + query_string + "\n" + timestamp + "\n" + body_hash`
  - Calculate `HMAC-SHA256(signature_string, secret_key)`
  - Return base64-encoded signature
- [ ] Test signature generation

#### 5.1.2 Body Hash Calculation
- [ ] Create function `hash_request_body(body)`:
  - If body is JSON, stringify and hash with SHA256
  - If body is empty, use empty string hash
  - Return hex-encoded hash
- [ ] Test body hash calculation

### 5.2 Signature Validation Middleware

#### 5.2.1 Validation Middleware
- [ ] Create `src/middleware/signature_validation.py`:
  - FastAPI middleware to validate request signatures
  - Extract headers: `X-Signature-Timestamp`, `X-Signature`, `X-Signature-Version`
  - Check timestamp (reject if >5 minutes old)
  - Reconstruct signature string
  - Calculate expected signature
  - Compare signatures (constant-time comparison)
  - Raise `UnauthorizedError` if invalid
- [ ] Make middleware optional (feature flag)
- [ ] Test middleware

#### 5.2.2 Secret Key Management
- [ ] Update API key schema to include `signing_secret`:
  - Generate signing secret per API key
  - Store in DynamoDB (encrypted at rest)
- [ ] Create function to retrieve signing secret by API key
- [ ] Test secret key management

#### 5.2.3 Middleware Integration
- [ ] Add signature validation middleware to FastAPI app:
  - Apply to all endpoints (except health check)
  - Make optional via environment variable or feature flag
  - Skip validation if signature headers not present (backward compatible)
- [ ] Test middleware integration

### 5.3 SDK Updates

#### 5.3.1 Python SDK
- [ ] Update `examples/python/triggers_api/client.py`:
  - Add `signing_secret` parameter to client
  - Add `_sign_request()` method
  - Add signature headers to all requests
- [ ] Test Python SDK signing

#### 5.3.2 JavaScript SDK
- [ ] Update `examples/javascript/src/client.js`:
  - Add `signingSecret` parameter to client
  - Add `_signRequest()` method
  - Add signature headers to all requests
- [ ] Test JavaScript SDK signing

#### 5.3.3 TypeScript SDK
- [ ] Update TypeScript SDK (if implemented):
  - Add signing support
  - Add signature headers to requests
- [ ] Test TypeScript SDK signing

#### 5.3.4 Go SDK
- [ ] Update Go SDK (if implemented):
  - Add signing support
  - Add signature headers to requests
- [ ] Test Go SDK signing

### 5.4 Testing

#### 5.4.1 Unit Tests
- [ ] Test signature generation
- [ ] Test signature validation
- [ ] Test timestamp validation
- [ ] Test body hash calculation

#### 5.4.2 Integration Tests
- [ ] Test signed request flow end-to-end
- [ ] Test invalid signature rejection
- [ ] Test expired timestamp rejection
- [ ] Test backward compatibility (unsigned requests)

#### 5.4.3 Manual Testing
- [ ] Test signed requests with Python SDK
- [ ] Test signed requests with JavaScript SDK
- [ ] Test invalid signatures are rejected
- [ ] Test unsigned requests still work (backward compatibility)

### 5.5 Documentation
- [ ] Update `docs/SECURITY.md`:
  - Request signing guide
  - Signature format specification
  - SDK usage examples
  - Troubleshooting
- [ ] Update SDK documentation with signing examples
- [ ] Add signing examples to `docs/EXAMPLES.md`

---

## Feature 6: Chaos Engineering (1 week)

### 6.1 Failure Injection Framework

#### 6.1.1 Failure Injection Utilities
- [ ] Create `src/chaos/` directory
- [ ] Create `src/chaos/injectors.py`:
  - `inject_network_latency(delay_ms)` - Add artificial latency
  - `inject_dynamodb_error(error_type)` - Inject DynamoDB errors
  - `inject_lambda_timeout()` - Simulate Lambda timeout
  - `inject_partial_failure(probability)` - Random failures
- [ ] Make injectors configurable via environment variables
- [ ] Test failure injection

#### 6.1.2 Chaos Configuration
- [ ] Create `src/chaos/config.py`:
  - Load chaos configuration from environment
  - Feature flags for each chaos type
  - Probability/threshold settings
- [ ] Test configuration loading

### 6.2 Chaos Scenarios

#### 6.2.1 Network Latency Scenario
- [ ] Create scenario: Inject 100-500ms latency randomly
- [ ] Apply to API requests
- [ ] Test scenario

#### 6.2.2 DynamoDB Error Scenario
- [ ] Create scenario: Inject DynamoDB errors (ThrottlingException, ProvisionedThroughputExceededException)
- [ ] Apply to database operations
- [ ] Test scenario

#### 6.2.3 Lambda Timeout Scenario
- [ ] Create scenario: Simulate Lambda timeout
- [ ] Apply to long-running operations
- [ ] Test scenario

#### 6.2.4 Partial Failure Scenario
- [ ] Create scenario: Random failures with configurable probability
- [ ] Apply to various operations
- [ ] Test scenario

### 6.3 Chaos Test Scenarios

#### 6.3.1 Test Suite
- [ ] Create `tests/chaos/` directory
- [ ] Create `tests/chaos/test_chaos_scenarios.py`:
  - Test network latency recovery
  - Test DynamoDB error recovery
  - Test Lambda timeout recovery
  - Test partial failure handling
- [ ] Test chaos scenarios

#### 6.3.2 Recovery Verification
- [ ] Create recovery verification tests:
  - Verify system recovers after failures
  - Verify data consistency after failures
  - Verify error handling works correctly
- [ ] Test recovery

### 6.4 Monitoring Integration

#### 6.4.1 Chaos Metrics
- [ ] Add CloudWatch metrics for chaos events:
  - Count of injected failures
  - Recovery time
  - Success rate during chaos
- [ ] Test metrics

#### 6.4.2 Logging
- [ ] Add structured logging for chaos events:
  - Log when failures are injected
  - Log recovery events
  - Include request IDs for correlation
- [ ] Test logging

### 6.5 CI/CD Integration (Optional)

#### 6.5.1 Chaos Tests in CI
- [ ] Add chaos tests to CI pipeline:
  - Run chaos scenarios in test environment
  - Verify system resilience
  - Fail build if recovery fails
- [ ] Test CI integration

### 6.6 Documentation
- [ ] Create `docs/CHAOS_ENGINEERING.md`:
  - Chaos engineering overview
  - Available scenarios
  - How to run chaos tests
  - Monitoring and recovery
  - Safety guidelines
- [ ] Add chaos testing to `docs/README.md`

---

## Success Criteria Checklist

### Webhook Support
- [ ] Webhooks are delivered successfully (> 99% success rate)
- [ ] Retry logic works correctly
- [ ] Dead letter queue handles failures
- [ ] Webhook management UI is functional
- [ ] HMAC signature verification works

### Analytics Dashboard
- [ ] Analytics are accurate
- [ ] Dashboard displays correctly
- [ ] Real-time updates work
- [ ] Export functionality works
- [ ] DynamoDB Streams processing works

### Additional SDKs
- [ ] TypeScript SDK works correctly
- [ ] Go SDK works correctly
- [ ] Examples are provided
- [ ] Documentation is complete
- [ ] SDKs are consistent with API

### API Key Rotation
- [ ] Key rotation works correctly
- [ ] Transition period is handled
- [ ] Migration script works
- [ ] Old keys are invalidated after transition
- [ ] Both keys work during transition

### Request Signing
- [ ] Signing works correctly
- [ ] Validation works correctly
- [ ] SDKs support signing
- [ ] Documentation is complete
- [ ] Backward compatibility maintained

### Chaos Engineering
- [ ] Failure injection works
- [ ] Test scenarios are comprehensive
- [ ] Recovery is verified
- [ ] Documentation is complete
- [ ] Safety measures in place

---

## Notes & Considerations

### Feature Independence
- All features can be implemented independently
- Features can be prioritized based on business needs
- No strict dependency order between features

### Infrastructure Costs
- SQS queues and Lambda functions for webhooks
- DynamoDB Streams for analytics
- Additional CloudWatch metrics
- Consider cost implications

### Testing Strategy
- Each feature should have comprehensive tests
- Integration tests for end-to-end flows
- Manual testing for UI features
- Chaos tests for resilience

### Documentation Requirements
- Each feature needs dedicated documentation
- Update main API documentation
- Add examples for new features
- Update SDK documentation

### Security Considerations
- Webhook secrets must be stored securely
- API key rotation must be secure
- Request signing secrets must be protected
- Chaos engineering must be disabled in production

### Performance Considerations
- Webhook delivery should not block event creation
- Analytics aggregation should be efficient
- Signature validation should be fast
- Chaos injection should have minimal overhead

---

## Next Steps After Completion

After Phase 10 completion:
1. Monitor webhook delivery rates
2. Monitor analytics accuracy
3. Gather feedback on new SDKs
4. Review security enhancements
5. Plan future enhancements based on usage

---

**Task List Status:** 🔄 Not Started  
**Last Updated:** 2025-11-11  
**Priority Order (Recommended):**
1. Webhook Support (High Priority)
2. API Key Rotation (High Priority)
3. Analytics Dashboard (Medium Priority)
4. Request Signing (Medium Priority)
5. Additional SDKs (Low Priority)
6. Chaos Engineering (Low Priority)

