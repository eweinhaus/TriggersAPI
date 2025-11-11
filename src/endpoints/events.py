"""Event endpoints: create, acknowledge, delete"""

from uuid import UUID
from fastapi import APIRouter, Request, Depends, HTTPException, Path
from src.models import EventCreate, EventResponse, EventDetailResponse, AckResponse, DeleteResponse
from src.database import create_event, acknowledge_event, delete_event, get_event
from src.auth import get_api_key
from src.exceptions import NotFoundError, ConflictError, PayloadTooLargeError, InternalError
from src.utils import validate_payload_size, format_not_found_error, format_conflict_error
from botocore.exceptions import ClientError

router = APIRouter()


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=201,
    tags=["events"],
    summary="Create a new event",
    description="""
    Ingest a new event into the system.
    
    **Features:**
    - Flexible payload structure (any valid JSON object)
    - Idempotency support via `metadata.idempotency_key`
    - Priority levels (low, normal, high)
    - Correlation ID tracking
    
    **Idempotency:** 
    If an event with the same idempotency key already exists within 24 hours, 
    the existing event is returned instead of creating a new one. This prevents 
    duplicate event creation in case of retries.
    
    **Payload Size Limit:** 400KB maximum
    
    **Event Status:** Events are created with status "pending" until acknowledged.
    """,
    responses={
        201: {
            "description": "Event created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "event_id": "550e8400-e29b-41d4-a716-446655440000",
                        "created_at": "2025-11-10T12:00:00.000000Z",
                        "status": "pending",
                        "message": "Event ingested successfully",
                        "request_id": "660e8400-e29b-41d4-a716-446655440001"
                    }
                }
            }
        },
        400: {
            "description": "Validation error - Invalid request payload",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "The 'source' field is required and cannot be empty",
                            "details": {
                                "field": "source",
                                "issue": "source field is required and cannot be empty",
                                "suggestion": "Provide a non-empty source value"
                            },
                            "request_id": "660e8400-e29b-41d4-a716-446655440001"
                        }
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
        },
        413: {
            "description": "Payload too large - Exceeds 400KB limit",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": "Payload size exceeds 400KB limit",
                            "details": {},
                            "request_id": "660e8400-e29b-41d4-a716-446655440001"
                        }
                    }
                }
            }
        }
    }
)
async def create_event_endpoint(
    event_data: EventCreate,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Create a new event.
    
    Requires API key authentication.
    Supports idempotency via metadata.idempotency_key.
    """
    # Validate payload size
    try:
        validate_payload_size(event_data.payload)
    except ValueError as e:
        raise PayloadTooLargeError(str(e))
    
    # Extract idempotency key from metadata
    idempotency_key = None
    if event_data.metadata and 'idempotency_key' in event_data.metadata:
        idempotency_key = event_data.metadata.get('idempotency_key')
    
    # Create event in database
    try:
        event = create_event(
            source=event_data.source,
            event_type=event_data.event_type,
            payload=event_data.payload,
            metadata=event_data.metadata,
            idempotency_key=idempotency_key
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


@router.get(
    "/events/{event_id}",
    response_model=EventDetailResponse,
    tags=["events"],
    summary="Get event details",
    description="""
    Retrieve detailed information about a specific event by its ID.
    
    Returns complete event information including:
    - Event payload and metadata
    - Current status (pending or acknowledged)
    - Timestamps (created_at, acknowledged_at if applicable)
    - Source and event type
    
    **Use Cases:**
    - Verify event details after creation
    - Check event status before processing
    - Retrieve event data for processing
    """,
    responses={
        200: {
            "description": "Event found and returned",
            "content": {
                "application/json": {
                    "example": {
                        "event_id": "550e8400-e29b-41d4-a716-446655440000",
                        "created_at": "2025-11-10T12:00:00.000000Z",
                        "source": "my-app",
                        "event_type": "user.created",
                        "payload": {"user_id": "123", "name": "John Doe"},
                        "status": "pending",
                        "metadata": {"priority": "normal"},
                        "acknowledged_at": None,
                        "request_id": "660e8400-e29b-41d4-a716-446655440001"
                    }
                }
            }
        },
        404: {
            "description": "Event not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "Event with ID '550e8400-e29b-41d4-a716-446655440000' was not found",
                            "details": {
                                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                                "suggestion": "Verify the event ID is correct and the event exists"
                            },
                            "request_id": "660e8400-e29b-41d4-a716-446655440001"
                        }
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
async def get_event_endpoint(
    event_id: UUID = Path(..., description="UUID v4 of the event to retrieve"),
    request: Request = None,
    api_key: str = Depends(get_api_key)
):
    """
    Retrieve detailed information about a specific event.
    
    Requires API key authentication.
    """
    event_id_str = str(event_id)
    request_id = request.state.request_id
    
    # Get event from database
    event = get_event(event_id_str)
    
    if event is None:
        raise NotFoundError(
            f"Event with ID '{event_id_str}' was not found",
            details={
                "event_id": event_id_str,
                "suggestion": "Verify the event ID is correct and the event exists"
            }
        )
    
    # Build response
    return EventDetailResponse(
        event_id=event['event_id'],
        created_at=event['created_at'],
        source=event['source'],
        event_type=event['event_type'],
        payload=event['payload'],
        status=event['status'],
        metadata=event.get('metadata'),
        acknowledged_at=event.get('acknowledged_at'),
        request_id=request_id
    )


@router.post(
    "/events/{event_id}/ack",
    response_model=AckResponse,
    tags=["events"],
    summary="Acknowledge an event",
    description="""
    Mark an event as acknowledged.
    
    **Behavior:**
    - Changes event status from "pending" to "acknowledged"
    - Records acknowledgment timestamp
    - Prevents duplicate acknowledgments (idempotent)
    
    **Conflict Scenarios:**
    - If event is already acknowledged, returns 409 Conflict
    - If event doesn't exist, returns 404 Not Found
    
    **Use Cases:**
    - Mark events as processed after handling
    - Prevent duplicate processing
    - Track event processing status
    """,
    responses={
        200: {
            "description": "Event acknowledged successfully",
            "content": {
                "application/json": {
                    "example": {
                        "event_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "acknowledged",
                        "acknowledged_at": "2025-11-10T12:05:00.000000Z",
                        "message": "Event acknowledged successfully",
                        "request_id": "660e8400-e29b-41d4-a716-446655440001"
                    }
                }
            }
        },
        404: {
            "description": "Event not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "Event with ID '550e8400-e29b-41d4-a716-446655440000' was not found",
                            "details": {
                                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                                "suggestion": "Verify the event ID is correct and the event exists"
                            },
                            "request_id": "660e8400-e29b-41d4-a716-446655440001"
                        }
                    }
                }
            }
        },
        409: {
            "description": "Conflict - Event already acknowledged",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "CONFLICT",
                            "message": "Event '550e8400-e29b-41d4-a716-446655440000' has already been acknowledged",
                            "details": {
                                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                                "current_status": "acknowledged",
                                "acknowledged_at": "2025-11-10T12:05:00.000000Z"
                            },
                            "request_id": "660e8400-e29b-41d4-a716-446655440001"
                        }
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
async def acknowledge_event_endpoint(
    event_id: UUID = Path(..., description="UUID v4 of the event to acknowledge"),
    request: Request = None,
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
            raise NotFoundError(
                f"Event with ID '{event_id_str}' was not found",
                details=format_not_found_error("Event", event_id_str)
            )
        else:
            # Event exists but acknowledge failed (already acknowledged)
            raise ConflictError(
                f"Event '{event_id_str}' has already been acknowledged",
                details=format_conflict_error(
                    "Event",
                    event_id_str,
                    {
                        "current_status": event.get('status', 'acknowledged'),
                        "acknowledged_at": event.get('acknowledged_at')
                    }
                )
            )
    
    return AckResponse(
        event_id=updated_event['event_id'],
        status=updated_event['status'],
        acknowledged_at=updated_event['acknowledged_at'],
        message="Event acknowledged successfully",
        request_id=request_id
    )


@router.delete(
    "/events/{event_id}",
    response_model=DeleteResponse,
    tags=["events"],
    summary="Delete an event",
    description="""
    Delete an event from the system.
    
    **Behavior:**
    - Permanently removes the event
    - Idempotent operation (safe to call multiple times)
    - Returns success even if event doesn't exist
    
    **Use Cases:**
    - Clean up processed events
    - Remove unwanted events
    - Maintain data hygiene
    """,
    responses={
        200: {
            "description": "Event deleted successfully (or didn't exist)",
            "content": {
                "application/json": {
                    "example": {
                        "event_id": "550e8400-e29b-41d4-a716-446655440000",
                        "message": "Event deleted successfully",
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
async def delete_event_endpoint(
    event_id: UUID = Path(..., description="UUID v4 of the event to delete"),
    request: Request = None,
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

