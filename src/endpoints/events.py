"""Event endpoints: create, acknowledge, delete"""

import time
from uuid import UUID
from fastapi import APIRouter, Request, Depends, HTTPException, Path
from src.models import EventCreate, EventResponse, EventDetailResponse, AckResponse, DeleteResponse, BulkEventCreate, BulkEventAcknowledge, BulkEventDelete, BulkEventResponse, BulkItemError
from src.database import create_event, acknowledge_event, delete_event, get_event, bulk_create_events, bulk_acknowledge_events, bulk_delete_events
from src.auth import get_api_key
from src.exceptions import NotFoundError, ConflictError, PayloadTooLargeError, InternalError
from src.utils import validate_payload_size, format_not_found_error, format_conflict_error, generate_uuid, get_iso_timestamp
from src.utils.logging import get_logger
from src.utils.metrics import record_latency, record_success, record_error, record_request_count
from botocore.exceptions import ClientError

router = APIRouter()
logger = get_logger(__name__)


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
        
        # Trigger webhook delivery (non-blocking)
        try:
            from src.database import get_active_webhooks_for_event
            from src.utils.sqs import send_webhook_message
            
            # Get active webhooks for this event type
            webhooks = get_active_webhooks_for_event(api_key, event_data.event_type)
            
            # Send to SQS for each matching webhook
            for webhook in webhooks:
                webhook_id = webhook['webhook_id']
                # Prepare event data for webhook (exclude internal fields)
                webhook_event_data = {
                    'event_id': event['event_id'],
                    'created_at': event['created_at'],
                    'source': event['source'],
                    'event_type': event['event_type'],
                    'payload': event['payload'],
                    'status': event['status']
                }
                if event.get('metadata'):
                    webhook_event_data['metadata'] = event['metadata']
                
                # Send to SQS queue (non-blocking, fire-and-forget)
                send_webhook_message(webhook_id, webhook_event_data)
        except Exception as webhook_error:
            # Log webhook error but don't fail event creation
            logger.warning(
                f"Failed to trigger webhook delivery: {webhook_error}",
                extra={
                    'event_id': event.get('event_id'),
                    'error': str(webhook_error)
                }
            )
    except Exception as e:
        # Record error metric
        endpoint = '/v1/events'
        method = 'POST'
        record_error(endpoint, method, 'INTERNAL_ERROR')
        record_request_count(endpoint, method)
        
        logger.error(
            "Failed to create event",
            extra={
                'operation': 'create_event',
                'source': event_data.source,
                'event_type': event_data.event_type,
                'error': str(e),
                'status_code': 500,
            }
        )
        raise InternalError(f"Failed to create event: {e}")
    
    request_id = request.state.request_id
    duration_ms = getattr(request.state, 'duration_ms', None)
    
    # Record metrics
    endpoint = '/v1/events'
    method = 'POST'
    if duration_ms:
        record_latency(endpoint, method, duration_ms)
    record_success(endpoint, method)
    record_request_count(endpoint, method)
    
    logger.info(
        "Event created successfully",
        extra={
            'operation': 'create_event',
            'event_id': event['event_id'],
            'source': event_data.source,
            'event_type': event_data.event_type,
            'status': event['status'],
            'status_code': 201,
            'duration_ms': duration_ms,
            'has_idempotency_key': idempotency_key is not None,
        }
    )
    
    return EventResponse(
        event_id=event['event_id'],
        created_at=event['created_at'],
        status=event['status'],
        message="Event ingested successfully",
        request_id=request_id
    )


