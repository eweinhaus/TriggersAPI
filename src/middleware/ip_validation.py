"""IP validation utilities and middleware"""

import ipaddress
import logging
from fastapi import Request
from src.database import get_allowed_ips_for_api_key
from src.exceptions import ForbiddenError

logger = logging.getLogger(__name__)


def validate_ip_format(ip: str) -> bool:
    """
    Validate IP address format (IPv4 or IPv6).
    
    Args:
        ip: IP address string
        
    Returns:
        True if valid, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_cidr_format(cidr: str) -> bool:
    """
    Validate CIDR notation format (IPv4 or IPv6).
    
    Args:
        cidr: CIDR notation string (e.g., "192.168.1.0/24")
        
    Returns:
        True if valid, False otherwise
    """
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except ValueError:
        return False


def ip_matches_allowlist(client_ip: str, allowed_ips: list) -> bool:
    """
    Check if client IP matches any allowed IP or CIDR range.
    
    Args:
        client_ip: Client IP address to check
        allowed_ips: List of allowed IPs/CIDR ranges (empty list = allow all)
        
    Returns:
        True if IP is allowed, False otherwise
    """
    # Empty list means allow all (backward compatible)
    if not allowed_ips:
        return True
    
    try:
        client_ip_obj = ipaddress.ip_address(client_ip)
        
        for allowed in allowed_ips:
            if '/' in allowed:
                # CIDR notation
                try:
                    network = ipaddress.ip_network(allowed, strict=False)
                    if client_ip_obj in network:
                        return True
                except ValueError:
                    # Invalid CIDR format, skip
                    logger.warning(f"Invalid CIDR format in allowlist: {allowed}")
                    continue
            else:
                # Exact match
                if client_ip == allowed:
                    return True
        
        return False
    except ValueError:
        # Invalid IP format
        logger.warning(f"Invalid IP format: {client_ip}")
        return False


def extract_client_ip(request: Request) -> str:
    """
    Extract client IP address from request headers.
    Handles proxy headers (X-Forwarded-For, X-Real-IP).
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address string
    """
    # Check X-Forwarded-For header (first IP in chain is client)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take first IP (client IP)
        ip = forwarded_for.split(",")[0].strip()
        if ip:
            return ip
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        ip = real_ip.strip()
        if ip:
            return ip
    
    # Fall back to request.client.host
    if request.client:
        return request.client.host
    
    return "unknown"


async def ip_validation_middleware(request: Request, call_next):
    """
    IP validation middleware.
    
    Checks if client IP is allowed based on API key's allowed_ips configuration.
    Skips IP validation for health check endpoint.
    """
    # Skip health check endpoint
    if request.url.path == "/v1/health":
        return await call_next(request)
    
    # Get API key from request (already validated by auth middleware)
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        # No API key - auth middleware will handle this
        return await call_next(request)
    
    # Get allowed IPs for API key
    try:
        allowed_ips = get_allowed_ips_for_api_key(api_key)
        # None means not configured = allow all (backward compatible)
        if allowed_ips is None:
            return await call_next(request)
    except Exception as e:
        # On error, log and allow request (fail open)
        logger.warning(f"Error getting allowed IPs for API key: {e}, allowing request")
        return await call_next(request)
    
    # Extract client IP
    client_ip = extract_client_ip(request)
    
    # Validate IP against allowlist
    if not ip_matches_allowlist(client_ip, allowed_ips):
        # IP not allowed
        logger.warning(
            f"IP address not allowed",
            extra={
                'client_ip': client_ip,
                'api_key': api_key[:10] + '...' if api_key else None,
                'allowed_ips': allowed_ips
            }
        )
        raise ForbiddenError(
            message="IP address not allowed",
            details={
                "client_ip": client_ip,
                "allowed_ips": allowed_ips
            }
        )
    
    # IP is allowed, continue
    return await call_next(request)

