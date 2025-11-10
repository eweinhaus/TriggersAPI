"""Unit tests for database layer"""

import pytest
import boto3
from moto import mock_aws
from datetime import datetime, timezone
from src.database import (
    create_event, get_event, query_pending_events,
    acknowledge_event, delete_event, create_tables
)
from src.utils import get_iso_timestamp, generate_uuid


@pytest.fixture
def mock_dynamodb_table(monkeypatch):
    """Create a mock DynamoDB table for testing."""
    with mock_aws():
        dynamodb = boto3.resource(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
        
        # Create events table
        table = dynamodb.create_table(
            TableName='triggers-api-events',
            KeySchema=[
                {'AttributeName': 'event_id', 'KeyType': 'HASH'},
                {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'event_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'status-created_at-index',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Patch the module-level table reference
        monkeypatch.setattr('src.database._events_table', table)
        monkeypatch.setenv('DYNAMODB_TABLE_EVENTS', 'triggers-api-events')
        
        yield table


class TestCreateEvent:
    """Tests for create_event function"""
    
    def test_create_event_success(self, mock_dynamodb_table):
        """Test successful event creation."""
        event = create_event(
            source="test-source",
            event_type="test-type",
            payload={"key": "value"},
            metadata={"priority": "high"}
        )
        
        assert "event_id" in event
        assert event["source"] == "test-source"
        assert event["event_type"] == "test-type"
        assert event["status"] == "pending"
        assert "created_at" in event
        assert "ttl" in event
        
        # Verify event stored in table
        stored = mock_dynamodb_table.get_item(
            Key={'event_id': event['event_id'], 'created_at': event['created_at']}
        )
        assert 'Item' in stored
        assert stored['Item']['status'] == 'pending'
    
    def test_create_event_generates_uuid(self, mock_dynamodb_table):
        """Test that event_id is a valid UUID."""
        event = create_event(
            source="test",
            event_type="test",
            payload={"key": "value"}
        )
        
        event_id = event["event_id"]
        # UUID format: 8-4-4-4-12 hex digits
        assert len(event_id) == 36
        assert event_id.count('-') == 4
    
    def test_create_event_sets_timestamp(self, mock_dynamodb_table):
        """Test that created_at timestamp is set correctly."""
        event = create_event(
            source="test",
            event_type="test",
            payload={"key": "value"}
        )
        
        created_at = event["created_at"]
        assert created_at.endswith('Z')  # UTC timezone
        assert 'T' in created_at  # ISO 8601 format
    
    def test_create_event_sets_status_pending(self, mock_dynamodb_table):
        """Test that status is set to pending."""
        event = create_event(
            source="test",
            event_type="test",
            payload={"key": "value"}
        )
        
        assert event["status"] == "pending"
    
    def test_create_event_calculates_ttl(self, mock_dynamodb_table):
        """Test that TTL is calculated correctly (7 days)."""
        import time
        event = create_event(
            source="test",
            event_type="test",
            payload={"key": "value"}
        )
        
        ttl = event["ttl"]
        current_time = int(time.time())
        expected_ttl = current_time + (7 * 24 * 60 * 60)
        
        # Allow 5 second tolerance
        assert abs(ttl - expected_ttl) < 5


class TestGetEvent:
    """Tests for get_event function"""
    
    def test_get_event_success(self, mock_dynamodb_table):
        """Test retrieving existing event."""
        # Create event first
        event = create_event(
            source="test",
            event_type="test",
            payload={"key": "value"}
        )
        
        # Retrieve it
        retrieved = get_event(event['event_id'], event['created_at'])
        
        assert retrieved is not None
        assert retrieved['event_id'] == event['event_id']
        assert retrieved['source'] == "test"
    
    def test_get_event_not_found(self, mock_dynamodb_table):
        """Test retrieving non-existent event."""
        retrieved = get_event("nonexistent-id")
        
        assert retrieved is None


class TestQueryPendingEvents:
    """Tests for query_pending_events function"""
    
    def test_query_pending_events_empty(self, mock_dynamodb_table):
        """Test querying when no pending events exist."""
        result = query_pending_events(limit=10)
        
        assert result['events'] == []
        assert result.get('last_evaluated_key') is None
    
    def test_query_pending_events_with_results(self, mock_dynamodb_table):
        """Test querying pending events."""
        # Create multiple events
        for i in range(3):
            create_event(
                source=f"source-{i}",
                event_type="test",
                payload={"index": i}
            )
        
        result = query_pending_events(limit=10)
        
        assert len(result['events']) == 3
        assert all(event['status'] == 'pending' for event in result['events'])
    
    def test_query_pending_events_respects_limit(self, mock_dynamodb_table):
        """Test that limit is respected."""
        # Create more events than limit
        for i in range(15):
            create_event(
                source=f"source-{i}",
                event_type="test",
                payload={"index": i}
            )
        
        result = query_pending_events(limit=10)
        
        assert len(result['events']) <= 10
    
    def test_query_pending_events_with_source_filter(self, mock_dynamodb_table):
        """Test filtering by source."""
        # Create events with different sources
        create_event(source="source-a", event_type="test", payload={})
        create_event(source="source-b", event_type="test", payload={})
        create_event(source="source-a", event_type="test", payload={})
        
        result = query_pending_events(limit=10, source="source-a")
        
        assert len(result['events']) == 2
        assert all(event['source'] == 'source-a' for event in result['events'])
    
    def test_query_pending_events_with_event_type_filter(self, mock_dynamodb_table):
        """Test filtering by event_type."""
        # Create events with different types
        create_event(source="test", event_type="type-a", payload={})
        create_event(source="test", event_type="type-b", payload={})
        create_event(source="test", event_type="type-a", payload={})
        
        result = query_pending_events(limit=10, event_type="type-a")
        
        assert len(result['events']) == 2
        assert all(event['event_type'] == 'type-a' for event in result['events'])


class TestAcknowledgeEvent:
    """Tests for acknowledge_event function"""
    
    def test_acknowledge_event_success(self, mock_dynamodb_table):
        """Test successful event acknowledgment."""
        # Create event
        event = create_event(
            source="test",
            event_type="test",
            payload={"key": "value"}
        )
        
        # Acknowledge it
        updated = acknowledge_event(event['event_id'])
        
        assert updated is not None
        assert updated['status'] == 'acknowledged'
        assert 'acknowledged_at' in updated
        
        # Verify in table
        stored = mock_dynamodb_table.get_item(
            Key={'event_id': event['event_id'], 'created_at': event['created_at']}
        )
        assert stored['Item']['status'] == 'acknowledged'
    
    def test_acknowledge_event_not_found(self, mock_dynamodb_table):
        """Test acknowledging non-existent event."""
        updated = acknowledge_event("nonexistent-id")
        
        assert updated is None
    
    def test_acknowledge_event_already_acknowledged(self, mock_dynamodb_table):
        """Test acknowledging already acknowledged event."""
        # Create and acknowledge event
        event = create_event(
            source="test",
            event_type="test",
            payload={"key": "value"}
        )
        acknowledge_event(event['event_id'])
        
        # Try to acknowledge again
        updated = acknowledge_event(event['event_id'])
        
        # Should return None (conditional update fails)
        assert updated is None


class TestDeleteEvent:
    """Tests for delete_event function"""
    
    def test_delete_event_success(self, mock_dynamodb_table):
        """Test successful event deletion."""
        # Create event
        event = create_event(
            source="test",
            event_type="test",
            payload={"key": "value"}
        )
        
        # Delete it
        result = delete_event(event['event_id'])
        
        assert result is True
        
        # Verify deleted
        stored = mock_dynamodb_table.get_item(
            Key={'event_id': event['event_id'], 'created_at': event['created_at']}
        )
        assert 'Item' not in stored
    
    def test_delete_event_idempotent(self, mock_dynamodb_table):
        """Test that deletion is idempotent."""
        # Delete non-existent event
        # According to implementation, get_event returns None, so delete_event returns True (idempotent)
        result = delete_event("nonexistent-id")
        
        # Should not raise error (idempotent)
        # Implementation returns True when event not found (idempotent behavior)
        assert result is True

