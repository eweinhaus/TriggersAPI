"""Migration script to add version and status attributes to existing API keys"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()


def get_dynamodb_resource():
    """Get DynamoDB resource."""
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')
    region = os.getenv('AWS_REGION', 'us-east-1')
    stage = os.getenv('STAGE', os.getenv('DEPLOYMENT_STAGE', 'prod'))
    
    if endpoint_url:
        # Local development
        return boto3.resource(
            'dynamodb',
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'test'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
        )
    else:
        # AWS
        table_name = f'triggers-api-keys-{stage}'
        return boto3.resource('dynamodb', region_name=region)


def migrate_api_keys():
    """Migrate existing API keys to include version and status."""
    dynamodb = get_dynamodb_resource()
    stage = os.getenv('STAGE', os.getenv('DEPLOYMENT_STAGE', 'prod'))
    
    if stage == 'local' or os.getenv('DYNAMODB_ENDPOINT_URL'):
        table_name = 'triggers-api-keys'
    else:
        table_name = f'triggers-api-keys-{stage}'
    
    table = dynamodb.Table(table_name)
    
    print(f"Migrating API keys in table: {table_name}")
    
    # Scan all keys
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        response = table.scan()
        items = response.get('Items', [])
        
        for item in items:
            api_key = item.get('api_key')
            if not api_key:
                continue
            
            # Check if already migrated
            if 'version' in item and 'status' in item:
                skipped_count += 1
                continue
            
            # Update with default values
            try:
                table.update_item(
                    Key={'api_key': api_key},
                    UpdateExpression='SET #version = :version, #status = :status',
                    ExpressionAttributeNames={
                        '#version': 'version',
                        '#status': 'status'
                    },
                    ExpressionAttributeValues={
                        ':version': 1,
                        ':status': 'active'
                    }
                )
                migrated_count += 1
                print(f"Migrated key: {api_key[:20]}...")
            except ClientError as e:
                error_count += 1
                print(f"Error migrating key {api_key[:20]}...: {e}")
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items = response.get('Items', [])
            
            for item in items:
                api_key = item.get('api_key')
                if not api_key:
                    continue
                
                if 'version' in item and 'status' in item:
                    skipped_count += 1
                    continue
                
                try:
                    table.update_item(
                        Key={'api_key': api_key},
                        UpdateExpression='SET #version = :version, #status = :status',
                        ExpressionAttributeNames={
                            '#version': 'version',
                            '#status': 'status'
                        },
                        ExpressionAttributeValues={
                            ':version': 1,
                            ':status': 'active'
                        }
                    )
                    migrated_count += 1
                    print(f"Migrated key: {api_key[:20]}...")
                except ClientError as e:
                    error_count += 1
                    print(f"Error migrating key {api_key[:20]}...: {e}")
        
        print(f"\nMigration complete:")
        print(f"  Migrated: {migrated_count}")
        print(f"  Skipped (already migrated): {skipped_count}")
        print(f"  Errors: {error_count}")
        
    except ClientError as e:
        print(f"Error scanning table: {e}")
        sys.exit(1)


if __name__ == '__main__':
    migrate_api_keys()

