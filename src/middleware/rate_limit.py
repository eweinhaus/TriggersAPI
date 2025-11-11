"""Rate limiting middleware"""

import time
import logging
from fastapi import Request
from botocore.exceptions import ClientError
from src.database import check_rate_limit, increment_rate_limit, get_rate_limit_for_api_key
from src.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware.
    
    Checks rate limit before processing request and adds rate limit headers to response.
    Skips rate limiting for health check endpoint.
    """
    # Skip health check endpoint
    if request.url.path == "/v1/health":
        return await call_next(request)
    
    # Get API key from request (already validated by auth middleware)
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        # No API key - auth middleware will handle this
        return await call_next(request)
    
    # Get rate limit config for API key (default: 1000/min)
    try:
        rate_limit = get_rate_limit_for_api_key(api_key)
    except Exception as e:
        logger.warning(f"Error getting rate limit for API key: {e}, using default")
        rate_limit = 1000
    
    # Calculate window start
    current_time = int(time.time())
    window_seconds = 60
    window_start = (current_time // window_seconds) * window_seconds
    
    # Check rate limit
    try:
        allowed, remaining, reset_timestamp = check_rate_limit(api_key, rate_limit, window_seconds)
        
        if not allowed:
            # Rate limit exceeded
            retry_after = reset_timestamp - current_time
            raise RateLimitExceededError(
                message="Rate limit exceeded",
                details={
                    "limit": rate_limit,
                    "reset_at": reset_timestamp,
                    "retry_after": retry_after
                }
            )
        
        # Increment rate limit counter
        try:
            increment_rate_limit(api_key, window_start, rate_limit)
            # Update remaining count after increment
            remaining = max(0, remaining - 1)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                # Rate limit exceeded during increment (race condition)
                retry_after = reset_timestamp - current_time
                raise RateLimitExceededError(
                    message="Rate limit exceeded",
                    details={
                        "limit": rate_limit,
                        "reset_at": reset_timestamp,
                        "retry_after": retry_after
                    }
                )
            # Other errors - log but allow request (fail open)
            logger.warning(f"Error incrementing rate limit: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_timestamp)
        
        return response
        
    except RateLimitExceededError:
        # Re-raise rate limit errors
        raise
    except Exception as e:
        # On unexpected error, log and allow request (fail open)
        logger.error(f"Unexpected error in rate limit middleware: {e}", exc_info=True)
        return await call_next(request)

