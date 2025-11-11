/**
 * Main client class for Triggers API
 */

const axios = require('axios');
const { mapStatusCodeToError } = require('./errors');

class TriggersAPIClient {
    /**
     * Initialize the Triggers API client.
     * 
     * @param {Object} options - Client configuration
     * @param {string} options.apiKey - Your API key for authentication
     * @param {string} [options.baseUrl='http://localhost:8080'] - Base URL of the API
     * @param {number} [options.timeout=30000] - Request timeout in milliseconds
     * @param {string} [options.requestId] - Optional default request ID for tracking
     */
    constructor({ apiKey, baseUrl = 'http://localhost:8080', timeout = 30000, requestId = null } = {}) {
        if (!apiKey) {
            throw new Error('API key is required');
        }
        
        this.apiKey = apiKey;
        this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
        this.timeout = timeout;
        this.defaultRequestId = requestId;
        
        // Create axios instance with default headers
        this.client = axios.create({
            baseURL: this.baseUrl,
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': this.apiKey,
            },
        });
    }

    /**
     * Make an HTTP request to the API.
     * 
     * @private
     * @param {string} method - HTTP method (GET, POST, DELETE, etc.)
     * @param {string} endpoint - API endpoint path (e.g., "/v1/events")
     * @param {Object} [data] - Request body data (for POST requests)
     * @param {Object} [params] - Query parameters (for GET requests)
     * @param {string} [requestId] - Optional request ID
     * @returns {Promise<Object>} Response data as object
     * @throws {TriggersAPIError} If the request fails
     */
    async _makeRequest(method, endpoint, data = null, params = null, requestId = null) {
        const headers = {};
        
        // Add request ID if provided
        if (requestId || this.defaultRequestId) {
            headers['X-Request-ID'] = requestId || this.defaultRequestId;
        }
        
        try {
            const response = await this.client.request({
                method,
                url: endpoint,
                data,
                params,
                headers,
            });
            return response.data;
        } catch (error) {
            if (error.response) {
                // API returned an error response
                this._handleError(error.response.status, error.response.data);
            } else if (error.request) {
                // Request was made but no response received
                throw new Error(`Network error: ${error.message}`);
            } else {
                // Error setting up the request
                throw new Error(`Request error: ${error.message}`);
            }
        }
    }

    /**
     * Handle API error responses.
     * 
     * @private
     * @param {number} statusCode - HTTP status code
     * @param {Object} responseData - Error response data
     * @throws {TriggersAPIError} Appropriate error subclass
     */
    _handleError(statusCode, responseData) {
        const errorData = responseData.error || {};
        const errorCode = errorData.code || 'UNKNOWN_ERROR';
        const message = errorData.message || 'An error occurred';
        const details = errorData.details || {};
        const requestId = errorData.request_id || null;
        
        const ErrorClass = mapStatusCodeToError(statusCode);
        throw new ErrorClass(message, statusCode, errorCode, details, requestId);
    }

    /**
     * Create a new event.
     * 
     * @param {Object} options - Event data
     * @param {string} options.source - Event source identifier
     * @param {string} options.eventType - Event type identifier
     * @param {Object} options.payload - Event payload (JSON object)
     * @param {Object} [options.metadata] - Optional metadata (idempotencyKey, priority, correlationId)
     * @param {string} [options.requestId] - Optional request ID for tracking
     * @returns {Promise<Object>} Event response with created event information
     * 
     * @example
     * const event = await client.createEvent({
     *   source: 'my-app',
     *   eventType: 'user.created',
     *   payload: { userId: '123', name: 'John' },
     *   metadata: { idempotencyKey: 'unique-key-123' }
     * });
     */
    async createEvent({ source, eventType, payload, metadata = null, requestId = null }) {
        const data = {
            source,
            event_type: eventType,
            payload,
        };
        if (metadata) {
            data.metadata = metadata;
        }
        
        return await this._makeRequest('POST', '/v1/events', data, null, requestId);
    }

    /**
     * Get detailed information about a specific event.
     * 
     * @param {string} eventId - UUID v4 of the event
     * @param {string} [requestId] - Optional request ID for tracking
     * @returns {Promise<Object>} Event details response
     * 
     * @example
     * const event = await client.getEvent('550e8400-e29b-41d4-a716-446655440000');
     */
    async getEvent(eventId, requestId = null) {
        return await this._makeRequest('GET', `/v1/events/${eventId}`, null, null, requestId);
    }

    /**
     * Get pending events with pagination and filtering.
     * 
     * @param {Object} [options] - Query options
     * @param {number} [options.limit=50] - Number of events to return (1-100)
     * @param {string} [options.cursor] - Pagination cursor from previous response
     * @param {string} [options.source] - Filter by source identifier
     * @param {string} [options.eventType] - Filter by event type
     * @param {string} [options.requestId] - Optional request ID for tracking
     * @returns {Promise<Object>} Inbox response with events and pagination info
     * 
     * @example
     * const inbox = await client.getInbox({ limit: 10, source: 'my-app' });
     */
    async getInbox({ limit = 50, cursor = null, source = null, eventType = null, requestId = null } = {}) {
        const params = { limit };
        if (cursor) params.cursor = cursor;
        if (source) params.source = source;
        if (eventType) params.event_type = eventType;
        
        return await this._makeRequest('GET', '/v1/inbox', null, params, requestId);
    }

    /**
     * Acknowledge an event.
     * 
     * @param {string} eventId - UUID v4 of the event to acknowledge
     * @param {string} [requestId] - Optional request ID for tracking
     * @returns {Promise<Object>} Acknowledgment response
     * 
     * @example
     * const ack = await client.acknowledgeEvent('550e8400-e29b-41d4-a716-446655440000');
     */
    async acknowledgeEvent(eventId, requestId = null) {
        return await this._makeRequest('POST', `/v1/events/${eventId}/ack`, null, null, requestId);
    }

    /**
     * Delete an event.
     * 
     * @param {string} eventId - UUID v4 of the event to delete
     * @param {string} [requestId] - Optional request ID for tracking
     * @returns {Promise<Object>} Deletion response
     * 
     * @example
     * const result = await client.deleteEvent('550e8400-e29b-41d4-a716-446655440000');
     */
    async deleteEvent(eventId, requestId = null) {
        return await this._makeRequest('DELETE', `/v1/events/${eventId}`, null, null, requestId);
    }
}

module.exports = TriggersAPIClient;

