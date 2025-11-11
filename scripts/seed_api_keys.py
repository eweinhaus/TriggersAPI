"""Script to seed API keys in DynamoDB"""

import os
import sys
import argparse
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


def create_api_key(api_key: str, source: str = None, stage: str = 'prod', region: str = 'us-east-1', 
                   rate_limit: int = None, allowed_ips: list = None):
    """
    Create an API key in DynamoDB.
    
    Args:
        api_key: API key value (required)
        source: Source identifier (optional)
        stage: Deployment stage (default: 'prod')
        region: AWS region (default: 'us-east-1')
        rate_limit: Rate limit (requests per minute, default: 1000)
        allowed_ips: List of allowed IPs/CIDR ranges (optional, empty list = allow all)
    """
    os.environ['AWS_REGION'] = region
    dynamodb = get_dynamodb_resource()
    
    table_name = f'triggers-api-keys-{stage}'
    table = dynamodb.Table(table_name)
    
    # Check if key already exists
    try:
        response = table.get_item(Key={'api_key': api_key})
        if 'Item' in response:
            print(f"API key already exists in table {table_name}")
            return
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            raise
    
    # Create API key item
    item = {
        'api_key': api_key,
        'is_active': True,
        'created_at': get_iso_timestamp()
    }
    
    if source:
        item['source'] = source
    
    if rate_limit is not None:
        item['rate_limit'] = rate_limit
    
    if allowed_ips is not None:
        item['allowed_ips'] = allowed_ips
    
    try:
        table.put_item(Item=item)
        print(f"API key created successfully in table {table_name}")
        print(f"  API Key: {api_key}")
        print(f"  Source: {source or 'N/A'}")
        print(f"  Active: True")
        if rate_limit is not None:
            print(f"  Rate Limit: {rate_limit} requests/min")
        if allowed_ips is not None:
            print(f"  Allowed IPs: {allowed_ips if allowed_ips else 'All IPs allowed'}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Error: Table {table_name} does not exist. Please create it first.")
        else:
            print(f"Error creating API key: {e}")
            raise


def main():
    """Main function to handle command-line arguments."""
    parser = argparse.ArgumentParser(description='Seed API keys in DynamoDB')
    parser.add_argument('--api-key', required=True, help='API key value')
    parser.add_argument('--source', help='Source identifier (optional)')
    parser.add_argument('--stage', default='prod', help='Deployment stage (default: prod)')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--rate-limit', type=int, help='Rate limit (requests per minute, default: 1000)')
    parser.add_argument('--allowed-ips', help='Comma-separated list of allowed IPs/CIDR ranges (optional, empty = allow all)')
    
    args = parser.parse_args()
    
    # Confirmation prompt for production (skip if running non-interactively)
    if args.stage == 'prod' and sys.stdin.isatty():
        response = input(f"Are you sure you want to create an API key in PRODUCTION ({args.stage})? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    # Parse allowed IPs
    allowed_ips_list = None
    if args.allowed_ips is not None:
        if args.allowed_ips.strip():
            allowed_ips_list = [ip.strip() for ip in args.allowed_ips.split(',')]
        else:
            allowed_ips_list = []  # Empty list = allow all
    
    create_api_key(
        api_key=args.api_key,
        source=args.source,
        stage=args.stage,
        region=args.region,
        rate_limit=args.rate_limit,
        allowed_ips=allowed_ips_list
    )


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    main()
