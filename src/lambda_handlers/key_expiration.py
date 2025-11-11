"""Lambda handler for API key expiration cleanup"""

import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
region = os.getenv('AWS_REGION', 'us-east-1')
stage = os.getenv('STAGE', 'prod')
api_keys_table_name = f'triggers-api-keys-{stage}'


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to expire old API keys.
    
    Runs on schedule (EventBridge rule, daily).
    Finds keys with status="rotating" and expires_at < now,
    updates them to status="expired".
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context
        
    Returns:
        Summary of expired keys
    """
    table = dynamodb.Table(api_keys_table_name)
    current_time = datetime.now(timezone.utc)
    expired_count = 0
    error_count = 0
    
    try:
        # Scan for keys with status="rotating"
        response = table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'rotating'}
        )
        
        items = response.get('Items', [])
        
        for item in items:
            expires_at_str = item.get('expires_at')
            if not expires_at_str:
                continue
            
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                
                if current_time > expires_at:
                    # Key has expired
                    api_key = item.get('api_key')
                    try:
                        table.update_item(
                            Key={'api_key': api_key},
                            UpdateExpression='SET #status = :status',
                            ExpressionAttributeNames={'#status': 'status'},
                            ExpressionAttributeValues={':status': 'expired'}
                        )
                        expired_count += 1
                        logger.info(f"Expired API key: {api_key[:20]}...")
                    except ClientError as e:
                        error_count += 1
                        logger.error(f"Error expiring key {api_key[:20]}...: {e}")
            except (ValueError, TypeError) as e:
                # Invalid date format, skip
                logger.warning(f"Invalid expires_at format for key: {e}")
                continue
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'rotating'},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            
            items = response.get('Items', [])
            for item in items:
                expires_at_str = item.get('expires_at')
                if not expires_at_str:
                    continue
                
                try:
                    expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    
                    if current_time > expires_at:
                        api_key = item.get('api_key')
                        try:
                            table.update_item(
                                Key={'api_key': api_key},
                                UpdateExpression='SET #status = :status',
                                ExpressionAttributeNames={'#status': 'status'},
                                ExpressionAttributeValues={':status': 'expired'}
                            )
                            expired_count += 1
                            logger.info(f"Expired API key: {api_key[:20]}...")
                        except ClientError as e:
                            error_count += 1
                            logger.error(f"Error expiring key {api_key[:20]}...: {e}")
                except (ValueError, TypeError):
                    continue
        
        logger.info(
            f"Key expiration cleanup complete",
            extra={
                'expired_count': expired_count,
                'error_count': error_count
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'expired_count': expired_count,
                'error_count': error_count
            })
        }
    except Exception as e:
        logger.error(f"Error in key expiration handler: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

