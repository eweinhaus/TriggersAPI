"""API key management endpoints: rotation, versions"""

from fastapi import APIRouter, Request, Depends, Path, Query
from src.models import ErrorDetail
from src.database import rotate_api_key, get_api_key_versions
from src.auth import get_api_key
from src.exceptions import NotFoundError, InternalError
from src.utils import format_not_found_error

router = APIRouter()


@router.post(
    "/api-keys/{key_id}/rotate",
    status_code=200,
    tags=["api-keys"],
    summary="Rotate API key",
    description="""
    Rotate an API key by creating a new version.
    
    **Rotation Process:**
    1. Creates a new API key version
    2. Marks old key as "rotating" (still valid during transition)
    3. Sets expiration date for old key (default: 7 days)
    4. Returns new key details
    
    **Transition Period:**
    - Both old and new keys work during transition period
    - Old key expires after transition period
    - Use this time to update all clients with new key
    
    **Security:**
    - New API key is only returned once in this response
    - Store it securely immediately
    """,
    responses={
        200: {
            "description": "Key rotated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "api_key": "tr_new-key-here",
                        "version": 2,
                        "previous_version": "tr_old-key-here",
                        "expires_at": "2025-11-18T12:00:00.000000Z",
                        "rotated_at": "2025-11-11T12:00:00.000000Z",
                        "request_id": "660e8400-e29b-41d4-a716-446655440001"
                    }
                }
            }
        },
        404: {"description": "API key not found"},
        401: {"description": "Unauthorized"}
    }
)
async def rotate_key_endpoint(
    request: Request,
    key_id: str = Path(..., description="API key to rotate"),
    transition_days: int = Query(7, ge=1, le=90, description="Transition period in days (1-90)"),
    authenticated_api_key: str = Depends(get_api_key)
):
    """Rotate API key."""
    # Verify key exists and belongs to requester (for now, allow if authenticated)
    # In production, you might want to check ownership
    try:
        result = rotate_api_key(key_id, transition_days)
        
        return {
            **result,
            "request_id": request.state.request_id
        }
    except NotFoundError:
        raise NotFoundError(
            message="API key not found",
            details=format_not_found_error("API Key", key_id),
            request_id=request.state.request_id
        )
    except Exception as e:
        raise InternalError(
            message="Failed to rotate API key",
            details={"error": str(e)},
            request_id=request.state.request_id
        )


@router.get(
    "/api-keys/{key_id}/versions",
    status_code=200,
    tags=["api-keys"],
    summary="List API key versions",
    description="""
    Get version history for an API key.
    
    **Returns:**
    - List of all versions (newest first)
    - Status, creation date, rotation date, expiration date
    - Does not include actual key values for security
    """,
    responses={
        200: {
            "description": "Key versions",
            "content": {
                "application/json": {
                    "example": {
                        "versions": [
                            {
                                "version": 2,
                                "status": "active",
                                "created_at": "2025-11-11T12:00:00.000000Z",
                                "rotated_at": "2025-11-11T12:00:00.000000Z",
                                "expires_at": None
                            },
                            {
                                "version": 1,
                                "status": "rotating",
                                "created_at": "2025-11-01T12:00:00.000000Z",
                                "rotated_at": "2025-11-11T12:00:00.000000Z",
                                "expires_at": "2025-11-18T12:00:00.000000Z"
                            }
                        ],
                        "request_id": "660e8400-e29b-41d4-a716-446655440001"
                    }
                }
            }
        },
        404: {"description": "API key not found"},
        401: {"description": "Unauthorized"}
    }
)
async def list_key_versions_endpoint(
    request: Request,
    key_id: str = Path(..., description="API key ID"),
    authenticated_api_key: str = Depends(get_api_key)
):
    """List all versions of an API key."""
    try:
        versions = get_api_key_versions(key_id)
        
        if not versions:
            raise NotFoundError(
                message="API key not found",
                details=format_not_found_error("API Key", key_id),
                request_id=request.state.request_id
            )
        
        return {
            "versions": versions,
            "request_id": request.state.request_id
        }
    except NotFoundError:
        raise
    except Exception as e:
        raise InternalError(
            message="Failed to get key versions",
            details={"error": str(e)},
            request_id=request.state.request_id
        )