@router.post(
    "/events/bulk",
    response_model=BulkEventResponse,
    status_code=201,
    tags=["events"],
    summary="Create multiple events",
    description="""
    Create multiple events in a single request.
    
    **Features:**
    - Create up to 25 events per request
    - Idempotency support via `metadata.idempotency_key` for each event
    - Partial success handling (returns both successful and failed items)
    - Efficient batch processing using DynamoDB batch operations
    
    **Response:**
    - `successful`: List of successfully created events
    - `failed`: List of failed items with error details and index
    - `request_id`: Request ID for correlation
    """,
    responses={
        201: {
            "description": "Bulk create completed (may have partial failures)",
        },
        400: {
            "description": "Validation error - Invalid request payload",
        },
        401: {
            "description": "Unauthorized - Invalid or missing API key",
        }
    }
)
async def bulk_create_events_endpoint(
    bulk_request: BulkEventCreate,
    request: Request = None,
    api_key: str = Depends(get_api_key)
):
    """
    Create multiple events in bulk.
    
    Requires API key authentication.
    """
    request_id = request.state.request_id
    
    # Prepare events for creation
    events_to_create = []
    for item in bulk_request.items:
        event_id = generate_uuid()
        created_at = get_iso_timestamp()
        status = "pending"
        ttl = int(time.time()) + (7 * 24 * 60 * 60)  # 7 days
        
        event = {
            'event_id': event_id,
            'created_at': created_at,
            'source': item.source,
            'event_type': item.event_type,
            'payload': item.payload,
            'status': status,
            'ttl': ttl
        }
        
        if item.metadata:
            event['metadata'] = item.metadata
        
        events_to_create.append(event)
    
    # Create events in bulk
    successful, failed = bulk_create_events(events_to_create, api_key)
    
    # Format successful events as EventResponse
    successful_responses = []
    for event in successful:
        successful_responses.append({
            'event_id': event['event_id'],
            'created_at': event['created_at'],
            'status': event['status'],
            'message': 'Event ingested successfully'
        })
    
    # Format failed items
    failed_items = []
    for fail in failed:
        failed_items.append(BulkItemError(
            index=fail['index'],
            error=fail['error']
        ))
    
    return BulkEventResponse(
        successful=successful_responses,
        failed=failed_items,
        request_id=request_id
    )


@router.post(
    "/events/bulk/ack",
    response_model=BulkEventResponse,
    tags=["events"],
    summary="Acknowledge multiple events",
    description="""
    Acknowledge multiple events in a single request.
    
    **Features:**
    - Acknowledge up to 25 events per request
    - Partial success handling (returns both successful and failed items)
    - Handles events that don't exist or are already acknowledged
    
    **Response:**
    - `successful`: List of successfully acknowledged events
    - `failed`: List of failed items with error details and index
    - `request_id`: Request ID for correlation
    """,
    responses={
        200: {
            "description": "Bulk acknowledge completed (may have partial failures)",
        },
        400: {
            "description": "Validation error - Invalid request payload",
        },
        401: {
            "description": "Unauthorized - Invalid or missing API key",
        }
    }
)
async def bulk_acknowledge_events_endpoint(
    bulk_request: BulkEventAcknowledge,
    request: Request = None,
    api_key: str = Depends(get_api_key)
):
    """
    Acknowledge multiple events in bulk.
    
    Requires API key authentication.
    """
    request_id = request.state.request_id
    
    # Acknowledge events in bulk
    successful, failed = bulk_acknowledge_events(bulk_request.event_ids, api_key)
    
    # Format successful acknowledgments
    successful_responses = []
    for event in successful:
        successful_responses.append({
            'event_id': event['event_id'],
            'status': event['status'],
            'acknowledged_at': event.get('acknowledged_at'),
            'message': 'Event acknowledged successfully'
        })
    
    # Format failed items
    failed_items = []
    for fail in failed:
        failed_items.append(BulkItemError(
            index=fail['index'],
            error=fail['error']
        ))
    
    return BulkEventResponse(
        successful=successful_responses,
        failed=failed_items,
        request_id=request_id
    )


