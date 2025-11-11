"""DynamoDB database operations and client setup"""

import os
import time
from typing import Optional
import boto3
from botocore.exceptions import ClientError

from src.utils import get_iso_timestamp, generate_uuid, encode_cursor, decode_cursor
from src.exceptions import NotFoundError
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Module-level table references
_events_table = None
_api_keys_table = None
_idempotency_table = None
_webhooks_table = None
_analytics_table = None
_rate_limits_table = None


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


def _get_webhooks_table():
    """Get or initialize webhooks table reference."""
    global _webhooks_table
    if _webhooks_table is None:
        dynamodb = get_dynamodb_resource()
        stage = os.getenv('STAGE', os.getenv('DEPLOYMENT_STAGE', 'prod'))
        if stage == 'local' or os.getenv('DYNAMODB_ENDPOINT_URL'):
            table_name = 'triggers-api-webhooks'
        else:
            table_name = f'triggers-api-webhooks-{stage}'
        _webhooks_table = dynamodb.Table(table_name)
    return _webhooks_table


def _get_analytics_table():
    """Get or initialize analytics table reference."""
    global _analytics_table
    if _analytics_table is None:
        dynamodb = get_dynamodb_resource()
        stage = os.getenv('STAGE', os.getenv('DEPLOYMENT_STAGE', 'prod'))
        if stage == 'local' or os.getenv('DYNAMODB_ENDPOINT_URL'):
            table_name = 'triggers-api-analytics'
        else:
            table_name = f'triggers-api-analytics-{stage}'
        _analytics_table = dynamodb.Table(table_name)
    return _analytics_table


def _get_rate_limits_table():
    """Get or initialize rate limits table reference."""
    global _rate_limits_table
    if _rate_limits_table is None:
        dynamodb = get_dynamodb_resource()
        stage = os.getenv('DEPLOYMENT_STAGE', 'prod')
        table_name = f'triggers-api-rate-limits-{stage}'
        _rate_limits_table = dynamodb.Table(table_name)
    return _rate_limits_table


def create_tables():
    """
    Create all required DynamoDB tables.
    Imports and calls the table creation script.
    """
    try:
        from scripts.create_tables import create_tables as _create_tables
        _create_tables()
        logger.info(
            "Tables created successfully",
            extra={'operation': 'create_tables'}
        )
    except Exception as e:
        logger.error(
            "Failed to create tables",
            extra={
                'operation': 'create_tables',
                'error': str(e),
                'error_type': type(e).__name__,
            }
        )
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
    
    Uses GSI 'event-id-index' for O(1) lookup when available (Phase 7 optimization).
    Falls back to direct get (if created_at provided) or scan (for backward compatibility).
    
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
            # Try GSI query first (O(1) lookup) - Phase 7 optimization
            try:
                response = table.query(
                    IndexName='event-id-index',
                    KeyConditionExpression='event_id = :event_id',
                    ExpressionAttributeValues={':event_id': event_id},
                    Limit=1
                )
                items = response.get('Items', [])
                if items:
                    logger.debug(
                        "Event found via GSI",
                        extra={
                            'operation': 'get_event',
                            'event_id': event_id,
                            'method': 'gsi_query',
                        }
                    )
                    return items[0]
            except ClientError as e:
                # GSI might not exist (backward compatibility)
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == 'ValidationException':
                    # GSI doesn't exist, fall back to scan
                    logger.debug(
                        "GSI not available, falling back to scan",
                        extra={
                            'operation': 'get_event',
                            'event_id': event_id,
                            'method': 'scan_fallback',
                        }
                    )
                else:
                    # Other error, log and fall back
                    logger.warning(
                        "GSI query failed, falling back to scan",
                        extra={
                            'operation': 'get_event',
                            'event_id': event_id,
                            'error': str(e),
                            'method': 'scan_fallback',
                        }
                    )
            
            # Fallback to scan (for backward compatibility with tables without GSI)
            # Use ConsistentRead to ensure we find recently written items
            # Paginate through scan results until we find the event or scan entire table
            scan_kwargs = {
                'FilterExpression': 'event_id = :event_id',
                'ExpressionAttributeValues': {':event_id': event_id},
                'ConsistentRead': True,
                'Limit': 100  # Scan 100 items at a time
            }
            
            while True:
                response = table.scan(**scan_kwargs)
                items = response.get('Items', [])
                
                # If we found the event, return it
                if items:
                    logger.debug(
                        "Event found via scan",
                        extra={
                            'operation': 'get_event',
                            'event_id': event_id,
                            'method': 'scan',
                        }
                    )
                    return items[0]
                
                # Check if there are more items to scan
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    # No more items to scan
                    return None
                
                # Continue scanning from where we left off
                scan_kwargs['ExclusiveStartKey'] = last_evaluated_key
    except ClientError as e:
        logger.error(
            "Error getting event",
            extra={
                'operation': 'get_event',
                'event_id': event_id,
                'error': str(e),
                'error_type': type(e).__name__,
            }
        )
        return None


