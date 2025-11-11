"""Utilities for request signing"""

import hmac
import hashlib
import base64
import time
from typing import Optional


def hash_request_body(body: Optional[bytes]) -> str:
    """
    Hash request body with SHA256.
    
    Args:
        body: Request body bytes (or None for empty body)
        
    Returns:
        Hex-encoded SHA256 hash
    """
    if not body:
        body = b''
    return hashlib.sha256(body).hexdigest()


def generate_request_signature(
    method: str,
    path: str,
    query_string: str,
    timestamp: str,
    body_hash: str,
    secret_key: str
) -> str:
    """
    Generate HMAC signature for request.
    
    Signature format:
    HMAC-SHA256(
      method + "\n" +
      path + "\n" +
      query_string + "\n" +
      timestamp + "\n" +
      body_hash,
      secret_key
    )
    
    Args:
        method: HTTP method (e.g., "POST")
        path: Request path (e.g., "/v1/events")
        query_string: Query string without ? (e.g., "limit=10" or "")
        timestamp: Unix timestamp as string
        body_hash: SHA256 hash of request body (hex-encoded)
        secret_key: Secret key for signing
        
    Returns:
        Base64-encoded HMAC-SHA256 signature
    """
    # Build signature string
    signature_string = f"{method}\n{path}\n{query_string}\n{timestamp}\n{body_hash}"
    
    # Calculate HMAC-SHA256
    signature = hmac.new(
        secret_key.encode(),
        signature_string.encode(),
        hashlib.sha256
    ).digest()
    
    # Return base64-encoded signature
    return base64.b64encode(signature).decode()


def sign_request(
    method: str,
    path: str,
    query_string: str,
    body: Optional[bytes],
    secret_key: str
) -> dict:
    """
    Generate signature headers for a request.
    
    Args:
        method: HTTP method
        path: Request path
        query_string: Query string (without ?)
        body: Request body bytes
        secret_key: Secret key for signing
        
    Returns:
        Dictionary with signature headers:
        - X-Signature-Timestamp: Unix timestamp
        - X-Signature: HMAC signature
        - X-Signature-Version: Signature version (v1)
    """
    timestamp = str(int(time.time()))
    body_hash = hash_request_body(body)
    signature = generate_request_signature(
        method=method,
        path=path,
        query_string=query_string,
        timestamp=timestamp,
        body_hash=body_hash,
        secret_key=secret_key
    )
    
    return {
        'X-Signature-Timestamp': timestamp,
        'X-Signature': signature,
        'X-Signature-Version': 'v1'
    }

