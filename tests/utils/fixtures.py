"""Test data generation utilities"""

from typing import List, Dict, Any
from faker import Faker
from src.utils import generate_uuid, get_iso_timestamp

fake = Faker()


def generate_event_data(
    source: str = None,
    event_type: str = None,
    payload: Dict[str, Any] = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate random event data for testing.
    
    Args:
        source: Event source (default: random company name)
        event_type: Event type (default: random word)
        payload: Event payload (default: random dict)
        metadata: Event metadata (default: random metadata)
    
    Returns:
        Dictionary with event data
    """
    return {
        "source": source or fake.company(),
        "event_type": event_type or fake.word(),
        "payload": payload or {
            "message": fake.sentence(),
            "timestamp": fake.iso8601(),
            "data": fake.pydict()
        },
        "metadata": metadata or {
            "priority": fake.random_element(elements=("low", "normal", "high")),
            "correlation_id": generate_uuid()
        }
    }


def generate_multiple_events(count: int, source: str = None, event_type: str = None) -> List[Dict[str, Any]]:
    """
    Generate multiple events for pagination/filtering tests.
    
    Args:
        count: Number of events to generate
        source: Optional source filter
        event_type: Optional event type filter
    
    Returns:
        List of event data dictionaries
    """
    events = []
    for _ in range(count):
        events.append(generate_event_data(source=source, event_type=event_type))
    return events


def create_test_event_in_db(table, event_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a test event in DynamoDB table.
    
    Args:
        table: DynamoDB table resource
        event_data: Event data (default: generated)
    
    Returns:
        Created event item
    """
    from src.database import create_event
    
    if event_data is None:
        event_data = generate_event_data()
    
    # Use database function to create event
    event = create_event(
        source=event_data["source"],
        event_type=event_data["event_type"],
        payload=event_data["payload"],
        metadata=event_data.get("metadata")
    )
    
    return event


def create_test_api_key(table, api_key: str = None, source: str = None) -> str:
    """
    Create a test API key in DynamoDB table.
    
    Args:
        table: DynamoDB table resource
        api_key: API key value (default: generated)
        source: Source identifier (default: random)
    
    Returns:
        API key string
    """
    if api_key is None:
        api_key = f"test-api-key-{generate_uuid()}"
    
    if source is None:
        source = fake.company()
    
    table.put_item(
        Item={
            "api_key": api_key,
            "source": source,
            "created_at": get_iso_timestamp(),
            "is_active": True
        }
    )
    
    return api_key

