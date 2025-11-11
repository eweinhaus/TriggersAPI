"""Unit tests for main.py exception handlers and startup"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError as PydanticValidationError
from src.main import app
from src.exceptions import APIException, ValidationError, NotFoundError, InternalError


class TestExceptionHandlers:
    """Test exception handlers in main.py"""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request with request_id."""
        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-id-123"
        return request
    
    def test_pydantic_validation_error_handler(self, mock_request):
        """Test Pydantic validation error handler."""
        from src.main import pydantic_validation_handler
        
        # Create a real Pydantic validation error
        try:
            from pydantic import BaseModel, Field
            class TestModel(BaseModel):
                source: str = Field(...)
            TestModel()
        except PydanticValidationError as exc:
            response = asyncio.run(pydantic_validation_handler(mock_request, exc))
            
            assert response.status_code == 400
            content = response.body.decode()
            assert "VALIDATION_ERROR" in content
            assert "test-request-id-123" in content
            # Check for enhanced error details
            assert "suggestion" in content or "details" in content
    
    def test_pydantic_validation_error_handler_no_request_id(self):
        """Test Pydantic validation handler without request_id."""
        from src.main import pydantic_validation_handler
        
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        # Simulate missing request_id by not setting it
        if hasattr(request.state, 'request_id'):
            delattr(request.state, 'request_id')
        
        # Create a real ValidationError
        try:
            from pydantic import BaseModel, Field
            class TestModel(BaseModel):
                source: str = Field(...)
            TestModel()
        except PydanticValidationError as exc:
            response = asyncio.run(pydantic_validation_handler(request, exc))
            
            assert response.status_code == 400
            # Should generate a new request_id
    
    def test_api_exception_handler(self, mock_request):
        """Test API exception handler."""
        from src.main import api_exception_handler
        
        exc = NotFoundError("Event not found", details={"event_id": "123"})
        
        with patch('src.main.log_level', 'INFO'):
            with patch('src.main.logger') as mock_logger:
                response = asyncio.run(api_exception_handler(mock_request, exc))
        
        assert response.status_code == 404
        content = response.body.decode()
        assert "NOT_FOUND" in content
        assert "test-request-id-123" in content
        assert "Event not found" in content
    
    def test_api_exception_handler_debug_mode(self, mock_request):
        """Test API exception handler in DEBUG mode."""
        from src.main import api_exception_handler
        
        exc = ValidationError("Invalid payload")
        
        with patch('src.main.log_level', 'DEBUG'):
            with patch('src.main.logger') as mock_logger:
                response = asyncio.run(api_exception_handler(mock_request, exc))
        
        assert response.status_code == 400
        # With structured logging, we use logger.error with extra fields
        mock_logger.error.assert_called_once()
    
    def test_http_exception_handler(self, mock_request):
        """Test HTTP exception handler."""
        from src.main import http_exception_handler
        
        exc = HTTPException(status_code=404, detail="Not found")
        
        response = asyncio.run(http_exception_handler(mock_request, exc))
        
        assert response.status_code == 404
        content = response.body.decode()
        assert "HTTP_ERROR" in content
        assert "test-request-id-123" in content
    
    def test_generic_exception_handler(self, mock_request):
        """Test generic exception handler."""
        from src.main import generic_exception_handler
        
        exc = Exception("Unexpected error")
        
        with patch('src.main.log_level', 'INFO'):
            with patch('src.main.logger') as mock_logger:
                response = asyncio.run(generic_exception_handler(mock_request, exc))
        
        assert response.status_code == 500
        content = response.body.decode()
        assert "INTERNAL_ERROR" in content
        assert "test-request-id-123" in content
        # Verify logger.error was called (may be called multiple times in some cases)
        assert mock_logger.error.called
    
    def test_generic_exception_handler_debug_mode(self, mock_request):
        """Test generic exception handler in DEBUG mode."""
        from src.main import generic_exception_handler
        
        exc = Exception("Unexpected error")
        
        with patch('src.main.log_level', 'DEBUG'):
            with patch('src.main.logger') as mock_logger:
                response = asyncio.run(generic_exception_handler(mock_request, exc))
        
        assert response.status_code == 500
        mock_logger.exception.assert_called_once()


class TestStartupEvent:
    """Test application startup event"""
    
    @patch('src.main.create_tables')
    @patch('src.main.logger')
    def test_startup_event_success(self, mock_logger, mock_create_tables):
        """Test successful startup event."""
        from src.main import startup_event
        
        asyncio.run(startup_event())
        
        mock_create_tables.assert_called_once()
        mock_logger.info.assert_called_once()
    
    @patch('src.main.create_tables')
    @patch('src.main.logger')
    def test_startup_event_failure(self, mock_logger, mock_create_tables):
        """Test startup event with table creation failure."""
        from src.main import startup_event
        
        mock_create_tables.side_effect = Exception("Table creation failed")
        
        # Should not raise exception
        asyncio.run(startup_event())
        
        mock_create_tables.assert_called_once()
        mock_logger.error.assert_called_once()


class TestLambdaHandler:
    """Test Lambda handler function"""
    
    @patch('src.main.mangum_handler')
    def test_lambda_handler(self, mock_mangum_handler):
        """Test Lambda handler wrapper."""
        from src.main import handler
        
        mock_event = {"httpMethod": "GET", "path": "/v1/health"}
        mock_context = MagicMock()
        mock_mangum_handler.return_value = {"statusCode": 200}
        
        result = handler(mock_event, mock_context)
        
        mock_mangum_handler.assert_called_once_with(mock_event, mock_context)
        assert result == {"statusCode": 200}

