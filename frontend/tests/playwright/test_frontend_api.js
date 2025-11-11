/**
 * Playwright MCP tests for frontend API integration
 * Tests API calls from frontend perspective
 */

import { test, expect } from '@playwright/test';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/v1';
const API_KEY = 'test-api-key-12345';

test.describe('Frontend API Integration', () => {
  test('Health check endpoint works', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('Create event via API', async ({ request }) => {
    const eventData = {
      source: 'test-frontend',
      event_type: 'test.created',
      payload: { test: true, frontend: true },
    };

    const response = await request.post(`${API_BASE_URL}/events`, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        'X-Request-ID': 'test-frontend-request-1',
      },
      data: eventData,
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.event_id).toBeDefined();
    expect(data.status).toBe('pending');
  });

  test('Get inbox via API', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/inbox`, {
      headers: {
        'X-API-Key': API_KEY,
        'X-Request-ID': 'test-frontend-request-2',
      },
      params: {
        limit: 10,
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.events).toBeDefined();
    expect(Array.isArray(data.events)).toBeTruthy();
  });

  test('API returns proper error for invalid API key', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/inbox`, {
      headers: {
        'X-API-Key': 'invalid-key',
        'X-Request-ID': 'test-frontend-request-3',
      },
    });

    expect(response.status()).toBe(401);
    const data = await response.json();
    expect(data.error).toBeDefined();
    expect(data.error.code).toBe('UNAUTHORIZED');
  });

  test('API returns proper error for missing API key', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/inbox`, {
      headers: {
        'X-Request-ID': 'test-frontend-request-4',
      },
    });

    expect(response.status()).toBe(401);
    const data = await response.json();
    expect(data.error).toBeDefined();
    expect(data.error.code).toBe('UNAUTHORIZED');
  });
});

