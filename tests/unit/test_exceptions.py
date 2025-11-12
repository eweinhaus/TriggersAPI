"""Unit tests for custom exception classes"""

import pytest
from src.exceptions import (
    APIException,
    ValidationError,
    UnauthorizedError,
    NotFoundError,
    ConflictError,
    PayloadTooLargeError,
    RateLimitExceededError,
    InternalError
)


class TestAPIException:
    """Test base APIException class"""
    
    def test_api_exception_initialization(self):
        """Test APIException initialization."""
        exc = APIException(400, "TEST_ERROR", "Test message", {"key": "value"})
        
        assert exc.status_code == 400
        assert exc.error_code == "TEST_ERROR"
        assert exc.message == "Test message"
        assert exc.details == {"key": "value"}
        assert str(exc) == "Test message"
    
    def test_api_exception_default_details(self):
        """Test APIException with default details."""
        exc = APIException(400, "TEST_ERROR", "Test message")
        
        assert exc.details == {}


class TestValidationError:
    """Test ValidationError exception"""
    
    def test_validation_error_default(self):
        """Test ValidationError with default message."""
        exc = ValidationError()
        
        assert exc.status_code == 400
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.message == "Invalid request payload"
    
    def test_validation_error_custom_message(self):
        """Test ValidationError with custom message."""
        exc = ValidationError("Custom validation error", {"field": "source"})
        
        assert exc.status_code == 400
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.message == "Custom validation error"
        assert exc.details == {"field": "source"}


class TestUnauthorizedError:
    """Test UnauthorizedError exception"""
    
    def test_unauthorized_error_default(self):
        """Test UnauthorizedError with default message."""
        exc = UnauthorizedError()
        
        assert exc.status_code == 401
        assert exc.error_code == "UNAUTHORIZED"
        assert exc.message == "Unauthorized"
    
    def test_unauthorized_error_custom_message(self):
        """Test UnauthorizedError with custom message."""
        exc = UnauthorizedError("Invalid API key")
        
        assert exc.status_code == 401
        assert exc.message == "Invalid API key"


class TestNotFoundError:
    """Test NotFoundError exception"""
    
    def test_not_found_error_default(self):
        """Test NotFoundError with default message."""
        exc = NotFoundError()
        
        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"
        assert exc.message == "Resource not found"
    
    def test_not_found_error_custom_message(self):
        """Test NotFoundError with custom message."""
        exc = NotFoundError("Event not found", {"event_id": "123"})
        
        assert exc.status_code == 404
        assert exc.message == "Event not found"
        assert exc.details == {"event_id": "123"}


class TestConflictError:
    """Test ConflictError exception"""
    
    def test_conflict_error_default(self):
        """Test ConflictError with default message."""
        exc = ConflictError()
        
        assert exc.status_code == 409
        assert exc.error_code == "CONFLICT"
        assert exc.message == "Resource conflict"
    
    def test_conflict_error_custom_message(self):
        """Test ConflictError with custom message."""
        exc = ConflictError("Event already acknowledged")
        
        assert exc.status_code == 409
        assert exc.message == "Event already acknowledged"


class TestPayloadTooLargeError:
    """Test PayloadTooLargeError exception"""
    
    def test_payload_too_large_error_default(self):
        """Test PayloadTooLargeError with default message."""
        exc = PayloadTooLargeError()
        
        assert exc.status_code == 413
        assert exc.error_code == "PAYLOAD_TOO_LARGE"
        assert exc.message == "Payload too large"
    
    def test_payload_too_large_error_custom_message(self):
        """Test PayloadTooLargeError with custom message."""
        exc = PayloadTooLargeError("Payload exceeds 400KB limit", {"size": 500000})
        
        assert exc.status_code == 413
        assert exc.message == "Payload exceeds 400KB limit"
        assert exc.details == {"size": 500000}


class TestRateLimitExceededError:
    """Test RateLimitExceededError exception"""
    
    def test_rate_limit_exceeded_error_default(self):
        """Test RateLimitExceededError with default message."""
        exc = RateLimitExceededError()
        
        assert exc.status_code == 429
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.message == "Rate limit exceeded"
    
    def test_rate_limit_exceeded_error_custom_message(self):
        """Test RateLimitExceededError with custom message."""
        exc = RateLimitExceededError("Rate limit exceeded: 100 requests/minute", {"limit": 100})
        
        assert exc.status_code == 429
        assert exc.message == "Rate limit exceeded: 100 requests/minute"
        assert exc.details == {"limit": 100}


class TestInternalError:
    """Test InternalError exception"""
    
    def test_internal_error_default(self):
        """Test InternalError with default message."""
        exc = InternalError()
        
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_ERROR"
        assert exc.message == "Internal server error"
    
    def test_internal_error_custom_message(self):
        """Test InternalError with custom message."""
        exc = InternalError("Database connection failed", {"error": "timeout"})
        
        assert exc.status_code == 500
        assert exc.message == "Database connection failed"
        assert exc.details == {"error": "timeout"}


