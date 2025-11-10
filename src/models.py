"""Pydantic models for request/response validation"""

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


class EventMetadata(BaseModel):
    """Optional metadata for events."""
    correlation_id: Optional[str] = None
    priority: Literal["low", "normal", "high"] = "normal"
    idempotency_key: Optional[str] = None


class EventCreate(BaseModel):
    """Request model for creating an event."""
    model_config = ConfigDict(extra='forbid')  # Reject unknown fields
    
    source: str
    event_type: str
    payload: dict
    metadata: Optional[dict] = None


class EventResponse(BaseModel):
    """Response model for event creation."""
    event_id: str
    created_at: str
    status: str
    message: str
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

