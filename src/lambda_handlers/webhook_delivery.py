"""Lambda handler for webhook delivery via SQS"""

import os
import json
import logging
import hmac
import hashlib
import time
import requests
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
region = os.getenv('AWS_REGION', 'us-east-1')
stage = os.getenv('STAGE', 'prod')
webhooks_table_name = f'triggers-api-webhooks-{stage}'


def get_webhook_details(webhook_id: str) -> Dict[str, Any]:
    """
    Get webhook details from DynamoDB.
    
    Args:
        webhook_id: Webhook ID
        
    Returns:
        Webhook dictionary or None if not found
    """
    try:
        table = dynamodb.Table(webhooks_table_name)
        response = table.get_item(Key={'webhook_id': webhook_id})
        return response.get('Item')
    except ClientError as e:
        logger.error(f"Error getting webhook {webhook_id}: {e}")
        return None


def generate_webhook_signature(payload: str, secret: str) -> str:
    """
    Generate HMAC signature for webhook payload.
    
    Args:
        payload: JSON string of event data
        secret: Webhook secret
        
    Returns:
        Hex-encoded HMAC-SHA256 signature
    """
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def deliver_webhook_sync(webhook: Dict[str, Any], event_data: Dict[str, Any], retry_count: int = 0) -> bool:
    """
    Deliver webhook via HTTP POST with retry logic.
    
    Args:
        webhook: Webhook dictionary
        event_data: Event data to send
        retry_count: Current retry attempt (0-based)
        
    Returns:
        True if delivery successful, False otherwise
    """
    webhook_id = webhook['webhook_id']
    url = webhook['url']
    secret = webhook.get('secret', '')
    
    # Generate payload and signature
    payload_json = json.dumps(event_data)
    signature = generate_webhook_signature(payload_json, secret)
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000000Z', time.gmtime())
    
    headers = {
        'X-Webhook-Signature': signature,
        'X-Webhook-Id': webhook_id,
        'X-Webhook-Timestamp': timestamp,
        'Content-Type': 'application/json'
    }
    
    # Exponential backoff: 1s, 2s, 4s
    if retry_count > 0:
        delay = 2 ** (retry_count - 1)
        logger.info(f"Retrying webhook {webhook_id}, attempt {retry_count + 1}, delay {delay}s")
        time.sleep(delay)
    
    try:
        response = requests.post(url, json=event_data, headers=headers, timeout=10.0)
        
        if 200 <= response.status_code < 300:
            logger.info(
                f"Webhook delivered successfully",
                extra={
                    'webhook_id': webhook_id,
                    'status_code': response.status_code,
                    'retry_count': retry_count
                }
            )
            return True
        else:
            # Don't retry 4xx errors (client errors)
            if 400 <= response.status_code < 500:
                logger.warning(
                    f"Webhook delivery failed with client error",
                    extra={
                        'webhook_id': webhook_id,
                        'status_code': response.status_code,
                        'retry_count': retry_count
                    }
                )
                return False
            else:
                # Retry 5xx errors (server errors)
                logger.warning(
                    f"Webhook delivery failed with server error",
                    extra={
                        'webhook_id': webhook_id,
                        'status_code': response.status_code,
                        'retry_count': retry_count
                    }
                )
                return False
                
    except requests.Timeout:
        logger.warning(
            f"Webhook delivery timeout",
            extra={
                'webhook_id': webhook_id,
                'retry_count': retry_count
            }
        )
        return False
    except Exception as e:
        logger.error(
            f"Webhook delivery error: {e}",
            extra={
                'webhook_id': webhook_id,
                'retry_count': retry_count,
                'error': str(e)
            }
        )
        return False


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to process SQS messages for webhook delivery.
    
    Args:
        event: SQS event with batch of messages
        context: Lambda context
        
    Returns:
        Batch item failures for DLQ routing
    """
    batch_item_failures = []
    
    for record in event.get('Records', []):
        message_id = record.get('messageId')
        receipt_handle = record.get('receiptHandle')
        
        try:
            # Parse message body
            body = json.loads(record.get('body', '{}'))
            webhook_id = body.get('webhook_id')
            event_data = body.get('event_data')
            
            if not webhook_id or not event_data:
                logger.error(f"Invalid message format: {body}")
                batch_item_failures.append({'itemIdentifier': message_id})
                continue
            
            # Get webhook details
            webhook = get_webhook_details(webhook_id)
            if not webhook:
                logger.error(f"Webhook not found: {webhook_id}")
                batch_item_failures.append({'itemIdentifier': message_id})
                continue
            
            # Check if webhook is active (stored as 1/0 in DynamoDB)
            is_active = webhook.get('is_active', 0)
            if not is_active or is_active == 0:
                logger.info(f"Webhook {webhook_id} is not active, skipping")
                # Don't add to failures - just skip (message will be deleted)
                continue
            
            # Get retry count from message attributes
            retry_count = int(record.get('attributes', {}).get('ApproximateReceiveCount', 1)) - 1
            
            # Deliver webhook (synchronous for Lambda)
            success = deliver_webhook_sync(webhook, event_data, retry_count)
            
            if not success:
                # Max 3 retries (0, 1, 2)
                if retry_count < 2:
                    # Will be retried by SQS - don't delete message
                    logger.info(f"Webhook delivery failed, will retry: {webhook_id}")
                    # Return failure to trigger SQS retry
                    batch_item_failures.append({'itemIdentifier': message_id})
                else:
                    # Max retries reached, send to DLQ
                    logger.error(f"Webhook delivery failed after max retries: {webhook_id}")
                    batch_item_failures.append({'itemIdentifier': message_id})
            
        except Exception as e:
            logger.error(
                f"Error processing webhook message: {e}",
                extra={
                    'message_id': message_id,
                    'error': str(e)
                }
            )
            # If we've already added to failures, don't add again
            if not any(f['itemIdentifier'] == message_id for f in batch_item_failures):
                batch_item_failures.append({'itemIdentifier': message_id})
    
    return {'batchItemFailures': batch_item_failures}

