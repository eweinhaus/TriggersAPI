"""Inbox endpoint: retrieve pending events"""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from src.models import InboxResponse
from src.database import query_pending_events
from src.auth import get_api_key
from src.utils import encode_cursor

router = APIRouter()


@router.get(
    "/inbox",
    response_model=InboxResponse,
    tags=["inbox"],
    summary="Get pending events",
    description="""
    Retrieve pending events with pagination and filtering.
    
    **Pagination:**
    - Uses cursor-based pagination for efficient large result sets
    - Use `limit` to control page size (1-100)
    - Use `cursor` from previous response to get next page
    - No total count available (DynamoDB limitation)
    
    **Filtering:**
    - Filter by `source` to get events from specific sources
    - Filter by `event_type` to get specific event types
    - Filters can be combined
    - Filters are applied after query (may affect pagination)
    
    **Use Cases:**
    - Poll for new events to process
    - Get events from specific sources
    - Process events by type
    - Implement event processing workflows
    """,
    responses={
        200: {
            "description": "Pending events retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "events": [
                            {
                                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                                "created_at": "2025-11-10T12:00:00.000000Z",
                                "source": "my-app",
                                "event_type": "user.created",
                                "payload": {"user_id": "123"},
                                "status": "pending",
                                "metadata": {"priority": "normal"}
                            }
                        ],
                        "pagination": {
                            "limit": 50,
                            "next_cursor": "eyJldmVudF9pZCI6ICI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJjcmVhdGVkX2F0IjogIjIwMjUtMTEtMTBUMTI6MDA6MDAuMDAwMDAwWiJ9"
                        },
                        "request_id": "660e8400-e29b-41d4-a716-446655440001"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing API key",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Invalid or missing API key",
                            "details": {},
                            "request_id": "660e8400-e29b-41d4-a716-446655440001"
                        }
                    }
                }
            }
        }
    }
)
async def get_inbox(
    limit: int = Query(default=50, ge=1, le=100, description="Number of events to return (1-100). Default: 50"),
    cursor: Optional[str] = Query(default=None, description="Pagination cursor from previous response (base64-encoded). Use to get next page of results."),
    source: Optional[str] = Query(default=None, min_length=1, description="Filter events by source identifier. Only events matching this source will be returned."),
    event_type: Optional[str] = Query(default=None, min_length=1, description="Filter events by event type. Only events matching this type will be returned."),
    request: Request = None,
    api_key: str = Depends(get_api_key)
):
    """
    Retrieve pending events with pagination and filtering.
    
    Requires API key authentication.
    """
    request_id = request.state.request_id
    
    # Query pending events
    result = query_pending_events(
        limit=limit,
        cursor=cursor,
        source=source,
        event_type=event_type
    )
    
    events = result['events']
    last_evaluated_key = result.get('last_evaluated_key')
    
    # Encode cursor if more results exist
    next_cursor = None
    if last_evaluated_key:
        try:
            next_cursor = encode_cursor(last_evaluated_key)
        except Exception as e:
            # Log error but don't fail the request
            pass
    
    pagination = {
        "limit": limit
    }
    if next_cursor:
        pagination["next_cursor"] = next_cursor
    
    return InboxResponse(
        events=events,
        pagination=pagination,
        request_id=request_id
    )

