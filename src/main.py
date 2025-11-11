"""FastAPI application entry point"""

import logging
import os
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import ValidationError as PydanticValidationError
from mangum import Mangum

from src.database import create_tables
from src.exceptions import APIException, ValidationError, InternalError
from src.utils import generate_uuid
from src.utils.logging import get_logger, set_request_context, clear_request_context
from src.utils.metrics import flush_metrics, record_error, record_latency, record_request_count
from src.models import ErrorResponse, ErrorDetail
from src.endpoints import health, events, inbox, webhooks, api_keys, analytics

# Configure structured JSON logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    handlers=[logging.StreamHandler()],
    force=True  # Override any existing configuration
)
# Configure root logger with JSON formatter
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    from src.utils.logging import JSONFormatter
    handler.setFormatter(JSONFormatter())

logger = get_logger(__name__)

# OpenAPI tags metadata
tags_metadata = [
    {
        "name": "health",
        "description": "Health check endpoints. No authentication required. Use these endpoints to verify API availability and status.",
    },
    {
        "name": "events",
        "description": "Event management endpoints. Create, retrieve, acknowledge, and delete events. All endpoints require API key authentication.",
    },
    {
        "name": "inbox",
        "description": "Inbox endpoints. Retrieve pending events with pagination and filtering. Requires API key authentication.",
    },
    {
        "name": "webhooks",
        "description": "Webhook management endpoints. Create, update, delete, and test webhooks for push-based event delivery. Requires API key authentication.",
    },
    {
        "name": "api-keys",
        "description": "API key management endpoints. Rotate keys and view version history. Requires API key authentication.",
    },
    {
        "name": "analytics",
        "description": "Analytics endpoints. Get event insights, metrics, and export data. Requires API key authentication.",
    },
]

