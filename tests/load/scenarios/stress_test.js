import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const stressTestSuccess = new Rate('stress_test_success');
const stressTestLatency = new Trend('stress_test_latency');

// Test configuration - Stress test with higher load
export const options = {
  stages: [
    { duration: '1m', target: 500 },   // Ramp up to 500
    { duration: '1m', target: 1000 },  // Ramp to 1000
    { duration: '1m', target: 2000 },  // Ramp to 2000 (stress level)
    { duration: '5m', target: 2000 },  // Stay at 2000
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    // More lenient thresholds for stress test
    http_req_duration: ['p(95)<500'],  // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.05'],   // Error rate must be less than 5%
    stress_test_success: ['rate>0.95'], // Success rate > 95%
  },
};

const API_URL = __ENV.API_URL || 'http://localhost:8080';
const API_KEY = __ENV.API_KEY || 'test-api-key-12345';

export default function () {
  // Mix of operations under stress
  const operations = ['create', 'inbox'];
  const operation = operations[Math.floor(Math.random() * operations.length)];

  const startTime = Date.now();
  let response;
  let success = false;

  if (operation === 'create') {
    const payload = {
      source: `stress-test-${Math.floor(Math.random() * 1000)}`,
      event_type: 'stress.test',
      payload: {
        test_id: `stress-${Date.now()}-${Math.random()}`,
        data: { value: Math.random() * 1000 },
      },
    };
    response = http.post(
      `${API_URL}/v1/events`,
      JSON.stringify(payload),
      {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
      }
    );
    success = check(response, {
      'create status is 201': (r) => r.status === 201,
    });
  } else {
    // Inbox query
    response = http.get(
      `${API_URL}/v1/inbox?limit=50`,
      {
        headers: { 'X-API-Key': API_KEY },
      }
    );
    success = check(response, {
      'inbox status is 200': (r) => r.status === 200,
    });
  }

  const duration = Date.now() - startTime;
  stressTestSuccess.add(success);
  stressTestLatency.add(duration);

  sleep(0.05); // Minimal delay for stress test
}


