"""Basic usage examples for Triggers API client"""

from triggers_api import TriggersAPIClient

# Initialize client
# For local development:
client = TriggersAPIClient(
    api_key="test-api-key-12345",
    base_url="http://localhost:8080"
)

# For production:
# client = TriggersAPIClient(
#     api_key="your-production-api-key",
#     base_url="https://your-api-url.com"
# )

print("=== Creating an Event ===")
# Create an event
event = client.create_event(
    source="my-app",
    event_type="user.created",
    payload={"user_id": "123", "name": "John Doe", "email": "john@example.com"}
)
print(f"Event created: {event.event_id}")
print(f"Status: {event.status}")
print(f"Created at: {event.created_at}")

print("\n=== Getting Event Details ===")
# Get event details
event_details = client.get_event(event.event_id)
print(f"Event ID: {event_details.event_id}")
print(f"Source: {event_details.source}")
print(f"Event Type: {event_details.event_type}")
print(f"Payload: {event_details.payload}")
print(f"Status: {event_details.status}")

print("\n=== Getting Inbox ===")
# Get pending events
inbox = client.get_inbox(limit=10)
print(f"Found {len(inbox.events)} pending events")
for event in inbox.events:
    print(f"  - {event['event_id']}: {event['source']}/{event['event_type']}")

print("\n=== Acknowledging an Event ===")
# Acknowledge the event we created
if inbox.events:
    first_event_id = inbox.events[0]['event_id']
    ack = client.acknowledge_event(first_event_id)
    print(f"Event {ack.event_id} acknowledged")
    print(f"Acknowledged at: {ack.acknowledged_at}")

print("\n=== Deleting an Event ===")
# Delete an event
if inbox.events:
    event_to_delete = inbox.events[0]['event_id']
    result = client.delete_event(event_to_delete)
    print(f"Event {result.event_id} deleted: {result.message}")

print("\n=== Example Complete ===")


