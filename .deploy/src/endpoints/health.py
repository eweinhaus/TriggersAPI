"""Health check endpoint"""

from fastapi import APIRouter
from src.models import HealthResponse
from src.utils import get_iso_timestamp

router = APIRouter()


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
async def health_check():
    """
    Health check endpoint.
    No authentication required.
    """
    return HealthResponse(
        status="healthy",
        timestamp=get_iso_timestamp(),
        version="1.0.0"
    )

