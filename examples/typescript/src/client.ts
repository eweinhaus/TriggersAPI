/**
 * Main client class for Triggers API
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import * as crypto from 'crypto';
import { mapStatusCodeToError } from './errors';

export interface ClientOptions {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
  requestId?: string | null;
  signingSecret?: string | null;
}

export interface EventResponse {
  event_id: string;
  created_at: string;
  status: string;
  message: string;
  request_id: string;
}

export interface EventDetailResponse {
  event_id: string;
  created_at: string;
  source: string;
  event_type: string;
  payload: Record<string, any>;
  status: string;
  metadata?: Record<string, any>;
  acknowledged_at?: string;
  request_id: string;
}

export interface InboxResponse {
  events: Array<Record<string, any>>;
  pagination: {
    limit: number;
    cursor?: string;
    next_cursor?: string;
  };
  request_id: string;
}

export interface CreateEventOptions {
  source: string;
  eventType: string;
  payload: Record<string, any>;
  metadata?: Record<string, any>;
  requestId?: string | null;
}

export interface GetInboxOptions {
  limit?: number;
  cursor?: string | null;
  source?: string | null;
  eventType?: string | null;
  requestId?: string | null;
}

export class TriggersAPIClient {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;
  private defaultRequestId: string | null;
  private signingSecret: string | null;
  private client: AxiosInstance;

  /**
   * Initialize the Triggers API client.
   * 
   * @param options - Client configuration
   */
  constructor({
    apiKey,
    baseUrl = 'http://localhost:8080',
    timeout = 30000,
    requestId = null,
    signingSecret = null,
  }: ClientOptions) {
    if (!apiKey) {
      throw new Error('API key is required');
    }

    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.timeout = timeout;
    this.defaultRequestId = requestId;
    this.signingSecret = signingSecret;

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
   */
  private async _makeRequest<T>(
    method: string,
    endpoint: string,
    data: any = null,
    params: any = null,
    requestId: string | null = null
  ): Promise<T> {
    const headers: Record<string, string> = {};

    // Add request ID if provided
    if (requestId || this.defaultRequestId) {
      headers['X-Request-ID'] = requestId || this.defaultRequestId || '';
    }

    // Add signature headers if signing secret is provided
    if (this.signingSecret) {
      const url = new URL(endpoint, this.baseUrl);
      const path = url.pathname;
      const queryString = url.search.substring(1); // Remove leading '?'

      // Get body hash
      const bodyString = data ? JSON.stringify(data) : '';
      const bodyHash = crypto.createHash('sha256').update(bodyString).digest('hex');

      // Generate signature
      const timestamp = Math.floor(Date.now() / 1000).toString();
      const signatureString = `${method}\n${path}\n${queryString}\n${timestamp}\n${bodyHash}`;
      const signature = crypto
        .createHmac('sha256', this.signingSecret)
        .update(signatureString)
        .digest('base64');

      headers['X-Signature-Timestamp'] = timestamp;
      headers['X-Signature'] = signature;
      headers['X-Signature-Version'] = 'v1';
    }

    try {
      const config: AxiosRequestConfig = {
        method: method as any,
        url: endpoint,
        data,
        params,
        headers,
      };

      const response = await this.client.request<T>(config);
      return response.data;
    } catch (error: any) {
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
   */
  private _handleError(statusCode: number, responseData: any): void {
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
   */
  async createEvent({
    source,
    eventType,
    payload,
    metadata = null,
    requestId = null,
  }: CreateEventOptions): Promise<EventResponse> {
    const data: any = {
      source,
      event_type: eventType,
      payload,
    };
    if (metadata) {
      data.metadata = metadata;
    }

    return await this._makeRequest<EventResponse>('POST', '/v1/events', data, null, requestId);
  }

  /**
   * Get detailed information about a specific event.
   */
  async getEvent(eventId: string, requestId: string | null = null): Promise<EventDetailResponse> {
    return await this._makeRequest<EventDetailResponse>(
      'GET',
      `/v1/events/${eventId}`,
      null,
      null,
      requestId
    );
  }

  /**
   * Get pending events with pagination and filtering.
   */
  async getInbox({
    limit = 50,
    cursor = null,
    source = null,
    eventType = null,
    requestId = null,
  }: GetInboxOptions = {}): Promise<InboxResponse> {
    const params: any = { limit };
    if (cursor) params.cursor = cursor;
    if (source) params.source = source;
    if (eventType) params.event_type = eventType;

    return await this._makeRequest<InboxResponse>('GET', '/v1/inbox', null, params, requestId);
  }

  /**
   * Acknowledge an event.
   */
  async acknowledgeEvent(eventId: string, requestId: string | null = null): Promise<any> {
    return await this._makeRequest('POST', `/v1/events/${eventId}/ack`, null, null, requestId);
  }

  /**
   * Delete an event.
   */
  async deleteEvent(eventId: string, requestId: string | null = null): Promise<any> {
    return await this._makeRequest('DELETE', `/v1/events/${eventId}`, null, null, requestId);
  }
}

export default TriggersAPIClient;

