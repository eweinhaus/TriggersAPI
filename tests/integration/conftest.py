"""Integration test fixtures"""

import pytest
import boto3
from moto import mock_dynamodb
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def mock_dynamodb_resource():
    """Mock DynamoDB resource using moto."""
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
        
        yield dynamodb


@pytest.fixture
def integration_client(mock_dynamodb_resource):
    """Test client for integration tests with mocked DynamoDB."""
    return TestClient(app)

