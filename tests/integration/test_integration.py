"""Integration tests for full event flow"""

import pytest
from tests.utils.test_helpers import assert_success_response, assert_request_id_present
from tests.utils.fixtures import generate_event_data, create_test_event_in_db


class TestEventLifecycle:
    """Test complete event lifecycle"""
    
    def test_complete_event_lifecycle(self, integration_client, api_key, dynamodb_table):
        """Test complete event lifecycle: create → inbox → ack → delete"""
        # Step 1: Create event
        event_data = generate_event_data()
        headers = {"X-API-Key": api_key}
        
        create_response = integration_client.post("/v1/events", json=event_data, headers=headers)
        
        assert_success_response(create_response, expected_status=201)
        assert_request_id_present(create_response)
        
        event_id = create_response.json()["event_id"]
        create_request_id = create_response.json()["request_id"]
        
        # Step 2: Get from inbox
        inbox_response = integration_client.get("/v1/inbox", headers=headers)
        
        assert_success_response(inbox_response, expected_status=200)
        assert_request_id_present(inbox_response)
        
        inbox_data = inbox_response.json()
        assert len(inbox_data["events"]) >= 1
        assert any(e["event_id"] == event_id for e in inbox_data["events"])
        
        # Step 3: Acknowledge event
        ack_response = integration_client.post(f"/v1/events/{event_id}/ack", headers=headers)
        
        assert_success_response(ack_response, expected_status=200)
        assert_request_id_present(ack_response)
        
        ack_data = ack_response.json()
        assert ack_data["status"] == "acknowledged"
        assert "acknowledged_at" in ack_data
        
        # Step 4: Verify removed from inbox
        inbox_response_2 = integration_client.get("/v1/inbox", headers=headers)
        inbox_data_2 = inbox_response_2.json()
        
        # Event should no longer be in inbox (status changed to acknowledged)
        assert not any(e["event_id"] == event_id for e in inbox_data_2["events"])
        
        # Step 5: Delete event
        delete_response = integration_client.delete(f"/v1/events/{event_id}", headers=headers)
        
        assert_success_response(delete_response, expected_status=200)
        assert_request_id_present(delete_response)
        
        # Verify all responses have request IDs
        assert "request_id" in create_response.json()
        assert "request_id" in inbox_response.json()
        assert "request_id" in ack_response.json()
        assert "request_id" in delete_response.json()


class TestPagination:
    """Test pagination functionality"""
    
    def test_pagination_flow(self, integration_client, api_key, dynamodb_table):
        """Test pagination with multiple pages"""
        # Create 25 events
        event_ids = []
        for i in range(25):
            event_data = generate_event_data()
            response = integration_client.post(
                "/v1/events",
                json=event_data,
                headers={"X-API-Key": api_key}
            )
            event_ids.append(response.json()["event_id"])
        
        # Query first page
        response = integration_client.get("/v1/inbox?limit=10", headers={"X-API-Key": api_key})
        data = response.json()
        
        assert len(data["events"]) == 10
        assert "next_cursor" in data["pagination"]
        
        # Query next page
        cursor = data["pagination"]["next_cursor"]
        response2 = integration_client.get(
            f"/v1/inbox?limit=10&cursor={cursor}",
            headers={"X-API-Key": api_key}
        )
        data2 = response2.json()
        
        assert len(data2["events"]) == 10
        
        # Query last page
        if "next_cursor" in data2["pagination"]:
            cursor2 = data2["pagination"]["next_cursor"]
            response3 = integration_client.get(
                f"/v1/inbox?limit=10&cursor={cursor2}",
                headers={"X-API-Key": api_key}
            )
            data3 = response3.json()
            
            # Should have remaining events
            assert len(data3["events"]) == 5
            assert "next_cursor" not in data3["pagination"]


class TestFiltering:
    """Test filtering functionality"""
    
    def test_source_filter(self, integration_client, api_key, dynamodb_table):
        """Test filtering by source"""
        # Create events with different sources
        for source in ["source-a", "source-b", "source-a"]:
            event_data = generate_event_data(source=source)
            integration_client.post(
                "/v1/events",
                json=event_data,
                headers={"X-API-Key": api_key}
            )
        
        # Filter by source
        response = integration_client.get(
            "/v1/inbox?source=source-a",
            headers={"X-API-Key": api_key}
        )
        
        data = response.json()
        assert all(e["source"] == "source-a" for e in data["events"])
    
    def test_event_type_filter(self, integration_client, api_key, dynamodb_table):
        """Test filtering by event_type"""
        # Create events with different types
        for event_type in ["type-a", "type-b", "type-a"]:
            event_data = generate_event_data(event_type=event_type)
            integration_client.post(
                "/v1/events",
                json=event_data,
                headers={"X-API-Key": api_key}
            )
        
        # Filter by event_type
        response = integration_client.get(
            "/v1/inbox?event_type=type-a",
            headers={"X-API-Key": api_key}
        )
        
        data = response.json()
        assert all(e["event_type"] == "type-a" for e in data["events"])
    
    def test_combined_filters(self, integration_client, api_key, dynamodb_table):
        """Test filtering by both source and event_type"""
        # Create events
        event_data = generate_event_data(source="source-a", event_type="type-a")
        integration_client.post(
            "/v1/events",
            json=event_data,
            headers={"X-API-Key": api_key}
        )
        
        # Filter by both
        response = integration_client.get(
            "/v1/inbox?source=source-a&event_type=type-a",
            headers={"X-API-Key": api_key}
        )
        
        data = response.json()
        assert all(
            e["source"] == "source-a" and e["event_type"] == "type-a"
            for e in data["events"]
        )

