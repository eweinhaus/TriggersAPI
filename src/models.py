"""Pydantic models for request/response validation"""

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, field_validator, Field


class EventMetadata(BaseModel):
    """Optional metadata for events."""
    correlation_id: Optional[str] = None
    priority: Literal["low", "normal", "high"] = "normal"
    idempotency_key: Optional[str] = None


class EventCreate(BaseModel):
    """Request model for creating an event."""
    model_config = ConfigDict(extra='forbid')  # Reject unknown fields
    
    source: str = Field(..., min_length=1, max_length=100, description="Event source identifier")
    event_type: str = Field(..., min_length=1, max_length=100, description="Event type identifier")
    payload: dict = Field(..., description="Event payload (JSON object)")
    metadata: Optional[dict] = Field(None, description="Optional event metadata")
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Validate source field."""
        if not v or not v.strip():
            raise ValueError("source field is required and cannot be empty")
        if len(v) > 100:
            raise ValueError("source field must be 100 characters or less")
        return v.strip()
    
    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate event_type field."""
        if not v or not v.strip():
            raise ValueError("event_type field is required and cannot be empty")
        if len(v) > 100:
            raise ValueError("event_type field must be 100 characters or less")
        return v.strip()
    
    @field_validator('payload')
    @classmethod
    def validate_payload(cls, v: dict) -> dict:
        """Validate payload field."""
        if not isinstance(v, dict):
            raise ValueError("payload must be a valid JSON object")
        if len(v) == 0:
            raise ValueError("payload cannot be empty")
        return v
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v: Optional[dict]) -> Optional[dict]:
        """Validate metadata field."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("metadata must be a valid JSON object")
            # Validate priority if provided
            if 'priority' in v and v['priority'] not in ['low', 'normal', 'high']:
                raise ValueError("metadata.priority must be one of: low, normal, high")
        return v


class EventResponse(BaseModel):
    """Response model for event creation."""
    event_id: str
    created_at: str
    status: str
    message: str
    request_id: str


class EventDetailResponse(BaseModel):
    """Response model for event details (GET /events/{event_id})."""
    event_id: str
    created_at: str
    source: str
    event_type: str
    payload: dict
    status: str
    metadata: Optional[dict] = None
    acknowledged_at: Optional[str] = None
    request_id: str


class InboxResponse(BaseModel):
    """Response model for inbox query."""
    events: list[dict]
    pagination: dict
    request_id: str


class AckResponse(BaseModel):
    """Response model for event acknowledgment."""
    event_id: str
    status: str
    acknowledged_at: str
    message: str
    request_id: str


class DeleteResponse(BaseModel):
    """Response model for event deletion."""
    event_id: str
    message: str
    request_id: str


class BulkEventCreate(BaseModel):
    """Request model for bulk event creation."""
    model_config = ConfigDict(extra='forbid')
    
    items: list[EventCreate] = Field(..., min_length=1, max_length=25, description="List of events to create (max 25)")


class BulkEventAcknowledge(BaseModel):
    """Request model for bulk event acknowledgment."""
    model_config = ConfigDict(extra='forbid')
    
    event_ids: list[str] = Field(..., min_length=1, max_length=25, description="List of event IDs to acknowledge (max 25)")


class BulkEventDelete(BaseModel):
    """Request model for bulk event deletion."""
    model_config = ConfigDict(extra='forbid')
    
    event_ids: list[str] = Field(..., min_length=1, max_length=25, description="List of event IDs to delete (max 25)")


class BulkItemError(BaseModel):
    """Error details for a failed bulk operation item."""
    index: int = Field(..., description="Index of the failed item in the request")
    error: dict = Field(..., description="Error details (code, message, details)")


class BulkEventResponse(BaseModel):
    """Response model for bulk event operations."""
    successful: list[dict] = Field(..., description="Successfully processed items")
    failed: list[BulkItemError] = Field(default_factory=list, description="Failed items with error details")
    request_id: str


class ErrorDetail(BaseModel):
    """Error detail in error response."""
    code: str
    message: str
    details: dict
    request_id: str


class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: ErrorDetail


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    version: str


class WebhookCreate(BaseModel):
    """Request model for creating a webhook."""
    model_config = ConfigDict(extra='forbid')
    
    url: str = Field(..., description="Webhook URL to receive events")
    events: list[str] = Field(..., description="List of event types to subscribe to (use ['*'] for all events)")
    secret: str = Field(..., min_length=16, description="Secret for HMAC signature verification (minimum 16 characters)")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        from urllib.parse import urlparse
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("url must be a valid HTTP/HTTPS URL")
        if parsed.scheme not in ['http', 'https']:
            raise ValueError("url must use http or https protocol")
        return v.strip()
    
    @field_validator('events')
    @classmethod
    def validate_events(cls, v: list[str]) -> list[str]:
        """Validate events list."""
        if not v or len(v) == 0:
            raise ValueError("events must contain at least one event type or '*'")
        for event in v:
            if not event or not event.strip():
                raise ValueError("event types cannot be empty")
            if len(event) > 100:
                raise ValueError("event types must be 100 characters or less")
        return [e.strip() for e in v]
    
    @field_validator('secret')
    @classmethod
    def validate_secret(cls, v: str) -> str:
        """Validate secret field."""
        if not v or len(v) < 16:
            raise ValueError("secret must be at least 16 characters long")
        return v


class WebhookUpdate(BaseModel):
    """Request model for updating a webhook."""
    model_config = ConfigDict(extra='forbid')
    
    url: Optional[str] = Field(None, description="Webhook URL to receive events")
    events: Optional[list[str]] = Field(None, description="List of event types to subscribe to")
    secret: Optional[str] = Field(None, min_length=16, description="Secret for HMAC signature verification")
    is_active: Optional[bool] = Field(None, description="Whether the webhook is active")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format."""
        if v is None:
            return v
        from urllib.parse import urlparse
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("url must be a valid HTTP/HTTPS URL")
        if parsed.scheme not in ['http', 'https']:
            raise ValueError("url must use http or https protocol")
        return v.strip()
    
    @field_validator('events')
    @classmethod
    def validate_events(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate events list."""
        if v is None:
            return v
        if len(v) == 0:
            raise ValueError("events must contain at least one event type or '*'")
        for event in v:
            if not event or not event.strip():
                raise ValueError("event types cannot be empty")
            if len(event) > 100:
                raise ValueError("event types must be 100 characters or less")
        return [e.strip() for e in v]
    
    @field_validator('secret')
    @classmethod
    def validate_secret(cls, v: Optional[str]) -> Optional[str]:
        """Validate secret field."""
        if v is None:
            return v
        if len(v) < 16:
            raise ValueError("secret must be at least 16 characters long")
        return v


class WebhookResponse(BaseModel):
    """Response model for webhook operations."""
    webhook_id: str
    url: str
    events: list[str]
    is_active: bool
    created_at: str
    request_id: str


class WebhookListResponse(BaseModel):
    """Response model for listing webhooks."""
    webhooks: list[dict]
    pagination: Optional[dict] = None
    request_id: str


class WebhookTestResponse(BaseModel):
    """Response model for webhook test."""
    webhook_id: str
    status: str
    status_code: Optional[int] = None
    message: str
    request_id: str

