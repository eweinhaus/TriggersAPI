import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

// Create Axios instance with base URL from environment variable
// Vite uses import.meta.env instead of process.env
const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || 'http://localhost:8080/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add API key and request ID
api.interceptors.request.use(
  (config) => {
    // Add API key from localStorage
    const apiKey = localStorage.getItem('apiKey');
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey;
    }

    // Generate request ID (UUID v4)
    const requestId = uuidv4();
    config.headers['X-Request-ID'] = requestId;

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Format error for easier handling
    if (error.response) {
      // Server responded with error
      const errorData = error.response.data;
      error.formattedError = {
        code: errorData?.error?.code || 'UNKNOWN_ERROR',
        message: errorData?.error?.message || error.message,
        details: errorData?.error?.details || {},
        requestId: errorData?.error?.request_id || error.response.headers['x-request-id'],
        status: error.response.status,
      };
    } else if (error.request) {
      // Request made but no response
      error.formattedError = {
        code: 'NETWORK_ERROR',
        message: 'Network error: Unable to reach the server',
        details: {},
        requestId: null,
        status: null,
      };
    } else {
      // Error setting up request
      error.formattedError = {
        code: 'REQUEST_ERROR',
        message: error.message || 'An error occurred',
        details: {},
        requestId: null,
        status: null,
      };
    }
    return Promise.reject(error);
  }
);

// API Methods

/**
 * Create a new event
 * @param {Object} data - Event data
 * @param {string} data.source - Event source
 * @param {string} data.event_type - Event type
 * @param {Object} data.payload - Event payload (JSON object)
 * @param {Object} [data.metadata] - Optional metadata
 * @returns {Promise} API response
 */
export const createEvent = async (data) => {
  return api.post('/events', data);
};

/**
 * Get inbox (pending events)
 * @param {Object} params - Query parameters
 * @param {number} [params.limit] - Number of events to return (default: 10)
 * @param {string} [params.cursor] - Pagination cursor
 * @param {string} [params.source] - Filter by source
 * @param {string} [params.event_type] - Filter by event type
 * @returns {Promise} API response
 */
export const getInbox = async (params = {}) => {
  return api.get('/inbox', { params });
};

/**
 * Get a single event by ID
 * @param {string} eventId - Event ID
 * @returns {Promise} API response
 */
export const getEvent = async (eventId) => {
  return api.get(`/events/${eventId}`);
};

/**
 * Acknowledge an event
 * @param {string} eventId - Event ID
 * @returns {Promise} API response
 */
export const acknowledgeEvent = async (eventId) => {
  return api.post(`/events/${eventId}/ack`);
};

/**
 * Delete an event
 * @param {string} eventId - Event ID
 * @returns {Promise} API response
 */
export const deleteEvent = async (eventId) => {
  return api.delete(`/events/${eventId}`);
};

/**
 * Health check
 * @returns {Promise} API response
 */
export const healthCheck = async () => {
  return api.get('/health');
};

export default api;