def query_pending_events(
    limit: int = 50,
    cursor: Optional[str] = None,
    source: Optional[str] = None,
    event_type: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    priority: Optional[str] = None,
    metadata_filters: Optional[dict] = None
) -> dict:
    """
    Query pending events using GSI, with pagination and filtering.
    
    Args:
        limit: Maximum number of items to return (max 100)
        cursor: Base64-encoded cursor for pagination
        source: Optional filter by source
        event_type: Optional filter by event_type
        created_after: Optional filter by created_after (ISO 8601 string)
        created_before: Optional filter by created_before (ISO 8601 string)
        priority: Optional filter by priority (low, normal, high)
        metadata_filters: Optional dict of metadata key-value pairs to filter by
        
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
            logger.warning(
                "Invalid cursor",
                extra={
                    'operation': 'query_pending_events',
                    'error': str(e),
                    'error_type': 'ValueError',
                }
            )
    
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
    
    # Date range filters (created_at is sort key, so we can use range conditions)
    if created_after:
        filter_expressions.append('created_at >= :created_after')
        expression_values[':created_after'] = created_after
    
    if created_before:
        filter_expressions.append('created_at <= :created_before')
        expression_values[':created_before'] = created_before
    
    # Priority filter (metadata.priority)
    if priority:
        filter_expressions.append('metadata.#priority = :priority')
        expression_names['#priority'] = 'priority'
        expression_values[':priority'] = priority
    
    # Metadata field filters
    if metadata_filters:
        for idx, (key, value) in enumerate(metadata_filters.items()):
            # Use unique placeholder names for each metadata field
            key_placeholder = f'#metadata_key_{idx}'
            value_placeholder = f':metadata_value_{idx}'
            filter_expressions.append(f'metadata.{key_placeholder} = {value_placeholder}')
            expression_names[key_placeholder] = key
            expression_values[value_placeholder] = value
    
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


def check_rate_limit(api_key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int, int]:
    """
    Check if API key has exceeded rate limit using token bucket algorithm.
    
    Args:
        api_key: API key to check
        limit: Maximum requests allowed per window
        window_seconds: Time window in seconds (default: 60)
        
    Returns:
        Tuple of (allowed: bool, remaining: int, reset_timestamp: int)
    """
    table = _get_rate_limits_table()
    current_time = int(time.time())
    window_start = (current_time // window_seconds) * window_seconds
    reset_timestamp = window_start + window_seconds
    
    try:
        # Get current count for this window
        response = table.get_item(
            Key={
                'api_key': api_key,
                'window_start': window_start
            }
        )
        
        item = response.get('Item')
        if item:
            request_count = item.get('request_count', 0)
            remaining = max(0, limit - request_count)
            allowed = request_count < limit
        else:
            # No record for this window, allow request
            remaining = limit
            allowed = True
        
        return (allowed, remaining, reset_timestamp)
    except ClientError as e:
        # On error, allow request (fail open)
        logger.warning(
            "Error checking rate limit for API key, allowing request",
            extra={
                'operation': 'check_rate_limit',
                'error': str(e),
                'error_type': 'ClientError',
            }
        )
        return (True, limit, reset_timestamp)


def increment_rate_limit(api_key: str, window_start: int, limit: int) -> dict:
    """
    Increment rate limit counter for API key.
    
    Args:
        api_key: API key
        window_start: Window start timestamp
        limit: Maximum requests allowed per window
        
    Returns:
        Updated rate limit record
    """
    table = _get_rate_limits_table()
    current_time = int(time.time())
    ttl = window_start + 3600  # 1 hour TTL
    
    try:
        # Try to increment existing record
        response = table.update_item(
            Key={
                'api_key': api_key,
                'window_start': window_start
            },
            UpdateExpression='ADD request_count :inc SET ttl = :ttl',
            ConditionExpression='request_count < :limit',
            ExpressionAttributeValues={
                ':inc': 1,
                ':limit': limit,
                ':ttl': ttl
            },
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes', {})
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Rate limit exceeded
            raise
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Record doesn't exist, create it
            try:
                table.put_item(
                    Item={
                        'api_key': api_key,
                        'window_start': window_start,
                        'request_count': 1,
                        'ttl': ttl
                    }
                )
                return {
                    'api_key': api_key,
                    'window_start': window_start,
                    'request_count': 1,
                    'ttl': ttl
                }
            except ClientError:
                raise
        else:
            raise


def get_rate_limit_for_api_key(api_key: str) -> int:
    """
    Get rate limit configuration for API key.
    
    Args:
        api_key: API key to check
        
    Returns:
        Rate limit (requests per minute), default 1000
    """
    table = _get_api_keys_table()
    
    try:
        response = table.get_item(Key={'api_key': api_key})
        item = response.get('Item')
        if item:
            return item.get('rate_limit', 1000)  # Default 1000/min
        return 1000
    except ClientError:
        return 1000  # Default on error


def create_webhook(webhook_id: str, url: str, events: list[str], secret: str, api_key: str) -> dict:
    """
    Create a new webhook.
    
    Args:
        webhook_id: Unique webhook ID (UUID)
        url: Webhook URL
        events: List of event types to subscribe to
        secret: Secret for HMAC signature
        api_key: API key that owns the webhook
        
    Returns:
        Created webhook dictionary
    """
    table = _get_webhooks_table()
    created_at = get_iso_timestamp()
    
    item = {
        'webhook_id': webhook_id,
        'url': url,
        'events': events,
        'secret': secret,
        'api_key': api_key,
        'is_active': 1,  # Store as 1/0 for DynamoDB compatibility
        'created_at': created_at
    }
    
    table.put_item(Item=item)
    return item


def get_webhook(webhook_id: str) -> Optional[dict]:
    """
    Get webhook by ID.
    
    Args:
        webhook_id: Webhook ID
        
    Returns:
        Webhook dictionary or None if not found
    """
    table = _get_webhooks_table()
    
    try:
        response = table.get_item(Key={'webhook_id': webhook_id})
        item = response.get('Item')
        if item and 'is_active' in item:
            item['is_active'] = bool(item['is_active'])
        return item
    except ClientError:
        return None


def list_webhooks(api_key: str, is_active: Optional[bool] = None, limit: int = 50, cursor: Optional[str] = None) -> dict:
    """
    List webhooks for an API key.
    
    Args:
        api_key: API key to filter by
        is_active: Optional filter by active status
        limit: Maximum number of results
        cursor: Pagination cursor
        
    Returns:
        Dictionary with webhooks and pagination info
    """
    table = _get_webhooks_table()
    
    # Use GSI to query by api_key
    query_params = {
        'IndexName': 'api-key-is-active-index',
        'KeyConditionExpression': 'api_key = :api_key',
        'ExpressionAttributeValues': {
            ':api_key': api_key
        },
        'Limit': min(limit, 100),
        'ScanIndexForward': False  # Newest first
    }
    
    # Filter by is_active if specified (convert bool to 1/0)
    if is_active is not None:
        query_params['KeyConditionExpression'] += ' AND is_active = :is_active'
        query_params['ExpressionAttributeValues'][':is_active'] = 1 if is_active else 0
    
    # Add pagination cursor
    if cursor:
        try:
            exclusive_start_key = decode_cursor(cursor)
            query_params['ExclusiveStartKey'] = exclusive_start_key
        except ValueError as e:
            logger.warning(f"Invalid cursor: {e}")
    
    response = table.query(**query_params)
    
    webhooks = response.get('Items', [])
    last_evaluated_key = response.get('LastEvaluatedKey')
    
    # Remove secret from response and convert is_active to boolean
    for webhook in webhooks:
        webhook.pop('secret', None)
        if 'is_active' in webhook:
            webhook['is_active'] = bool(webhook['is_active'])
    
    return {
        'webhooks': webhooks,
        'last_evaluated_key': last_evaluated_key
    }


def update_webhook(webhook_id: str, url: Optional[str] = None, events: Optional[list[str]] = None, 
                   secret: Optional[str] = None, is_active: Optional[bool] = None) -> Optional[dict]:
    """
    Update webhook.
    
    Args:
        webhook_id: Webhook ID
        url: Optional new URL
        events: Optional new events list
        secret: Optional new secret
        is_active: Optional new active status
        
    Returns:
        Updated webhook dictionary or None if not found
    """
    table = _get_webhooks_table()
    
    # Build update expression
    update_parts = []
    expression_values = {}
    expression_names = {}
    
    if url is not None:
        update_parts.append('url = :url')
        expression_values[':url'] = url
    
    if events is not None:
        update_parts.append('events = :events')
        expression_values[':events'] = events
    
    if secret is not None:
        update_parts.append('secret = :secret')
        expression_values[':secret'] = secret
    
    if is_active is not None:
        update_parts.append('is_active = :is_active')
        expression_values[':is_active'] = 1 if is_active else 0
    
    if not update_parts:
        # Nothing to update
        return get_webhook(webhook_id)
    
    update_expression = 'SET ' + ', '.join(update_parts)
    
    try:
        response = table.update_item(
            Key={'webhook_id': webhook_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )
        item = response.get('Attributes')
        # Remove secret from response and convert is_active to boolean
        if item:
            item.pop('secret', None)
            if 'is_active' in item:
                item['is_active'] = bool(item['is_active'])
        return item
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None
        raise


def delete_webhook(webhook_id: str) -> bool:
    """
    Delete webhook.
    
    Args:
        webhook_id: Webhook ID to delete
        
    Returns:
        True if deleted, False if not found
    """
    table = _get_webhooks_table()
    
    try:
        table.delete_item(Key={'webhook_id': webhook_id})
        return True
    except ClientError:
        return False


def get_active_webhooks_for_event(api_key: str, event_type: str) -> list[dict]:
    """
    Get active webhooks that should receive an event.
    
    Args:
        api_key: API key that created the event
        event_type: Event type to match
        
    Returns:
        List of webhook dictionaries (without secrets)
    """
    # Get all active webhooks for this API key (is_active=1)
    result = list_webhooks(api_key, is_active=True, limit=100)
    webhooks = result.get('webhooks', [])
    
    # Convert is_active from 1/0 to boolean for easier handling
    for webhook in webhooks:
        if 'is_active' in webhook:
            webhook['is_active'] = bool(webhook['is_active'])
    
    # Filter by event type (support '*' wildcard)
    matching_webhooks = []
    for webhook in webhooks:
        events = webhook.get('events', [])
        if '*' in events or event_type in events:
            matching_webhooks.append(webhook)
    
    return matching_webhooks


def rotate_api_key(key_id: str, transition_days: int = 7) -> dict:
    """
    Rotate an API key by creating a new version.
    
    Args:
        key_id: Current API key to rotate
        transition_days: Number of days for transition period (default: 7)
        
    Returns:
        Dictionary with new key details
        
    Raises:
        NotFoundError: If key not found
    """
    table = _get_api_keys_table()
    from datetime import datetime, timedelta, timezone
    
    # Get current key
    try:
        response = table.get_item(Key={'api_key': key_id})
        current_key = response.get('Item')
        if not current_key:
            raise NotFoundError("API key not found")
    except ClientError:
        raise NotFoundError("API key not found")
    
    # Generate new API key
    new_api_key = generate_api_key()
    
    # Get current version (default to 1 if not set)
    current_version = current_key.get('version', 1)
    new_version = current_version + 1
    
    # Calculate expiration date
    expires_at = (datetime.now(timezone.utc) + timedelta(days=transition_days)).isoformat().replace('+00:00', 'Z')
    rotated_at = get_iso_timestamp()
    
    # Update old key status to "rotating"
    table.update_item(
        Key={'api_key': key_id},
        UpdateExpression='SET #status = :status, expires_at = :expires_at, rotated_at = :rotated_at',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'rotating',
            ':expires_at': expires_at,
            ':rotated_at': rotated_at
        }
    )
    
    # Create new key
    new_key_item = {
        'api_key': new_api_key,
        'source': current_key.get('source', 'unknown'),
        'version': new_version,
        'previous_version': key_id,
        'status': 'active',
        'created_at': get_iso_timestamp(),
        'rotated_at': rotated_at,
        'is_active': True
    }
    
    table.put_item(Item=new_key_item)
    
    return {
        'api_key': new_api_key,
        'version': new_version,
        'previous_version': key_id,
        'expires_at': expires_at,
        'rotated_at': rotated_at
    }


def generate_api_key() -> str:
    """
    Generate a new API key.
    
    Returns:
        New API key string
    """
    import secrets
    # Generate secure random string
    random_part = secrets.token_urlsafe(32)
    return f"tr_{random_part}"


def get_api_key_versions(key_id: str) -> list:
    """
    Get all versions of an API key.
    
    Args:
        key_id: API key ID to get versions for
        
    Returns:
        List of key versions
    """
    table = _get_api_keys_table()
    versions = []
    
    # Start with current key
    current_key_id = key_id
    
    while current_key_id:
        try:
            response = table.get_item(Key={'api_key': current_key_id})
            key = response.get('Item')
            if not key:
                break
            
            # Add to versions (exclude actual key value for security)
            versions.append({
                'version': key.get('version', 1),
                'status': key.get('status', 'active'),
                'created_at': key.get('created_at'),
                'rotated_at': key.get('rotated_at'),
                'expires_at': key.get('expires_at')
            })
            
            # Get previous version
            current_key_id = key.get('previous_version')
        except ClientError:
            break
    
    return sorted(versions, key=lambda x: x.get('version', 1), reverse=True)


def get_allowed_ips_for_api_key(api_key: str) -> Optional[list]:
    """
    Get allowed IPs for API key.
    
    Args:
        api_key: API key to check
        
    Returns:
        List of allowed IPs/CIDR ranges, or None if not configured (allows all)
    """
    table = _get_api_keys_table()
    
    try:
        response = table.get_item(Key={'api_key': api_key})
        item = response.get('Item')
        if item:
            allowed_ips = item.get('allowed_ips')
            if allowed_ips is not None:
                return allowed_ips if isinstance(allowed_ips, list) else []
            return None  # Not configured = allow all
        return None
    except ClientError:
        return None  # Default on error (allow all)


def bulk_create_events(events: list[dict], api_key: str) -> tuple[list[dict], list[dict]]:
    """
    Create multiple events in bulk using DynamoDB batch operations.
    Handles idempotency for each event.
    
    Args:
        events: List of event dictionaries to create (already formatted with event_id, created_at, etc.)
        api_key: API key (for idempotency checks)
        
    Returns:
        Tuple of (successful_events, failed_events)
        failed_events contains dicts with 'index' and 'error' keys
    """
    table = _get_events_table()
    dynamodb = get_dynamodb_resource()
    client = dynamodb.meta.client
    successful = []
    failed = []
    
    # Process in chunks of 25 (DynamoDB batch limit)
    chunk_size = 25
    for chunk_start in range(0, len(events), chunk_size):
        chunk = events[chunk_start:chunk_start + chunk_size]
        
        # Check idempotency for each event in chunk
        events_to_create = []
        for idx, event in enumerate(chunk):
            global_idx = chunk_start + idx
            # Check idempotency key if present
            metadata = event.get('metadata', {})
            idempotency_key = metadata.get('idempotency_key') if isinstance(metadata, dict) else None
            
            if idempotency_key:
                existing_event_id = check_idempotency_key(idempotency_key)
                if existing_event_id:
                    # Return existing event
                    existing_event = get_event(existing_event_id)
                    if existing_event:
                        successful.append(existing_event)
                        continue
                    # Idempotency key exists but event not found - create new
                    events_to_create.append((global_idx, event))
                else:
                    events_to_create.append((global_idx, event))
            else:
                events_to_create.append((global_idx, event))
        
        if not events_to_create:
            continue
        
        # Prepare batch write items
        put_requests = []
        for global_idx, event in events_to_create:
            put_requests.append({
                'PutRequest': {
                    'Item': event
                }
            })
        
        # Execute batch write
        try:
            response = client.batch_write_item(
                RequestItems={
                    table.name: put_requests
                }
            )
            
            # Check for unprocessed items
            unprocessed = response.get('UnprocessedItems', {})
            if unprocessed:
                # Retry once for unprocessed items
                retry_response = client.batch_write_item(
                    RequestItems=unprocessed
                )
                # If still unprocessed, mark as failed
                still_unprocessed = retry_response.get('UnprocessedItems', {})
                if still_unprocessed:
                    # Extract failed indices from unprocessed items
                    failed_indices = set()
                    for table_name, requests in still_unprocessed.items():
                        for req in requests:
                            # Find which event this corresponds to
                            for global_idx, event in events_to_create:
                                if event['event_id'] == req['PutRequest']['Item']['event_id']:
                                    failed_indices.add(global_idx)
                                    break
                    
                    for global_idx, event in events_to_create:
                        if global_idx in failed_indices:
                            failed.append({
                                'index': global_idx,
                                'error': {
                                    'code': 'INTERNAL_ERROR',
                                    'message': 'Failed to create event after retry',
                                    'details': {}
                                }
                            })
                        else:
                            successful.append(event)
                    continue
            
            # All items in chunk succeeded - store idempotency keys
            for global_idx, event in events_to_create:
                successful.append(event)
                # Store idempotency key if present
                metadata = event.get('metadata', {})
                idempotency_key = metadata.get('idempotency_key') if isinstance(metadata, dict) else None
                if idempotency_key:
                    store_idempotency_key(idempotency_key, event['event_id'])
            
        except ClientError as e:
            # Mark all items in chunk as failed
            for global_idx, event in events_to_create:
                failed.append({
                    'index': global_idx,
                    'error': {
                        'code': 'INTERNAL_ERROR',
                        'message': f'Batch write error: {str(e)}',
                        'details': {}
                    }
                })
    
    return (successful, failed)


def bulk_acknowledge_events(event_ids: list[str], api_key: str) -> tuple[list[dict], list[dict]]:
    """
    Acknowledge multiple events in bulk.
    
    Args:
        event_ids: List of event IDs to acknowledge
        api_key: API key
        
    Returns:
        Tuple of (successful_acknowledgments, failed_acknowledgments)
        failed_acknowledgments contains dicts with 'index' and 'error' keys
    """
    table = _get_events_table()
    successful = []
    failed = []
    acknowledged_at = get_iso_timestamp()
    
    # First, get all events to find their created_at timestamps
    events_to_ack = []
    for idx, event_id in enumerate(event_ids):
        event = get_event(event_id)
        if event:
            events_to_ack.append((idx, event))
        else:
            failed.append({
                'index': idx,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': f'Event {event_id} not found',
                    'details': {'event_id': event_id}
                }
            })
    
    # Acknowledge events one by one (DynamoDB doesn't support conditional batch updates easily)
    for idx, event in events_to_ack:
        try:
            updated = acknowledge_event(event['event_id'])
            if updated:
                successful.append(updated)
            else:
                # Already acknowledged or status changed
                failed.append({
                    'index': idx,
                    'error': {
                        'code': 'CONFLICT',
                        'message': f'Event {event["event_id"]} is already acknowledged or status changed',
                        'details': {'event_id': event['event_id']}
                    }
                })
        except Exception as e:
            failed.append({
                'index': idx,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': f'Error acknowledging event: {str(e)}',
                    'details': {'event_id': event['event_id']}
                }
            })
    
    return (successful, failed)


def bulk_delete_events(event_ids: list[str], api_key: str) -> tuple[list[str], list[dict]]:
    """
    Delete multiple events in bulk.
    
    Args:
        event_ids: List of event IDs to delete
        api_key: API key
        
    Returns:
        Tuple of (successful_deletions, failed_deletions)
        successful_deletions is a list of event IDs
        failed_deletions contains dicts with 'index' and 'error' keys
    """
    table = _get_events_table()
    successful = []
    failed = []
    
    # Process in chunks of 25 (DynamoDB batch limit)
    chunk_size = 25
    for chunk_start in range(0, len(event_ids), chunk_size):
        chunk = event_ids[chunk_start:chunk_start + chunk_size]
        
        # Get events to find created_at timestamps
        events_to_delete = []
        for idx, event_id in enumerate(chunk):
            event = get_event(event_id)
            if event:
                events_to_delete.append((chunk_start + idx, event))
            else:
                # Event not found - idempotent, consider it successful
                successful.append(event_id)
        
        # Prepare batch delete requests
        delete_requests = []
        for idx, event in events_to_delete:
            delete_requests.append({
                'DeleteRequest': {
                    'Key': {
                        'event_id': event['event_id'],
                        'created_at': event['created_at']
                    }
                }
            })
        
        if not delete_requests:
            continue
        
        # Execute batch write (delete operations)
        try:
            dynamodb = get_dynamodb_resource()
            client = dynamodb.meta.client
            response = client.batch_write_item(
                RequestItems={
                    table.name: delete_requests
                }
            )
            
            # Check for unprocessed items
            unprocessed = response.get('UnprocessedItems', {})
            if unprocessed:
                # Retry once
                retry_response = client.batch_write_item(
                    RequestItems=unprocessed
                )
                still_unprocessed = retry_response.get('UnprocessedItems', {})
                if still_unprocessed:
                    # Mark unprocessed as failed
                    for idx, event in events_to_delete:
                        failed.append({
                            'index': idx,
                            'error': {
                                'code': 'INTERNAL_ERROR',
                                'message': 'Failed to delete event after retry',
                                'details': {'event_id': event['event_id']}
                            }
                        })
                    continue
            
            # All deletes succeeded
            for idx, event in events_to_delete:
                successful.append(event['event_id'])
            
        except ClientError as e:
            # Mark all items in chunk as failed
            for idx, event in events_to_delete:
                failed.append({
                    'index': idx,
                    'error': {
                        'code': 'INTERNAL_ERROR',
                        'message': f'Batch delete error: {str(e)}',
                        'details': {'event_id': event['event_id']}
                    }
                })
    
    return (successful, failed)

