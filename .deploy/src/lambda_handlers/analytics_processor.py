"""Lambda handler for analytics aggregation from DynamoDB Streams"""

import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
region = os.getenv('AWS_REGION', 'us-east-1')
stage = os.getenv('STAGE', 'prod')
analytics_table_name = f'triggers-api-analytics-{stage}'


def get_analytics_table():
    """Get analytics table."""
    return dynamodb.Table(analytics_table_name)


def aggregate_event(event_data: Dict[str, Any]) -> None:
    """
    Aggregate event data into analytics metrics.
    
    Args:
        event_data: Event data from stream
    """
    table = get_analytics_table()
    
    # Extract event information
    source = event_data.get('source', 'unknown')
    event_type = event_data.get('event_type', 'unknown')
    created_at = event_data.get('created_at')
    
    if not created_at:
        return
    
    # Parse timestamp
    try:
        event_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        logger.warning(f"Invalid timestamp format: {created_at}")
        return
    
    # Generate metric keys
    date_str = event_time.strftime('%Y-%m-%d')
    hour_str = event_time.strftime('%H')
    
    # Hourly aggregation
    hourly_key = {
        'metric_date': date_str,
        'metric_type': f'hourly-{hour_str}'
    }
    
    # Daily aggregation
    daily_key = {
        'metric_date': date_str,
        'metric_type': 'daily'
    }
    
    # Update hourly metrics
    try:
        table.update_item(
            Key=hourly_key,
            UpdateExpression='ADD event_count :inc',
            ExpressionAttributeValues={':inc': 1},
            ReturnValues='NONE'
        )
        
        # Update source distribution
        table.update_item(
            Key=hourly_key,
            UpdateExpression='ADD source_distribution.#source :inc',
            ExpressionAttributeNames={'#source': source},
            ExpressionAttributeValues={':inc': 1},
            ReturnValues='NONE'
        )
        
        # Update event type distribution
        table.update_item(
            Key=hourly_key,
            UpdateExpression='ADD event_type_distribution.#event_type :inc',
            ExpressionAttributeNames={'#event_type': event_type},
            ExpressionAttributeValues={':inc': 1},
            ReturnValues='NONE'
        )
    except ClientError as e:
        # If item doesn't exist, create it
        if e.response['Error']['Code'] == 'ValidationException':
            # Initialize item
            ttl = int((datetime.now(timezone.utc).timestamp()) + (30 * 24 * 60 * 60))  # 30 days
            table.put_item(
                Item={
                    **hourly_key,
                    'event_count': 1,
                    'source_distribution': {source: 1},
                    'event_type_distribution': {event_type: 1},
                    'ttl': ttl
                }
            )
        else:
            logger.error(f"Error updating hourly metrics: {e}")
    
    # Update daily metrics
    try:
        table.update_item(
            Key=daily_key,
            UpdateExpression='ADD event_count :inc',
            ExpressionAttributeValues={':inc': 1},
            ReturnValues='NONE'
        )
        
        # Update source distribution
        table.update_item(
            Key=daily_key,
            UpdateExpression='ADD source_distribution.#source :inc',
            ExpressionAttributeNames={'#source': source},
            ExpressionAttributeValues={':inc': 1},
            ReturnValues='NONE'
        )
        
        # Update event type distribution
        table.update_item(
            Key=daily_key,
            UpdateExpression='ADD event_type_distribution.#event_type :inc',
            ExpressionAttributeNames={'#event_type': event_type},
            ExpressionAttributeValues={':inc': 1},
            ReturnValues='NONE'
        )
    except ClientError as e:
        # If item doesn't exist, create it
        if e.response['Error']['Code'] == 'ValidationException':
            # Initialize item
            ttl = int((datetime.now(timezone.utc).timestamp()) + (30 * 24 * 60 * 60))  # 30 days
            table.put_item(
                Item={
                    **daily_key,
                    'event_count': 1,
                    'source_distribution': {source: 1},
                    'event_type_distribution': {event_type: 1},
                    'ttl': ttl
                }
            )
        else:
            logger.error(f"Error updating daily metrics: {e}")


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to process DynamoDB Stream records for analytics.
    
    Args:
        event: DynamoDB Stream event
        context: Lambda context
        
    Returns:
        Processing summary
    """
    processed_count = 0
    error_count = 0
    
    for record in event.get('Records', []):
        try:
            # Only process INSERT events (new events)
            if record.get('eventName') != 'INSERT':
                continue
            
            # Get new image (event data)
            new_image = record.get('dynamodb', {}).get('NewImage', {})
            if not new_image:
                continue
            
            # Convert DynamoDB format to regular dict
            event_data = {}
            for key, value in new_image.items():
                if 'S' in value:
                    event_data[key] = value['S']
                elif 'N' in value:
                    event_data[key] = value['N']
                elif 'M' in value:
                    event_data[key] = {k: list(v.values())[0] for k, v in value['M'].items()}
                elif 'L' in value:
                    event_data[key] = [list(item.values())[0] for item in value['L']]
            
            # Aggregate event
            aggregate_event(event_data)
            processed_count += 1
            
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing stream record: {e}", exc_info=True)
    
    logger.info(
        f"Analytics processing complete",
        extra={
            'processed_count': processed_count,
            'error_count': error_count
        }
    )
    
    return {
        'statusCode': 200,
        'processed_count': processed_count,
        'error_count': error_count
    }

