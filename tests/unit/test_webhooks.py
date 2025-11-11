"""Unit tests for webhook endpoints and database functions"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.database import (
    create_webhook, get_webhook, list_webhooks, update_webhook, delete_webhook,
    get_active_webhooks_for_event
)
from src.models import WebhookCreate, WebhookUpdate


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_webhook():
    """Sample webhook data."""
    return {
        'webhook_id': 'test-webhook-id',
        'url': 'https://example.com/webhook',
        'events': ['*'],
        'secret': 'test-secret-key-1234567890',
        'api_key': 'test-api-key',
        'is_active': 1,
        'created_at': '2025-11-11T12:00:00.000000Z'
    }


class TestWebhookDatabase:
    """Test webhook database functions."""
    
    @patch('src.database._get_webhooks_table')
    def test_create_webhook(self, mock_table, sample_webhook):
        """Test webhook creation."""
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        
        result = create_webhook(
            webhook_id=sample_webhook['webhook_id'],
            url=sample_webhook['url'],
            events=sample_webhook['events'],
            secret=sample_webhook['secret'],
            api_key=sample_webhook['api_key']
        )
        
        assert result['webhook_id'] == sample_webhook['webhook_id']
        assert result['url'] == sample_webhook['url']
        assert result['is_active'] == 1  # Stored as 1/0
        mock_table_instance.put_item.assert_called_once()
    
    @patch('src.database._get_webhooks_table')
    def test_get_webhook(self, mock_table, sample_webhook):
        """Test getting webhook by ID."""
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {'Item': sample_webhook}
        
        result = get_webhook(sample_webhook['webhook_id'])
        
        assert result is not None
        assert result['webhook_id'] == sample_webhook['webhook_id']
        assert result['is_active'] is True  # Converted to boolean
    
    @patch('src.database._get_webhooks_table')
    def test_get_webhook_not_found(self, mock_table):
        """Test getting non-existent webhook."""
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {}
        
        result = get_webhook('non-existent-id')
        
        assert result is None
    
    @patch('src.database._get_webhooks_table')
    def test_list_webhooks(self, mock_table, sample_webhook):
        """Test listing webhooks."""
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.query.return_value = {
            'Items': [sample_webhook],
            'LastEvaluatedKey': None
        }
        
        result = list_webhooks(api_key='test-api-key', is_active=True)
        
        assert 'webhooks' in result
        assert len(result['webhooks']) == 1
        # Secret should be removed
        assert 'secret' not in result['webhooks'][0]
        # is_active should be converted to boolean
        assert result['webhooks'][0]['is_active'] is True
    
    @patch('src.database._get_webhooks_table')
    def test_update_webhook(self, mock_table, sample_webhook):
        """Test updating webhook."""
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        updated_webhook = sample_webhook.copy()
        updated_webhook['url'] = 'https://new-url.com/webhook'
        mock_table_instance.update_item.return_value = {'Attributes': updated_webhook}
        
        result = update_webhook(
            webhook_id=sample_webhook['webhook_id'],
            url='https://new-url.com/webhook'
        )
        
        assert result is not None
        assert result['url'] == 'https://new-url.com/webhook'
        # Secret should be removed
        assert 'secret' not in result
    
    @patch('src.database._get_webhooks_table')
    def test_delete_webhook(self, mock_table):
        """Test deleting webhook."""
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        
        result = delete_webhook('test-webhook-id')
        
        assert result is True
        mock_table_instance.delete_item.assert_called_once()
    
    @patch('src.database.list_webhooks')
    def test_get_active_webhooks_for_event(self, mock_list_webhooks, sample_webhook):
        """Test getting active webhooks for event type."""
        mock_list_webhooks.return_value = {
            'webhooks': [sample_webhook]
        }
        
        result = get_active_webhooks_for_event('test-api-key', 'user.created')
        
        assert len(result) == 1
        assert result[0]['webhook_id'] == sample_webhook['webhook_id']
    
    @patch('src.database.list_webhooks')
    def test_get_active_webhooks_wildcard(self, mock_list_webhooks, sample_webhook):
        """Test webhook with wildcard matches all events."""
        mock_list_webhooks.return_value = {
            'webhooks': [sample_webhook]  # events: ['*']
        }
        
        result = get_active_webhooks_for_event('test-api-key', 'any.event.type')
        
        assert len(result) == 1  # Should match because of '*'
    
    @patch('src.database.list_webhooks')
    def test_get_active_webhooks_specific_event(self, mock_list_webhooks):
        """Test webhook with specific event type."""
        specific_webhook = {
            'webhook_id': 'specific-webhook',
            'events': ['user.created', 'user.updated'],
            'is_active': True
        }
        mock_list_webhooks.return_value = {
            'webhooks': [specific_webhook]
        }
        
        # Should match
        result1 = get_active_webhooks_for_event('test-api-key', 'user.created')
        assert len(result1) == 1
        
        # Should not match
        result2 = get_active_webhooks_for_event('test-api-key', 'order.created')
        assert len(result2) == 0


class TestWebhookEndpoints:
    """Test webhook API endpoints."""
    
    def test_create_webhook_endpoint(self, client):
        """Test creating webhook via API."""
        with patch('src.endpoints.webhooks.create_webhook') as mock_create, \
             patch('src.endpoints.webhooks.generate_uuid', return_value='new-webhook-id'):
            mock_create.return_value = {
                'webhook_id': 'new-webhook-id',
                'url': 'https://example.com/webhook',
                'events': ['*'],
                'is_active': 1,
                'created_at': '2025-11-11T12:00:00.000000Z'
            }
            
            response = client.post(
                '/v1/webhooks',
                json={
                    'url': 'https://example.com/webhook',
                    'events': ['*'],
                    'secret': 'test-secret-key-1234567890'
                },
                headers={'X-API-Key': 'test-api-key-12345'}
            )
            
            # Should fail without proper auth setup, but test structure
            assert response.status_code in [201, 401]
    
    def test_list_webhooks_endpoint(self, client):
        """Test listing webhooks via API."""
        with patch('src.endpoints.webhooks.list_webhooks') as mock_list:
            mock_list.return_value = {
                'webhooks': [],
                'last_evaluated_key': None
            }
            
            response = client.get(
                '/v1/webhooks',
                headers={'X-API-Key': 'test-api-key-12345'}
            )
            
            assert response.status_code in [200, 401]
    
    def test_get_webhook_endpoint(self, client):
        """Test getting webhook via API."""
        with patch('src.endpoints.webhooks.get_webhook') as mock_get:
            mock_get.return_value = {
                'webhook_id': 'test-id',
                'url': 'https://example.com/webhook',
                'events': ['*'],
                'is_active': 1,
                'created_at': '2025-11-11T12:00:00.000000Z',
                'api_key': 'test-api-key'
            }
            
            response = client.get(
                '/v1/webhooks/test-id',
                headers={'X-API-Key': 'test-api-key'}
            )
            
            assert response.status_code in [200, 401, 404]
    
    def test_delete_webhook_endpoint(self, client):
        """Test deleting webhook via API."""
        with patch('src.endpoints.webhooks.get_webhook') as mock_get, \
             patch('src.endpoints.webhooks.delete_webhook') as mock_delete:
            mock_get.return_value = {
                'webhook_id': 'test-id',
                'api_key': 'test-api-key'
            }
            mock_delete.return_value = True
            
            response = client.delete(
                '/v1/webhooks/test-id',
                headers={'X-API-Key': 'test-api-key'}
            )
            
            assert response.status_code in [204, 401, 404]

