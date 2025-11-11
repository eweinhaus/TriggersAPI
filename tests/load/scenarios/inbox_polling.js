import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const inboxQuerySuccess = new Rate('inbox_query_success');
const inboxLatency = new Trend('inbox_query_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 500 },  // Ramp up to 500 users
    { duration: '5m', target: 500 },  // Stay at 500 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],  // 95% of requests must complete below 200ms
    http_req_failed: ['rate<0.001'],   // Error rate must be less than 0.1%
    inbox_query_success: ['rate>0.999'], // Success rate > 99.9%
  },
};

const API_URL = __ENV.API_URL || 'http://localhost:8080';
const API_KEY = __ENV.API_KEY || 'test-api-key-12345';

export default function () {
  const params = {
    headers: {
      'X-API-Key': API_KEY,
    },
    tags: { name: 'InboxPolling' },
  };

  // Randomly vary query parameters
  const limit = [10, 25, 50, 100][Math.floor(Math.random() * 4)];
  const source = Math.random() > 0.7 ? `source-${Math.floor(Math.random() * 10)}` : null;
  const eventType = Math.random() > 0.7 ? `event.type.${Math.floor(Math.random() * 5)}` : null;

  let url = `${API_URL}/v1/inbox?limit=${limit}`;
  if (source) url += `&source=${source}`;
  if (eventType) url += `&event_type=${eventType}`;

  const startTime = Date.now();
  const response = http.get(url, params);
  const duration = Date.now() - startTime;

  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'has events array': (r) => {
      const body = JSON.parse(r.body);
      return Array.isArray(body.events);
    },
    'has pagination': (r) => {
      const body = JSON.parse(r.body);
      return body.pagination !== undefined;
    },
  });

  inboxQuerySuccess.add(success);
  inboxLatency.add(duration);

  sleep(0.5); // Delay between polling requests
}

