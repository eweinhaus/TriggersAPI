import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const eventIngestionRate = new Rate('event_ingestion_success');
const eventLatency = new Trend('event_ingestion_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 1000 },  // Ramp up to 1000 users
    { duration: '5m', target: 1000 },  // Stay at 1000 users
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<100'],  // 95% of requests must complete below 100ms
    http_req_failed: ['rate<0.001'],   // Error rate must be less than 0.1%
    event_ingestion_success: ['rate>0.999'], // Success rate > 99.9%
  },
};

const API_URL = __ENV.API_URL || 'http://localhost:8080';
const API_KEY = __ENV.API_KEY || 'test-api-key-12345';

export default function () {
  const payload = {
    source: `load-test-${Math.floor(Math.random() * 1000)}`,
    event_type: 'test.event',
    payload: {
      test_id: `test-${Date.now()}-${Math.random()}`,
      timestamp: new Date().toISOString(),
      data: {
        value: Math.random() * 1000,
        category: ['A', 'B', 'C'][Math.floor(Math.random() * 3)],
      },
    },
    metadata: {
      priority: ['low', 'normal', 'high'][Math.floor(Math.random() * 3)],
    },
  };

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
    tags: { name: 'EventIngestion' },
  };

  const startTime = Date.now();
  const response = http.post(`${API_URL}/v1/events`, JSON.stringify(payload), params);
  const duration = Date.now() - startTime;

  const success = check(response, {
    'status is 201': (r) => r.status === 201,
    'has event_id': (r) => {
      const body = JSON.parse(r.body);
      return body.event_id !== undefined;
    },
  });

  eventIngestionRate.add(success);
  eventLatency.add(duration);

  sleep(0.1); // Small delay between requests
}


