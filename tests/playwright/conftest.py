"""Playwright MCP test fixtures"""

import os
import pytest


@pytest.fixture
def api_base_url():
    """
    Base URL for API (local or deployed).
    
    Can be overridden with environment variable API_BASE_URL.
    Defaults to localhost:8080 for local testing.
    For deployed API, set: export API_BASE_URL=https://your-api-url.com
    """
    return os.getenv('API_BASE_URL', 'http://localhost:8080')


@pytest.fixture
def playwright_api_key():
    """Test API key for Playwright tests."""
    return "test-api-key-12345"


@pytest.fixture
def playwright_headers(playwright_api_key):
    """Headers with API key for Playwright tests."""
    return {
        "X-API-Key": playwright_api_key,
        "Content-Type": "application/json"
    }

