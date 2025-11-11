"""Error handling examples for Triggers API client"""

from triggers_api import (
    TriggersAPIClient,
    TriggersAPIError,
    ValidationError,
    UnauthorizedError,
    NotFoundError,
    ConflictError,
    PayloadTooLargeError,
    RateLimitError,
    InternalError,
)

# Initialize client
client = TriggersAPIClient(
    api_key="test-api-key-12345",
    base_url="http://localhost:8080"
)

print("=== Error Handling Examples ===\n")

# Example 1: Handling validation errors
print("1. Validation Error Example")
try:
    # This will fail because source is empty
    event = client.create_event(
        source="",  # Invalid: empty source
        event_type="test.event",
        payload={"test": "data"}
    )
except ValidationError as e:
    print(f"   ✓ Caught ValidationError: {e.message}")
    print(f"   Error Code: {e.error_code}")
    if e.details:
        print(f"   Details: {e.details}")
except TriggersAPIError as e:
    print(f"   ✓ Caught TriggersAPIError: {e.message}")

# Example 2: Handling not found errors
print("\n2. Not Found Error Example")
try:
    # This will fail because event doesn't exist
    event = client.get_event("00000000-0000-0000-0000-000000000000")
except NotFoundError as e:
    print(f"   ✓ Caught NotFoundError: {e.message}")
    print(f"   Error Code: {e.error_code}")
    if e.details:
        suggestion = e.details.get("suggestion")
        if suggestion:
            print(f"   Suggestion: {suggestion}")
except TriggersAPIError as e:
    print(f"   ✓ Caught TriggersAPIError: {e.message}")

# Example 3: Handling conflict errors
print("\n3. Conflict Error Example")
try:
    # First, create and acknowledge an event
    event = client.create_event(
        source="test-app",
        event_type="test.event",
        payload={"test": "data"}
    )
    # Acknowledge it
    client.acknowledge_event(event.event_id)
    # Try to acknowledge again (this will cause a conflict)
    client.acknowledge_event(event.event_id)
except ConflictError as e:
    print(f"   ✓ Caught ConflictError: {e.message}")
    print(f"   Error Code: {e.error_code}")
    if e.details:
        current_status = e.details.get("current_status")
        if current_status:
            print(f"   Current Status: {current_status}")
except TriggersAPIError as e:
    print(f"   ✓ Caught TriggersAPIError: {e.message}")

# Example 4: Handling unauthorized errors
print("\n4. Unauthorized Error Example")
try:
    # Create a client with invalid API key
    invalid_client = TriggersAPIClient(
        api_key="invalid-key",
        base_url="http://localhost:8080"
    )
    invalid_client.get_inbox()
except UnauthorizedError as e:
    print(f"   ✓ Caught UnauthorizedError: {e.message}")
    print(f"   Error Code: {e.error_code}")
except TriggersAPIError as e:
    print(f"   ✓ Caught TriggersAPIError: {e.message}")

# Example 5: Generic error handling
print("\n5. Generic Error Handling Example")
try:
    # Try to create an event with invalid data
    event = client.create_event(
        source="test",
        event_type="test",
        payload={}  # Invalid: empty payload
    )
except ValidationError as e:
    print(f"   ✓ Validation error: {e.message}")
except PayloadTooLargeError as e:
    print(f"   ✓ Payload too large: {e.message}")
except TriggersAPIError as e:
    # Catch-all for any API error
    print(f"   ✓ API error: {e.message}")
    print(f"   Status Code: {e.status_code}")
    print(f"   Error Code: {e.error_code}")
    if e.request_id:
        print(f"   Request ID: {e.request_id}")

# Example 6: Error handling with request ID tracking
print("\n6. Error Handling with Request ID")
try:
    event = client.create_event(
        source="",  # Invalid
        event_type="test",
        payload={"test": "data"},
        request_id="my-custom-request-id-123"
    )
except ValidationError as e:
    print(f"   ✓ Error: {e.message}")
    if e.request_id:
        print(f"   Request ID: {e.request_id}")
        print(f"   You can use this request ID for support/debugging")

# Example 7: Retry logic with exponential backoff
print("\n7. Retry Logic with Exponential Backoff")
import time
import random

def create_event_with_retry(client, event_data, max_retries=3):
    """Retry event creation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return client.create_event(**event_data)
        except (RateLimitError, InternalError) as e:
            if attempt == max_retries - 1:
                print(f"   ✗ All retries failed: {e.message}")
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"   ⚠ Retry {attempt + 1}/{max_retries} after {wait_time:.2f}s")
            time.sleep(wait_time)
        except Exception as e:
            # Don't retry on client errors
            print(f"   ✗ Non-retryable error: {e.message}")
            raise
    return None

try:
    # This will succeed on first attempt (or retry if transient error)
    event = create_event_with_retry(
        client,
        {
            "source": "test-app",
            "event_type": "test.event",
            "payload": {"test": "retry-example"}
        }
    )
    print(f"   ✓ Event created: {event.event_id}")
except Exception as e:
    print(f"   ✗ Failed after retries: {e.message}")

# Example 8: Retry with idempotency key
print("\n8. Retry with Idempotency Key")
import uuid

def create_event_with_retry_and_idempotency(client, event_data, max_retries=3):
    """Retry with idempotency key to prevent duplicates."""
    # Generate idempotency key
    idempotency_key = str(uuid.uuid4())
    event_data.setdefault("metadata", {})["idempotency_key"] = idempotency_key
    
    print(f"   Using idempotency key: {idempotency_key[:20]}...")
    
    for attempt in range(max_retries):
        try:
            return client.create_event(**event_data)
        except (RateLimitError, InternalError) as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            print(f"   ⚠ Retry {attempt + 1}/{max_retries} after {wait_time}s")
            time.sleep(wait_time)
    
    return None

try:
    event = create_event_with_retry_and_idempotency(
        client,
        {
            "source": "test-app",
            "event_type": "test.event",
            "payload": {"test": "idempotency-retry"}
        }
    )
    print(f"   ✓ Event created with idempotency: {event.event_id}")
    
    # Retry with same idempotency key (should return same event)
    event2 = create_event_with_retry_and_idempotency(
        client,
        {
            "source": "test-app",
            "event_type": "test.event",
            "payload": {"test": "idempotency-retry"},
            "metadata": {"idempotency_key": event.metadata.get("idempotency_key")}
        }
    )
    if event.event_id == event2.event_id:
        print(f"   ✓ Idempotency working: Same event returned")
except Exception as e:
    print(f"   ✗ Error: {e.message}")

print("\n=== Error Handling Examples Complete ===")

