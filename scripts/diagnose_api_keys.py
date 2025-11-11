#!/usr/bin/env python3
"""Diagnostic script to check API key configuration in deployment"""

import os
import sys
import boto3
import json
from botocore.exceptions import ClientError

REGION = os.getenv('AWS_REGION', 'us-east-1')
STAGE = os.getenv('STAGE', 'prod')
FUNCTION_NAME = f'triggers-api-{STAGE}'
API_KEYS_TABLE = f'triggers-api-keys-{STAGE}'


def check_lambda_env_vars():
    """Check Lambda function environment variables."""
    print("=" * 60)
    print("1. Checking Lambda Function Environment Variables")
    print("=" * 60)
    
    try:
        lambda_client = boto3.client('lambda', region_name=REGION)
        response = lambda_client.get_function_configuration(FunctionName=FUNCTION_NAME)
        
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        print(f"\nFunction: {FUNCTION_NAME}")
        print(f"Region: {REGION}")
        print(f"\nEnvironment Variables:")
        for key, value in sorted(env_vars.items()):
            print(f"  {key}: {value}")
        
        # Check critical variables
        critical_vars = {
            'AUTH_MODE': 'aws',
            'DYNAMODB_TABLE_KEYS': API_KEYS_TABLE,
            'AWS_REGION': REGION
        }
        
        print(f"\n✓ Critical Variables Check:")
        all_ok = True
        for var, expected in critical_vars.items():
            actual = env_vars.get(var)
            if actual == expected:
                print(f"  ✓ {var}: {actual} (correct)")
            else:
                print(f"  ✗ {var}: {actual} (expected: {expected})")
                all_ok = False
        
        return all_ok, env_vars
        
    except ClientError as e:
        print(f"✗ Error checking Lambda function: {e}")
        return False, {}
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False, {}


def check_api_keys_table():
    """Check if API keys table exists and has keys."""
    print("\n" + "=" * 60)
    print("2. Checking API Keys DynamoDB Table")
    print("=" * 60)
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(API_KEYS_TABLE)
        
        # Check if table exists
        try:
            table.load()
            print(f"\n✓ Table exists: {API_KEYS_TABLE}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"✗ Table does not exist: {API_KEYS_TABLE}")
                return False, []
            else:
                raise
        
        # Scan for API keys (limit to first 10 for display)
        print(f"\nScanning for API keys (showing first 10)...")
        response = table.scan(Limit=10)
        items = response.get('Items', [])
        
        if items:
            print(f"✓ Found {len(items)} API key(s):")
            for item in items:
                api_key = item.get('api_key', 'N/A')
                is_active = item.get('is_active', True)
                created_at = item.get('created_at', 'N/A')
                # Mask API key for display
                masked_key = api_key[:8] + '...' + api_key[-4:] if len(api_key) > 12 else '***'
                status = "✓ Active" if is_active else "✗ Inactive"
                print(f"  - {masked_key} ({status}, created: {created_at})")
        else:
            print(f"✗ No API keys found in table!")
            print(f"  Run: python scripts/seed_api_keys.py --api-key <your-key> --stage {STAGE}")
            return False, []
        
        return True, items
        
    except ClientError as e:
        print(f"✗ Error checking table: {e}")
        return False, []
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False, []


def check_iam_permissions():
    """Check IAM role permissions for Lambda."""
    print("\n" + "=" * 60)
    print("3. Checking IAM Permissions")
    print("=" * 60)
    
    try:
        lambda_client = boto3.client('lambda', region_name=REGION)
        response = lambda_client.get_function_configuration(FunctionName=FUNCTION_NAME)
        
        role_arn = response.get('Role')
        if not role_arn:
            print("✗ No IAM role found for Lambda function")
            return False
        
        print(f"\n✓ Lambda IAM Role: {role_arn}")
        
        # Extract role name from ARN
        role_name = role_arn.split('/')[-1]
        iam = boto3.client('iam', region_name=REGION)
        
        # Get role policies
        try:
            # Get inline policies
            inline_policies = iam.list_role_policies(RoleName=role_name)
            print(f"\nInline Policies: {', '.join(inline_policies.get('PolicyNames', []))}")
            
            # Get attached policies
            attached_policies = iam.list_attached_role_policies(RoleName=role_name)
            policy_arns = [p['PolicyArn'] for p in attached_policies.get('AttachedPolicies', [])]
            print(f"Attached Policies: {len(policy_arns)} policy(ies)")
            
            # Check for DynamoDB permissions
            print(f"\nNote: Verify that the role has DynamoDB GetItem permission for:")
            print(f"  - {API_KEYS_TABLE}")
            
        except ClientError as e:
            print(f"⚠ Could not check IAM policies: {e}")
        
        return True
        
    except ClientError as e:
        print(f"✗ Error checking IAM: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_api_key_lookup(api_key: str = None):
    """Test API key lookup from Lambda's perspective."""
    print("\n" + "=" * 60)
    print("4. Testing API Key Lookup")
    print("=" * 60)
    
    if not api_key:
        print("⚠ No API key provided, skipping lookup test")
        return False
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(API_KEYS_TABLE)
        
        response = table.get_item(Key={'api_key': api_key})
        item = response.get('Item')
        
        if item:
            is_active = item.get('is_active', True)
            print(f"\n✓ API key found in table")
            print(f"  Active: {is_active}")
            if is_active:
                print(f"  ✓ API key is active and should work")
            else:
                print(f"  ✗ API key is inactive")
            return is_active
        else:
            print(f"\n✗ API key not found in table")
            print(f"  Make sure the key exists in: {API_KEYS_TABLE}")
            return False
            
    except ClientError as e:
        print(f"✗ Error looking up API key: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def main():
    """Run all diagnostic checks."""
    print("\n" + "=" * 60)
    print("API Key Authentication Diagnostic Tool")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Region: {REGION}")
    print(f"  Stage: {STAGE}")
    print(f"  Function: {FUNCTION_NAME}")
    print(f"  API Keys Table: {API_KEYS_TABLE}")
    
    # Run checks
    lambda_ok, env_vars = check_lambda_env_vars()
    table_ok, api_keys = check_api_keys_table()
    iam_ok = check_iam_permissions()
    
    # Test lookup if we have keys
    lookup_ok = False
    if api_keys:
        test_key = api_keys[0].get('api_key')
        if test_key:
            lookup_ok = test_api_key_lookup(test_key)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    checks = [
        ("Lambda Environment Variables", lambda_ok),
        ("API Keys Table", table_ok),
        ("IAM Permissions", iam_ok),
        ("API Key Lookup", lookup_ok if api_keys else None)
    ]
    
    all_ok = True
    for name, status in checks:
        if status is None:
            print(f"  ⚠ {name}: Not checked")
        elif status:
            print(f"  ✓ {name}: OK")
        else:
            print(f"  ✗ {name}: FAILED")
            all_ok = False
    
    if all_ok:
        print("\n✓ All checks passed! API keys should work.")
    else:
        print("\n✗ Some checks failed. See details above.")
        print("\nCommon fixes:")
        print("  1. Update Lambda environment variables:")
        print(f"     aws lambda update-function-configuration \\")
        print(f"       --function-name {FUNCTION_NAME} \\")
        print(f"       --environment Variables={{AUTH_MODE=aws,DYNAMODB_TABLE_KEYS={API_KEYS_TABLE},AWS_REGION={REGION}}}")
        print("  2. Seed API keys:")
        print(f"     python scripts/seed_api_keys.py --api-key <your-key> --stage {STAGE}")
        print("  3. Check IAM role has DynamoDB GetItem permission for API keys table")


if __name__ == '__main__':
    main()

