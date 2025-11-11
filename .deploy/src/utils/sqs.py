"""SQS utilities for webhook delivery"""

import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Optional

logger = logging.getLogger(__name__)

_sqs_client = None


def get_sqs_client():
    """Get or initialize SQS client."""
    global _sqs_client
    if _sqs_client is None:
        region = os.getenv('AWS_REGION', 'us-east-1')
        endpoint_url = os.getenv('SQS_ENDPOINT_URL')  # For local testing
        if endpoint_url:
            _sqs_client = boto3.client('sqs', endpoint_url=endpoint_url, region_name=region)
        else:
            _sqs_client = boto3.client('sqs', region_name=region)
    return _sqs_client


def send_webhook_message(webhook_id: str, event_data: dict, queue_url: Optional[str] = None) -> bool:
    """
    Send webhook delivery message to SQS queue.
    
    Args:
        webhook_id: Webhook ID to deliver to
        event_data: Event data to send
        queue_url: Optional SQS queue URL (defaults to environment variable)
        
    Returns:
        True if message sent successfully, False otherwise
    """
    try:
        if queue_url is None:
            queue_url = os.getenv('WEBHOOK_DELIVERY_QUEUE_URL')
            if not queue_url:
                logger.error("WEBHOOK_DELIVERY_QUEUE_URL environment variable not set")
                return False
        
        message_body = {
            'webhook_id': webhook_id,
            'event_data': event_data
        }
        
        client = get_sqs_client()
        response = client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body)
        )
        
        logger.info(
            f"Webhook message sent to SQS",
            extra={
                'webhook_id': webhook_id,
                'message_id': response.get('MessageId'),
                'queue_url': queue_url
            }
        )
        
        return True
    except ClientError as e:
        logger.error(
            f"Failed to send webhook message to SQS: {e}",
            extra={
                'webhook_id': webhook_id,
                'error': str(e)
            }
        )
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error sending webhook message: {e}",
            extra={
                'webhook_id': webhook_id,
                'error': str(e)
            }
        )
        return False

