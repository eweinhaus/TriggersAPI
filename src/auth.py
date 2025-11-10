"""API key authentication"""

import os
import logging
from fastapi import Request, Depends
from botocore.exceptions import ClientError
from src.exceptions import UnauthorizedError
from src.database import _get_api_keys_table

logger = logging.getLogger(__name__)


def validate_api_key(request: Request) -> str:
    """
    Validate API key from request header.
    Supports both local (hardcoded) and AWS (DynamoDB) modes.
    
    Args:
        request: FastAPI request object
        
    Returns:
        API key if valid
        
    Raises:
        UnauthorizedError: If API key is missing or invalid
    """
    auth_mode = os.getenv('AUTH_MODE', 'local')
    api_key = request.headers.get('X-API-Key')
    
    if not api_key:
        raise UnauthorizedError("Missing X-API-Key header")
    
    if auth_mode == 'local':
        # Hardcoded test key for local development
        valid_key = 'test-api-key-12345'
        if api_key != valid_key:
            raise UnauthorizedError("Invalid API key")
        return api_key
    elif auth_mode == 'aws':
        # Validate against DynamoDB API Keys table
        try:
            table = _get_api_keys_table()
            response = table.get_item(
                Key={'api_key': api_key}
            )
            
            item = response.get('Item')
            if not item:
                raise UnauthorizedError("Invalid API key")
            
            # Check if key is active
            is_active = item.get('is_active', True)
            if not is_active:
                raise UnauthorizedError("API key is inactive")
            
            return api_key
        except ClientError as e:
            logger.error(f"DynamoDB error during API key validation: {e}")
            raise UnauthorizedError("Error validating API key")
        except Exception as e:
            logger.error(f"Unexpected error during API key validation: {e}")
            raise UnauthorizedError("Error validating API key")
    else:
        raise UnauthorizedError(f"Unsupported AUTH_MODE: {auth_mode}")


def get_api_key(request: Request) -> str:
    """
    FastAPI dependency for API key validation.
    
    Args:
        request: FastAPI request object (automatically injected)
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: 401 if invalid
    """
    return validate_api_key(request)

