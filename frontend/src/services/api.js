import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

// Create Axios instance with base URL from environment variable
// Vite uses import.meta.env instead of process.env
const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || 'http://localhost:8080/v1';

// Log API URL in development for debugging
if (import.meta.env.DEV) {
  console.log('API Base URL:', API_BASE_URL);
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
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
      let errorMessage = 'Network error: Unable to reach the server';
      let errorDetails = {};
      
      // Provide more specific error messages
      if (error.code === 'ECONNREFUSED') {
        errorMessage = `Connection refused. Is the API server running at ${API_BASE_URL}?`;
        errorDetails = { 
          apiUrl: API_BASE_URL,
          suggestion: 'Make sure the backend server is running on the configured port'
        };
      } else if (error.code === 'ENOTFOUND' || error.code === 'ECONNABORTED') {
        errorMessage = `Cannot connect to ${API_BASE_URL}. Check your network connection and API URL configuration.`;
        errorDetails = { apiUrl: API_BASE_URL };
      } else if (error.message.includes('timeout')) {
        errorMessage = `Request timeout. The server at ${API_BASE_URL} did not respond in time.`;
        errorDetails = { apiUrl: API_BASE_URL };
      } else if (error.message) {
        errorMessage = `Network error: ${error.message}`;
        errorDetails = { apiUrl: API_BASE_URL, originalError: error.message };
      }
      
      // Log full error in development
      if (import.meta.env.DEV) {
        console.error('Network error details:', {
          error,
          apiUrl: API_BASE_URL,
          requestUrl: error.config?.url,
          fullUrl: error.config ? `${error.config.baseURL}${error.config.url}` : 'unknown'
        });
      }
      
      error.formattedError = {
        code: 'NETWORK_ERROR',
        message: errorMessage,
        details: errorDetails,
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
 * Create a new webhook
 * @param {Object} data - Webhook data
 * @param {string} data.url - Webhook URL
 * @param {string[]} data.events - Event types to subscribe to
 * @param {string} data.secret - Webhook secret (min 16 chars)
 * @returns {Promise} API response
 */
export const createWebhook = async (data) => {
  return api.post('/webhooks', data);
};

/**
 * List webhooks
 * @param {Object} params - Query parameters
 * @param {number} [params.limit] - Number of webhooks to return
 * @param {string} [params.cursor] - Pagination cursor
 * @param {boolean} [params.is_active] - Filter by active status
 * @returns {Promise} API response
 */
export const getWebhooks = async (params = {}) => {
  return api.get('/webhooks', { params });
};

/**
 * Get webhook by ID
 * @param {string} webhookId - Webhook ID
 * @returns {Promise} API response
 */
export const getWebhook = async (webhookId) => {
  return api.get(`/webhooks/${webhookId}`);
};

/**
 * Update webhook
 * @param {string} webhookId - Webhook ID
 * @param {Object} data - Webhook update data
 * @returns {Promise} API response
 */
export const updateWebhook = async (webhookId, data) => {
  return api.put(`/webhooks/${webhookId}`, data);
};

/**
 * Delete webhook
 * @param {string} webhookId - Webhook ID
 * @returns {Promise} API response
 */
export const deleteWebhook = async (webhookId) => {
  return api.delete(`/webhooks/${webhookId}`);
};

/**
 * Test webhook
 * @param {string} webhookId - Webhook ID
 * @returns {Promise} API response
 */
export const testWebhook = async (webhookId) => {
  return api.post(`/webhooks/${webhookId}/test`);
};

/**
 * Get analytics data
 * @param {Object} params - Query parameters
 * @param {string} [params.start_date] - Start date (YYYY-MM-DD)
 * @param {string} [params.end_date] - End date (YYYY-MM-DD)
 * @param {string} [params.metric_type] - Metric type (hourly|daily)
 * @returns {Promise} API response
 */
export const getAnalytics = async (params = {}) => {
  return api.get('/analytics', { params });
};

/**
 * Get analytics summary
 * @param {Object} params - Query parameters
 * @param {string} [params.start_date] - Start date (YYYY-MM-DD)
 * @param {string} [params.end_date] - End date (YYYY-MM-DD)
 * @returns {Promise} API response
 */
export const getAnalyticsSummary = async (params = {}) => {
  return api.get('/analytics/summary', { params });
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

