"""Test helper functions for assertions and utilities"""

import base64
import json
from typing import Dict, Any


def assert_error_response(response, expected_code: str, expected_status: int = None):
    """
    Assert that a response is an error response with the expected error code.
    
    Args:
        response: HTTP response object
        expected_code: Expected error code (e.g., "VALIDATION_ERROR")
        expected_status: Expected HTTP status code (optional)
    """
    assert response.status_code >= 400, f"Expected error status, got {response.status_code}"
    
    if expected_status:
        assert response.status_code == expected_status, \
            f"Expected status {expected_status}, got {response.status_code}"
    
    data = response.json()
    assert "error" in data, "Response should contain 'error' key"
    assert data["error"]["code"] == expected_code, \
        f"Expected error code '{expected_code}', got '{data['error']['code']}'"
    assert "request_id" in data["error"], "Error response should include request_id"
    assert "message" in data["error"], "Error response should include message"


def assert_success_response(response, expected_status: int = 200):
    """
    Assert that a response is a successful response.
    
    Args:
        response: HTTP response object
        expected_status: Expected HTTP status code (default: 200)
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}"
    
    data = response.json()
    assert "request_id" in data, "Success response should include request_id"


def assert_request_id_present(response):
    """
    Assert that a response includes a request_id.
    
    Args:
        response: HTTP response object
    """
    data = response.json()
    
    # Check if it's an error response
    if "error" in data:
        assert "request_id" in data["error"], "Error response should include request_id in error object"
    else:
        assert "request_id" in data, "Success response should include request_id"


def encode_cursor(last_evaluated_key: Dict[str, Any]) -> str:
    """
    Encode DynamoDB LastEvaluatedKey as base64 cursor.
    
    Args:
        last_evaluated_key: DynamoDB LastEvaluatedKey dictionary
    
    Returns:
        Base64-encoded cursor string
    """
    json_str = json.dumps(last_evaluated_key)
    encoded = base64.b64encode(json_str.encode()).decode()
    return encoded


def decode_cursor(cursor: str) -> Dict[str, Any]:
    """
    Decode base64 cursor to DynamoDB LastEvaluatedKey.
    
    Args:
        cursor: Base64-encoded cursor string
    
    Returns:
        DynamoDB LastEvaluatedKey dictionary
    """
    decoded = base64.b64decode(cursor.encode()).decode()
    return json.loads(decoded)


def calculate_payload_size(payload: Dict[str, Any]) -> int:
    """
    Calculate the size of a JSON payload in bytes.
    
    Args:
        payload: JSON-serializable dictionary
    
    Returns:
        Size in bytes
    """
    json_str = json.dumps(payload)
    return len(json_str.encode('utf-8'))


def create_large_payload(size_kb: int) -> Dict[str, Any]:
    """
    Create a payload of approximately the specified size in KB.
    
    Args:
        size_kb: Desired size in KB
    
    Returns:
        Dictionary payload
    """
    # Create a string that's approximately the right size
    target_bytes = size_kb * 1024
    # Account for JSON overhead
    data_size = target_bytes - 100  # Rough estimate for JSON structure
    
    large_string = "x" * data_size
    
    return {
        "data": large_string,
        "type": "large_payload"
    }

