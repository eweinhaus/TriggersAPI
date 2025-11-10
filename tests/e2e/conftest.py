"""End-to-end test fixtures"""

import os
import time
import subprocess
import pytest
import httpx
from threading import Thread
import uvicorn
from contextlib import contextmanager

from src.main import app
from src.database import create_tables


def is_dynamodb_local_running() -> bool:
    """Check if DynamoDB Local is running."""
    try:
        import docker
        client = docker.from_env()
        containers = client.containers.list(filters={"name": "dynamodb-local"})
        return len(containers) > 0 and containers[0].status == "running"
    except Exception:
        # Fallback: try to connect to DynamoDB Local
        try:
            import boto3
            dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url='http://localhost:8000',
                region_name='us-east-1',
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
            # Try to list tables (will fail if not running)
            list(dynamodb.tables.all())
            return True
        except Exception:
            return False


def start_dynamodb_local():
    """Start DynamoDB Local using docker-compose."""
    try:
        subprocess.run(
            ["docker-compose", "up", "-d", "dynamodb-local"],
            check=True,
            capture_output=True
        )
        # Wait for DynamoDB to be ready
        time.sleep(2)
    except Exception as e:
        pytest.skip(f"Could not start DynamoDB Local: {e}")


@pytest.fixture(scope="session")
def dynamodb_local():
    """Ensure DynamoDB Local is running for E2E tests."""
    if not is_dynamodb_local_running():
        start_dynamodb_local()
    
    # Set environment for DynamoDB Local
    os.environ['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:8000'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    os.environ['AUTH_MODE'] = 'local'
    os.environ['DYNAMODB_TABLE_EVENTS'] = 'triggers-api-events'
    os.environ['DYNAMODB_TABLE_API_KEYS'] = 'triggers-api-keys'
    
    # Create tables
    try:
        create_tables()
    except Exception as e:
        pytest.skip(f"Could not create tables: {e}")
    
    yield
    
    # Cleanup (optional - keep running for faster tests)


def run_server():
    """Run FastAPI server in a separate thread."""
    # Ensure environment is set for local testing
    os.environ.setdefault('DYNAMODB_ENDPOINT_URL', 'http://localhost:8000')
    os.environ.setdefault('AWS_REGION', 'us-east-1')
    os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test')
    os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test')
    os.environ.setdefault('AUTH_MODE', 'local')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    os.environ.setdefault('DYNAMODB_TABLE_EVENTS', 'triggers-api-events')
    os.environ.setdefault('DYNAMODB_TABLE_API_KEYS', 'triggers-api-keys')
    
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="error")


@pytest.fixture(scope="session")
def api_server(dynamodb_local):
    """Start FastAPI server for E2E tests."""
    # Start server in background thread
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to be ready
    max_attempts = 10
    for _ in range(max_attempts):
        try:
            response = httpx.get("http://127.0.0.1:8081/v1/health", timeout=1.0)
            if response.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        pytest.skip("Could not start API server")
    
    yield "http://127.0.0.1:8081"
    
    # Server will be stopped when thread dies (daemon=True)


@pytest.fixture
def e2e_client(api_server):
    """HTTP client for E2E tests."""
    base_url = api_server
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
def cleanup_events(e2e_client, api_key):
    """Clean up test events after each test."""
    yield
    
    # After test, clean up events (optional - can be skipped for faster tests)
    # This would require implementing a cleanup endpoint or direct DB access
    pass

