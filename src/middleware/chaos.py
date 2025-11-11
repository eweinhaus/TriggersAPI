"""Chaos engineering middleware for failure injection"""

import os
import random
import logging
from fastapi import Request, Response
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ChaosMiddleware:
    """
    Middleware for injecting controlled failures for resilience testing.
    
    Features:
    - Random delays
    - Random errors
    - Configurable failure rates
    - Per-endpoint configuration
    """
    
    def __init__(self, app):
        self.app = app
        self.enabled = os.getenv('CHAOS_ENABLED', 'false').lower() == 'true'
        self.error_rate = float(os.getenv('CHAOS_ERROR_RATE', '0.0'))  # 0.0 to 1.0
        self.delay_rate = float(os.getenv('CHAOS_DELAY_RATE', '0.0'))  # 0.0 to 1.0
        self.max_delay_ms = int(os.getenv('CHAOS_MAX_DELAY_MS', '1000'))
        self.error_codes = [500, 503, 504]  # Error codes to inject
        
        if self.enabled:
            logger.warning(
                "Chaos engineering enabled",
                extra={
                    'error_rate': self.error_rate,
                    'delay_rate': self.delay_rate,
                    'max_delay_ms': self.max_delay_ms
                }
            )
    
    async def __call__(self, scope, receive, send):
        if not self.enabled:
            await self.app(scope, receive, send)
            return
        
        # Only apply to HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Inject delay
        if random.random() < self.delay_rate:
            delay_ms = random.randint(1, self.max_delay_ms)
            import asyncio
            await asyncio.sleep(delay_ms / 1000.0)
            logger.info(f"Chaos: Injected {delay_ms}ms delay")
        
        # Inject error
        if random.random() < self.error_rate:
            error_code = random.choice(self.error_codes)
            error_message = f"Chaos: Injected {error_code} error"
            logger.warning(error_message)
            
            # Send error response
            response = Response(
                content=f'{{"error": {{"code": "CHAOS_ERROR", "message": "{error_message}", "details": {{}}, "request_id": null}}}}',
                status_code=error_code,
                media_type="application/json"
            )
            await response(scope, receive, send)
            return
        
        # Continue normal processing
        await self.app(scope, receive, send)


def inject_chaos_delay(delay_ms: int):
    """
    Decorator to inject a fixed delay for testing.
    
    Args:
        delay_ms: Delay in milliseconds
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            import asyncio
            await asyncio.sleep(delay_ms / 1000.0)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def inject_chaos_error(error_code: int = 500):
    """
    Decorator to inject a fixed error for testing.
    
    Args:
        error_code: HTTP status code to return
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=error_code,
                detail={"code": "CHAOS_ERROR", "message": "Injected error for testing"}
            )
        return wrapper
    return decorator

