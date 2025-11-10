"""Unit tests for event endpoints"""

import pytest
from unittest.mock import patch, MagicMock
from src.exceptions import ValidationError, PayloadTooLargeError, NotFoundError, ConflictError, UnauthorizedError, InternalError
from tests.utils.test_helpers import assert_error_response, assert_success_response, assert_request_id_present, create_large_payload


class TestCreateEvent:
    """Tests for POST /v1/events endpoint"""
    
    def test_create_event_success(self, client, auth_headers, sample_event):
        """Test successful event creation."""
        with patch('src.endpoints.events.create_event') as mock_create:
            mock_create.return_value = {
                'event_id': 'test-event-id',
                'created_at': '2024-01-01T12:00:00.000000Z',
                'status': 'pending'
            }
            
            response = client.post("/v1/events", json=sample_event, headers=auth_headers)
            
            assert_success_response(response, expected_status=201)
            assert_request_id_present(response)
            
            data = response.json()
            assert data["event_id"] == "test-event-id"
            assert data["status"] == "pending"
            assert "message" in data
    
    def test_create_event_missing_source(self, client, auth_headers):
        """Test event creation with missing source field."""
        event_data = {
            "event_type": "test",
            "payload": {"key": "value"}
        }
        
        response = client.post("/v1/events", json=event_data, headers=auth_headers)
        
        assert_error_response(response, "VALIDATION_ERROR", expected_status=400)
        assert_request_id_present(response)
    
    def test_create_event_missing_event_type(self, client, auth_headers):
        """Test event creation with missing event_type field."""
        event_data = {
            "source": "test-source",
            "payload": {"key": "value"}
        }
        
        response = client.post("/v1/events", json=event_data, headers=auth_headers)
        
        assert_error_response(response, "VALIDATION_ERROR", expected_status=400)
    
    def test_create_event_missing_payload(self, client, auth_headers):
        """Test event creation with missing payload field."""
        event_data = {
            "source": "test-source",
            "event_type": "test"
        }
        
        response = client.post("/v1/events", json=event_data, headers=auth_headers)
        
        assert_error_response(response, "VALIDATION_ERROR", expected_status=400)
    
    def test_create_event_empty_source(self, client, auth_headers):
        """Test event creation with empty source field."""
        event_data = {
            "source": "",
            "event_type": "test",
            "payload": {"key": "value"}
        }
        
        response = client.post("/v1/events", json=event_data, headers=auth_headers)
        
        assert_error_response(response, "VALIDATION_ERROR", expected_status=400)
    
    def test_create_event_empty_event_type(self, client, auth_headers):
        """Test event creation with empty event_type field."""
        event_data = {
            "source": "test-source",
            "event_type": "",
            "payload": {"key": "value"}
        }
        
        response = client.post("/v1/events", json=event_data, headers=auth_headers)
        
        assert_error_response(response, "VALIDATION_ERROR", expected_status=400)
    
    def test_create_event_empty_payload(self, client, auth_headers):
        """Test event creation with empty payload."""
        event_data = {
            "source": "test-source",
            "event_type": "test",
            "payload": {}
        }
        
        response = client.post("/v1/events", json=event_data, headers=auth_headers)
        
        assert_error_response(response, "VALIDATION_ERROR", expected_status=400)
    
    def test_create_event_payload_too_large(self, client, auth_headers):
        """Test event creation with payload exceeding 400KB limit."""
        large_payload = create_large_payload(401)  # 401 KB
        
        event_data = {
            "source": "test-source",
            "event_type": "test",
            "payload": large_payload
        }
        
        response = client.post("/v1/events", json=event_data, headers=auth_headers)
        
        assert_error_response(response, "PAYLOAD_TOO_LARGE", expected_status=413)
        assert_request_id_present(response)
    
    def test_create_event_unknown_fields(self, client, auth_headers, sample_event):
        """Test event creation with unknown fields (should be rejected)."""
        event_data = sample_event.copy()
        event_data["unknown_field"] = "should be rejected"
        
        response = client.post("/v1/events", json=event_data, headers=auth_headers)
        
        assert_error_response(response, "VALIDATION_ERROR", expected_status=400)
    
    def test_create_event_missing_api_key(self, client, sample_event):
        """Test event creation without API key."""
        response = client.post("/v1/events", json=sample_event)
        
        assert_error_response(response, "UNAUTHORIZED", expected_status=401)
        assert_request_id_present(response)
    
    def test_create_event_invalid_api_key(self, client, sample_event):
        """Test event creation with invalid API key."""
        headers = {"X-API-Key": "invalid-key"}
        response = client.post("/v1/events", json=sample_event, headers=headers)
        
        assert_error_response(response, "UNAUTHORIZED", expected_status=401)
    
    def test_create_event_database_error(self, client, auth_headers, sample_event):
        """Test event creation with database error."""
        with patch('src.endpoints.events.create_event') as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            response = client.post("/v1/events", json=sample_event, headers=auth_headers)
            
            # Should return 500 Internal Error
            assert response.status_code == 500
            assert_request_id_present(response)


