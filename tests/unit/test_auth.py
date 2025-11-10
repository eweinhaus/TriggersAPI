"""Unit tests for authentication"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.main import app
from src.exceptions import UnauthorizedError


class TestAuthentication:
    """Tests for API key authentication"""
    
    def test_valid_api_key(self, client, auth_headers, sample_event):
        """Test that valid API key allows request."""
        with patch('src.endpoints.events.create_event') as mock_create:
            mock_create.return_value = {
                'event_id': 'test-id',
                'created_at': '2024-01-01T12:00:00Z',
                'status': 'pending'
            }
            
            response = client.post("/v1/events", json=sample_event, headers=auth_headers)
            
            assert response.status_code == 201
            # Request should proceed successfully
    
    def test_invalid_api_key(self, client, sample_event):
        """Test that invalid API key is rejected."""
        headers = {"X-API-Key": "invalid-key"}
        
        response = client.post("/v1/events", json=sample_event, headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "UNAUTHORIZED"
        assert "request_id" in data["error"]
    
    def test_missing_api_key(self, client, sample_event):
        """Test that missing API key is rejected."""
        response = client.post("/v1/events", json=sample_event)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "UNAUTHORIZED"
        assert "request_id" in data["error"]
    
    def test_api_key_case_sensitive(self, client, sample_event):
        """Test that API key is case-sensitive."""
        # Use wrong case
        headers = {"X-API-Key": "TEST-API-KEY-12345"}
        
        response = client.post("/v1/events", json=sample_event, headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "UNAUTHORIZED"

