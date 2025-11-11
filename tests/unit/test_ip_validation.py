"""Unit tests for IP validation"""

import pytest
from unittest.mock import Mock, patch
from src.middleware.ip_validation import (
    validate_ip_format,
    validate_cidr_format,
    ip_matches_allowlist,
    extract_client_ip
)
from src.exceptions import ForbiddenError
from fastapi import Request
from fastapi.responses import Response


class TestIPValidation:
    """Test IP validation utilities."""
    
    def test_validate_ip_format_ipv4(self):
        """Test validating IPv4 address."""
        assert validate_ip_format("192.168.1.1") is True
        assert validate_ip_format("0.0.0.0") is True
        assert validate_ip_format("255.255.255.255") is True
    
    def test_validate_ip_format_ipv6(self):
        """Test validating IPv6 address."""
        assert validate_ip_format("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
        assert validate_ip_format("::1") is True
    
    def test_validate_ip_format_invalid(self):
        """Test invalid IP addresses."""
        assert validate_ip_format("not.an.ip") is False
        assert validate_ip_format("256.256.256.256") is False
        assert validate_ip_format("") is False
    
    def test_validate_cidr_format_valid(self):
        """Test validating valid CIDR notation."""
        assert validate_cidr_format("192.168.1.0/24") is True
        assert validate_cidr_format("10.0.0.0/8") is True
        assert validate_cidr_format("2001:db8::/32") is True
    
    def test_validate_cidr_format_invalid(self):
        """Test invalid CIDR notation."""
        assert validate_cidr_format("not.cidr") is False
        assert validate_cidr_format("192.168.1.0/33") is False
    
    def test_ip_matches_allowlist_empty_list(self):
        """Test empty allowlist allows all."""
        assert ip_matches_allowlist("192.168.1.1", []) is True
        assert ip_matches_allowlist("10.0.0.1", []) is True
    
    def test_ip_matches_allowlist_exact_match(self):
        """Test exact IP matching."""
        assert ip_matches_allowlist("192.168.1.1", ["192.168.1.1"]) is True
        assert ip_matches_allowlist("192.168.1.1", ["192.168.1.2"]) is False
    
    def test_ip_matches_allowlist_cidr(self):
        """Test CIDR range matching."""
        assert ip_matches_allowlist("192.168.1.50", ["192.168.1.0/24"]) is True
        assert ip_matches_allowlist("192.168.2.50", ["192.168.1.0/24"]) is False
        assert ip_matches_allowlist("10.0.0.5", ["10.0.0.0/8"]) is True
    
    def test_extract_client_ip_from_forwarded_for(self):
        """Test extracting IP from X-Forwarded-For header."""
        request = Mock(spec=Request)
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.client = None
        
        ip = extract_client_ip(request)
        assert ip == "192.168.1.1"
    
    def test_extract_client_ip_from_real_ip(self):
        """Test extracting IP from X-Real-IP header."""
        request = Mock(spec=Request)
        request.headers = {"X-Real-IP": "192.168.1.1"}
        request.client = None
        
        ip = extract_client_ip(request)
        assert ip == "192.168.1.1"
    
    def test_extract_client_ip_from_client_host(self):
        """Test extracting IP from request.client.host."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        ip = extract_client_ip(request)
        assert ip == "192.168.1.1"


class TestIPValidationMiddleware:
    """Test IP validation middleware."""
    
    @pytest.mark.asyncio
    @patch('src.middleware.ip_validation.get_allowed_ips_for_api_key')
    @patch('src.middleware.ip_validation.extract_client_ip')
    @patch('src.middleware.ip_validation.ip_matches_allowlist')
    async def test_ip_validation_allows_request(self, mock_matches, mock_extract, mock_get_ips):
        """Test middleware allows request when IP is allowed."""
        request = Mock(spec=Request)
        request.url.path = "/v1/events"
        request.headers = {"X-API-Key": "test-key"}
        
        mock_get_ips.return_value = ["192.168.1.0/24"]
        mock_extract.return_value = "192.168.1.50"
        mock_matches.return_value = True
        
        from src.middleware.ip_validation import ip_validation_middleware
        
        async def call_next(req):
            return Response(content="OK", status_code=200)
        
        response = await ip_validation_middleware(request, call_next)
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    @patch('src.middleware.ip_validation.get_allowed_ips_for_api_key')
    @patch('src.middleware.ip_validation.extract_client_ip')
    @patch('src.middleware.ip_validation.ip_matches_allowlist')
    async def test_ip_validation_blocks_request(self, mock_matches, mock_extract, mock_get_ips):
        """Test middleware blocks request when IP is not allowed."""
        request = Mock(spec=Request)
        request.url.path = "/v1/events"
        request.headers = {"X-API-Key": "test-key"}
        
        mock_get_ips.return_value = ["192.168.1.0/24"]
        mock_extract.return_value = "10.0.0.1"
        mock_matches.return_value = False
        
        from src.middleware.ip_validation import ip_validation_middleware
        
        async def call_next(req):
            return Response(content="OK", status_code=200)
        
        with pytest.raises(ForbiddenError):
            await ip_validation_middleware(request, call_next)
    
    @pytest.mark.asyncio
    async def test_ip_validation_skips_health_check(self):
        """Test middleware skips health check endpoint."""
        request = Mock(spec=Request)
        request.url.path = "/v1/health"
        
        from src.middleware.ip_validation import ip_validation_middleware
        
        async def call_next(req):
            return Response(content="OK", status_code=200)
        
        response = await ip_validation_middleware(request, call_next)
        
        assert response.status_code == 200

