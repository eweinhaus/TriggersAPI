# Zapier Triggers API - Product Requirements Document

**Organization:** Zapier  
**Project ID:** K1oUUDeoZrvJkVZafqHL_1761943818847  
**Version:** 2.0  
**Last Updated:** 2024

---

## 1. Executive Summary

The Zapier Triggers API is a unified, real-time event ingestion system that enables external systems to send events into Zapier via a standardized RESTful interface. This API empowers developers to build event-driven automations and agentic workflows, moving beyond traditional scheduled polling to true real-time reactivity.

**Implementation Approach:** This project is split into 6 phases, each independently testable and deployable. See `planning/PRDs/` for phase-specific PRDs.

**Key Value Propositions:**
- **For Developers:** Simple REST API with minimal integration effort
- **For Automation Specialists:** Real-time event-driven workflows without manual intervention
- **For Business Analysts:** Access to real-time event data for insights and optimization

---

## 2. Problem Statement

### Current State
Zapier triggers are currently defined within individual integrations, creating several limitations:
- **Fragmentation:** Each integration implements its own trigger mechanism
- **Scalability Issues:** No centralized event processing infrastructure
- **Limited Real-time Capabilities:** Heavy reliance on scheduled polling rather than event-driven architecture
- **Developer Friction:** Inconsistent patterns across integrations make it difficult to add new event sources

### Solution
A centralized Triggers API that provides:
- Unified event ingestion endpoint
- Durable event storage with delivery tracking
- Standardized authentication and authorization
- Developer-friendly documentation and tooling

---

## 3. Goals & Success Metrics

### Primary Goals
1. **Reliability:** Achieve 99.9% event ingestion success rate
2. **Performance:** Sub-100ms response time for event ingestion
3. **Developer Experience:** Positive feedback on ease of integration
4. **Adoption:** Foundation for future Zapier integrations

### Success Metrics
- **Technical Metrics:**
  - Event ingestion latency: < 100ms (p95)
  - API availability: > 99.9% uptime
  - Event delivery success rate: > 99%
  - Error rate: < 0.1%

- **Business Metrics:**
  - Developer adoption: 10+ integrations using API within 6 months
  - Developer satisfaction: > 4.5/5 on ease of use surveys
  - Time to integrate: < 2 hours for basic integration

---

## 4. Implementation Phases

This project is split into 6 phases, each independently testable and deployable:

**Phase 1: Core API Backend (P0)** - Working API with all P0 endpoints, testable locally  
**Phase 2: AWS Infrastructure & Deployment** - API deployed and accessible on AWS  
**Phase 3: Testing & Error Handling** - Production-ready API with comprehensive testing  
**Phase 4: Developer Experience (P1)** - Enhanced API with P1 features  
**Phase 5: Documentation & Example Clients** - Complete developer documentation  
**Phase 6: Frontend Dashboard (P2)** - Web-based UI for testing and managing events

See `planning/PRDs/phase-*.md` for detailed phase-specific requirements.

---

## 5. Functional Requirements

### 5.1 P0: Core Event Ingestion & Delivery

**API Versioning:** All endpoints are prefixed with `/v1` (e.g., `/v1/events`). This allows for future API versions without breaking changes.

#### GET /v1/health - Health Check
**Purpose:** Health check endpoint for monitoring and deployment verification.