@router.delete(
    "/events/bulk",
    response_model=BulkEventResponse,
    tags=["events"],
    summary="Delete multiple events",
    description="""
    Delete multiple events in a single request.
    
    **Features:**
    - Delete up to 25 events per request
    - Partial success handling (returns both successful and failed items)
    - Idempotent operation (events that don't exist are considered successful)
    
    **Response:**
    - `successful`: List of successfully deleted event IDs
    - `failed`: List of failed items with error details and index
    - `request_id`: Request ID for correlation
    """,
    responses={
        200: {
            "description": "Bulk delete completed (may have partial failures)",
        },
        400: {
            "description": "Validation error - Invalid request payload",
        },
        401: {
            "description": "Unauthorized - Invalid or missing API key",
        }
    }
)
async def bulk_delete_events_endpoint(
    bulk_request: BulkEventDelete,
    request: Request = None,
    api_key: str = Depends(get_api_key)
):
    """
    Delete multiple events in bulk.
    
    Requires API key authentication.
    """
    request_id = request.state.request_id
    
    # Delete events in bulk
    successful, failed = bulk_delete_events(bulk_request.event_ids, api_key)
    
    # Format successful deletions
    successful_responses = []
    for event_id in successful:
        successful_responses.append({
            'event_id': event_id,
            'message': 'Event deleted successfully'
        })
    
    # Format failed items
    failed_items = []
    for fail in failed:
        failed_items.append(BulkItemError(
            index=fail['index'],
            error=fail['error']
        ))
    
    return BulkEventResponse(
        successful=successful_responses,
        failed=failed_items,
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
    duration_ms = getattr(request.state, 'duration_ms', None)
    
    # Get event from database
    event = get_event(event_id_str)
    
    if event is None:
        # Record error metric
        endpoint = '/v1/events/{event_id}'
        method = 'GET'
        if duration_ms:
            record_latency(endpoint, method, duration_ms)
        record_error(endpoint, method, 'NOT_FOUND')
        record_request_count(endpoint, method)
        
        logger.warning(
            "Event not found",
            extra={
                'operation': 'get_event',
                'event_id': event_id_str,
                'status_code': 404,
                'duration_ms': duration_ms,
            }
        )
        raise NotFoundError(
            f"Event with ID '{event_id_str}' was not found",
            details={
                "event_id": event_id_str,
                "suggestion": "Verify the event ID is correct and the event exists"
            }
        )
    
    # Record metrics
    endpoint = '/v1/events/{event_id}'
    method = 'GET'
    if duration_ms:
        record_latency(endpoint, method, duration_ms)
    record_success(endpoint, method)
    record_request_count(endpoint, method)
    
    logger.info(
        "Event retrieved successfully",
        extra={
            'operation': 'get_event',
            'event_id': event_id_str,
            'status': event['status'],
            'status_code': 200,
            'duration_ms': duration_ms,
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
    duration_ms = getattr(request.state, 'duration_ms', None)
    
    # Acknowledge event
    updated_event = acknowledge_event(event_id_str)
    
    if updated_event is None:
        # Check if event exists
        event = get_event(event_id_str)
        if event is None:
            # Record error metric
            endpoint = '/v1/events/{event_id}/ack'
            method = 'POST'
            if duration_ms:
                record_latency(endpoint, method, duration_ms)
            record_error(endpoint, method, 'NOT_FOUND')
            record_request_count(endpoint, method)
            
            logger.warning(
                "Event not found for acknowledgment",
                extra={
                    'operation': 'acknowledge_event',
                    'event_id': event_id_str,
                    'status_code': 404,
                    'duration_ms': duration_ms,
                }
            )
            raise NotFoundError(
                f"Event with ID '{event_id_str}' was not found",
                details=format_not_found_error("Event", event_id_str)
            )
        else:
            # Event exists but acknowledge failed (already acknowledged)
            # Record error metric
            endpoint = '/v1/events/{event_id}/ack'
            method = 'POST'
            if duration_ms:
                record_latency(endpoint, method, duration_ms)
            record_error(endpoint, method, 'CONFLICT')
            record_request_count(endpoint, method)
            
            logger.warning(
                "Event already acknowledged",
                extra={
                    'operation': 'acknowledge_event',
                    'event_id': event_id_str,
                    'current_status': event.get('status', 'acknowledged'),
                    'status_code': 409,
                    'duration_ms': duration_ms,
                }
            )
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
    
    # Record metrics
    endpoint = '/v1/events/{event_id}/ack'
    method = 'POST'
    if duration_ms:
        record_latency(endpoint, method, duration_ms)
    record_success(endpoint, method)
    record_request_count(endpoint, method)
    
    logger.info(
        "Event acknowledged successfully",
        extra={
            'operation': 'acknowledge_event',
            'event_id': event_id_str,
            'status': updated_event['status'],
            'acknowledged_at': updated_event['acknowledged_at'],
            'status_code': 200,
            'duration_ms': duration_ms,
        }
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
    duration_ms = getattr(request.state, 'duration_ms', None)
    
    # Delete event (idempotent)
    delete_event(event_id_str)
    
    # Record metrics
    endpoint = '/v1/events/{event_id}'
    method = 'DELETE'
    if duration_ms:
        record_latency(endpoint, method, duration_ms)
    record_success(endpoint, method)
    record_request_count(endpoint, method)
    
    logger.info(
        "Event deleted successfully",
        extra={
            'operation': 'delete_event',
            'event_id': event_id_str,
            'status_code': 200,
            'duration_ms': duration_ms,
        }
    )
    
    return DeleteResponse(
        event_id=event_id_str,
        message="Event deleted successfully",
        request_id=request_id
    )

