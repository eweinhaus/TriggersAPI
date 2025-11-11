"""Unit tests for AWS mode authentication"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request
from botocore.exceptions import ClientError
from src.auth import validate_api_key, get_api_key
from src.exceptions import UnauthorizedError


class TestAWSModeAuthentication:
    """Test AWS mode API key authentication"""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        return request
    
    @patch.dict(os.environ, {'AUTH_MODE': 'aws'})
    @patch('src.auth._get_api_keys_table')
    def test_validate_api_key_aws_mode_valid(self, mock_get_table, mock_request):
        """Test AWS mode with valid API key."""
        mock_request.headers.get.return_value = 'valid-key-123'
        
        # Mock DynamoDB table response
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'api_key': 'valid-key-123',
                'is_active': True,
                'source': 'test'
            }
        }
        mock_get_table.return_value = mock_table
        
        result = validate_api_key(mock_request)
        
        assert result == 'valid-key-123'
        mock_table.get_item.assert_called_once_with(Key={'api_key': 'valid-key-123'})
        mock_request.headers.get.assert_called_with('X-API-Key')
    
    @patch.dict(os.environ, {'AUTH_MODE': 'aws'})
    @patch('src.auth._get_api_keys_table')
    def test_validate_api_key_aws_mode_invalid_key(self, mock_get_table, mock_request):
        """Test AWS mode with invalid API key (not in DB)."""
        mock_request.headers.get.return_value = 'invalid-key'
        
        # Mock DynamoDB table response - key not found (no 'Item' key)
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # Empty response means no Item
        mock_get_table.return_value = mock_table
        
        with pytest.raises(UnauthorizedError) as exc_info:
            validate_api_key(mock_request)
        
        # Should raise UnauthorizedError with appropriate message
        error_msg = str(exc_info.value)
        assert "Invalid API key" in error_msg or "API key is inactive" in error_msg or "Error validating API key" in error_msg
    
    @patch.dict(os.environ, {'AUTH_MODE': 'aws'})
    @patch('src.auth._get_api_keys_table')
    def test_validate_api_key_aws_mode_inactive_key(self, mock_get_table, mock_request):
        """Test AWS mode with inactive API key."""
        mock_request.headers.get.return_value = 'inactive-key'
        
        # Mock DynamoDB table response - key exists but inactive
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'api_key': 'inactive-key',
                'is_active': False,
                'source': 'test'
            }
        }
        mock_get_table.return_value = mock_table
        
        with pytest.raises(UnauthorizedError) as exc_info:
            validate_api_key(mock_request)
        
        # Should raise UnauthorizedError with appropriate message
        error_msg = str(exc_info.value)
        assert "Invalid API key" in error_msg or "API key is inactive" in error_msg or "Error validating API key" in error_msg
    
    @patch.dict(os.environ, {'AUTH_MODE': 'aws'})
    @patch('src.auth._get_api_keys_table')
    def test_validate_api_key_aws_mode_missing_is_active(self, mock_get_table, mock_request):
        """Test AWS mode with key missing is_active field (defaults to True)."""
        mock_request.headers.get.return_value = 'key-without-active-flag'
        
        # Mock DynamoDB table response - key exists without is_active
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'api_key': 'key-without-active-flag',
                'source': 'test'
            }
        }
        mock_get_table.return_value = mock_table
        
        result = validate_api_key(mock_request)
        
        assert result == 'key-without-active-flag'
    
    @patch.dict(os.environ, {'AUTH_MODE': 'aws'})
    @patch('src.auth._get_api_keys_table')
    def test_validate_api_key_aws_mode_client_error(self, mock_get_table, mock_request):
        """Test AWS mode with DynamoDB ClientError."""
        mock_request.headers.get.return_value = 'valid-key'
        
        # Mock DynamoDB ClientError
        mock_table = MagicMock()
        mock_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}},
            'GetItem'
        )
        mock_get_table.return_value = mock_table
        
        with pytest.raises(UnauthorizedError) as exc_info:
            validate_api_key(mock_request)
        
        assert "Error validating API key" in str(exc_info.value)
    
    @patch.dict(os.environ, {'AUTH_MODE': 'aws'})
    @patch('src.auth._get_api_keys_table')
    def test_validate_api_key_aws_mode_generic_exception(self, mock_get_table, mock_request):
        """Test AWS mode with unexpected exception."""
        mock_request.headers.get.return_value = 'valid-key'
        
        # Mock unexpected exception
        mock_table = MagicMock()
        mock_table.get_item.side_effect = Exception("Unexpected error")
        mock_get_table.return_value = mock_table
        
        with pytest.raises(UnauthorizedError) as exc_info:
            validate_api_key(mock_request)
        
        assert "Error validating API key" in str(exc_info.value)
    
    @patch.dict(os.environ, {'AUTH_MODE': 'invalid-mode'})
    def test_validate_api_key_unsupported_auth_mode(self, mock_request):
        """Test with unsupported AUTH_MODE."""
        mock_request.headers.get.return_value = 'test-key'
        
        with pytest.raises(UnauthorizedError) as exc_info:
            validate_api_key(mock_request)
        
        assert "Unsupported AUTH_MODE" in str(exc_info.value)
        assert "invalid-mode" in str(exc_info.value)
    
    @patch.dict(os.environ, {'AUTH_MODE': 'local'})
    def test_get_api_key_dependency(self, mock_request):
        """Test get_api_key FastAPI dependency."""
        mock_request.headers.get.return_value = 'test-api-key-12345'
        
        result = get_api_key(mock_request)
        assert result == 'test-api-key-12345'

