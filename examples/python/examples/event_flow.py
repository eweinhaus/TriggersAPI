"""Complete event lifecycle example"""

from triggers_api import TriggersAPIClient, TriggersAPIError

# Initialize client
client = TriggersAPIClient(
    api_key="test-api-key-12345",
    base_url="http://localhost:8080"
)

print("=== Complete Event Lifecycle Example ===\n")

try:
    # Step 1: Create an event
    print("1. Creating event...")
    event = client.create_event(
        source="workflow-app",
        event_type="task.completed",
        payload={
            "task_id": "task-123",
            "user_id": "user-456",
            "completed_at": "2025-11-10T12:00:00Z"
        },
        metadata={
            "priority": "high",
            "correlation_id": "workflow-789",
            "idempotency_key": "task-123-completed"
        }
    )
    print(f"   ✓ Event created: {event.event_id}")
    print(f"   Status: {event.status}")
    
    # Step 2: Get inbox to see the event
    print("\n2. Checking inbox...")
    inbox = client.get_inbox(limit=50, source="workflow-app")
    print(f"   ✓ Found {len(inbox.events)} pending events from workflow-app")
    
    # Step 3: Get full event details
    print("\n3. Getting event details...")
    event_details = client.get_event(event.event_id)
    print(f"   ✓ Event details retrieved")
    print(f"   Source: {event_details.source}")
    print(f"   Type: {event_details.event_type}")
    print(f"   Payload: {event_details.payload}")
    print(f"   Metadata: {event_details.metadata}")
    
    # Step 4: Process the event (simulate processing)
    print("\n4. Processing event...")
    # In a real application, you would process the event here
    print(f"   ✓ Processing event {event.event_id}")
    print(f"   Task ID: {event_details.payload.get('task_id')}")
    
    # Step 5: Acknowledge the event
    print("\n5. Acknowledging event...")
    ack = client.acknowledge_event(event.event_id)
    print(f"   ✓ Event acknowledged")
    print(f"   Acknowledged at: {ack.acknowledged_at}")
    
    # Step 6: Verify event is acknowledged
    print("\n6. Verifying acknowledgment...")
    updated_event = client.get_event(event.event_id)
    print(f"   ✓ Event status: {updated_event.status}")
    print(f"   Acknowledged at: {updated_event.acknowledged_at}")
    
    # Step 7: Clean up - delete the event
    print("\n7. Cleaning up...")
    result = client.delete_event(event.event_id)
    print(f"   ✓ Event deleted: {result.message}")
    
    print("\n=== Event Lifecycle Complete ===")
    
except TriggersAPIError as e:
    print(f"\n✗ API Error: {e}")
    print(f"   Error Code: {e.error_code}")
    print(f"   Status Code: {e.status_code}")
    if e.request_id:
        print(f"   Request ID: {e.request_id}")
    if e.details:
        print(f"   Details: {e.details}")


