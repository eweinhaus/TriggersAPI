"""Health check endpoint"""

from fastapi import APIRouter
from src.models import HealthResponse
from src.utils import get_iso_timestamp

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
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

