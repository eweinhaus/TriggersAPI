"""Main client class for Triggers API"""

import json
from typing import Optional, Dict, Any, List
import requests
from pydantic import BaseModel, Field

from .exceptions import (
    TriggersAPIError,
    map_status_code_to_error,
)


class EventResponse(BaseModel):
    """Response model for event creation."""
    event_id: str
    created_at: str
    status: str
    message: str
    request_id: str


class EventDetailResponse(BaseModel):
    """Response model for event details."""
    event_id: str
    created_at: str
    source: str
    event_type: str
    payload: Dict[str, Any]
    status: str
    metadata: Optional[Dict[str, Any]] = None
    acknowledged_at: Optional[str] = None
    request_id: str


class InboxResponse(BaseModel):
    """Response model for inbox query."""
    events: List[Dict[str, Any]]
    pagination: Dict[str, Any]
    request_id: str


class AckResponse(BaseModel):
    """Response model for event acknowledgment."""
    event_id: str
    status: str
    acknowledged_at: str
    message: str
    request_id: str


class DeleteResponse(BaseModel):
    """Response model for event deletion."""
    event_id: str
    message: str
    request_id: str


class TriggersAPIClient:
    """
    Client for interacting with the Zapier Triggers API.
    
    Example:
        >>> client = TriggersAPIClient(
        ...     api_key="your-api-key",
        ...     base_url="https://api.example.com"
        ... )
        >>> event = client.create_event(
        ...     source="my-app",
        ...     event_type="user.created",
        ...     payload={"user_id": "123"}
        ... )
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8080",
        timeout: int = 30,
        request_id: Optional[str] = None,
        signing_secret: Optional[str] = None
    ):
        """
        Initialize the Triggers API client.
        
        Args:
            api_key: Your API key for authentication
            base_url: Base URL of the API (default: http://localhost:8080)
            timeout: Request timeout in seconds (default: 30)
            request_id: Optional request ID for tracking (default: None)
            signing_secret: Optional secret for HMAC request signing (default: None)
        """
        self.api_key = api_key
        # Ensure base_url doesn't end with a slash
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_request_id = request_id
        self.signing_secret = signing_secret
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path (e.g., "/v1/events")
            data: Request body data (for POST requests)
            params: Query parameters (for GET requests)
            request_id: Optional request ID (uses default if not provided)
        
        Returns:
            Response data as dictionary
        
        Raises:
            TriggersAPIError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        # Add request ID if provided
        if request_id or self.default_request_id:
            headers["X-Request-ID"] = request_id or self.default_request_id
        
        # Add signature headers if signing secret is provided
        if self.signing_secret:
            import time
            import hmac
            import hashlib
            import base64
            from urllib.parse import urlparse, parse_qs, urlencode
            
            # Parse URL to get path and query
            parsed_url = urlparse(url)
            path = parsed_url.path
            query_string = urlencode(parse_qs(parsed_url.query), doseq=True) if parsed_url.query else ''
            
            # Get body hash
            body_bytes = json.dumps(data).encode() if data else b''
            body_hash = hashlib.sha256(body_bytes).hexdigest()
            
            # Generate signature
            timestamp = str(int(time.time()))
            signature_string = f"{method}\n{path}\n{query_string}\n{timestamp}\n{body_hash}"
            signature = base64.b64encode(
                hmac.new(
                    self.signing_secret.encode(),
                    signature_string.encode(),
                    hashlib.sha256
                ).digest()
            ).decode()
            
            headers["X-Signature-Timestamp"] = timestamp
            headers["X-Signature"] = signature
            headers["X-Signature-Version"] = "v1"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
        except requests.exceptions.RequestException as e:
            raise TriggersAPIError(
                message=f"Network error: {str(e)}",
                status_code=None
            )
        
        # Parse response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            raise TriggersAPIError(
                message=f"Invalid JSON response: {response.text[:200]}",
                status_code=response.status_code
            )
        
        # Handle errors
        if not response.ok:
            self._handle_error(response.status_code, response_data)
        
        return response_data
    
    def _handle_error(self, status_code: int, response_data: Dict[str, Any]) -> None:
        """
        Handle API error responses.
        
        Args:
            status_code: HTTP status code
            response_data: Error response data
        
        Raises:
            Appropriate TriggersAPIError subclass
        """
        error_data = response_data.get("error", {})
        error_code = error_data.get("code", "UNKNOWN_ERROR")
        message = error_data.get("message", "An error occurred")
        details = error_data.get("details", {})
        request_id = error_data.get("request_id")
        
        error_class = map_status_code_to_error(status_code)
        raise error_class(
            message=message,
            status_code=status_code,
            error_code=error_code,
            details=details,
            request_id=request_id
        )
    
    def create_event(
        self,
        source: str,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> EventResponse:
        """
        Create a new event.
        
        Args:
            source: Event source identifier
            event_type: Event type identifier
            payload: Event payload (JSON object)
            metadata: Optional metadata (idempotency_key, priority, correlation_id)
            request_id: Optional request ID for tracking
        
        Returns:
            EventResponse with created event information
        
        Example:
            >>> event = client.create_event(
            ...     source="my-app",
            ...     event_type="user.created",
            ...     payload={"user_id": "123", "name": "John"},
            ...     metadata={"idempotency_key": "unique-key-123"}
            ... )
        """
        data = {
            "source": source,
            "event_type": event_type,
            "payload": payload,
        }
        if metadata:
            data["metadata"] = metadata
        
        response_data = self._make_request(
            method="POST",
            endpoint="/v1/events",
            data=data,
            request_id=request_id
        )
        return EventResponse(**response_data)
    
    def get_event(
        self,
        event_id: str,
        request_id: Optional[str] = None
    ) -> EventDetailResponse:
        """
        Get detailed information about a specific event.
        
        Args:
            event_id: UUID v4 of the event
            request_id: Optional request ID for tracking
        
        Returns:
            EventDetailResponse with complete event information
        
        Example:
            >>> event = client.get_event("550e8400-e29b-41d4-a716-446655440000")
        """
        response_data = self._make_request(
            method="GET",
            endpoint=f"/v1/events/{event_id}",
            request_id=request_id
        )
        return EventDetailResponse(**response_data)
    
    def get_inbox(
        self,
        limit: int = 50,
        cursor: Optional[str] = None,
        source: Optional[str] = None,
        event_type: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> InboxResponse:
        """
        Get pending events with pagination and filtering.
        
        Args:
            limit: Number of events to return (1-100, default: 50)
            cursor: Pagination cursor from previous response
            source: Filter by source identifier
            event_type: Filter by event type
            request_id: Optional request ID for tracking
        
        Returns:
            InboxResponse with events and pagination info
        
        Example:
            >>> inbox = client.get_inbox(limit=10, source="my-app")
            >>> for event in inbox.events:
            ...     print(event["event_id"])
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if source:
            params["source"] = source
        if event_type:
            params["event_type"] = event_type
        
        response_data = self._make_request(
            method="GET",
            endpoint="/v1/inbox",
            params=params,
            request_id=request_id
        )
        return InboxResponse(**response_data)
    
    def acknowledge_event(
        self,
        event_id: str,
        request_id: Optional[str] = None
    ) -> AckResponse:
        """
        Acknowledge an event.
        
        Args:
            event_id: UUID v4 of the event to acknowledge
            request_id: Optional request ID for tracking
        
        Returns:
            AckResponse with acknowledgment information
        
        Example:
            >>> ack = client.acknowledge_event("550e8400-e29b-41d4-a716-446655440000")
        """
        response_data = self._make_request(
            method="POST",
            endpoint=f"/v1/events/{event_id}/ack",
            request_id=request_id
        )
        return AckResponse(**response_data)
    
    def delete_event(
        self,
        event_id: str,
        request_id: Optional[str] = None
    ) -> DeleteResponse:
        """
        Delete an event.
        
        Args:
            event_id: UUID v4 of the event to delete
            request_id: Optional request ID for tracking
        
        Returns:
            DeleteResponse with deletion confirmation
        
        Example:
            >>> result = client.delete_event("550e8400-e29b-41d4-a716-446655440000")
        """
        response_data = self._make_request(
            method="DELETE",
            endpoint=f"/v1/events/{event_id}",
            request_id=request_id
        )
        return DeleteResponse(**response_data)

