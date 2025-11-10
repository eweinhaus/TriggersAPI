"""Unit tests for Pydantic models"""

import pytest
from pydantic import ValidationError
from src.models import EventCreate, EventResponse, InboxResponse, ErrorResponse, EventMetadata


class TestEventCreate:
    """Tests for EventCreate model"""
    
    def test_valid_event_create(self):
        """Test creating EventCreate with valid data."""
        event = EventCreate(
            source="test-source",
            event_type="test-type",
            payload={"key": "value"}
        )
        
        assert event.source == "test-source"
        assert event.event_type == "test-type"
        assert event.payload == {"key": "value"}
    
    def test_event_create_missing_source(self):
        """Test EventCreate with missing source field."""
        with pytest.raises(ValidationError) as exc_info:
            EventCreate(
                event_type="test-type",
                payload={"key": "value"}
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("source",) for error in errors)
    
    def test_event_create_missing_event_type(self):
        """Test EventCreate with missing event_type field."""
        with pytest.raises(ValidationError) as exc_info:
            EventCreate(
                source="test-source",
                payload={"key": "value"}
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("event_type",) for error in errors)
    
    def test_event_create_missing_payload(self):
        """Test EventCreate with missing payload field."""
        with pytest.raises(ValidationError) as exc_info:
            EventCreate(
                source="test-source",
                event_type="test-type"
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("payload",) for error in errors)
    
    def test_event_create_empty_source(self):
        """Test EventCreate with empty source."""
        with pytest.raises(ValidationError):
            EventCreate(
                source="",
                event_type="test-type",
                payload={"key": "value"}
            )
    
    def test_event_create_empty_event_type(self):
        """Test EventCreate with empty event_type."""
        with pytest.raises(ValidationError):
            EventCreate(
                source="test-source",
                event_type="",
                payload={"key": "value"}
            )
    
    def test_event_create_empty_payload(self):
        """Test EventCreate with empty payload."""
        with pytest.raises(ValidationError):
            EventCreate(
                source="test-source",
                event_type="test-type",
                payload={}
            )
    
    def test_event_create_source_too_long(self):
        """Test EventCreate with source exceeding 100 characters."""
        long_source = "a" * 101
        
        with pytest.raises(ValidationError):
            EventCreate(
                source=long_source,
                event_type="test-type",
                payload={"key": "value"}
            )
    
    def test_event_create_event_type_too_long(self):
        """Test EventCreate with event_type exceeding 100 characters."""
        long_type = "a" * 101
        
        with pytest.raises(ValidationError):
            EventCreate(
                source="test-source",
                event_type=long_type,
                payload={"key": "value"}
            )
    
    def test_event_create_unknown_fields(self):
        """Test EventCreate with unknown fields (should be rejected)."""
        with pytest.raises(ValidationError) as exc_info:
            EventCreate(
                source="test-source",
                event_type="test-type",
                payload={"key": "value"},
                unknown_field="should be rejected"
            )
        
        errors = exc_info.value.errors()
        assert any("unknown_field" in str(error["loc"]) for error in errors)
    
    def test_event_create_with_metadata(self):
        """Test EventCreate with valid metadata."""
        event = EventCreate(
            source="test-source",
            event_type="test-type",
            payload={"key": "value"},
            metadata={"priority": "high", "correlation_id": "test-id"}
        )
        
        assert event.metadata is not None
        assert event.metadata["priority"] == "high"
    
    def test_event_create_metadata_invalid_priority(self):
        """Test EventCreate with invalid priority in metadata."""
        with pytest.raises(ValidationError):
            EventCreate(
                source="test-source",
                event_type="test-type",
                payload={"key": "value"},
                metadata={"priority": "invalid"}
            )


class TestEventResponse:
    """Tests for EventResponse model"""
    
    def test_valid_event_response(self):
        """Test creating EventResponse with valid data."""
        response = EventResponse(
            event_id="test-id",
            created_at="2024-01-01T12:00:00Z",
            status="pending",
            message="Success",
            request_id="req-id"
        )
        
        assert response.event_id == "test-id"
        assert response.status == "pending"
        assert response.request_id == "req-id"


class TestInboxResponse:
    """Tests for InboxResponse model"""
    
    def test_valid_inbox_response(self):
        """Test creating InboxResponse with valid data."""
        response = InboxResponse(
            events=[{"event_id": "test-id"}],
            pagination={"limit": 50},
            request_id="req-id"
        )
        
        assert len(response.events) == 1
        assert response.pagination["limit"] == 50
        assert response.request_id == "req-id"

