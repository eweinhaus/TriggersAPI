"""Webhook endpoints: create, list, get, update, delete, test"""

import httpx
import hmac
import hashlib
import json
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Path, Query
from src.models import (
    WebhookCreate, WebhookResponse, WebhookListResponse, WebhookUpdate, WebhookTestResponse
)
from src.database import (
    create_webhook, get_webhook, list_webhooks, update_webhook, delete_webhook
)
from src.auth import get_api_key
from src.exceptions import NotFoundError, ValidationError, InternalError
from src.utils import generate_uuid, format_not_found_error, get_iso_timestamp

router = APIRouter()


@router.post(
    "/webhooks",
    response_model=WebhookResponse,
    status_code=201,
    tags=["webhooks"],
    summary="Create a new webhook",
    description="""
    Register a new webhook to receive events via HTTP POST.
    
    **Features:**
    - Subscribe to specific event types or all events (use `["*"]`)
    - HMAC signature verification for security
    - Automatic event delivery when events are created
    
    **Event Filtering:**
    - Use `["*"]` to receive all events
    - Use specific event types like `["user.created", "order.completed"]`
    
    **Security:**
    - Secret is used to generate HMAC signatures for webhook payloads
    - Secret must be at least 16 characters long
    - Secret is never returned in API responses
    """,
    responses={
        201: {
            "description": "Webhook created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "webhook_id": "550e8400-e29b-41d4-a716-446655440000",
                        "url": "https://example.com/webhook",
                        "events": ["*"],
                        "is_active": True,
                        "created_at": "2025-11-11T12:00:00.000000Z",
                        "request_id": "660e8400-e29b-41d4-a716-446655440001"
                    }
                }
            }
        },
        400: {"description": "Validation error"},
        401: {"description": "Unauthorized"}
    }
)
async def create_webhook_endpoint(
    webhook_data: WebhookCreate,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """Create a new webhook."""
    try:
        webhook_id = generate_uuid()
        
        # Create webhook in database
        webhook = create_webhook(
            webhook_id=webhook_id,
            url=webhook_data.url,
            events=webhook_data.events,
            secret=webhook_data.secret,
            api_key=api_key
        )
        
        return WebhookResponse(
            webhook_id=webhook['webhook_id'],
            url=webhook['url'],
            events=webhook['events'],
            is_active=webhook['is_active'],
            created_at=webhook['created_at'],
            request_id=request.state.request_id
        )
    except Exception as e:
        raise InternalError(
            message="Failed to create webhook",
            details={"error": str(e)},
            request_id=request.state.request_id
        )


@router.get(
    "/webhooks",
    response_model=WebhookListResponse,
    tags=["webhooks"],
    summary="List webhooks",
    description="""
    List all webhooks for the authenticated API key.
    
    **Pagination:**
    - Use `limit` to control page size (max 100)
    - Use `cursor` from previous response for next page
    - Use `is_active` filter to show only active/inactive webhooks
    """,
    responses={
        200: {"description": "List of webhooks"},
        401: {"description": "Unauthorized"}
    }
)
async def list_webhooks_endpoint(
    request: Request,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    api_key: str = Depends(get_api_key)
):
    """List webhooks for the authenticated API key."""
    try:
        result = list_webhooks(api_key=api_key, is_active=is_active, limit=limit, cursor=cursor)
        
        webhooks = result.get('webhooks', [])
        last_evaluated_key = result.get('last_evaluated_key')
        
        pagination = None
        if last_evaluated_key:
            from src.utils import encode_cursor
            pagination = {
                "next_cursor": encode_cursor(last_evaluated_key),
                "has_more": True
            }
        
        return WebhookListResponse(
            webhooks=webhooks,
            pagination=pagination,
            request_id=request.state.request_id
        )
    except Exception as e:
        raise InternalError(
            message="Failed to list webhooks",
            details={"error": str(e)},
            request_id=request.state.request_id
        )


@router.get(
    "/webhooks/{webhook_id}",
    response_model=WebhookResponse,
    tags=["webhooks"],
    summary="Get webhook details",
    description="""
    Get details of a specific webhook.
    
    **Security:**
    - Only webhooks owned by the authenticated API key can be accessed
    - Secret is never returned in the response
    """,
    responses={
        200: {"description": "Webhook details"},
        404: {"description": "Webhook not found"},
        401: {"description": "Unauthorized"}
    }
)
async def get_webhook_endpoint(
    request: Request,
    webhook_id: str = Path(..., description="Webhook ID"),
    api_key: str = Depends(get_api_key)
):
    """Get webhook by ID."""
    webhook = get_webhook(webhook_id)
    
    if not webhook:
        raise NotFoundError(
            message="Webhook not found",
            details=format_not_found_error("Webhook", webhook_id),
            request_id=request.state.request_id
        )
    
    # Verify webhook belongs to API key
    if webhook.get('api_key') != api_key:
        raise NotFoundError(
            message="Webhook not found",
            details=format_not_found_error("Webhook", webhook_id),
            request_id=request.state.request_id
        )
    
    # Remove secret from response
    webhook.pop('secret', None)
    
    return WebhookResponse(
        webhook_id=webhook['webhook_id'],
        url=webhook['url'],
        events=webhook['events'],
        is_active=webhook['is_active'],
        created_at=webhook['created_at'],
        request_id=request.state.request_id
    )


@router.put(
    "/webhooks/{webhook_id}",
    response_model=WebhookResponse,
    tags=["webhooks"],
    summary="Update webhook",
    description="""
    Update webhook configuration.
    
    **Partial Updates:**
    - Only provided fields are updated
    - Omitted fields remain unchanged
    - Secret can be updated for security rotation
    """,
    responses={
        200: {"description": "Webhook updated successfully"},
        404: {"description": "Webhook not found"},
        400: {"description": "Validation error"},
        401: {"description": "Unauthorized"}
    }
)
async def update_webhook_endpoint(
    request: Request,
    webhook_id: str = Path(..., description="Webhook ID"),
    webhook_data: WebhookUpdate = None,
    api_key: str = Depends(get_api_key)
):
    """Update webhook."""
    # Verify webhook exists and belongs to API key
    webhook = get_webhook(webhook_id)
    if not webhook or webhook.get('api_key') != api_key:
        raise NotFoundError(
            message="Webhook not found",
            details=format_not_found_error("Webhook", webhook_id),
            request_id=request.state.request_id
        )
    
    # Update webhook
    updated = update_webhook(
        webhook_id=webhook_id,
        url=webhook_data.url if webhook_data else None,
        events=webhook_data.events if webhook_data else None,
        secret=webhook_data.secret if webhook_data else None,
        is_active=webhook_data.is_active if webhook_data else None
    )
    
    if not updated:
        raise InternalError(
            message="Failed to update webhook",
            details={},
            request_id=request.state.request_id
        )
    
    return WebhookResponse(
        webhook_id=updated['webhook_id'],
        url=updated['url'],
        events=updated['events'],
        is_active=updated['is_active'],
        created_at=updated['created_at'],
        request_id=request.state.request_id
    )


@router.delete(
    "/webhooks/{webhook_id}",
    status_code=204,
    tags=["webhooks"],
    summary="Delete webhook",
    description="""
    Delete a webhook.
    
    **Effects:**
    - Webhook will no longer receive events
    - Deletion is permanent and cannot be undone
    """,
    responses={
        204: {"description": "Webhook deleted successfully"},
        404: {"description": "Webhook not found"},
        401: {"description": "Unauthorized"}
    }
)
async def delete_webhook_endpoint(
    request: Request,
    webhook_id: str = Path(..., description="Webhook ID"),
    api_key: str = Depends(get_api_key)
):
    """Delete webhook."""
    # Verify webhook exists and belongs to API key
    webhook = get_webhook(webhook_id)
    if not webhook or webhook.get('api_key') != api_key:
        raise NotFoundError(
            message="Webhook not found",
            details=format_not_found_error("Webhook", webhook_id),
            request_id=request.state.request_id
        )
    
    deleted = delete_webhook(webhook_id)
    if not deleted:
        raise InternalError(
            message="Failed to delete webhook",
            details={},
            request_id=request.state.request_id
        )
    
    return None


@router.post(
    "/webhooks/{webhook_id}/test",
    response_model=WebhookTestResponse,
    tags=["webhooks"],
    summary="Test webhook",
    description="""
    Send a test event to the webhook URL.
    
    **Test Event:**
    - Sends a test event payload to the webhook URL
    - Includes HMAC signature for verification
    - Returns delivery status immediately
    
    **Use Cases:**
    - Verify webhook URL is accessible
    - Test signature verification
    - Debug webhook delivery issues
    """,
    responses={
        200: {"description": "Test webhook delivery status"},
        404: {"description": "Webhook not found"},
        401: {"description": "Unauthorized"}
    }
)
async def test_webhook_endpoint(
    request: Request,
    webhook_id: str = Path(..., description="Webhook ID"),
    api_key: str = Depends(get_api_key)
):
    """Test webhook by sending a test event."""
    # Verify webhook exists and belongs to API key
    webhook = get_webhook(webhook_id)
    if not webhook or webhook.get('api_key') != api_key:
        raise NotFoundError(
            message="Webhook not found",
            details=format_not_found_error("Webhook", webhook_id),
            request_id=request.state.request_id
        )
    
    # Create test event payload
    test_event = {
        "event_id": generate_uuid(),
        "created_at": get_iso_timestamp(),
        "source": "test",
        "event_type": "webhook.test",
        "payload": {
            "message": "This is a test webhook event",
            "test": True
        },
        "status": "pending"
    }
    
    # Generate HMAC signature
    payload_json = json.dumps(test_event)
    secret = webhook.get('secret')
    signature = hmac.new(
        secret.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Send HTTP POST to webhook URL
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook['url'],
                json=test_event,
                headers={
                    'X-Webhook-Signature': signature,
                    'X-Webhook-Id': webhook_id,
                    'X-Webhook-Timestamp': get_iso_timestamp(),
                    'Content-Type': 'application/json'
                }
            )
            
            status = "success" if 200 <= response.status_code < 300 else "failed"
            return WebhookTestResponse(
                webhook_id=webhook_id,
                status=status,
                status_code=response.status_code,
                message=f"Webhook test {status} with status code {response.status_code}",
                request_id=request.state.request_id
            )
    except httpx.TimeoutException:
        return WebhookTestResponse(
            webhook_id=webhook_id,
            status="failed",
            status_code=None,
            message="Webhook test failed: request timeout",
            request_id=request.state.request_id
        )
    except Exception as e:
        return WebhookTestResponse(
            webhook_id=webhook_id,
            status="failed",
            status_code=None,
            message=f"Webhook test failed: {str(e)}",
            request_id=request.state.request_id
        )

