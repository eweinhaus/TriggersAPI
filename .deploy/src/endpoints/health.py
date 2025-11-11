"""Health check endpoint"""

from fastapi import APIRouter, Request
from src.models import HealthResponse
from src.utils import get_iso_timestamp
from src.utils.logging import get_logger
from src.utils.metrics import record_latency, record_success, record_request_count

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="""
    Health check endpoint to verify API availability and status.
    
    **Use Cases:**
    - Monitor API uptime and availability
    - Verify API version
    - Check system status before making requests
    
    **No authentication required** - This endpoint is publicly accessible.
    """,
    responses={
        200: {
            "description": "API is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2025-11-10T12:00:00.000000Z",
                        "version": "1.0.0"
                    }
                }
            }
        }
    }
)
async def health_check(request: Request = None):
    """
    Health check endpoint.
    No authentication required.
    """
    duration_ms = getattr(request.state, 'duration_ms', None) if request else None
    
    # Record metrics
    endpoint = '/v1/health'
    method = 'GET'
    if duration_ms:
        record_latency(endpoint, method, duration_ms)
    record_success(endpoint, method)
    record_request_count(endpoint, method)
    
    logger.info(
        "Health check",
        extra={
            'operation': 'health_check',
            'status': 'healthy',
            'status_code': 200,
            'duration_ms': duration_ms,
        }
    )
    
    return HealthResponse(
        status="healthy",
        timestamp=get_iso_timestamp(),
        version="1.0.0"
    )

