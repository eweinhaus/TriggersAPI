"""Exception classes for Triggers API client"""

from typing import Optional, Dict, Any


class TriggersAPIError(Exception):
    """Base exception for all Triggers API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.request_id = request_id
        super().__init__(self.message)
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.append(f"Code: {self.error_code}")
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        return " | ".join(parts)


class ValidationError(TriggersAPIError):
    """Raised when request validation fails (400)."""
    pass


class UnauthorizedError(TriggersAPIError):
    """Raised when authentication fails (401)."""
    pass


class NotFoundError(TriggersAPIError):
    """Raised when a resource is not found (404)."""
    pass


class ConflictError(TriggersAPIError):
    """Raised when a resource conflict occurs (409)."""
    pass


class PayloadTooLargeError(TriggersAPIError):
    """Raised when payload exceeds size limit (413)."""
    pass


class RateLimitError(TriggersAPIError):
    """Raised when rate limit is exceeded (429)."""
    pass


class InternalError(TriggersAPIError):
    """Raised when an internal server error occurs (500)."""
    pass


def map_status_code_to_error(status_code: int) -> type[TriggersAPIError]:
    """Map HTTP status code to appropriate error class."""
    mapping = {
        400: ValidationError,
        401: UnauthorizedError,
        404: NotFoundError,
        409: ConflictError,
        413: PayloadTooLargeError,
        429: RateLimitError,
        500: InternalError,
    }
    return mapping.get(status_code, TriggersAPIError)

