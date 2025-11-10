"""Event endpoints: create, acknowledge, delete"""

from uuid import UUID
from fastapi import APIRouter, Request, Depends, HTTPException
from src.models import EventCreate, EventResponse, AckResponse, DeleteResponse
from src.database import create_event, acknowledge_event, delete_event, get_event
from src.auth import get_api_key
from src.exceptions import NotFoundError, ConflictError, PayloadTooLargeError, InternalError
from src.utils import validate_payload_size
from botocore.exceptions import ClientError

router = APIRouter()


@router.post("/events", response_model=EventResponse, status_code=201)
async def create_event_endpoint(
    event_data: EventCreate,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Create a new event.
    
    Requires API key authentication.
    """
    # Validate payload size
    try:
        validate_payload_size(event_data.payload)
    except ValueError as e:
        raise PayloadTooLargeError(str(e))
    
    # Create event in database
    try:
        event = create_event(
            source=event_data.source,
            event_type=event_data.event_type,
            payload=event_data.payload,
            metadata=event_data.metadata
        )
    except Exception as e:
        raise InternalError(f"Failed to create event: {e}")
    
    request_id = request.state.request_id
    
    return EventResponse(
        event_id=event['event_id'],
        created_at=event['created_at'],
        status=event['status'],
        message="Event ingested successfully",
        request_id=request_id
    )


@router.post("/events/{event_id}/ack", response_model=AckResponse)
async def acknowledge_event_endpoint(
    event_id: UUID,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Acknowledge an event.
    
    Requires API key authentication.
    """
    event_id_str = str(event_id)
    request_id = request.state.request_id
    
    # Acknowledge event
    updated_event = acknowledge_event(event_id_str)
    
    if updated_event is None:
        # Check if event exists
        event = get_event(event_id_str)
        if event is None:
            raise NotFoundError(f"Event {event_id_str} not found")
        else:
            # Event exists but acknowledge failed (already acknowledged)
            raise ConflictError(f"Event {event_id_str} already acknowledged")
    
    return AckResponse(
        event_id=updated_event['event_id'],
        status=updated_event['status'],
        acknowledged_at=updated_event['acknowledged_at'],
        message="Event acknowledged successfully",
        request_id=request_id
    )


@router.delete("/events/{event_id}", response_model=DeleteResponse)
async def delete_event_endpoint(
    event_id: UUID,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Delete an event.
    
    Requires API key authentication.
    Idempotent operation.
    """
    event_id_str = str(event_id)
    request_id = request.state.request_id
    
    # Delete event (idempotent)
    delete_event(event_id_str)
    
    return DeleteResponse(
        event_id=event_id_str,
        message="Event deleted successfully",
        request_id=request_id
    )