**Request:**
- Method: GET
- No authentication required

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "ISO 8601",
  "version": "1.0.0"
}
```

#### POST /v1/events - Event Ingestion
**Purpose:** Accept events from external systems and store them durably.

**Request:**
- Method: POST
- Headers: `Content-Type: application/json`, `X-API-Key: <api_key>` (required)
- Optional Headers: `X-Request-ID: <request_id>` (for request tracking)
- Body: JSON payload
  ```json
  {
    "source": "string (required)",
    "event_type": "string (required, e.g., 'user.created')",
    "payload": {} (required, any valid JSON),
    "metadata": {
      "correlation_id": "string (optional)",
      "priority": "low|normal|high (optional, default: normal)",
      "idempotency_key": "string (optional, accepted but ignored in Phase 1, duplicate prevention in Phase 4)"
    }
  }
  ```

**Response (201 Created):**
```json
{
  "event_id": "uuid-v4",
  "created_at": "ISO 8601",
  "status": "pending",
  "message": "Event ingested successfully",
  "request_id": "uuid-v4 (if X-Request-ID header provided)"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid payload, missing required fields
- `401 Unauthorized`: Missing or invalid API key
- `500 Internal Server Error`: Server error

#### GET /v1/inbox - Retrieve Undelivered Events
**Purpose:** List events that are pending delivery (not yet acknowledged).

**Request:**
- Method: GET
- Headers: `X-API-Key: <api_key>` (required)
- Optional Headers: `X-Request-ID: <request_id>` (for request tracking)
- Query Parameters:
  - `limit`: integer (optional, default: 50, max: 100)
  - `cursor`: string (optional, for pagination)
  - `source`: string (optional, filter by source)
  - `event_type`: string (optional, filter by event type)

**Response (200 OK):**
```json
{
  "events": [
    {
      "event_id": "uuid-v4",
      "created_at": "ISO 8601",
      "source": "string",
      "event_type": "string",
      "payload": {},
      "status": "pending",
      "metadata": {}
    }
  ],
  "pagination": {
    "next_cursor": "string (optional)",
    "limit": 50
  },
  "request_id": "uuid-v4 (if X-Request-ID header provided)"
}
```

#### POST /v1/events/{event_id}/ack - Acknowledge Event
**Purpose:** Mark an event as acknowledged/delivered after processing.

**Request:**
- Method: POST
- Headers: `X-API-Key: <api_key>` (required)
- Optional Headers: `X-Request-ID: <request_id>` (for request tracking)
- Path Parameter: `event_id` (required)

**Response (200 OK):**
```json
{
  "event_id": "uuid-v4",
  "status": "acknowledged",
  "acknowledged_at": "ISO 8601",
  "message": "Event acknowledged successfully",
  "request_id": "uuid-v4 (if X-Request-ID header provided)"
}
```

**Error Responses:**
- `404 Not Found`: Event not found
- `409 Conflict`: Event already acknowledged
- `401 Unauthorized`: Invalid API key

#### DELETE /v1/events/{event_id} - Delete Event
**Purpose:** Permanently delete an event from the system.

**Request:**
- Method: DELETE
- Headers: `X-API-Key: <api_key>` (required)
- Optional Headers: `X-Request-ID: <request_id>` (for request tracking)
- Path Parameter: `event_id` (required)

**Response (200 OK):**
```json
{
  "event_id": "uuid-v4",
  "message": "Event deleted successfully",
  "request_id": "uuid-v4 (if X-Request-ID header provided)"
}
```

### 5.2 P1: Developer Experience Enhancements
- GET /v1/events/{event_id} endpoint for event details
- Event status tracking (pending/acknowledged)
- Structured error responses with error codes
- Response standardization across endpoints
- Enhanced error messages
- Optional idempotency key support (via metadata.idempotency_key)

### 5.3 P2: Documentation & Examples
- OpenAPI/Swagger documentation (auto-generated)
- Python example client
- JavaScript/Node.js example client
- cURL examples
- React dashboard with Material-UI

---

## 6. Technical Architecture

### 6.1 System Components

**Backend:**
- FastAPI application deployed as AWS Lambda function
- API Gateway for HTTP interface
- DynamoDB for event storage
- CloudWatch for logging & metrics

**Storage Schema:**
- **Events Table:** `triggers-api-events`
  - Partition Key: `event_id` (String, UUID v4)
  - Sort Key: `created_at` (String, ISO 8601)
  - Attributes: source, event_type, payload, status, metadata, acknowledged_at, idempotency_key
  - TTL Attribute: `ttl` (Number, Unix timestamp, 7 days)
  - Billing Mode: On-demand
  - **Note:** For MVP, no scaling concerns. The Inbox GSI with status as partition key is acceptable for low-to-moderate volume.

- **Inbox GSI:** `status-created_at-index`
  - Partition Key: `status` (String)
  - Sort Key: `created_at` (String)
  - Projection: All attributes
  - **Note:** For MVP scale, this GSI design is sufficient. No sharding needed.

- **API Keys Table:** `triggers-api-keys`
  - Partition Key: `api_key` (String)
  - Attributes: source, created_at, is_active
  - Billing Mode: On-demand

- **Idempotency Table (Optional, Phase 4):** `triggers-api-idempotency`
  - Partition Key: `idempotency_key` (String)
  - Attributes: event_id, created_at
  - TTL Attribute: `ttl` (Number, Unix timestamp, 24 hours)
  - Billing Mode: On-demand

### 6.2 Technology Stack

**Backend:**
- Python 3.11+
- FastAPI framework
- Pydantic for validation
- boto3 for AWS services
- AWS SAM for deployment

**Frontend (Phase 6):**
- React 18+
- Material-UI (MUI) v5
- Axios for HTTP client

**Infrastructure:**
- AWS Lambda (Python runtime)
- API Gateway (REST API)
- DynamoDB (NoSQL database)
- CloudWatch (logging & metrics)
- S3 + CloudFront (frontend hosting)

### 6.3 Implementation Details

#### Project Structure
```
triggers-api/
├── src/
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # Pydantic models
│   ├── database.py          # DynamoDB client wrapper
│   ├── auth.py              # API key validation
│   └── endpoints/
│       ├── events.py        # Event endpoints
│       └── inbox.py         # Inbox endpoints
├── tests/
│   ├── test_events.py
│   ├── test_inbox.py
│   ├── test_auth.py
│   └── conftest.py          # pytest fixtures
├── scripts/
│   ├── seed_api_keys.py     # Create test API keys
│   └── local_setup.sh       # Local development setup
├── template.yaml             # SAM template
├── requirements.txt
├── docker-compose.yml        # For DynamoDB Local
└── README.md
```

#### API Key Management (MVP)
- **Phase 1 (Local):** Use hardcoded test key `test-api-key-12345` for local development
- **Phase 2 (AWS):** Migrate to DynamoDB `triggers-api-keys` table
- **Migration Path:** 
  - Phase 1: Hardcoded key validation in `src/auth.py`
  - Phase 2: Add environment variable `AUTH_MODE` (local|aws)
  - Phase 2: Support both modes during transition
  - Phase 2: Use `scripts/seed_api_keys.py` to create production keys
- **Production Keys:** Generate securely using UUID v4
- **API Key Lookup:** For MVP, no caching needed. Direct DynamoDB lookup is sufficient.

#### Pagination Implementation
- Use DynamoDB `LastEvaluatedKey` as cursor
- Encode as base64 JSON string: `base64.b64encode(json.dumps(last_evaluated_key).encode()).decode()`
- Decode: `json.loads(base64.b64decode(cursor).decode())`
- Client sends `cursor` query parameter
- Response includes `next_cursor` if more results exist
- **Note:** Total count is not provided (DynamoDB doesn't efficiently support this)
- Filtering by `source`/`event_type` uses FilterExpression (applied after query, may affect pagination)

#### Error Response Format
All errors follow this structure:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}, // Optional, field-level errors
    "request_id": "uuid-v4" // Always included for debugging
  }
}
```

**Request ID Tracking:**
- All requests generate a unique request ID (UUID v4)
- Request ID is included in all responses (success and error)
- If client provides `X-Request-ID` header, use that; otherwise generate one
- Request ID is logged in CloudWatch for correlation
- Request ID helps with debugging and support

Standard error codes:
- `VALIDATION_ERROR`: Invalid request payload
- `UNAUTHORIZED`: Missing or invalid API key
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Resource conflict (e.g., already acknowledged)
- `INTERNAL_ERROR`: Server error

#### CORS Configuration
- **Phase 1:** CORS not needed (local development only)
- **Phase 2:** Configure CORS for API Gateway:
  - Allow origins: `*` (for MVP, restrict in production)
  - Allow methods: `GET, POST, DELETE, OPTIONS`
  - Allow headers: `Content-Type, X-API-Key, X-Request-ID`
  - Max age: 3600

---

## 7. Non-Functional Requirements

### 7.1 Performance
- **Latency:** < 100ms p95 for event ingestion
- **Throughput:** MVP scale - no specific throughput requirements
- **Response Time:** < 200ms p95 for inbox queries
- **Cold Start:** Lambda cold starts < 2 seconds (acceptable for MVP)

### 7.2 Reliability & Availability
- **Uptime:** 99.9% availability target (AWS managed services)
- **Durability:** Zero data loss (events stored before acknowledgment)
- **Error Rate:** < 0.1% error rate

### 7.3 Security
- **Authentication:** API key-based authentication (X-API-Key header)
- **Data Encryption:** TLS 1.2+ for data in transit
- **Storage Encryption:** DynamoDB encryption at rest
- **Input Validation:** Strict JSON schema validation

### 7.4 Scalability
- **Note:** No specific scaling requirements for MVP
- **Horizontal Scaling:** Lambda auto-scaling (AWS managed)
- **Storage:** DynamoDB on-demand billing (no capacity planning needed)
- **Capacity:** Sufficient for MVP use cases without optimization

### 7.5 Observability
- **Logging:** Structured logging to CloudWatch with request IDs
- **Metrics:** Event count, latency, error rate (CloudWatch metrics)
- **Tracing:** Request ID tracking in all logs and responses
- **Health Check:** `/v1/health` endpoint for monitoring

---

## 8. Dependencies & Assumptions

### Dependencies
- AWS account with appropriate permissions
- AWS CLI and SAM CLI installed
- Python 3.11+ for development
- Node.js 18+ for frontend development (Phase 6)
- Docker for local DynamoDB (Phase 1)

### Assumptions
- Developers are familiar with REST APIs and JSON
- API keys are managed manually for MVP
- Events are idempotent (duplicate events acceptable unless idempotency_key provided)
- Event ordering is not strictly required (best-effort by created_at timestamp)
- Frontend and backend can be deployed separately
- No scaling requirements for MVP (low-to-moderate volume expected)
- All timestamps are in UTC (ISO 8601 format)

---

## 9. Out of Scope (MVP)

The following features are explicitly out of scope for the initial MVP (Phases 1-3):

- **Rate Limiting:** Deferred to post-MVP (can use API Gateway throttling)
- **Advanced Filtering:** Complex query filters beyond source/event_type
- **Event Transformation:** Data transformation or enrichment
- **Webhooks:** Push-based event delivery (polling only)
- **Event Replay:** Re-sending previously delivered events
- **Analytics Dashboard:** Advanced analytics and reporting
- **Multi-tenancy:** Organization/workspace management
- **Event Batching:** Bulk event ingestion endpoint
- **Long-term Retention:** Events beyond 7-day TTL
- **Event Versioning:** Schema versioning support

**Note:** P1 features (Phase 4) and P2 features (Phases 5-6) are planned but not required for MVP.

---

## 10. Success Criteria by Phase

### Phase 1 Success Criteria
- [ ] All 4 P0 endpoints implemented (with /v1 prefix)
- [ ] Health check endpoint (GET /v1/health) implemented
- [ ] Events stored in DynamoDB (local)
- [ ] API key authentication functional
- [ ] Request ID tracking implemented
- [ ] Testable locally with cURL
- [ ] Basic project structure complete

### Phase 2 Success Criteria
- [ ] SAM template complete
- [ ] API deployed to AWS
- [ ] All endpoints accessible via API Gateway (with /v1 prefix)
- [ ] DynamoDB tables created
- [ ] API key migration from hardcoded to DynamoDB complete
- [ ] CloudWatch logs working with request IDs
- [ ] CORS configured

### Phase 3 Success Criteria
- [ ] Unit tests with >80% coverage
- [ ] Integration tests for all endpoints (with mocks)
- [ ] E2E tests for all endpoints (against real server)
- [ ] Playwright MCP tests for all endpoints
- [ ] Test automation script works (single command)
- [ ] All tests passing (unit, integration, e2e, playwright)
- [ ] Standardized error responses
- [ ] Input validation working
- [ ] Tests are fully automated (no manual intervention)

### Phase 4 Success Criteria
- [ ] GET /v1/events/{event_id} implemented
- [ ] Status tracking functional
- [ ] Enhanced error messages
- [ ] Response standardization complete
- [ ] Optional idempotency key support implemented

### Phase 5 Success Criteria
- [ ] OpenAPI docs accessible at /docs
- [ ] Python example client functional
- [ ] JavaScript example client functional
- [ ] README with quick start
- [ ] cURL examples documented

### Phase 6 Success Criteria
- [ ] React dashboard deployed
- [ ] Can send events via UI
- [ ] Can view inbox
- [ ] Can acknowledge/delete events
- [ ] UI is responsive
- [ ] Cursor browser tests pass (all UI workflows)
- [ ] Playwright MCP frontend tests pass
- [ ] All frontend tests automated (no manual testing)

---

## 11. Risks & Mitigation

### Technical Risks
1. **Lambda Cold Starts:** Acceptable for MVP (< 2 seconds). No mitigation needed unless problematic.
2. **DynamoDB Throttling:** Use on-demand billing. For MVP scale, throttling unlikely.
3. **Race Conditions:** Use conditional updates, optimistic locking (already planned)
4. **CORS Issues:** Test early, configure correctly
5. **API Key Migration:** Document clear migration path from Phase 1 to Phase 2

### Operational Risks
1. **Cost Overruns:** Monitor AWS usage, use free tier where possible
2. **Deployment Complexity:** Use SAM for simplified deployment
3. **Testing Gaps:** Comprehensive test coverage, integration tests

---

**Document Status:** Active  
**Next Review:** After Phase 1 completion
