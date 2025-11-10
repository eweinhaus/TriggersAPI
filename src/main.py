"""FastAPI application entry point"""

import logging
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from mangum import Mangum

from src.database import create_tables
from src.exceptions import APIException, ValidationError, InternalError
from src.utils import generate_uuid
from src.models import ErrorResponse, ErrorDetail
from src.endpoints import health, events, inbox

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Zapier Triggers API",
    description="Unified event ingestion system for Zapier",
    version="1.0.0"
)

# Create v1 router
v1_router = app.router  # We'll use the main router with prefix

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Extract or generate request ID and add to request state and response."""
    request_id = request.headers.get("X-Request-ID") or generate_uuid()
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


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
    
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request payload",
                "details": {"validation_errors": errors},
                "request_id": request_id
            }
        }
    )


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions."""
    request_id = getattr(request.state, 'request_id', generate_uuid())
    
    if log_level == 'DEBUG':
        logger.exception(f"API Exception: {exc.error_code} - {exc.message}")
    else:
        logger.error(f"API Exception: {exc.error_code} - {exc.message}")
    
    return JSONResponse(
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
    
    if log_level == 'DEBUG':
        logger.exception("Unexpected error occurred")
    else:
        logger.error(f"Unexpected error: {str(exc)}")
    
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


# Startup event
@app.on_event("startup")
async def startup_event():
    """Create DynamoDB tables on application startup."""
    try:
        create_tables()
        logger.info("Application startup complete - tables created")
    except Exception as e:
        logger.error(f"Failed to create tables on startup: {e}")
        # Don't crash - tables might already exist


# Lambda handler for AWS deployment
mangum_handler = Mangum(app, lifespan="off")

def handler(event, context):
    """Lambda handler function wrapper for Mangum."""
    return mangum_handler(event, context)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)

