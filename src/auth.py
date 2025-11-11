"""API key authentication"""

import os
from fastapi import Request, Depends
from botocore.exceptions import ClientError
from src.exceptions import UnauthorizedError
from src.database import _get_api_keys_table
from src.utils.logging import get_logger

logger = get_logger(__name__)


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
                logger.warning(
                    "API key not found in DynamoDB",
                    extra={
                        'operation': 'validate_api_key',
                        'auth_mode': 'aws',
                        'api_key_length': len(api_key),
                        'error': 'key_not_found',
                    }
                )
                raise UnauthorizedError("Invalid API key")
            
            # Check if key is active
            is_active = item.get('is_active', True)
            if not is_active:
                logger.warning(
                    "API key is inactive",
                    extra={
                        'operation': 'validate_api_key',
                        'auth_mode': 'aws',
                        'api_key_length': len(api_key),
                        'error': 'key_inactive',
                    }
                )
                raise UnauthorizedError("API key is inactive")
            
            # Check key status (support rotation)
            status = item.get('status', 'active')
            if status == 'expired':
                logger.warning(
                    "API key is expired",
                    extra={
                        'operation': 'validate_api_key',
                        'auth_mode': 'aws',
                        'api_key_length': len(api_key),
                        'error': 'key_expired',
                    }
                )
                raise UnauthorizedError("API key is expired")
            
            # Check expiration date if present
            expires_at = item.get('expires_at')
            if expires_at:
                from datetime import datetime, timezone
                try:
                    exp_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) > exp_time:
                        logger.warning(
                            "API key has expired",
                            extra={
                                'operation': 'validate_api_key',
                                'auth_mode': 'aws',
                                'api_key_length': len(api_key),
                                'error': 'key_expired',
                            }
                        )
                        raise UnauthorizedError("API key has expired")
                except (ValueError, TypeError):
                    # Invalid date format, skip expiration check
                    pass
            
            # Accept both "active" and "rotating" status during transition
            if status not in ['active', 'rotating']:
                logger.warning(
                    f"API key has invalid status: {status}",
                    extra={
                        'operation': 'validate_api_key',
                        'auth_mode': 'aws',
                        'api_key_length': len(api_key),
                        'error': 'invalid_status',
                        'status': status,
                    }
                )
                raise UnauthorizedError("API key is not valid")
            
            logger.info(
                "API key validated successfully",
                extra={
                    'operation': 'validate_api_key',
                    'auth_mode': 'aws',
                    'api_key_length': len(api_key),
                }
            )
            return api_key
        except UnauthorizedError:
            # Re-raise UnauthorizedError as-is
            raise
        except ClientError as e:
            logger.error(
                "DynamoDB error during API key validation",
                extra={
                    'operation': 'validate_api_key',
                    'auth_mode': 'aws',
                    'error': str(e),
                    'error_type': 'ClientError',
                }
            )
            raise UnauthorizedError("Error validating API key")
        except Exception as e:
            logger.error(
                "Unexpected error during API key validation",
                extra={
                    'operation': 'validate_api_key',
                    'auth_mode': 'aws',
                    'error': str(e),
                    'error_type': type(e).__name__,
                },
                exc_info=True
            )
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

