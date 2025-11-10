"""End-to-end tests for event endpoints"""

import pytest
from tests.utils.test_helpers import assert_success_response, assert_error_response, assert_request_id_present


class TestE2EEvents:
    """E2E tests for event endpoints against real server"""
    
    @pytest.mark.e2e
    def test_create_event_e2e(self, e2e_client, api_key, sample_event):
        """Test event creation against real server."""
        headers = {"X-API-Key": api_key}
        
        response = e2e_client.post("/v1/events", json=sample_event, headers=headers)
        
        assert_success_response(response, expected_status=201)
        assert_request_id_present(response)
        
        data = response.json()
        assert "event_id" in data
        assert data["status"] == "pending"
    
    @pytest.mark.e2e
    def test_acknowledge_event_e2e(self, e2e_client, api_key, sample_event):
        """Test event acknowledgment against real server."""
        headers = {"X-API-Key": api_key}
        
        # Create event first
        create_response = e2e_client.post("/v1/events", json=sample_event, headers=headers)
        event_id = create_response.json()["event_id"]
        
        # Acknowledge it
        ack_response = e2e_client.post(f"/v1/events/{event_id}/ack", headers=headers)
        
        assert_success_response(ack_response, expected_status=200)
        assert_request_id_present(ack_response)
        
        ack_data = ack_response.json()
        assert ack_data["status"] == "acknowledged"
        assert "acknowledged_at" in ack_data
    
    @pytest.mark.e2e
    def test_acknowledge_already_acknowledged_e2e(self, e2e_client, api_key, sample_event):
        """Test acknowledging already acknowledged event."""
        headers = {"X-API-Key": api_key}
        
        # Create and acknowledge event
        create_response = e2e_client.post("/v1/events", json=sample_event, headers=headers)
        event_id = create_response.json()["event_id"]
        e2e_client.post(f"/v1/events/{event_id}/ack", headers=headers)
        
        # Try to acknowledge again
        ack_response = e2e_client.post(f"/v1/events/{event_id}/ack", headers=headers)
        
        assert_error_response(ack_response, "CONFLICT", expected_status=409)
    
    @pytest.mark.e2e
    def test_delete_event_e2e(self, e2e_client, api_key, sample_event):
        """Test event deletion against real server."""
        headers = {"X-API-Key": api_key}
        
        # Create event first
        create_response = e2e_client.post("/v1/events", json=sample_event, headers=headers)
        event_id = create_response.json()["event_id"]
        
        # Delete it
        delete_response = e2e_client.delete(f"/v1/events/{event_id}", headers=headers)
        
        assert_success_response(delete_response, expected_status=200)
        assert_request_id_present(delete_response)
    
    @pytest.mark.e2e
    def test_delete_event_idempotent_e2e(self, e2e_client, api_key):
        """Test that deletion is idempotent."""
        headers = {"X-API-Key": api_key}
        non_existent_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Should return 200 (idempotent)
        delete_response = e2e_client.delete(f"/v1/events/{non_existent_id}", headers=headers)
        
        assert_success_response(delete_response, expected_status=200)

