# System Architecture

Complete architecture documentation for the Zapier Triggers API.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Deployment Architecture](#deployment-architecture)
- [Request Flow](#request-flow)
- [Component Descriptions](#component-descriptions)
- [Design Patterns](#design-patterns)

---

## Overview

The Zapier Triggers API is a serverless, event-driven REST API built on AWS. It provides a unified interface for ingesting and managing events, enabling real-time event-driven automations and workflows.

**Key Characteristics:**
- Serverless architecture (AWS Lambda)
- Event-driven design
- RESTful API with versioning (`/v1`)
- API key authentication
- DynamoDB for data persistence
- Auto-scaling and on-demand billing

---

## System Architecture

High-level system architecture showing all major components and their interactions.

```mermaid
graph TB
    subgraph "Client Layer"
        CLIENT[Client Applications]
        FRONTEND[Frontend Dashboard<br/>React + Material-UI]
    end
    
    subgraph "API Layer"
        APIGW[API Gateway<br/>REST API<br/>CORS Enabled]
    end
    
    subgraph "Compute Layer"
        LAMBDA[Lambda Function<br/>FastAPI Application<br/>Python 3.11]
    end
    
    subgraph "Data Layer"
        EVENTS[(Events Table<br/>PK: event_id<br/>SK: created_at)]
        INBOX[(Inbox GSI<br/>PK: status<br/>SK: created_at)]
        KEYS[(API Keys Table<br/>PK: api_key)]
        IDEMPOTENCY[(Idempotency Table<br/>PK: idempotency_key)]
    end
    
    subgraph "Observability"
        CLOUDWATCH[CloudWatch<br/>Logs & Metrics]
    end
    
    subgraph "Frontend Hosting"
        S3[S3 Bucket<br/>Static Assets]
        CF[CloudFront<br/>CDN Distribution]
    end
    
    CLIENT -->|HTTPS| APIGW
    FRONTEND -->|HTTPS| CF
    CF -->|HTTPS| S3
    FRONTEND -->|API Calls| APIGW
    APIGW -->|Invoke| LAMBDA
    LAMBDA -->|Read/Write| EVENTS
    LAMBDA -->|Query| INBOX
    LAMBDA -->|Read| KEYS
    LAMBDA -->|Read/Write| IDEMPOTENCY
    LAMBDA -->|Logs| CLOUDWATCH
    
    style CLIENT fill:#e1f5ff
    style FRONTEND fill:#e1f5ff
    style APIGW fill:#fff4e1
    style LAMBDA fill:#ffe1f5
    style EVENTS fill:#e1ffe1
    style INBOX fill:#e1ffe1
    style KEYS fill:#e1ffe1
    style IDEMPOTENCY fill:#e1ffe1
    style CLOUDWATCH fill:#f0e1ff
    style S3 fill:#e1f5ff
    style CF fill:#e1f5ff
```

**Key Components:**
- **Client Applications**: External systems sending events via REST API
- **Frontend Dashboard**: React-based web UI for testing and managing events
- **API Gateway**: Managed REST API with CORS support
- **Lambda Function**: FastAPI application handling all API requests
- **DynamoDB Tables**: Event storage, API key management, and idempotency tracking
- **CloudWatch**: Logging and monitoring

---

## Component Architecture

Detailed view of the FastAPI application structure and internal components.

```mermaid
graph TB
    subgraph "FastAPI Application"
        MAIN[main.py<br/>Application Entry Point<br/>Middleware & Error Handlers]
        ROUTER[v1 Router<br/>APIRouter prefix=/v1]
        
        subgraph "Endpoints"
            HEALTH[health.py<br/>GET /health]
            EVENTS_EP[events.py<br/>POST /events<br/>GET /events/:id<br/>POST /events/:id/ack<br/>DELETE /events/:id]
            INBOX_EP[inbox.py<br/>GET /inbox]
        end
        
        subgraph "Core Components"
            AUTH[auth.py<br/>API Key Validation<br/>Dependency Injection]
            DB[database.py<br/>DynamoDB Operations<br/>Table Management]
            MODELS[models.py<br/>Pydantic Models<br/>Request/Response Schemas]
            EXCEPTIONS[exceptions.py<br/>Custom Exception Classes<br/>Error Definitions]
            UTILS[utils.py<br/>Helper Functions<br/>UUID, Timestamps, Cursors]
        end
    end
    
    MAIN --> ROUTER
    ROUTER --> HEALTH
    ROUTER --> EVENTS_EP
    ROUTER --> INBOX_EP
    
    EVENTS_EP --> AUTH
    EVENTS_EP --> DB
    EVENTS_EP --> MODELS
    EVENTS_EP --> EXCEPTIONS
    
    INBOX_EP --> AUTH
    INBOX_EP --> DB
    INBOX_EP --> MODELS
    
    HEALTH --> MODELS
    
    AUTH --> DB
    DB --> EXCEPTIONS
    MAIN --> EXCEPTIONS
    
    style MAIN fill:#ffe1f5
    style ROUTER fill:#fff4e1
    style AUTH fill:#e1ffe1
    style DB fill:#e1ffe1
    style MODELS fill:#e1f5ff
    style EXCEPTIONS fill:#ffe1f5
```

**Component Relationships:**
- **main.py**: Orchestrates the application, registers routers, middleware, and error handlers
- **Endpoints**: Handle HTTP requests and delegate to business logic
- **auth.py**: Validates API keys before endpoint execution
- **database.py**: Abstracts DynamoDB operations
- **models.py**: Defines request/response schemas with validation
- **exceptions.py**: Provides standardized error handling

---

## Data Flow

Data flow diagram showing request and response paths through the system.

```mermaid
sequenceDiagram
    participant Client
    participant APIGW as API Gateway
    participant Lambda
    participant Auth as Authentication
    participant Endpoint
    participant DB as DynamoDB
    participant CloudWatch
    
    Client->>APIGW: HTTP Request<br/>(POST /v1/events)
    APIGW->>Lambda: Invoke Function
    
    Lambda->>Lambda: Generate Request ID
    Lambda->>Auth: Validate API Key
    Auth->>DB: Check API Key Table
    DB-->>Auth: API Key Valid/Invalid
    Auth-->>Lambda: API Key Status
    
    alt API Key Valid
        Lambda->>Endpoint: Route to Endpoint
        Endpoint->>Endpoint: Validate Request (Pydantic)
        Endpoint->>DB: Create Event
        DB-->>Endpoint: Event Created
        Endpoint->>Lambda: Success Response
        Lambda->>APIGW: HTTP 201 Response
        APIGW->>Client: HTTP 201 Response
    else API Key Invalid
        Lambda->>Lambda: Raise UnauthorizedError
        Lambda->>APIGW: HTTP 401 Response
        APIGW->>Client: HTTP 401 Response
    end
    
    Lambda->>CloudWatch: Log Request/Response
```

**Flow Steps:**
1. **Request Arrival**: Client sends HTTP request to API Gateway
2. **Request ID Generation**: Lambda middleware generates/extracts request ID
3. **Authentication**: API key validated against DynamoDB
4. **Routing**: Request routed to appropriate endpoint
5. **Validation**: Pydantic validates request payload
6. **Database Operation**: DynamoDB operation executed
7. **Response Generation**: Success or error response created
8. **Logging**: Request/response logged to CloudWatch

---

## Deployment Architecture

AWS deployment architecture showing all services and their configuration.

```mermaid
graph TB
    subgraph "Frontend Deployment"
        S3[S3 Bucket<br/>triggers-api-frontend-*<br/>Static Assets]
        CF[CloudFront<br/>Distribution E1392QCULSIX14<br/>CDN + Custom Error Handling]
    end
    
    subgraph "API Deployment"
        APIGW[API Gateway<br/>Regional REST API<br/>Stage: prod<br/>CORS Enabled]
        LAMBDA[Lambda Function<br/>triggers-api-prod<br/>Runtime: Python 3.11<br/>Memory: 512MB<br/>Timeout: 30s]
        ROLE[IAM Role<br/>triggers-api-lambda-role<br/>DynamoDB + CloudWatch Permissions]
    end
    
    subgraph "Data Storage"
        EVENTS_TABLE[(Events Table<br/>triggers-api-events-prod<br/>On-Demand Billing<br/>TTL Enabled)]
        KEYS_TABLE[(API Keys Table<br/>triggers-api-keys-prod<br/>On-Demand Billing)]
        IDEMPOTENCY_TABLE[(Idempotency Table<br/>triggers-api-idempotency-prod<br/>On-Demand Billing<br/>TTL: 24h)]
    end
    
    subgraph "Monitoring"
        LOGS[CloudWatch Logs<br/>/aws/lambda/triggers-api-prod<br/>Retention: 7 days]
        METRICS[CloudWatch Metrics<br/>Lambda Metrics<br/>API Gateway Metrics]
    end
    
    CF --> S3
    APIGW --> LAMBDA
    LAMBDA --> ROLE
    LAMBDA --> EVENTS_TABLE
    LAMBDA --> KEYS_TABLE
    LAMBDA --> IDEMPOTENCY_TABLE
    LAMBDA --> LOGS
    LAMBDA --> METRICS
    
    style S3 fill:#e1f5ff
    style CF fill:#e1f5ff
    style APIGW fill:#fff4e1
    style LAMBDA fill:#ffe1f5
    style ROLE fill:#f0e1ff
    style EVENTS_TABLE fill:#e1ffe1
    style KEYS_TABLE fill:#e1ffe1
    style IDEMPOTENCY_TABLE fill:#e1ffe1
    style LOGS fill:#f0e1ff
    style METRICS fill:#f0e1ff
```

**Deployment Details:**
- **Frontend**: S3 static hosting + CloudFront CDN with custom error responses for SPA routing
- **API Gateway**: Regional REST API with `/v1/{proxy+}` catch-all route
- **Lambda**: Python 3.11 runtime, 512MB memory, 30s timeout
- **DynamoDB**: On-demand billing, TTL enabled for automatic cleanup
- **IAM**: Role with permissions for DynamoDB operations and CloudWatch logging

---

## Request Flow

Detailed step-by-step request processing flow.

```mermaid
flowchart TD
    START([HTTP Request Arrives]) --> MIDDLEWARE[Request ID Middleware<br/>Extract/Generate UUID]
    MIDDLEWARE --> AUTH_CHECK{API Key<br/>Present?}
    
    AUTH_CHECK -->|No| ERROR_401[Return 401<br/>Unauthorized]
    AUTH_CHECK -->|Yes| VALIDATE_KEY{API Key<br/>Valid?}
    
    VALIDATE_KEY -->|No| ERROR_401
    VALIDATE_KEY -->|Yes| ROUTE[Route to Endpoint<br/>Based on Path]
    
    ROUTE --> VALIDATE[Validate Request<br/>Pydantic Models]
    VALIDATE -->|Invalid| ERROR_400[Return 400<br/>Validation Error]
    VALIDATE -->|Valid| BUSINESS[Execute Business Logic]
    
    BUSINESS --> DB_OP[DynamoDB Operation]
    DB_OP -->|Success| RESPONSE[Generate Response<br/>Include Request ID]
    DB_OP -->|Error| ERROR_HANDLER[Error Handler<br/>Format Error Response]
    
    RESPONSE --> LOG[Log to CloudWatch<br/>Include Request ID]
    ERROR_HANDLER --> LOG
    LOG --> RETURN([Return HTTP Response])
    ERROR_401 --> LOG
    ERROR_400 --> LOG
    
    style START fill:#e1f5ff
    style MIDDLEWARE fill:#fff4e1
    style AUTH_CHECK fill:#ffe1f5
    style VALIDATE_KEY fill:#ffe1f5
    style ROUTE fill:#fff4e1
    style VALIDATE fill:#fff4e1
    style BUSINESS fill:#e1ffe1
    style DB_OP fill:#e1ffe1
    style RESPONSE fill:#e1f5ff
    style ERROR_HANDLER fill:#ffe1f5
    style LOG fill:#f0e1ff
    style RETURN fill:#e1f5ff
```

**Processing Steps:**
1. **Request ID Middleware**: Extracts `X-Request-ID` header or generates UUID v4
2. **Authentication Check**: Validates `X-API-Key` header
3. **Routing**: Routes to appropriate endpoint based on path
4. **Validation**: Pydantic validates request payload
5. **Business Logic**: Endpoint-specific logic execution
6. **Database Operation**: DynamoDB read/write operation
7. **Response Generation**: Success response with request ID
8. **Error Handling**: Standardized error response if errors occur
9. **Logging**: Structured logging to CloudWatch with request ID

---

## Component Descriptions

### FastAPI Application (`src/main.py`)

**Purpose**: Application entry point that orchestrates all components.

**Key Responsibilities:**
- Initialize FastAPI application
- Register API routers with version prefix (`/v1`)
- Configure middleware (request ID tracking, CORS)
- Register exception handlers for error standardization
- Create DynamoDB tables on startup
- Configure structured JSON logging

**Key Functions:**
- `handler`: Lambda handler function (Mangum adapter)
- Request ID middleware: Extracts/generates request ID
- Exception handlers: Standardize error responses

**Code Reference**: ```1:50:src/main.py```

---

### DynamoDB Storage (`src/database.py`)

**Purpose**: Abstracts all DynamoDB operations and table management.

**Key Responsibilities:**
- DynamoDB resource initialization (local vs AWS)
- Table creation and management
- Event CRUD operations
- Inbox querying with pagination
- API key validation queries
- Idempotency key management

**Key Functions:**
- `create_event()`: Create new event in Events table
- `get_event()`: Retrieve event by ID
- `acknowledge_event()`: Update event status to acknowledged
- `delete_event()`: Delete event from table
- `get_inbox()`: Query pending events with pagination and filtering
- `check_idempotency_key()`: Check for existing idempotency key
- `store_idempotency_key()`: Store idempotency key mapping

**Tables Managed:**
- Events table: `triggers-api-events-{stage}`
- API Keys table: `triggers-api-keys-{stage}`
- Idempotency table: `triggers-api-idempotency-{stage}`

**Code Reference**: ```1:50:src/database.py```

---

### Authentication Layer (`src/auth.py`)

**Purpose**: Validates API keys for authenticated endpoints.

**Key Responsibilities:**
- Extract API key from `X-API-Key` header
- Validate API key (local mode or AWS mode)
- Support dual-mode authentication (local/AWS)
- Raise `UnauthorizedError` for invalid keys

**Key Functions:**
- `validate_api_key()`: FastAPI dependency for API key validation
- `get_api_key()`: Dependency function used by endpoints

**Authentication Modes:**
- **Local Mode** (`AUTH_MODE=local`): Hardcoded test key `test-api-key-12345`
- **AWS Mode** (`AUTH_MODE=aws`): Validates against DynamoDB API Keys table

**Code Reference**: ```1:50:src/auth.py```

---

### Error Handling System (`src/exceptions.py`)

**Purpose**: Provides standardized error handling across the application.

**Key Responsibilities:**
- Define custom exception classes
- Standardize error response format
- Include request ID in all error responses
- Provide actionable error messages

**Exception Classes:**
- `APIException`: Base exception class
- `ValidationError` (400): Invalid request payload
- `UnauthorizedError` (401): Missing/invalid API key
- `NotFoundError` (404): Resource not found
- `ConflictError` (409): Resource conflict
- `PayloadTooLargeError` (413): Payload exceeds 400KB
- `RateLimitExceededError` (429): Rate limit exceeded
- `InternalError` (500): Server error

**Error Response Format:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {},
    "request_id": "uuid-v4"
  }
}
```

**Code Reference**: Check `src/exceptions.py` and error handlers in `src/main.py`

---

### Endpoint Structure (`src/endpoints/`)

**Purpose**: Handles HTTP requests and delegates to business logic.

**Endpoints:**
- **health.py**: `GET /v1/health` - Health check endpoint
- **events.py**: 
  - `POST /v1/events` - Create event
  - `GET /v1/events/{event_id}` - Get event details
  - `POST /v1/events/{event_id}/ack` - Acknowledge event
  - `DELETE /v1/events/{event_id}` - Delete event
- **inbox.py**: `GET /v1/inbox` - Retrieve pending events with pagination

**Key Responsibilities:**
- Route HTTP requests to business logic
- Validate request payloads (Pydantic)
- Handle errors and return standardized responses
- Include request ID in all responses

**Code Reference**: ```1:30:src/endpoints/events.py```

---

### Data Models (`src/models.py`)

**Purpose**: Defines request and response schemas with Pydantic validation.

**Key Models:**
- **Request Models**: `EventCreate`, `InboxQueryParams`
- **Response Models**: `EventResponse`, `EventDetailResponse`, `InboxResponse`, `AckResponse`, `DeleteResponse`, `ErrorResponse`
- **Metadata Models**: `EventMetadata`, `PaginationInfo`

**Key Responsibilities:**
- Validate request payloads
- Serialize response data
- Enforce data constraints (field lengths, required fields, enums)
- Provide type hints for API documentation

**Code Reference**: Check `src/models.py`

---

## Design Patterns

### API Versioning Pattern

All endpoints are prefixed with `/v1` using FastAPI's `APIRouter`:

```python
v1_router = APIRouter(prefix="/v1")
app.include_router(v1_router)
```

This allows future API versions (`/v2`, `/v3`) without breaking changes.

### Request ID Tracking Pattern

Request ID is extracted from `X-Request-ID` header or generated as UUID v4, stored in `request.state.request_id`, and included in all responses for request correlation.

### Dependency Injection Pattern (Authentication)

FastAPI dependency injection is used for API key validation:

```python
@router.post("/events")
async def create_event(
    event: EventCreate,
    api_key: str = Depends(get_api_key)
):
    # Endpoint logic
```

### Conditional Update Pattern (Idempotency)

DynamoDB conditional updates prevent race conditions:

```python
UpdateExpression = "SET #status = :status"
ConditionExpression = "#status = :pending"
```

### Cursor-Based Pagination Pattern

Pagination uses DynamoDB `LastEvaluatedKey` encoded as base64 JSON:

```python
cursor = base64.b64encode(json.dumps(last_evaluated_key).encode()).decode()
```

### Error Response Standardization

All errors follow a consistent format with error code, message, details, and request ID for easy debugging and support.

---

## See Also

- [API Reference](API.md) - Complete endpoint documentation
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- [Performance Tuning](PERFORMANCE.md) - Optimization best practices
- [Usage Examples](EXAMPLES.md) - Code examples and patterns

