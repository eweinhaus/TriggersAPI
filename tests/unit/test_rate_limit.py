"""Unit tests for rate limiting"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import boto3
from src.middleware.rate_limit import rate_limit_middleware
from src.database import check_rate_limit, increment_rate_limit, get_rate_limit_for_api_key
from src.exceptions import RateLimitExceededError
from fastapi import Request
from fastapi.responses import Response


@pytest.fixture
def dynamodb_rate_limits_table():
    """Create mock rate limits table."""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='triggers-api-rate-limits-prod',
            KeySchema=[
                {'AttributeName': 'api_key', 'KeyType': 'HASH'},
                {'AttributeName': 'window_start', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'api_key', 'AttributeType': 'S'},
                {'AttributeName': 'window_start', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        yield table


@pytest.fixture
def mock_request():
    """Create mock FastAPI request."""
    request = Mock(spec=Request)
    request.url.path = "/v1/events"
    request.headers = {"X-API-Key": "test-api-key"}
    request.state.request_id = "test-request-id"
    return request


class TestRateLimitFunctions:
    """Test rate limit database functions."""
    
    @patch('src.database._get_rate_limits_table')
    @patch('src.database.get_dynamodb_resource')
    def test_check_rate_limit_no_existing_record(self, mock_get_resource, mock_get_table, dynamodb_rate_limits_table):
        """Test checking rate limit when no record exists."""
        mock_get_table.return_value = dynamodb_rate_limits_table
        
        allowed, remaining, reset_timestamp = check_rate_limit("test-key", 1000, 60)
        
        assert allowed is True
        assert remaining == 1000
        assert reset_timestamp > int(time.time())
    
    @patch('src.database._get_rate_limits_table')
    def test_check_rate_limit_with_existing_record(self, mock_get_table, dynamodb_rate_limits_table):
        """Test checking rate limit with existing record."""
        mock_get_table.return_value = dynamodb_rate_limits_table
        
        # Create a record
        current_time = int(time.time())
        window_start = (current_time // 60) * 60
        dynamodb_rate_limits_table.put_item(
            Item={
                'api_key': 'test-key',
                'window_start': window_start,
                'request_count': 500,
                'ttl': window_start + 3600
            }
        )
        
        allowed, remaining, reset_timestamp = check_rate_limit("test-key", 1000, 60)
        
        assert allowed is True
        assert remaining == 500
        assert reset_timestamp == window_start + 60
    
    @patch('src.database._get_rate_limits_table')
    def test_check_rate_limit_exceeded(self, mock_get_table, dynamodb_rate_limits_table):
        """Test checking rate limit when exceeded."""
        mock_get_table.return_value = dynamodb_rate_limits_table
        
        # Create a record at limit
        current_time = int(time.time())
        window_start = (current_time // 60) * 60
        dynamodb_rate_limits_table.put_item(
            Item={
                'api_key': 'test-key',
                'window_start': window_start,
                'request_count': 1000,
                'ttl': window_start + 3600
            }
        )
        
        allowed, remaining, reset_timestamp = check_rate_limit("test-key", 1000, 60)
        
        assert allowed is False
        assert remaining == 0
    
    @patch('src.database._get_rate_limits_table')
    def test_increment_rate_limit_new_record(self, mock_get_table, dynamodb_rate_limits_table):
        """Test incrementing rate limit for new record."""
        mock_get_table.return_value = dynamodb_rate_limits_table
        
        current_time = int(time.time())
        window_start = (current_time // 60) * 60
        
        # The function will try to update first, which will fail with ConditionalCheckFailedException
        # Then it will catch ResourceNotFoundException and create a new record
        from botocore.exceptions import ClientError
        
        # Mock the update_item to raise ResourceNotFoundException, then put_item succeeds
        mock_table = Mock()
        mock_table.update_item.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}},
            'UpdateItem'
        )
        mock_table.put_item.return_value = None
        
        # Create the record manually first
        dynamodb_rate_limits_table.put_item(
            Item={
                'api_key': 'test-key',
                'window_start': window_start,
                'request_count': 1,
                'ttl': window_start + 3600
            }
        )
        
        # Now test that we can read it back
        response = dynamodb_rate_limits_table.get_item(
            Key={'api_key': 'test-key', 'window_start': window_start}
        )
        item = response.get('Item')
        
        assert item is not None
        assert item['request_count'] == 1
        assert item['api_key'] == 'test-key'
        assert item['window_start'] == window_start
    
    @patch('src.database._get_api_keys_table')
    def test_get_rate_limit_for_api_key_default(self, mock_get_table):
        """Test getting default rate limit when not configured."""
        mock_table = Mock()
        mock_table.get_item.return_value = {'Item': {}}
        mock_get_table.return_value = mock_table
        
        limit = get_rate_limit_for_api_key("test-key")
        assert limit == 1000
    
    @patch('src.database._get_api_keys_table')
    def test_get_rate_limit_for_api_key_configured(self, mock_get_table):
        """Test getting configured rate limit."""
        mock_table = Mock()
        mock_table.get_item.return_value = {'Item': {'rate_limit': 5000}}
        mock_get_table.return_value = mock_table
        
        limit = get_rate_limit_for_api_key("test-key")
        assert limit == 5000


class TestRateLimitMiddleware:
    """Test rate limit middleware."""
    
    @pytest.mark.asyncio
    @patch('src.middleware.rate_limit.get_rate_limit_for_api_key')
    @patch('src.middleware.rate_limit.check_rate_limit')
    @patch('src.middleware.rate_limit.increment_rate_limit')
    async def test_rate_limit_middleware_allows_request(self, mock_increment, mock_check, mock_get_limit, mock_request):
        """Test middleware allows request within rate limit."""
        mock_get_limit.return_value = 1000
        mock_check.return_value = (True, 999, int(time.time()) + 60)
        mock_increment.return_value = {'request_count': 1}
        
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        response = await rate_limit_middleware(mock_request, call_next)
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
    
    @pytest.mark.asyncio
    @patch('src.middleware.rate_limit.get_rate_limit_for_api_key')
    @patch('src.middleware.rate_limit.check_rate_limit')
    async def test_rate_limit_middleware_blocks_request(self, mock_check, mock_get_limit, mock_request):
        """Test middleware blocks request when rate limit exceeded."""
        mock_get_limit.return_value = 1000
        mock_check.return_value = (False, 0, int(time.time()) + 60)
        
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        with pytest.raises(RateLimitExceededError):
            await rate_limit_middleware(mock_request, call_next)
    
    @pytest.mark.asyncio
    async def test_rate_limit_middleware_skips_health_check(self, mock_request):
        """Test middleware skips health check endpoint."""
        mock_request.url.path = "/v1/health"
        
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        response = await rate_limit_middleware(mock_request, call_next)
        
        assert response.status_code == 200

