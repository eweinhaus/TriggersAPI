import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const mixedWorkloadSuccess = new Rate('mixed_workload_success');
const mixedWorkloadLatency = new Trend('mixed_workload_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 1000 },  // Ramp up to 1000 users
    { duration: '10m', target: 1000 }, // Stay at 1000 users
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<150'],  // 95% of requests must complete below 150ms
    http_req_failed: ['rate<0.001'],   // Error rate must be less than 0.1%
    mixed_workload_success: ['rate>0.999'], // Success rate > 99.9%
  },
};

const API_URL = __ENV.API_URL || 'http://localhost:8080';
const API_KEY = __ENV.API_KEY || 'test-api-key-12345';

// Workload distribution: 70% create, 20% inbox, 5% ack, 5% delete
function getWorkloadType() {
  const rand = Math.random();
  if (rand < 0.7) return 'create';
  if (rand < 0.9) return 'inbox';
  if (rand < 0.95) return 'ack';
  return 'delete';
}

let createdEventIds = [];

export default function () {
  const workloadType = getWorkloadType();
  const startTime = Date.now();
  let response;
  let success = false;

  switch (workloadType) {
    case 'create':
      // 70% - Create events
      const payload = {
        source: `mixed-test-${Math.floor(Math.random() * 100)}`,
        event_type: 'test.event',
        payload: {
          test_id: `test-${Date.now()}-${Math.random()}`,
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
      if (success && response.body) {
        const body = JSON.parse(response.body);
        if (body.event_id) {
          createdEventIds.push(body.event_id);
          // Keep only last 100 event IDs
          if (createdEventIds.length > 100) {
            createdEventIds.shift();
          }
        }
      }
      break;

    case 'inbox':
      // 20% - Query inbox
      const limit = [10, 25, 50][Math.floor(Math.random() * 3)];
      response = http.get(
        `${API_URL}/v1/inbox?limit=${limit}`,
        {
          headers: { 'X-API-Key': API_KEY },
        }
      );
      success = check(response, {
        'inbox status is 200': (r) => r.status === 200,
      });
      break;

    case 'ack':
      // 5% - Acknowledge events
      if (createdEventIds.length > 0) {
        const eventId = createdEventIds[Math.floor(Math.random() * createdEventIds.length)];
        response = http.post(
          `${API_URL}/v1/events/${eventId}/ack`,
          null,
          {
            headers: { 'X-API-Key': API_KEY },
          }
        );
        success = check(response, {
          'ack status is 200 or 409': (r) => r.status === 200 || r.status === 409,
        });
      } else {
        success = true; // Skip if no events to ack
      }
      break;

    case 'delete':
      // 5% - Delete events
      if (createdEventIds.length > 0) {
        const eventId = createdEventIds[Math.floor(Math.random() * createdEventIds.length)];
        response = http.del(
          `${API_URL}/v1/events/${eventId}`,
          null,
          {
            headers: { 'X-API-Key': API_KEY },
          }
        );
        success = check(response, {
          'delete status is 200': (r) => r.status === 200,
        });
        // Remove from list
        createdEventIds = createdEventIds.filter(id => id !== eventId);
      } else {
        success = true; // Skip if no events to delete
      }
      break;
  }

  const duration = Date.now() - startTime;
  mixedWorkloadSuccess.add(success);
  mixedWorkloadLatency.add(duration);

  sleep(0.1 + Math.random() * 0.2); // Random delay between 0.1-0.3s
}

