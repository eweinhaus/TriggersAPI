"""Unit tests for inbox endpoint"""

import pytest
from unittest.mock import patch, MagicMock
from tests.utils.test_helpers import assert_error_response, assert_success_response, assert_request_id_present, encode_cursor, decode_cursor


class TestGetInbox:
    """Tests for GET /v1/inbox endpoint"""
    
    def test_get_inbox_empty(self, client, auth_headers):
        """Test getting inbox when empty."""
        with patch('src.endpoints.inbox.query_pending_events') as mock_query:
            mock_query.return_value = {
                'events': [],
                'last_evaluated_key': None
            }
            
            response = client.get("/v1/inbox", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            assert_request_id_present(response)
            
            data = response.json()
            assert data["events"] == []
            assert "pagination" in data
            assert "next_cursor" not in data["pagination"]
    
    def test_get_inbox_single_event(self, client, auth_headers):
        """Test getting inbox with single event."""
        event = {
            'event_id': 'test-id',
            'source': 'test-source',
            'event_type': 'test-type',
            'status': 'pending'
        }
        
        with patch('src.endpoints.inbox.query_pending_events') as mock_query:
            mock_query.return_value = {
                'events': [event],
                'last_evaluated_key': None
            }
            
            response = client.get("/v1/inbox", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            data = response.json()
            assert len(data["events"]) == 1
            assert data["events"][0]["event_id"] == "test-id"
    
    def test_get_inbox_multiple_events(self, client, auth_headers):
        """Test getting inbox with multiple events."""
        events = [
            {'event_id': f'test-id-{i}', 'source': 'test', 'status': 'pending'}
            for i in range(5)
        ]
        
        with patch('src.endpoints.inbox.query_pending_events') as mock_query:
            mock_query.return_value = {
                'events': events,
                'last_evaluated_key': None
            }
            
            response = client.get("/v1/inbox", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            data = response.json()
            assert len(data["events"]) == 5
    
    def test_get_inbox_pagination_first_page(self, client, auth_headers):
        """Test pagination - first page with cursor."""
        events = [{'event_id': f'test-id-{i}'} for i in range(10)]
        last_key = {'event_id': {'S': 'test-id-9'}, 'created_at': {'S': '2024-01-01T12:00:00Z'}}
        
        with patch('src.endpoints.inbox.query_pending_events') as mock_query:
            mock_query.return_value = {
                'events': events,
                'last_evaluated_key': last_key
            }
            
            response = client.get("/v1/inbox?limit=10", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            data = response.json()
            assert len(data["events"]) == 10
            assert "next_cursor" in data["pagination"]
    
    def test_get_inbox_pagination_next_page(self, client, auth_headers):
        """Test pagination - next page with cursor."""
        cursor = encode_cursor({'event_id': {'S': 'test-id-9'}, 'created_at': {'S': '2024-01-01T12:00:00Z'}})
        events = [{'event_id': f'test-id-{i}'} for i in range(10, 20)]
        
        with patch('src.endpoints.inbox.query_pending_events') as mock_query:
            mock_query.return_value = {
                'events': events,
                'last_evaluated_key': None
            }
            
            response = client.get(f"/v1/inbox?limit=10&cursor={cursor}", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            data = response.json()
            assert len(data["events"]) == 10
            assert "next_cursor" not in data["pagination"]
    
    def test_get_inbox_pagination_last_page(self, client, auth_headers):
        """Test pagination - last page (no cursor)."""
        events = [{'event_id': f'test-id-{i}'} for i in range(5)]
        
        with patch('src.endpoints.inbox.query_pending_events') as mock_query:
            mock_query.return_value = {
                'events': events,
                'last_evaluated_key': None
            }
            
            response = client.get("/v1/inbox?limit=10", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            data = response.json()
            assert len(data["events"]) == 5
            assert "next_cursor" not in data["pagination"]
    
    def test_get_inbox_invalid_cursor(self, client, auth_headers):
        """Test pagination with invalid cursor."""
        invalid_cursor = "not-valid-base64"
        
        response = client.get(f"/v1/inbox?cursor={invalid_cursor}", headers=auth_headers)
        
        # Should handle gracefully or return error
        # The actual behavior depends on decode_cursor implementation
        assert response.status_code in [200, 400]
    
    def test_get_inbox_filter_by_source(self, client, auth_headers):
        """Test filtering by source."""
        events = [{'event_id': 'test-id', 'source': 'test-source', 'status': 'pending'}]
        
        with patch('src.endpoints.inbox.query_pending_events') as mock_query:
            mock_query.return_value = {
                'events': events,
                'last_evaluated_key': None
            }
            
            response = client.get("/v1/inbox?source=test-source", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            mock_query.assert_called_once()
            call_kwargs = mock_query.call_args[1]
            assert call_kwargs['source'] == 'test-source'
    
    def test_get_inbox_filter_by_event_type(self, client, auth_headers):
        """Test filtering by event_type."""
        events = [{'event_id': 'test-id', 'event_type': 'test-type', 'status': 'pending'}]
        
        with patch('src.endpoints.inbox.query_pending_events') as mock_query:
            mock_query.return_value = {
                'events': events,
                'last_evaluated_key': None
            }
            
            response = client.get("/v1/inbox?event_type=test-type", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            call_kwargs = mock_query.call_args[1]
            assert call_kwargs['event_type'] == 'test-type'
    
    def test_get_inbox_filter_by_both(self, client, auth_headers):
        """Test filtering by both source and event_type."""
        events = [{'event_id': 'test-id', 'source': 'test-source', 'event_type': 'test-type'}]
        
        with patch('src.endpoints.inbox.query_pending_events') as mock_query:
            mock_query.return_value = {
                'events': events,
                'last_evaluated_key': None
            }
            
            response = client.get("/v1/inbox?source=test-source&event_type=test-type", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            call_kwargs = mock_query.call_args[1]
            assert call_kwargs['source'] == 'test-source'
            assert call_kwargs['event_type'] == 'test-type'
    
    def test_get_inbox_filter_no_matches(self, client, auth_headers):
        """Test filtering with no matching events."""
        with patch('src.endpoints.inbox.query_pending_events') as mock_query:
            mock_query.return_value = {
                'events': [],
                'last_evaluated_key': None
            }
            
            response = client.get("/v1/inbox?source=nonexistent", headers=auth_headers)
            
            assert_success_response(response, expected_status=200)
            data = response.json()
            assert data["events"] == []
    
    def test_get_inbox_invalid_limit_too_low(self, client, auth_headers):
        """Test with invalid limit (< 1)."""
        response = client.get("/v1/inbox?limit=0", headers=auth_headers)
        
        assert_error_response(response, "VALIDATION_ERROR", expected_status=422)
    
    def test_get_inbox_invalid_limit_too_high(self, client, auth_headers):
        """Test with invalid limit (> 100)."""
        response = client.get("/v1/inbox?limit=101", headers=auth_headers)
        
        assert_error_response(response, "VALIDATION_ERROR", expected_status=422)
    
    def test_get_inbox_empty_source_filter(self, client, auth_headers):
        """Test with empty source filter (should be rejected)."""
        response = client.get("/v1/inbox?source=", headers=auth_headers)
        
        # Should be rejected due to min_length=1 validation
        assert_error_response(response, "VALIDATION_ERROR", expected_status=422)
    
    def test_get_inbox_missing_api_key(self, client):
        """Test getting inbox without API key."""
        response = client.get("/v1/inbox")
        
        assert_error_response(response, "UNAUTHORIZED", expected_status=401)
    
    def test_get_inbox_invalid_api_key(self, client):
        """Test getting inbox with invalid API key."""
        headers = {"X-API-Key": "invalid-key"}
        response = client.get("/v1/inbox", headers=headers)
        
        assert_error_response(response, "UNAUTHORIZED", expected_status=401)

