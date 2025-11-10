"""Custom exception classes for API errors"""


class APIException(Exception):
    """Base exception for API errors."""
    
    def __init__(self, status_code: int, error_code: str, message: str, details: dict = None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIException):
    """Invalid request payload."""
    
    def __init__(self, message: str = "Invalid request payload", details: dict = None):
        super().__init__(400, "VALIDATION_ERROR", message, details)


class UnauthorizedError(APIException):
    """Missing or invalid API key."""
    
    def __init__(self, message: str = "Unauthorized", details: dict = None):
        super().__init__(401, "UNAUTHORIZED", message, details)


class NotFoundError(APIException):
    """Resource not found."""
    
    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(404, "NOT_FOUND", message, details)


class ConflictError(APIException):
    """Resource conflict (e.g., already acknowledged)."""
    
    def __init__(self, message: str = "Resource conflict", details: dict = None):
        super().__init__(409, "CONFLICT", message, details)


class PayloadTooLargeError(APIException):
    """Payload exceeds maximum size."""
    
    def __init__(self, message: str = "Payload too large", details: dict = None):
        super().__init__(413, "PAYLOAD_TOO_LARGE", message, details)


class InternalError(APIException):
    """Internal server error."""
    
    def __init__(self, message: str = "Internal server error", details: dict = None):
        super().__init__(500, "INTERNAL_ERROR", message, details)

