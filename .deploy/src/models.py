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

