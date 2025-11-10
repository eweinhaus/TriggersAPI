"""Inbox endpoint: retrieve pending events"""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from src.models import InboxResponse
from src.database import query_pending_events
from src.auth import get_api_key
from src.utils import encode_cursor

router = APIRouter()


@router.get("/inbox", response_model=InboxResponse)
async def get_inbox(
    limit: int = Query(default=50, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
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

