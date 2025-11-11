"""Structured JSON logging with request context"""

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import contextvars

# Context variable for request context (thread-safe for async)
request_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    'request_context', default={}
)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging compatible with CloudWatch Log Insights."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
        }
        
        # Add request context if available
        ctx = request_context.get({})
        if ctx:
            log_data.update(ctx)
        
        # Add any extra fields from the log call
        if hasattr(record, 'extra') and record.extra:
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info) if record.exc_info else None,
            }
        
        # Add stack info if present
        if record.stack_info:
            log_data['stack_info'] = record.stack_info
        
        # Ensure all values are JSON serializable
        return json.dumps(log_data, default=str, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger configured with JSON formatter.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handler if it doesn't already have one
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


def set_request_context(
    request_id: Optional[str] = None,
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    **kwargs
) -> None:
    """
    Set request context for structured logging.
    
    Args:
        request_id: Request ID for correlation
        api_key: API key (will be masked)
        endpoint: Endpoint path
        method: HTTP method
        **kwargs: Additional context fields
    """
    ctx = {}
    
    if request_id:
        ctx['request_id'] = request_id
    
    if api_key:
        # Mask API key: show first 8 chars + "..."
        if len(api_key) > 8:
            ctx['api_key'] = api_key[:8] + '...'
        else:
            ctx['api_key'] = '***'
    
    if endpoint:
        ctx['endpoint'] = endpoint
    
    if method:
        ctx['method'] = method
    
    # Add any additional context
    ctx.update(kwargs)
    
    request_context.set(ctx)


def clear_request_context() -> None:
    """Clear request context."""
    request_context.set({})


def get_request_context() -> Dict[str, Any]:
    """
    Get current request context.
    
    Returns:
        Current request context dictionary
    """
    return request_context.get({})

