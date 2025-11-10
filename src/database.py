"""DynamoDB database operations and client setup"""

import os
import time
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError

from src.utils import get_iso_timestamp, generate_uuid, encode_cursor, decode_cursor

logger = logging.getLogger(__name__)

# Module-level table references
_events_table = None
_api_keys_table = None
_idempotency_table = None


def get_dynamodb_resource():
    """
    Get DynamoDB resource configured for local or AWS.
    
    In AWS Lambda, boto3 automatically uses IAM role credentials.
    For local development, uses environment variables or defaults.
    
    Returns:
        boto3 DynamoDB resource
    """
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    # Only set credentials if endpoint_url is set (local development)
    # In Lambda, boto3 uses IAM role automatically
    if endpoint_url:
        # Local development with DynamoDB Local
        access_key = os.getenv('AWS_ACCESS_KEY_ID', 'test')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
        return boto3.resource(
            'dynamodb',
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    else:
        # AWS Lambda - use IAM role credentials automatically
        return boto3.resource('dynamodb', region_name=region)


def _get_events_table():
    """Get or initialize events table reference."""
    global _events_table
    if _events_table is None:
        dynamodb = get_dynamodb_resource()
        table_name = os.getenv('DYNAMODB_TABLE_EVENTS', 'triggers-api-events')
        _events_table = dynamodb.Table(table_name)
    return _events_table


def _get_api_keys_table():
    """Get or initialize API keys table reference."""
    global _api_keys_table
    if _api_keys_table is None:
        dynamodb = get_dynamodb_resource()
        table_name = os.getenv('DYNAMODB_TABLE_KEYS', 'triggers-api-keys')
        _api_keys_table = dynamodb.Table(table_name)
    return _api_keys_table


def _get_idempotency_table():
    """Get or initialize idempotency table reference."""
    global _idempotency_table
    if _idempotency_table is None:
        dynamodb = get_dynamodb_resource()
        table_name = os.getenv('DYNAMODB_TABLE_IDEMPOTENCY', 'triggers-api-idempotency')
        _idempotency_table = dynamodb.Table(table_name)
    return _idempotency_table


def create_tables():
    """
    Create all required DynamoDB tables.
    Imports and calls the table creation script.
    """
    try:
        from scripts.create_tables import create_tables as _create_tables
        _create_tables()
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        # Don't raise - tables might already exist


def check_idempotency_key(idempotency_key: str) -> Optional[str]:
    """
    Check if idempotency key exists and return associated event_id.
    
    Args:
        idempotency_key: Idempotency key to check
        
    Returns:
        Event ID if found, None otherwise
    """
    table = _get_idempotency_table()
    
    try:
        response = table.get_item(
            Key={'idempotency_key': idempotency_key}
        )
        item = response.get('Item')
        if item:
            return item.get('event_id')
        return None
    except ClientError:
        return None


def store_idempotency_key(idempotency_key: str, event_id: str) -> bool:
    """
    Store idempotency key mapping with TTL.
    
    Args:
        idempotency_key: Idempotency key
        event_id: Associated event ID
        
    Returns:
        True if stored successfully, False if key already exists (race condition)
    """
    table = _get_idempotency_table()
    created_at = get_iso_timestamp()
    ttl = int(time.time()) + (24 * 60 * 60)  # 24 hours
    
    try:
        table.put_item(
            Item={
                'idempotency_key': idempotency_key,
                'event_id': event_id,
                'created_at': created_at,
                'ttl': ttl
            },
            ConditionExpression='attribute_not_exists(idempotency_key)'
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Key already exists (race condition)
            return False
        raise


def create_event(source: str, event_type: str, payload: dict, metadata: Optional[dict] = None, idempotency_key: Optional[str] = None) -> dict:
    """
    Create a new event in DynamoDB.
    
    Args:
        source: Event source identifier
        event_type: Type of event (e.g., 'user.created')
        payload: Event payload (any JSON-serializable dict)
        metadata: Optional metadata dict
        idempotency_key: Optional idempotency key for duplicate prevention
        
    Returns:
        Created or existing event dictionary
    """
    # Check idempotency if key provided
    if idempotency_key:
        existing_event_id = check_idempotency_key(idempotency_key)
        if existing_event_id:
            # Return existing event
            existing_event = get_event(existing_event_id)
            if existing_event:
                return existing_event
    
    # Create new event
    event_id = generate_uuid()
    created_at = get_iso_timestamp()
    status = "pending"
    ttl = int(time.time()) + (7 * 24 * 60 * 60)  # 7 days from now
    
    event = {
        'event_id': event_id,
        'created_at': created_at,
        'source': source,
        'event_type': event_type,
        'payload': payload,
        'status': status,
        'ttl': ttl
    }
    
    if metadata:
        event['metadata'] = metadata
    
    table = _get_events_table()
    table.put_item(Item=event)
    
    # Store idempotency key if provided
    if idempotency_key:
        store_idempotency_key(idempotency_key, event_id)
    
    return event


def get_event(event_id: str, created_at: Optional[str] = None) -> Optional[dict]:
    """
    Get an event by event_id.
    
    For MVP, we use a scan with filter since event_id is partition key
    but we may not have created_at. For production, consider querying
    by event_id if it's unique or storing event_id as a separate attribute.
    
    Args:
        event_id: Event ID (UUID)
        created_at: Optional created_at timestamp (if provided, use direct get)
        
    Returns:
        Event dictionary or None if not found
    """
    table = _get_events_table()
    
    try:
        if created_at:
            # Direct get with both keys
            response = table.get_item(
                Key={
                    'event_id': event_id,
                    'created_at': created_at
                }
            )
            return response.get('Item')
        else:
            # Scan with filter (acceptable for MVP low volume)
            response = table.scan(
                FilterExpression='event_id = :event_id',
                ExpressionAttributeValues={':event_id': event_id},
                Limit=1
            )
            items = response.get('Items', [])
            return items[0] if items else None
    except ClientError:
        return None


def query_pending_events(
    limit: int = 50,
    cursor: Optional[str] = None,
    source: Optional[str] = None,
    event_type: Optional[str] = None
) -> dict:
    """
    Query pending events using GSI, with pagination and filtering.
    
    Args:
        limit: Maximum number of items to return (max 100)
        cursor: Base64-encoded cursor for pagination
        source: Optional filter by source
        event_type: Optional filter by event_type
        
    Returns:
        Dictionary with 'events' list and 'last_evaluated_key' (if more results)
    """
    table = _get_events_table()
    
    # Build query parameters
    query_params = {
        'IndexName': 'status-created_at-index',
        'KeyConditionExpression': '#status = :status',
        'ExpressionAttributeNames': {
            '#status': 'status'
        },
        'ExpressionAttributeValues': {
            ':status': 'pending'
        },
        'ScanIndexForward': True,  # Ascending order (oldest first)
        'Limit': min(limit, 100)  # Max 100
    }
    
    # Add pagination cursor
    if cursor:
        try:
            exclusive_start_key = decode_cursor(cursor)
            query_params['ExclusiveStartKey'] = exclusive_start_key
        except ValueError as e:
            logger.warning(f"Invalid cursor: {e}")
    
    # Build filter expression (escape reserved keywords)
    filter_expressions = []
    expression_values = query_params['ExpressionAttributeValues'].copy()
    expression_names = query_params['ExpressionAttributeNames'].copy()
    
    if source:
        filter_expressions.append('#source = :source')
        expression_names['#source'] = 'source'
        expression_values[':source'] = source
    
    if event_type:
        filter_expressions.append('#event_type = :event_type')
        expression_names['#event_type'] = 'event_type'
        expression_values[':event_type'] = event_type
    
    if filter_expressions:
        query_params['FilterExpression'] = ' AND '.join(filter_expressions)
        query_params['ExpressionAttributeValues'] = expression_values
        query_params['ExpressionAttributeNames'] = expression_names
    
    # Execute query
    response = table.query(**query_params)
    
    events = response.get('Items', [])
    last_evaluated_key = response.get('LastEvaluatedKey')
    
    return {
        'events': events,
        'last_evaluated_key': last_evaluated_key
    }


def acknowledge_event(event_id: str) -> Optional[dict]:
    """
    Acknowledge an event using conditional update.
    
    Args:
        event_id: Event ID to acknowledge
        
    Returns:
        Updated event dictionary or None if not found or already acknowledged
    """
    table = _get_events_table()
    acknowledged_at = get_iso_timestamp()
    
    # First, find the event (we need created_at for the composite key)
    event = get_event(event_id)
    if not event:
        return None
    
    created_at = event['created_at']
    
    # Perform conditional update
    try:
        response = table.update_item(
            Key={
                'event_id': event_id,
                'created_at': created_at
            },
            UpdateExpression='SET #status = :status, acknowledged_at = :ack_at',
            ConditionExpression='#status = :pending',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'acknowledged',
                ':pending': 'pending',
                ':ack_at': acknowledged_at
            },
            ReturnValues='ALL_NEW'
        )
        
        return response.get('Attributes')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Already acknowledged or status changed
            return None
        raise


def delete_event(event_id: str) -> bool:
    """
    Delete an event by event_id.
    
    Args:
        event_id: Event ID to delete
        
    Returns:
        True if deleted, False if not found (idempotent)
    """
    table = _get_events_table()
    
    # Find the event first (need created_at for composite key)
    event = get_event(event_id)
    if not event:
        return True  # Idempotent - return True even if not found
    
    created_at = event['created_at']
    
    try:
        table.delete_item(
            Key={
                'event_id': event_id,
                'created_at': created_at
            }
        )
        return True
    except ClientError:
        return False

