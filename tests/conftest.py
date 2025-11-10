"""Base pytest fixtures for all tests"""

import os
import pytest
from unittest.mock import patch
from faker import Faker
import boto3
from moto import mock_dynamodb
from fastapi.testclient import TestClient

from src.main import app
from src.utils import generate_uuid

fake = Faker()


@pytest.fixture
def app_instance():
    """FastAPI app instance for testing."""
    return app


@pytest.fixture
def client(app_instance):
    """Test client for FastAPI app."""
    return TestClient(app_instance)


@pytest.fixture
def dynamodb_table():
    """Mock DynamoDB table using moto."""
    with mock_dynamodb():
        dynamodb = boto3.resource(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
        
        # Create events table
        table = dynamodb.create_table(
            TableName='triggers-api-events',
            KeySchema=[
                {'AttributeName': 'event_id', 'KeyType': 'HASH'},
                {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'event_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'status-created_at-index',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield table


@pytest.fixture
def api_key():
    """Test API key for authentication."""
    return "test-api-key-12345"


@pytest.fixture
def sample_event():
    """Sample event data for testing."""
    return {
        "source": fake.company(),
        "event_type": fake.word(),
        "payload": {
            "message": fake.sentence(),
            "timestamp": fake.iso8601()
        },
        "metadata": {
            "priority": "normal",
            "correlation_id": generate_uuid()
        }
    }


@pytest.fixture
def request_id():
    """Generate a request ID for testing."""
    return generate_uuid()


@pytest.fixture
def auth_headers(api_key):
    """Headers with API key for authenticated requests."""
    return {"X-API-Key": api_key}


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    # Save original values
    original_env = os.environ.copy()
    
    # Set test defaults
    os.environ.setdefault('DYNAMODB_ENDPOINT_URL', 'http://localhost:8000')
    os.environ.setdefault('AWS_REGION', 'us-east-1')
    os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test')
    os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test')
    os.environ.setdefault('AUTH_MODE', 'local')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    os.environ.setdefault('DYNAMODB_TABLE_EVENTS', 'triggers-api-events')
    os.environ.setdefault('DYNAMODB_TABLE_API_KEYS', 'triggers-api-keys')
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

