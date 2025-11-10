"""Playwright MCP tests for API endpoints using HTTP requests"""

import pytest
import httpx
from tests.utils.test_helpers import assert_success_response, assert_error_response, assert_request_id_present
from tests.utils.fixtures import generate_event_data


class TestPlaywrightAPI:
    """Playwright MCP tests for API endpoints via HTTP"""
    
    @pytest.mark.playwright
    def test_health_endpoint_playwright(self, api_base_url):
        """Test GET /v1/health via HTTP."""
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            response = client.get("/v1/health")
            
            assert_success_response(response, expected_status=200)
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data
    
    @pytest.mark.playwright
    def test_create_event_playwright(self, api_base_url, playwright_api_key, sample_event):
        """Test POST /v1/events via HTTP."""
        headers = {
            "X-API-Key": playwright_api_key,
            "Content-Type": "application/json"
        }
        
        with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
            response = client.post("/v1/events", json=sample_event, headers=headers)
            
            assert_success_response(response, expected_status=201)
            assert_request_id_present(response)
            
            data = response.json()
            assert "event_id" in data
            assert data["status"] == "pending"
            assert "X-Request-ID" in response.headers
    
    @pytest.mark.playwright
    def test_create_event_error_cases_playwright(self, api_base_url, playwright_api_key):
        """Test POST /v1/events error cases via HTTP."""
        headers = {
            "X-API-Key": playwright_api_key,
            "Content-Type": "application/json"
        }
        
        with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
            # Missing source
            response = client.post(
                "/v1/events",
                json={"event_type": "test", "payload": {"key": "value"}},
                headers=headers
            )
            assert_error_response(response, "VALIDATION_ERROR", expected_status=400)
            
            # Missing API key
            response = client.post(
                "/v1/events",
                json={"source": "test", "event_type": "test", "payload": {"key": "value"}}
            )
            assert_error_response(response, "UNAUTHORIZED", expected_status=401)
    
    @pytest.mark.playwright
    def test_get_inbox_playwright(self, api_base_url, playwright_api_key, sample_event):
        """Test GET /v1/inbox via HTTP."""
        headers = {
            "X-API-Key": playwright_api_key,
            "Content-Type": "application/json"
        }
        
        with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
            # Create an event first
            create_response = client.post("/v1/events", json=sample_event, headers=headers)
            assert create_response.status_code == 201
            
            # Get inbox
            response = client.get("/v1/inbox", headers=headers)
            
            assert_success_response(response, expected_status=200)
            assert_request_id_present(response)
            
            data = response.json()
            assert "events" in data
            assert "pagination" in data
            assert isinstance(data["events"], list)
    
    @pytest.mark.playwright
    def test_get_inbox_with_filters_playwright(self, api_base_url, playwright_api_key):
        """Test GET /v1/inbox with filters via HTTP."""
        headers = {
            "X-API-Key": playwright_api_key,
            "Content-Type": "application/json"
        }
        
        with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
            # Create event with specific source
            event_data = generate_event_data(source="filter-test-source")
            client.post("/v1/events", json=event_data, headers=headers)
            
            # Filter by source
            response = client.get(
                "/v1/inbox?source=filter-test-source",
                headers=headers
            )
            
            assert_success_response(response, expected_status=200)
            data = response.json()
            # All returned events should match the filter
            assert all(e.get("source") == "filter-test-source" for e in data["events"])
    
    @pytest.mark.playwright
    def test_acknowledge_event_playwright(self, api_base_url, playwright_api_key, sample_event):
        """Test POST /v1/events/{id}/ack via HTTP."""
        headers = {
            "X-API-Key": playwright_api_key,
            "Content-Type": "application/json"
        }
        
        with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
            # Create event first
            create_response = client.post("/v1/events", json=sample_event, headers=headers)
            event_id = create_response.json()["event_id"]
            
            # Acknowledge it
            ack_response = client.post(f"/v1/events/{event_id}/ack", headers=headers)
            
            assert_success_response(ack_response, expected_status=200)
            assert_request_id_present(ack_response)
            
            ack_data = ack_response.json()
            assert ack_data["status"] == "acknowledged"
            assert "acknowledged_at" in ack_data
    
    @pytest.mark.playwright
    def test_acknowledge_event_error_cases_playwright(self, api_base_url, playwright_api_key):
        """Test POST /v1/events/{id}/ack error cases via HTTP."""
        headers = {
            "X-API-Key": playwright_api_key,
            "Content-Type": "application/json"
        }
        
        with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
            # Non-existent event
            non_existent_id = "550e8400-e29b-41d4-a716-446655440000"
            response = client.post(f"/v1/events/{non_existent_id}/ack", headers=headers)
            assert_error_response(response, "NOT_FOUND", expected_status=404)
            
            # Invalid UUID
            response = client.post("/v1/events/invalid-uuid/ack", headers=headers)
            assert_error_response(response, "VALIDATION_ERROR", expected_status=422)
    
    @pytest.mark.playwright
    def test_delete_event_playwright(self, api_base_url, playwright_api_key, sample_event):
        """Test DELETE /v1/events/{id} via HTTP."""
        headers = {
            "X-API-Key": playwright_api_key,
            "Content-Type": "application/json"
        }
        
        with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
            # Create event first
            create_response = client.post("/v1/events", json=sample_event, headers=headers)
            event_id = create_response.json()["event_id"]
            
            # Delete it
            delete_response = client.delete(f"/v1/events/{event_id}", headers=headers)
            
            assert_success_response(delete_response, expected_status=200)
            assert_request_id_present(delete_response)
            
            delete_data = delete_response.json()
            assert delete_data["event_id"] == event_id
    
    @pytest.mark.playwright
    def test_delete_event_idempotent_playwright(self, api_base_url, playwright_api_key):
        """Test DELETE /v1/events/{id} is idempotent via HTTP."""
        headers = {
            "X-API-Key": playwright_api_key,
            "Content-Type": "application/json"
        }
        
        with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
            # Delete non-existent event (should still return 200)
            non_existent_id = "550e8400-e29b-41d4-a716-446655440000"
            response = client.delete(f"/v1/events/{non_existent_id}", headers=headers)
            
            assert_success_response(response, expected_status=200)
    
    @pytest.mark.playwright
    def test_full_workflow_playwright(self, api_base_url, playwright_api_key, sample_event):
        """Test complete workflow via HTTP: create → inbox → ack → delete."""
        headers = {
            "X-API-Key": playwright_api_key,
            "Content-Type": "application/json"
        }
        
        with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
            # Step 1: Create event
            create_response = client.post("/v1/events", json=sample_event, headers=headers)
            assert create_response.status_code == 201
            event_id = create_response.json()["event_id"]
            create_request_id = create_response.json()["request_id"]
            
            # Step 2: Get from inbox
            inbox_response = client.get("/v1/inbox", headers=headers)
            assert inbox_response.status_code == 200
            inbox_data = inbox_response.json()
            assert any(e["event_id"] == event_id for e in inbox_data["events"])
            
            # Step 3: Acknowledge event
            ack_response = client.post(f"/v1/events/{event_id}/ack", headers=headers)
            assert ack_response.status_code == 200
            assert ack_response.json()["status"] == "acknowledged"
            
            # Step 4: Verify removed from inbox
            inbox_response_2 = client.get("/v1/inbox", headers=headers)
            inbox_data_2 = inbox_response_2.json()
            assert not any(e["event_id"] == event_id for e in inbox_data_2["events"])
            
            # Step 5: Delete event
            delete_response = client.delete(f"/v1/events/{event_id}", headers=headers)
            assert delete_response.status_code == 200
            
            # Verify all responses have request IDs
            assert "request_id" in create_response.json()
            assert "request_id" in inbox_response.json()
            assert "request_id" in ack_response.json()
            assert "request_id" in delete_response.json()

