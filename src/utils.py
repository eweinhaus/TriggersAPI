"""Utility functions for timestamps, UUIDs, cursors, and validation"""

import base64
import json
import uuid
from datetime import datetime, timezone
from typing import Any


def get_iso_timestamp() -> str:
    """
    Generate ISO 8601 UTC timestamp with Z suffix and microseconds.
    
    Returns:
        ISO 8601 formatted timestamp (e.g., "2024-01-01T12:00:00.123456Z")
    """
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def generate_uuid() -> str:
    """
    Generate a lowercase UUID v4 string.
    
    Returns:
        Lowercase UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")
    """
    return str(uuid.uuid4()).lower()


def encode_cursor(key: dict[str, Any]) -> str:
    """
    Encode DynamoDB LastEvaluatedKey as base64-encoded JSON string.
    
    Args:
        key: DynamoDB LastEvaluatedKey dictionary
        
    Returns:
        Base64-encoded JSON string
    """
    return base64.b64encode(json.dumps(key).encode()).decode()


def decode_cursor(cursor: str) -> dict[str, Any]:
    """
    Decode base64-encoded cursor to DynamoDB LastEvaluatedKey.
    
    Args:
        cursor: Base64-encoded JSON string
        
    Returns:
        DynamoDB LastEvaluatedKey dictionary
        
    Raises:
        ValueError: If cursor is invalid
    """
    try:
        decoded = base64.b64decode(cursor).decode()
        return json.loads(decoded)
    except (base64.binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Invalid cursor format: {e}")


def validate_payload_size(payload: dict, max_size: int = 400 * 1024) -> None:
    """
    Validate that JSON payload size doesn't exceed maximum.
    
    Args:
        payload: Dictionary to validate
        max_size: Maximum size in bytes (default: 400KB)
        
    Raises:
        ValueError: If payload exceeds maximum size
    """
    payload_json = json.dumps(payload)
    payload_size = len(payload_json.encode('utf-8'))
    
    if payload_size > max_size:
        raise ValueError(
            f"Payload size ({payload_size} bytes) exceeds maximum ({max_size} bytes)"
        )

