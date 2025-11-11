package triggersapi

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

// Client is the main client for interacting with the Triggers API
type Client struct {
	apiKey       string
	baseURL      string
	timeout      time.Duration
	signingSecret string
	httpClient   *http.Client
}

// ClientOptions configures the client
type ClientOptions struct {
	APIKey        string
	BaseURL       string
	Timeout       time.Duration
	SigningSecret string
}

// NewClient creates a new Triggers API client
func NewClient(options ClientOptions) (*Client, error) {
	if options.APIKey == "" {
		return nil, fmt.Errorf("API key is required")
	}

	if options.BaseURL == "" {
		options.BaseURL = "http://localhost:8080"
	}

	if options.Timeout == 0 {
		options.Timeout = 30 * time.Second
	}

	return &Client{
		apiKey:        options.APIKey,
		baseURL:       options.BaseURL,
		timeout:       options.Timeout,
		signingSecret: options.SigningSecret,
		httpClient: &http.Client{
			Timeout: options.Timeout,
		},
	}, nil
}

// EventResponse represents the response from creating an event
type EventResponse struct {
	EventID   string `json:"event_id"`
	CreatedAt string `json:"created_at"`
	Status    string `json:"status"`
	Message   string `json:"message"`
	RequestID string `json:"request_id"`
}

// EventDetailResponse represents detailed event information
type EventDetailResponse struct {
	EventID       string                 `json:"event_id"`
	CreatedAt     string                 `json:"created_at"`
	Source        string                 `json:"source"`
	EventType     string                 `json:"event_type"`
	Payload       map[string]interface{} `json:"payload"`
	Status        string                 `json:"status"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
	AcknowledgedAt string                `json:"acknowledged_at,omitempty"`
	RequestID     string                 `json:"request_id"`
}

// InboxResponse represents the inbox query response
type InboxResponse struct {
	Events     []map[string]interface{} `json:"events"`
	Pagination struct {
		Limit     int    `json:"limit"`
		Cursor    string `json:"cursor,omitempty"`
		NextCursor string `json:"next_cursor,omitempty"`
	} `json:"pagination"`
	RequestID string `json:"request_id"`
}

// CreateEventOptions configures event creation
type CreateEventOptions struct {
	Source    string
	EventType string
	Payload   map[string]interface{}
	Metadata  map[string]interface{}
	RequestID string
}

// GetInboxOptions configures inbox query
type GetInboxOptions struct {
	Limit     int
	Cursor    string
	Source    string
	EventType string
	RequestID string
}

func (c *Client) generateSignature(method, path, queryString, timestamp string, bodyHash string) string {
	signatureString := fmt.Sprintf("%s\n%s\n%s\n%s\n%s", method, path, queryString, timestamp, bodyHash)
	mac := hmac.New(sha256.New, []byte(c.signingSecret))
	mac.Write([]byte(signatureString))
	return base64.StdEncoding.EncodeToString(mac.Sum(nil))
}

func (c *Client) makeRequest(method, endpoint string, body interface{}, params map[string]string, requestID string) ([]byte, error) {
	// Build URL
	reqURL, err := url.Parse(c.baseURL + endpoint)
	if err != nil {
		return nil, err
	}

	// Add query parameters
	if params != nil {
		q := reqURL.Query()
		for k, v := range params {
			if v != "" {
				q.Set(k, v)
			}
		}
		reqURL.RawQuery = q.Encode()
	}

	// Prepare body
	var bodyBytes []byte
	if body != nil {
		bodyBytes, err = json.Marshal(body)
		if err != nil {
			return nil, err
		}
	}

	// Create request
	req, err := http.NewRequest(method, reqURL.String(), bytes.NewBuffer(bodyBytes))
	if err != nil {
		return nil, err
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", c.apiKey)
	if requestID != "" {
		req.Header.Set("X-Request-ID", requestID)
	}

	// Add signature if signing secret is provided
	if c.signingSecret != "" {
		timestamp := strconv.FormatInt(time.Now().Unix(), 10)
		bodyHash := sha256Hash(bodyBytes)
		signature := c.generateSignature(method, reqURL.Path, reqURL.RawQuery, timestamp, bodyHash)
		req.Header.Set("X-Signature-Timestamp", timestamp)
		req.Header.Set("X-Signature", signature)
		req.Header.Set("X-Signature-Version", "v1")
	}

	// Make request
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	// Check for errors
	if resp.StatusCode >= 400 {
		var errorResp struct {
			Error struct {
				Code    string                 `json:"code"`
				Message string                 `json:"message"`
				Details map[string]interface{} `json:"details"`
			} `json:"error"`
		}
		if err := json.Unmarshal(respBody, &errorResp); err == nil {
			return nil, fmt.Errorf("API error (%d): %s", resp.StatusCode, errorResp.Error.Message)
		}
		return nil, fmt.Errorf("API error (%d): %s", resp.StatusCode, string(respBody))
	}

	return respBody, nil
}

func sha256Hash(data []byte) string {
	hash := sha256.Sum256(data)
	return fmt.Sprintf("%x", hash)
}

// CreateEvent creates a new event
func (c *Client) CreateEvent(options CreateEventOptions) (*EventResponse, error) {
	data := map[string]interface{}{
		"source":      options.Source,
		"event_type":  options.EventType,
		"payload":     options.Payload,
	}
	if options.Metadata != nil {
		data["metadata"] = options.Metadata
	}

	respBody, err := c.makeRequest("POST", "/v1/events", data, nil, options.RequestID)
	if err != nil {
		return nil, err
	}

	var eventResp EventResponse
	if err := json.Unmarshal(respBody, &eventResp); err != nil {
		return nil, err
	}

	return &eventResp, nil
}

// GetEvent gets detailed information about a specific event
func (c *Client) GetEvent(eventID, requestID string) (*EventDetailResponse, error) {
	respBody, err := c.makeRequest("GET", fmt.Sprintf("/v1/events/%s", eventID), nil, nil, requestID)
	if err != nil {
		return nil, err
	}

	var eventResp EventDetailResponse
	if err := json.Unmarshal(respBody, &eventResp); err != nil {
		return nil, err
	}

	return &eventResp, nil
}

// GetInbox gets pending events with pagination and filtering
func (c *Client) GetInbox(options GetInboxOptions) (*InboxResponse, error) {
	params := make(map[string]string)
	params["limit"] = strconv.Itoa(options.Limit)
	if options.Cursor != "" {
		params["cursor"] = options.Cursor
	}
	if options.Source != "" {
		params["source"] = options.Source
	}
	if options.EventType != "" {
		params["event_type"] = options.EventType
	}

	respBody, err := c.makeRequest("GET", "/v1/inbox", nil, params, options.RequestID)
	if err != nil {
		return nil, err
	}

	var inboxResp InboxResponse
	if err := json.Unmarshal(respBody, &inboxResp); err != nil {
		return nil, err
	}

	return &inboxResp, nil
}

// AcknowledgeEvent acknowledges an event
func (c *Client) AcknowledgeEvent(eventID, requestID string) error {
	_, err := c.makeRequest("POST", fmt.Sprintf("/v1/events/%s/ack", eventID), nil, nil, requestID)
	return err
}

// DeleteEvent deletes an event
func (c *Client) DeleteEvent(eventID, requestID string) error {
	_, err := c.makeRequest("DELETE", fmt.Sprintf("/v1/events/%s", eventID), nil, nil, requestID)
	return err
}

