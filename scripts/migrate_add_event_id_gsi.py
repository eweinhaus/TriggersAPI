"""Migration script to add event-id-index GSI to existing Events table"""

import os
import sys
import boto3
import time
from botocore.exceptions import ClientError

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def get_dynamodb_client():
    """Get DynamoDB client configured for local or AWS."""
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    if endpoint_url:
        # Local development
        access_key = os.getenv('AWS_ACCESS_KEY_ID', 'test')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
        return boto3.client(
            'dynamodb',
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    else:
        # AWS Lambda - use IAM role credentials automatically
        return boto3.client('dynamodb', region_name=region)


def check_gsi_exists(client, table_name, gsi_name):
    """Check if GSI already exists."""
    try:
        response = client.describe_table(TableName=table_name)
        gsis = response['Table'].get('GlobalSecondaryIndexes', [])
        return any(gsi['IndexName'] == gsi_name for gsi in gsis)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise ValueError(f"Table {table_name} does not exist")
        raise


def wait_for_gsi_active(client, table_name, gsi_name, timeout=600):
    """Wait for GSI to become active."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = client.describe_table(TableName=table_name)
            gsis = response['Table'].get('GlobalSecondaryIndexes', [])
            for gsi in gsis:
                if gsi['IndexName'] == gsi_name:
                    status = gsi['IndexStatus']
                    if status == 'ACTIVE':
                        return True
                    elif status == 'FAILED':
                        raise RuntimeError(f"GSI {gsi_name} creation failed")
                    print(f"GSI status: {status}, waiting...")
                    time.sleep(5)
                    break
        except ClientError as e:
            print(f"Error checking GSI status: {e}")
            time.sleep(5)
    
    raise TimeoutError(f"GSI {gsi_name} did not become active within {timeout} seconds")


def create_gsi(client, table_name, dry_run=False):
    """Create event-id-index GSI on Events table."""
    gsi_name = 'event-id-index'
    
    # Check if GSI already exists
    if check_gsi_exists(client, table_name, gsi_name):
        print(f"GSI {gsi_name} already exists on table {table_name}")
        return True
    
    if dry_run:
        print(f"[DRY RUN] Would create GSI {gsi_name} on table {table_name}")
        return False
    
    print(f"Creating GSI {gsi_name} on table {table_name}...")
    
    try:
        response = client.update_table(
            TableName=table_name,
            AttributeDefinitions=[
                {
                    'AttributeName': 'event_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexUpdates=[
                {
                    'Create': {
                        'IndexName': gsi_name,
                        'KeySchema': [
                            {
                                'AttributeName': 'event_id',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                }
            ]
        )
        
        print(f"GSI {gsi_name} creation initiated. Waiting for it to become active...")
        wait_for_gsi_active(client, table_name, gsi_name)
        print(f"GSI {gsi_name} created successfully and is now active")
        return True
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceInUseException':
            print(f"Table {table_name} is being modified. Please wait and try again.")
        else:
            print(f"Error creating GSI: {e}")
        raise


def delete_gsi(client, table_name, dry_run=False):
    """Delete event-id-index GSI from Events table."""
    gsi_name = 'event-id-index'
    
    # Check if GSI exists
    if not check_gsi_exists(client, table_name, gsi_name):
        print(f"GSI {gsi_name} does not exist on table {table_name}")
        return True
    
    if dry_run:
        print(f"[DRY RUN] Would delete GSI {gsi_name} from table {table_name}")
        return False
    
    print(f"Deleting GSI {gsi_name} from table {table_name}...")
    
    try:
        response = client.update_table(
            TableName=table_name,
            GlobalSecondaryIndexUpdates=[
                {
                    'Delete': {
                        'IndexName': gsi_name
                    }
                }
            ]
        )
        
        print(f"GSI {gsi_name} deletion initiated. Waiting for completion...")
        # Wait for table to be back to active state
        waiter = client.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        print(f"GSI {gsi_name} deleted successfully")
        return True
        
    except ClientError as e:
        print(f"Error deleting GSI: {e}")
        raise


def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate Events table to add event-id-index GSI')
    parser.add_argument('--table-name', required=True, help='DynamoDB table name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--rollback', action='store_true', help='Delete GSI if exists')
    
    args = parser.parse_args()
    
    # Set region
    os.environ['AWS_REGION'] = args.region
    
    client = get_dynamodb_client()
    
    try:
        if args.rollback:
            delete_gsi(client, args.table_name, dry_run=args.dry_run)
        else:
            create_gsi(client, args.table_name, dry_run=args.dry_run)
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    main()