# Initialize FastAPI app
app = FastAPI(
    title="Zapier Triggers API",
    description="""
    A unified, real-time event ingestion system that enables external systems to send events into Zapier via a standardized RESTful interface.
    
    ## Features
    
    - **Event Ingestion**: Send events with flexible payloads
    - **Idempotency**: Prevent duplicate events using idempotency keys
    - **Event Management**: Retrieve, acknowledge, and delete events
    - **Inbox System**: Query pending events with pagination and filtering
    - **Request Tracking**: All requests include request IDs for correlation
    
    ## Authentication
    
    Most endpoints require API key authentication via the `X-API-Key` header.
    Get your API key from your account settings.
    
    ## Rate Limits
    
    API requests are subject to rate limiting. See error responses for rate limit information.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
)


# Custom OpenAPI schema with security scheme
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication. Include this header in all authenticated requests. Get your API key from your account settings."
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add CORS middleware
# Note: allow_credentials=True cannot be used with allow_origins=["*"]
# For MVP, we allow all origins without credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP, allow all origins
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "DELETE", "OPTIONS", "PUT"],
    allow_headers=["Content-Type", "X-API-Key", "X-Request-ID", "X-Signature", "X-Signature-Timestamp", "X-Signature-Version"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"],  # Expose rate limit headers
    max_age=3600,
)

# Add optional signature validation middleware
# Only enabled if ENABLE_REQUEST_SIGNING=true
enable_signing = os.getenv('ENABLE_REQUEST_SIGNING', 'false').lower() == 'true'
if enable_signing:
    from src.middleware.signature_validation import signature_validation_middleware
    app.middleware("http")(signature_validation_middleware)

# Create v1 router
v1_router = app.router  # We'll use the main router with prefix

# Request ID and context middleware with timing
@app.middleware("http")
async def add_request_id_and_context(request: Request, call_next):
    """Extract or generate request ID, set logging context, and measure request duration."""
    # Generate or extract request ID
    request_id = request.headers.get("X-Request-ID") or generate_uuid()
    request.state.request_id = request_id
    
    # Extract request context for logging
    api_key = request.headers.get("X-API-Key")
    endpoint = request.url.path
    method = request.method
    
    # Set logging context
    set_request_context(
        request_id=request_id,
        api_key=api_key,
        endpoint=endpoint,
        method=method
    )
    
    # Measure request duration
    start_time = time.perf_counter()
    
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        request.state.duration_ms = duration_ms
        
        # Add duration to response headers for debugging
        response.headers["X-Request-ID"] = request_id
        
        return response
    finally:
        # Flush metrics and clear logging context after request
        try:
            flush_metrics()
        except Exception as e:
            # Don't fail request if metrics flush fails
            logger.warning(
                "Failed to flush metrics",
                extra={'error': str(e)}
            )
        clear_request_context()


# IP validation middleware (after auth, before rate limit)
from src.middleware.ip_validation import ip_validation_middleware
app.middleware("http")(ip_validation_middleware)

# Rate limiting middleware (after IP validation, before endpoints)
from src.middleware.rate_limit import rate_limit_middleware
app.middleware("http")(rate_limit_middleware)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI request validation errors (path/query params)."""
    request_id = getattr(request.state, 'request_id', generate_uuid())
    
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": {"validation_errors": errors},
                "request_id": request_id
            }
        }
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_handler(request: Request, exc: PydanticValidationError):
    """Handle Pydantic validation errors."""
    request_id = getattr(request.state, 'request_id', generate_uuid())
    
    from src.utils import format_validation_error
    
    # Get first error for main message
    first_error = exc.errors()[0]
    field_path = ".".join(str(loc) for loc in first_error["loc"])
    error_msg = first_error["msg"]
    
    # Format enhanced error details
    details = format_validation_error(
        field=field_path,
        issue=error_msg,
        value=first_error.get("input")
    )
    
    # Include all validation errors
    all_errors = []
    for error in exc.errors():
        all_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    details["validation_errors"] = all_errors
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": f"The '{field_path}' field {error_msg.lower()}",
                "details": details,
                "request_id": request_id
            }
        }
    )


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions."""
    request_id = getattr(request.state, 'request_id', generate_uuid())
    duration_ms = getattr(request.state, 'duration_ms', None)
    
    # Record error metrics
    endpoint = request.url.path
    method = request.method
    if duration_ms:
        record_latency(endpoint, method, duration_ms)
    record_error(endpoint, method, exc.error_code)
    record_request_count(endpoint, method)
    
    # Log with structured context
    logger.error(
        "API Exception",
        extra={
            'error_code': exc.error_code,
            'error_message': exc.message,
            'status_code': exc.status_code,
            'duration_ms': duration_ms,
        }
    )
    
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id
            }
        }
    )
    
    # Add rate limit headers for rate limit errors
    if exc.error_code == "RATE_LIMIT_EXCEEDED":
        import time
        reset_timestamp = exc.details.get("reset_at", int(time.time()) + 60)
        retry_after = exc.details.get("retry_after", reset_timestamp - int(time.time()))
        response.headers["Retry-After"] = str(retry_after)
        response.headers["X-RateLimit-Limit"] = str(exc.details.get("limit", 1000))
        response.headers["X-RateLimit-Reset"] = str(reset_timestamp)
        response.headers["X-RateLimit-Remaining"] = "0"
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions."""
    request_id = getattr(request.state, 'request_id', generate_uuid())
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {},
                "request_id": request_id
            }
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, 'request_id', generate_uuid())
    duration_ms = getattr(request.state, 'duration_ms', None)
    
    # Log with structured context
    if log_level == 'DEBUG':
        logger.exception(
            "Unexpected error occurred",
            extra={
                'error_type': type(exc).__name__,
                'error_message': str(exc),
                'duration_ms': duration_ms,
            }
        )
    else:
        logger.error(
            "Unexpected error occurred",
            extra={
                'error_type': type(exc).__name__,
                'error_message': str(exc),
                'duration_ms': duration_ms,
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": {},
                "request_id": request_id
            }
        }
    )


# Include routers with /v1 prefix
app.include_router(health.router, prefix="/v1", tags=["health"])
app.include_router(events.router, prefix="/v1", tags=["events"])
app.include_router(inbox.router, prefix="/v1", tags=["inbox"])
app.include_router(webhooks.router, prefix="/v1", tags=["webhooks"])
app.include_router(api_keys.router, prefix="/v1", tags=["api-keys"])
app.include_router(analytics.router, prefix="/v1", tags=["analytics"])

# Explicit OPTIONS handler for CORS preflight (backup to CORS middleware)
@app.options("/{full_path:path}")
async def options_handler(request: Request):
    """Handle OPTIONS requests for CORS preflight."""
    return JSONResponse(
        content={},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-API-Key, X-Request-ID",
            "Access-Control-Expose-Headers": "X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After",
            "Access-Control-Max-Age": "3600",
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Create DynamoDB tables on application startup."""
    try:
        create_tables()
        logger.info("Application startup complete - tables created", extra={'event': 'startup'})
    except Exception as e:
        logger.error(
            "Failed to create tables on startup",
            extra={'event': 'startup', 'error': str(e)}
        )
        # Don't crash - tables might already exist


# Lambda handler for AWS deployment
mangum_handler = Mangum(app, lifespan="off")

def handler(event, context):
    """Lambda handler function wrapper for Mangum."""
    return mangum_handler(event, context)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)

