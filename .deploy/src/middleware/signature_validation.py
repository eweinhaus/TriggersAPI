"""Middleware for optional HMAC request signature validation"""

import os
import hmac
import hashlib
import base64
import time
from fastapi import Request, HTTPException
from src.exceptions import UnauthorizedError
from src.database import _get_api_keys_table
from src.utils.logging import get_logger

logger = get_logger(__name__)


def hash_request_body(body: bytes) -> str:
    """
    Hash request body with SHA256.
    
    Args:
        body: Request body bytes
        
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
    
    Args:
        method: HTTP method
        path: Request path
        query_string: Query string (without ?)
        timestamp: Unix timestamp (string)
        body_hash: SHA256 hash of request body
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


async def validate_request_signature(request: Request) -> bool:
    """
    Validate request signature if present.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if valid or not required, False if invalid
        
    Raises:
        UnauthorizedError: If signature is invalid
    """
    # Check if signature validation is enabled
    enable_signing = os.getenv('ENABLE_REQUEST_SIGNING', 'false').lower() == 'true'
    if not enable_signing:
        return True  # Signing not enabled, skip validation
    
    # Get signature headers
    signature = request.headers.get('X-Signature')
    timestamp = request.headers.get('X-Signature-Timestamp')
    signature_version = request.headers.get('X-Signature-Version', 'v1')
    
    # If no signature headers, allow request (backward compatible)
    if not signature or not timestamp:
        return True
    
    # Validate timestamp (reject if >5 minutes old)
    try:
        timestamp_int = int(timestamp)
        current_time = int(time.time())
        if abs(current_time - timestamp_int) > 300:  # 5 minutes
            raise UnauthorizedError("Signature timestamp is too old or too far in the future")
    except (ValueError, TypeError):
        raise UnauthorizedError("Invalid signature timestamp")
    
    # Get API key from request
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        raise UnauthorizedError("API key required for signed requests")
    
    # Get signing secret from API key
    try:
        table = _get_api_keys_table()
        response = table.get_item(Key={'api_key': api_key})
        item = response.get('Item')
        if not item:
            raise UnauthorizedError("Invalid API key")
        
        signing_secret = item.get('signing_secret')
        if not signing_secret:
            # No signing secret configured, allow request (backward compatible)
            return True
    except Exception as e:
        logger.warning(f"Error getting signing secret: {e}")
        # On error, allow request (fail open for backward compatibility)
        return True
    
    # Get request body
    body = await request.body()
    body_hash = hash_request_body(body)
    
    # Build query string
    query_string = str(request.url.query) if request.url.query else ''
    
    # Generate expected signature
    expected_signature = generate_request_signature(
        method=request.method,
        path=request.url.path,
        query_string=query_string,
        timestamp=timestamp,
        body_hash=body_hash,
        secret_key=signing_secret
    )
    
    # Compare signatures (constant-time comparison)
    if not hmac.compare_digest(signature, expected_signature):
        raise UnauthorizedError("Invalid request signature")
    
    return True


async def signature_validation_middleware(request: Request, call_next):
    """
    FastAPI middleware for request signature validation.
    
    Only validates if ENABLE_REQUEST_SIGNING=true and signature headers are present.
    Backward compatible - unsigned requests still work.
    """
    try:
        await validate_request_signature(request)
    except UnauthorizedError as e:
        # Return 401 for invalid signatures
        from fastapi.responses import JSONResponse
        request_id = getattr(request.state, 'request_id', None)
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": str(e),
                    "details": {},
                    "request_id": request_id
                }
            }
        )
    
    response = await call_next(request)
    return response

