"""Script to create DynamoDB tables for local development"""

import os
import sys
import boto3
from botocore.exceptions import ClientError

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import get_iso_timestamp


def get_dynamodb_resource():
    """Get DynamoDB resource configured for local or AWS."""
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')
    region = os.getenv('AWS_REGION', 'us-east-1')
    access_key = os.getenv('AWS_ACCESS_KEY_ID', 'test')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
    
    return boto3.resource(
        'dynamodb',
        endpoint_url=endpoint_url,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )


def create_events_table(dynamodb):
    """
    Create the events table with GSI for inbox queries.
    
    Args:
        dynamodb: boto3 DynamoDB resource
    """
    table_name = 'triggers-api-events'
    
    try:
        # Check if table exists
        table = dynamodb.Table(table_name)
        table.load()
        print(f"Table {table_name} already exists")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            raise
    
    # Create table
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'event_id',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'created_at',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'event_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'status-created_at-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_at',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        print(f"Table {table_name} created successfully")
        return table
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {table_name} already exists")
            return dynamodb.Table(table_name)
        raise


def create_api_keys_table(dynamodb):
    """
    Create the API keys table.
    
    Args:
        dynamodb: boto3 DynamoDB resource
    """
    table_name = 'triggers-api-keys'
    
    try:
        # Check if table exists
        table = dynamodb.Table(table_name)
        table.load()
        print(f"Table {table_name} already exists")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            raise
    
    # Create table
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'api_key',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'api_key',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        print(f"Table {table_name} created successfully")
        return table
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {table_name} already exists")
            return dynamodb.Table(table_name)
        raise


def create_idempotency_table(dynamodb):
    """
    Create the idempotency table.
    
    Args:
        dynamodb: boto3 DynamoDB resource
    """
    table_name = os.getenv('DYNAMODB_TABLE_IDEMPOTENCY', 'triggers-api-idempotency')
    
    try:
        # Check if table exists
        table = dynamodb.Table(table_name)
        table.load()
        print(f"Table {table_name} already exists")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            raise
    
    # Create table
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'idempotency_key',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'idempotency_key',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        print(f"Table {table_name} created successfully")
        return table
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {table_name} already exists")
            return dynamodb.Table(table_name)
        raise


def create_tables():
    """Create all required DynamoDB tables."""
    dynamodb = get_dynamodb_resource()
    
    print("Creating DynamoDB tables...")
    create_events_table(dynamodb)
    create_api_keys_table(dynamodb)
    create_idempotency_table(dynamodb)
    print("All tables created successfully")


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    create_tables()

