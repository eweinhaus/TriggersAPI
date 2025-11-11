"""Inbox endpoint: retrieve pending events"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Query
from src.models import InboxResponse
from src.database import query_pending_events
from src.auth import get_api_key
from src.utils import encode_cursor
from src.utils.logging import get_logger
from src.utils.metrics import record_latency, record_success, record_request_count

router = APIRouter()
logger = get_logger(__name__)


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
    - Filter by `created_after` (ISO 8601 timestamp) to get events after a date
    - Filter by `created_before` (ISO 8601 timestamp) to get events before a date
    - Filter by `priority` (low, normal, high) to filter by event priority
    - Filter by metadata fields using `metadata_key` and `metadata_value` for exact matches
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
    created_after: Optional[str] = Query(default=None, description="Filter events created after this ISO 8601 timestamp (e.g., '2025-11-10T12:00:00Z')."),
    created_before: Optional[str] = Query(default=None, description="Filter events created before this ISO 8601 timestamp (e.g., '2025-11-10T12:00:00Z')."),
    priority: Optional[str] = Query(default=None, description="Filter events by priority level: low, normal, or high."),
    metadata_key: Optional[str] = Query(default=None, description="Metadata field key to filter by (use with metadata_value)."),
    metadata_value: Optional[str] = Query(default=None, description="Metadata field value to filter by (use with metadata_key)."),
    request: Request = None,
    api_key: str = Depends(get_api_key)
):
    """
    Retrieve pending events with pagination and filtering.
    
    Requires API key authentication.
    """
    request_id = request.state.request_id
    duration_ms = getattr(request.state, 'duration_ms', None)
    
    # Parse and validate date filters
    created_after_dt = None
    created_before_dt = None
    if created_after:
        try:
            created_after_dt = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
        except ValueError:
            from src.exceptions import ValidationError
            raise ValidationError(f"Invalid created_after format. Expected ISO 8601 timestamp, got: {created_after}")
    if created_before:
        try:
            created_before_dt = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
        except ValueError:
            from src.exceptions import ValidationError
            raise ValidationError(f"Invalid created_before format. Expected ISO 8601 timestamp, got: {created_before}")
    
    # Validate date range
    if created_after_dt and created_before_dt and created_after_dt > created_before_dt:
        from src.exceptions import ValidationError
        raise ValidationError("created_after must be before created_before")
    
    # Validate priority
    if priority and priority not in ['low', 'normal', 'high']:
        from src.exceptions import ValidationError
        raise ValidationError(f"Invalid priority. Must be one of: low, normal, high. Got: {priority}")
    
    # Validate metadata filters
    if (metadata_key and not metadata_value) or (metadata_value and not metadata_key):
        from src.exceptions import ValidationError
        raise ValidationError("Both metadata_key and metadata_value must be provided together")
    
    # Build metadata filter dict
    metadata_filters = None
    if metadata_key and metadata_value:
        metadata_filters = {metadata_key: metadata_value}
    
    # Query pending events
    result = query_pending_events(
        limit=limit,
        cursor=cursor,
        source=source,
        event_type=event_type,
        created_after=created_after_dt.isoformat().replace('+00:00', 'Z') if created_after_dt else None,
        created_before=created_before_dt.isoformat().replace('+00:00', 'Z') if created_before_dt else None,
        priority=priority,
        metadata_filters=metadata_filters
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
            logger.warning(
                "Failed to encode cursor",
                extra={
                    'operation': 'get_inbox',
                    'error': str(e),
                }
            )
    
    pagination = {
        "limit": limit
    }
    if next_cursor:
        pagination["next_cursor"] = next_cursor
    
    # Record metrics
    endpoint = '/v1/inbox'
    method = 'GET'
    if duration_ms:
        record_latency(endpoint, method, duration_ms)
    record_success(endpoint, method)
    record_request_count(endpoint, method)
    
    logger.info(
        "Inbox query completed",
        extra={
            'operation': 'get_inbox',
            'result_count': len(events),
            'limit': limit,
            'has_cursor': cursor is not None,
            'has_next_cursor': next_cursor is not None,
            'source_filter': source,
            'event_type_filter': event_type,
            'created_after_filter': created_after,
            'created_before_filter': created_before,
            'priority_filter': priority,
            'metadata_filter': metadata_filters,
            'status_code': 200,
            'duration_ms': duration_ms,
        }
    )
    
    return InboxResponse(
        events=events,
        pagination=pagination,
        request_id=request_id
    )