class TestAcknowledgeEvent:
    """Tests for POST /v1/events/{id}/ack endpoint"""
    
    def test_acknowledge_event_success(self, client, auth_headers):
        """Test successful event acknowledgment."""
        event_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('src.endpoints.events.acknowledge_event') as mock_ack:
            mock_ack.return_value = {
                'event_id': event_id,
                'status': 'acknowledged',
                'acknowledged_at': '2024-01-01T12:00:00.000000Z'
            }
            
            response = client.post(f"/v1/events/{event_id}/ack", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            assert_request_id_present(response)
            
            data = response.json()
            assert data["event_id"] == event_id
            assert data["status"] == "acknowledged"
            assert "acknowledged_at" in data
    
    def test_acknowledge_event_not_found(self, client, auth_headers):
        """Test acknowledgment of non-existent event."""
        event_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('src.endpoints.events.acknowledge_event') as mock_ack:
            mock_ack.return_value = None
            
            with patch('src.endpoints.events.get_event') as mock_get:
                mock_get.return_value = None
                
                response = client.post(f"/v1/events/{event_id}/ack", headers=auth_headers)
                
                assert_error_response(response, "NOT_FOUND", expected_status=404)
                assert_request_id_present(response)
    
    def test_acknowledge_event_already_acknowledged(self, client, auth_headers):
        """Test acknowledgment of already acknowledged event."""
        event_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('src.endpoints.events.acknowledge_event') as mock_ack:
            mock_ack.return_value = None  # Returns None when already acknowledged
            
            with patch('src.endpoints.events.get_event') as mock_get:
                mock_get.return_value = {
                    'event_id': event_id,
                    'status': 'acknowledged'
                }
                
                from botocore.exceptions import ClientError
                error = ClientError(
                    {'Error': {'Code': 'ConditionalCheckFailedException'}},
                    'UpdateItem'
                )
                mock_ack.side_effect = error
                
                response = client.post(f"/v1/events/{event_id}/ack", headers=auth_headers)
                
                assert_error_response(response, "CONFLICT", expected_status=409)
                assert_request_id_present(response)
    
    def test_acknowledge_event_invalid_uuid(self, client, auth_headers):
        """Test acknowledgment with invalid UUID format."""
        invalid_id = "not-a-uuid"
        
        response = client.post(f"/v1/events/{invalid_id}/ack", headers=auth_headers)
        
        assert_error_response(response, "VALIDATION_ERROR", expected_status=422)
    
    def test_acknowledge_event_missing_api_key(self, client):
        """Test acknowledgment without API key."""
        event_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.post(f"/v1/events/{event_id}/ack")
        
        assert_error_response(response, "UNAUTHORIZED", expected_status=401)
    
    def test_acknowledge_event_invalid_api_key(self, client):
        """Test acknowledgment with invalid API key."""
        event_id = "550e8400-e29b-41d4-a716-446655440000"
        headers = {"X-API-Key": "invalid-key"}
        
        response = client.post(f"/v1/events/{event_id}/ack", headers=headers)
        
        assert_error_response(response, "UNAUTHORIZED", expected_status=401)


class TestDeleteEvent:
    """Tests for DELETE /v1/events/{id} endpoint"""
    
    def test_delete_event_success(self, client, auth_headers):
        """Test successful event deletion."""
        event_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('src.endpoints.events.delete_event') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete(f"/v1/events/{event_id}", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            assert_request_id_present(response)
            
            data = response.json()
            assert data["event_id"] == event_id
            assert "message" in data
    
    def test_delete_event_idempotent(self, client, auth_headers):
        """Test that deletion is idempotent (no error if event doesn't exist)."""
        event_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('src.endpoints.events.delete_event') as mock_delete:
            mock_delete.return_value = False  # Event doesn't exist
            
            response = client.delete(f"/v1/events/{event_id}", headers=auth_headers)
            
            # Should still return 200 (idempotent)
            assert_success_response(response, expected_status=200)
    
    def test_delete_event_invalid_uuid(self, client, auth_headers):
        """Test deletion with invalid UUID format."""
        invalid_id = "not-a-uuid"
        
        response = client.delete(f"/v1/events/{invalid_id}", headers=auth_headers)
        
        assert_error_response(response, "VALIDATION_ERROR", expected_status=422)
    
    def test_delete_event_missing_api_key(self, client):
        """Test deletion without API key."""
        event_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.delete(f"/v1/events/{event_id}")
        
        assert_error_response(response, "UNAUTHORIZED", expected_status=401)
    
    def test_delete_event_invalid_api_key(self, client):
        """Test deletion with invalid API key."""
        event_id = "550e8400-e29b-41d4-a716-446655440000"
        headers = {"X-API-Key": "invalid-key"}
        
        response = client.delete(f"/v1/events/{event_id}", headers=headers)
        
        assert_error_response(response, "UNAUTHORIZED", expected_status=401)

