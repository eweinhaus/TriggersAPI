# Phase 6: Frontend Dashboard - Task List

**Phase:** 6 of 6  
**Priority:** P2 (Nice to Have)  
**Status:** Not Started  
**Created:** 2025-01-XX  
**Estimated Duration:** 3-4 hours  
**Dependencies:** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5

---

## Overview

This task list covers the implementation of Phase 6: Frontend Dashboard. The goal is to deliver a React-based web dashboard with Material-UI for testing and managing events through a visual interface.

**Key Deliverables:**
- React application with Material-UI components
- Event creation form with JSON editor
- Inbox viewer with pagination and filtering
- Event details page with actions
- Statistics page with basic charts
- API key management
- Responsive design
- Automated browser tests (Cursor + Playwright MCP)
- Production deployment to S3 + CloudFront

---

## Task Breakdown

### 1. Project Setup & Structure

#### 1.1 Create React Application
- [ ] Create `frontend/` directory in project root
- [ ] Initialize React app using `create-react-app` or Vite
- [ ] Verify Node.js 18+ is installed
- [ ] Test React app starts correctly: `npm start`
- [ ] Verify app accessible at `http://localhost:3000`

#### 1.2 Install Dependencies
- [ ] Install Material-UI (MUI) v5: `npm install @mui/material @emotion/react @emotion/styled`
- [ ] Install React Router v6: `npm install react-router-dom`
- [ ] Install Axios: `npm install axios`
- [ ] Install React Query: `npm install @tanstack/react-query`
- [ ] Install JSON viewer: `npm install react-json-view` or `react-json-pretty`
- [ ] Install date formatting: `npm install date-fns`
- [ ] Install chart library (optional): `npm install recharts` or `chart.js`
- [ ] Install testing dependencies: `npm install --save-dev @playwright/test`
- [ ] Verify all dependencies installed correctly

#### 1.3 Create Project Structure
- [ ] Create `frontend/src/components/` directory
- [ ] Create `frontend/src/components/Layout/` directory
- [ ] Create `frontend/src/components/EventForm/` directory
- [ ] Create `frontend/src/components/Inbox/` directory
- [ ] Create `frontend/src/components/EventDetails/` directory
- [ ] Create `frontend/src/components/Statistics/` directory
- [ ] Create `frontend/src/services/` directory
- [ ] Create `frontend/src/hooks/` directory
- [ ] Create `frontend/src/utils/` directory
- [ ] Create `frontend/tests/` directory structure
- [ ] Create `frontend/tests/browser/` directory
- [ ] Create `frontend/tests/helpers/` directory

#### 1.4 Configure Environment Variables
- [ ] Create `frontend/.env.example` with `REACT_APP_API_URL`
- [ ] Create `frontend/.env` for local development
- [ ] Set `REACT_APP_API_URL` to local API: `http://localhost:8080/v1`
- [ ] Document environment variable usage in README

---

### 2. API Client Setup

#### 2.1 Create API Service
- [ ] Create `frontend/src/services/api.js`
- [ ] Set up Axios instance with base URL from environment variable
- [ ] Configure default headers: `Content-Type: application/json`
- [ ] Implement request interceptor to add API key from localStorage
- [ ] Implement request interceptor to add X-Request-ID header (UUID v4)
- [ ] Implement response interceptor for error handling
- [ ] Test API client configuration

#### 2.2 Implement API Methods
- [ ] Implement `createEvent(data)` - POST /v1/events
- [ ] Implement `getInbox(params)` - GET /v1/inbox (with pagination params)
- [ ] Implement `getEvent(eventId)` - GET /v1/events/{id}
- [ ] Implement `acknowledgeEvent(eventId)` - POST /v1/events/{id}/ack
- [ ] Implement `deleteEvent(eventId)` - DELETE /v1/events/{id}
- [ ] Implement `healthCheck()` - GET /v1/health
- [ ] Add error handling for all methods
- [ ] Test all API methods with real API (local or production)

#### 2.3 Error Handling
- [ ] Create error handling utility functions
- [ ] Handle 401 Unauthorized (invalid API key)
- [ ] Handle 400/422 Validation errors
- [ ] Handle 404 Not Found errors
- [ ] Handle 409 Conflict errors
- [ ] Handle 500 Internal Server errors
- [ ] Format error messages for user display
- [ ] Test error handling with various error scenarios

---

### 3. Layout Components

#### 3.1 Create Header Component
- [ ] Create `frontend/src/components/Layout/Header.jsx`
- [ ] Add Material-UI AppBar component
- [ ] Add API key input field with TextField
- [ ] Add API key validation indicator (icon/color)
- [ ] Add "Clear" button for API key
- [ ] Store API key in localStorage on change
- [ ] Load API key from localStorage on mount
- [ ] Add title/logo area
- [ ] Test Header component renders correctly

#### 3.2 Create Sidebar Component
- [ ] Create `frontend/src/components/Layout/Sidebar.jsx`
- [ ] Add Material-UI Drawer component
- [ ] Add navigation menu items:
  - Send Event
  - Inbox
  - Statistics
- [ ] Use React Router Link components
- [ ] Add active route highlighting
- [ ] Make sidebar responsive (collapsible on mobile)
- [ ] Test Sidebar navigation works

#### 3.3 Create Layout Wrapper
- [ ] Create `frontend/src/components/Layout/Layout.jsx`
- [ ] Combine Header and Sidebar components
- [ ] Add main content area with Material-UI Container
- [ ] Set up responsive layout with Material-UI Grid
- [ ] Add theme provider wrapper
- [ ] Test Layout component structure

#### 3.4 Configure Material-UI Theme
- [ ] Create theme configuration file
- [ ] Set up light theme (default)
- [ ] Configure color palette
- [ ] Set up responsive breakpoints
- [ ] Configure typography
- [ ] Configure spacing
- [ ] Wrap app with ThemeProvider
- [ ] Test theme applies correctly

---

### 4. Send Event Page

#### 4.1 Create EventForm Component
- [ ] Create `frontend/src/components/EventForm/EventForm.jsx`
- [ ] Add form with Material-UI components:
  - Source (TextField, required)
  - Event Type (TextField, required)
  - Payload (JSON editor, required)
  - Correlation ID (TextField, optional)
  - Priority (Select dropdown: low/normal/high, optional)
- [ ] Add form validation:
  - Required field validation
  - JSON payload validation
  - Source/event_type max length (100 chars)
- [ ] Add submit button
- [ ] Add clear/reset button
- [ ] Test form renders correctly

#### 4.2 Integrate JSON Editor
- [ ] Install and configure JSON editor library
- [ ] Add syntax highlighting
- [ ] Add JSON validation
- [ ] Display validation errors
- [ ] Add format/beautify button (optional)
- [ ] Test JSON editor functionality

#### 4.3 Integrate with API
- [ ] Connect form to `createEvent` API method
- [ ] Handle form submission
- [ ] Show loading state during submission
- [ ] Show success notification on success
- [ ] Show error notification on failure
- [ ] Clear form after successful submission
- [ ] Test event creation flow

#### 4.4 Add Notifications
- [ ] Set up Material-UI Snackbar for notifications
- [ ] Show success message on event creation
- [ ] Show error message on failure
- [ ] Display API error details in notification
- [ ] Auto-dismiss notifications after timeout
- [ ] Test notification system

---

### 5. Inbox Page

#### 5.1 Create EventCard Component
- [ ] Create `frontend/src/components/Inbox/EventCard.jsx`
- [ ] Display event information:
  - Event ID (truncated)
  - Source
  - Event Type
  - Timestamp (formatted)
  - Payload preview (truncated)
- [ ] Add action buttons:
  - View Details
  - Acknowledge
  - Delete
- [ ] Use Material-UI Card component
- [ ] Add hover effects
- [ ] Test EventCard renders correctly

#### 5.2 Create InboxList Component
- [ ] Create `frontend/src/components/Inbox/InboxList.jsx`
- [ ] Fetch inbox data using React Query
- [ ] Display list of EventCard components
- [ ] Add loading state (skeleton/spinner)
- [ ] Add empty state (no events message)
- [ ] Add error state (error message)
- [ ] Test InboxList renders correctly

#### 5.3 Add Pagination
- [ ] Add pagination controls (Previous/Next buttons)
- [ ] Add limit selector (10, 25, 50, 100)
- [ ] Implement cursor-based pagination
- [ ] Store pagination state in React Query
- [ ] Handle pagination navigation
- [ ] Display current page info
- [ ] Test pagination works correctly

#### 5.4 Add Filtering
- [ ] Add filter inputs (Source, Event Type)
- [ ] Implement filter state management
- [ ] Apply filters to API query
- [ ] Reset filters button
- [ ] Update React Query on filter change
- [ ] Test filtering works correctly

#### 5.5 Add Auto-Refresh
- [ ] Set up auto-refresh interval (30 seconds)
- [ ] Use React Query refetch interval
- [ ] Add manual refresh button
- [ ] Pause auto-refresh when user is interacting
- [ ] Show last updated timestamp
- [ ] Test auto-refresh functionality

#### 5.6 Add Actions (Acknowledge/Delete)
- [ ] Implement acknowledge action
- [ ] Implement delete action
- [ ] Show confirmation dialog for delete
- [ ] Update React Query cache after actions
- [ ] Show success/error notifications
- [ ] Refresh inbox after action
- [ ] Test acknowledge and delete flows

---

### 6. Event Details Page

#### 6.1 Create EventDetails Component
- [ ] Create `frontend/src/components/EventDetails/EventDetails.jsx`
- [ ] Fetch event data using React Query
- [ ] Display full event information:
  - Event ID
  - Source
  - Event Type
  - Status badge
  - Created timestamp
  - Acknowledged timestamp (if applicable)
  - Metadata
- [ ] Add loading state
- [ ] Add error state (event not found)
- [ ] Test EventDetails renders correctly

#### 6.2 Add JSON Viewer
- [ ] Integrate JSON viewer library
- [ ] Display formatted payload with syntax highlighting
- [ ] Add expand/collapse functionality
- [ ] Add copy payload button
- [ ] Show copy confirmation
- [ ] Test JSON viewer functionality

#### 6.3 Add Actions
- [ ] Add acknowledge button (if status is pending)
- [ ] Add delete button
- [ ] Show confirmation dialog for delete
- [ ] Handle action success/error
- [ ] Navigate back to inbox after acknowledge/delete
- [ ] Update React Query cache
- [ ] Test action buttons work correctly

#### 6.4 Add Copy Functionality
- [ ] Add copy event ID button
- [ ] Add copy payload button
- [ ] Use browser Clipboard API
- [ ] Show copy confirmation toast
- [ ] Handle copy errors
- [ ] Test copy functionality

---

### 7. Statistics Page

#### 7.1 Create Statistics Component
- [ ] Create `frontend/src/components/Statistics/Statistics.jsx`
- [ ] Design statistics layout
- [ ] Add loading state
- [ ] Add error state
- [ ] Test Statistics component renders

#### 7.2 Implement Statistics Queries
- [ ] Determine statistics data source (API or client-side calculation)
- [ ] If API doesn't provide stats, implement client-side aggregation:
  - Fetch all events (with pagination)
  - Calculate statistics in frontend
- [ ] If API provides stats endpoint, create API method
- [ ] Set up React Query for statistics
- [ ] Test statistics data fetching

#### 7.3 Add Statistics Display
- [ ] Display total events count
- [ ] Display pending events count
- [ ] Display acknowledged events count
- [ ] Add time range selector (last hour, day, week)
- [ ] Filter statistics by time range
- [ ] Test statistics display

#### 7.4 Add Charts (Optional)
- [ ] Install chart library (recharts or chart.js)
- [ ] Create events by source chart (bar chart)
- [ ] Create events by type chart (bar chart)
- [ ] Create recent activity timeline (line chart)
- [ ] Make charts responsive
- [ ] Test charts render correctly

#### 7.5 Add Auto-Refresh
- [ ] Set up auto-refresh for statistics (every 30 seconds)
- [ ] Add manual refresh button
- [ ] Update React Query cache
- [ ] Test auto-refresh works

---

### 8. API Key Management

#### 8.1 Create useApiKey Hook
- [ ] Create `frontend/src/hooks/useApiKey.js`
- [ ] Implement API key state management
- [ ] Load API key from localStorage on mount
- [ ] Save API key to localStorage on change
- [ ] Validate API key format (optional)
- [ ] Test useApiKey hook

#### 8.2 Add API Key Validation
- [ ] Implement API key validation function
- [ ] Call health check endpoint to validate API key
- [ ] Show validation status (valid/invalid/checking)
- [ ] Update validation status indicator
- [ ] Handle validation errors
- [ ] Test API key validation

#### 8.3 Integrate with Header
- [ ] Connect Header to useApiKey hook
- [ ] Update validation status on API key change
- [ ] Show validation indicator in Header
- [ ] Disable API calls if API key is invalid
- [ ] Test API key integration

---

### 9. React Query Setup

#### 9.1 Configure Query Client
- [ ] Create QueryClient instance
- [ ] Configure default options:
  - `refetchOnWindowFocus: false`
  - `retry: 1`
- [ ] Wrap app with QueryClientProvider
- [ ] Test React Query setup

#### 9.2 Create Custom Hooks
- [ ] Create `frontend/src/hooks/useEvents.js`
- [ ] Implement `useCreateEvent` mutation
- [ ] Implement `useInbox` query
- [ ] Implement `useEvent` query
- [ ] Implement `useAcknowledgeEvent` mutation
- [ ] Implement `useDeleteEvent` mutation
- [ ] Test all custom hooks

#### 9.3 Configure Cache Management
- [ ] Set up cache invalidation after mutations
- [ ] Configure cache timeouts
- [ ] Handle cache updates for optimistic updates (optional)
- [ ] Test cache management

---

### 10. Routing Setup

#### 10.1 Configure React Router
- [ ] Install and configure React Router v6
- [ ] Set up routes:
  - `/` - Redirect to `/send-event` or `/inbox`
  - `/send-event` - Send Event page
  - `/inbox` - Inbox page
  - `/events/:eventId` - Event Details page
  - `/statistics` - Statistics page
- [ ] Add route protection (optional - check API key)
- [ ] Test routing works correctly

#### 10.2 Add Navigation
- [ ] Connect Sidebar to React Router
- [ ] Add active route highlighting
- [ ] Add navigation from EventCard to EventDetails
- [ ] Add back navigation from EventDetails
- [ ] Test navigation flows

---

### 11. Error Handling & Notifications

#### 11.1 Create Error Boundary
- [ ] Create Error Boundary component
- [ ] Wrap app with Error Boundary
- [ ] Display user-friendly error message
- [ ] Add error reporting (optional)
- [ ] Test Error Boundary catches errors

#### 11.2 Set Up Notification System
- [ ] Create notification context/provider
- [ ] Implement success notifications
- [ ] Implement error notifications
- [ ] Implement info notifications
- [ ] Add auto-dismiss functionality
- [ ] Test notification system

#### 11.3 Handle API Errors
- [ ] Format API errors for display
- [ ] Show error messages in notifications
- [ ] Handle network errors
- [ ] Handle timeout errors
- [ ] Handle validation errors with field details
- [ ] Test error handling

#### 11.4 Add Loading States
- [ ] Add loading spinners for async operations
- [ ] Add skeleton loaders for data fetching
- [ ] Disable buttons during loading
- [ ] Show loading indicators in appropriate places
- [ ] Test loading states

---

### 12. Responsive Design

#### 12.1 Test Mobile Layout
- [ ] Test Header on mobile devices
- [ ] Test Sidebar on mobile (should be collapsible)
- [ ] Test EventForm on mobile
- [ ] Test InboxList on mobile
- [ ] Test EventDetails on mobile
- [ ] Test Statistics on mobile
- [ ] Fix any mobile layout issues

#### 12.2 Test Tablet Layout
- [ ] Test all pages on tablet sizes
- [ ] Adjust breakpoints if needed
- [ ] Fix any tablet layout issues

#### 12.3 Test Desktop Layout
- [ ] Test all pages on desktop sizes
- [ ] Ensure proper spacing and alignment
- [ ] Fix any desktop layout issues

---

### 13. Automated Testing Setup

#### 13.1 Set Up Cursor Browser Tests
- [ ] Create `frontend/tests/browser/` directory
- [ ] Create test helper utilities in `frontend/tests/helpers/browser_helpers.js`
- [ ] Document Cursor browser extension MCP usage
- [ ] Create test structure for browser tests
- [ ] Test Cursor browser extension connection

#### 13.2 Create Cursor Browser Test: Send Event
- [ ] Create `frontend/tests/browser/test_send_event.js`
- [ ] Test: Navigate to send event page
- [ ] Test: Fill in form fields (source, event_type, payload)
- [ ] Test: Submit form
- [ ] Test: Verify success message appears
- [ ] Test: Verify form clears after success
- [ ] Test: Verify event appears in inbox
- [ ] Run test and verify it passes

#### 13.3 Create Cursor Browser Test: Inbox
- [ ] Create `frontend/tests/browser/test_inbox.js`
- [ ] Test: Navigate to inbox page
- [ ] Test: Verify events are displayed
- [ ] Test: Test pagination (next/previous)
- [ ] Test: Test filtering (source, event_type)
- [ ] Test: Verify event cards render correctly
- [ ] Test: Test refresh button
- [ ] Run test and verify it passes

#### 13.4 Create Cursor Browser Test: Event Details
- [ ] Create `frontend/tests/browser/test_event_details.js`
- [ ] Test: Click on event card
- [ ] Test: Verify event details page loads
- [ ] Test: Verify all event data displayed
- [ ] Test: Test acknowledge button
- [ ] Test: Test delete button
- [ ] Test: Verify navigation back to inbox
- [ ] Run test and verify it passes

#### 13.5 Create Cursor Browser Test: Full Workflow
- [ ] Create `frontend/tests/browser/test_full_workflow.js`
- [ ] Test: Complete end-to-end workflow:
  1. Create event via UI
  2. View in inbox
  3. View details
  4. Acknowledge event
  5. Verify removed from inbox
- [ ] Run test and verify it passes

#### 13.6 Create Cursor Browser Test: Statistics
- [ ] Create `frontend/tests/browser/test_statistics.js`
- [ ] Test: Navigate to statistics page
- [ ] Test: Verify statistics display
- [ ] Test: Test time range selector
- [ ] Test: Verify charts render (if implemented)
- [ ] Run test and verify it passes

#### 13.7 Set Up Playwright MCP Tests
- [ ] Create `frontend/tests/playwright/` directory
- [ ] Install Playwright MCP dependencies
- [ ] Create Playwright test configuration
- [ ] Create test helper utilities
- [ ] Test Playwright MCP connection

#### 13.8 Create Playwright MCP Tests: UI Components
- [ ] Create `frontend/tests/playwright/test_ui_components.js`
- [ ] Test: Form validation
- [ ] Test: Button clicks
- [ ] Test: Navigation
- [ ] Test: Error messages display
- [ ] Run tests and verify they pass

#### 13.9 Create Playwright MCP Tests: API Integration
- [ ] Create `frontend/tests/playwright/test_api_integration.js`
- [ ] Test: API calls from frontend
- [ ] Test: Request/response handling
- [ ] Test: Error handling in UI
- [ ] Test: API key authentication
- [ ] Run tests and verify they pass

#### 13.10 Create Playwright MCP Tests: User Flows
- [ ] Create `frontend/tests/playwright/test_user_flows.js`
- [ ] Test: Complete user workflows
- [ ] Test: All user interactions
- [ ] Test: State changes
- [ ] Run tests and verify they pass

#### 13.11 Create Test Automation Scripts
- [ ] Create `frontend/package.json` scripts:
  - `test:browser` - Run all browser tests
  - `test:cursor` - Run Cursor browser tests only
  - `test:playwright` - Run Playwright MCP tests only
- [ ] Create test setup script to start dev server
- [ ] Create test teardown script to stop dev server
- [ ] Ensure tests are fully automated (no manual intervention)
- [ ] Test all test scripts work correctly

---

### 14. Testing & Polish

#### 14.1 Run All Automated Tests
- [ ] Run Cursor browser tests
- [ ] Run Playwright MCP tests
- [ ] Fix any failing tests
- [ ] Verify all tests pass

#### 14.2 Manual Testing (Quick Verification)
- [ ] Test all pages load correctly
- [ ] Test all forms submit correctly
- [ ] Test all actions work (ack, delete)
- [ ] Test navigation flows
- [ ] Test error handling
- [ ] Test responsive design

#### 14.3 UX Improvements
- [ ] Improve loading states
- [ ] Improve error messages
- [ ] Add tooltips where helpful
- [ ] Improve button labels
- [ ] Improve form validation messages
- [ ] Add keyboard shortcuts (optional)

#### 14.4 Code Quality
- [ ] Review code for consistency
- [ ] Remove console.logs
- [ ] Add comments where needed
- [ ] Format code consistently
- [ ] Verify no linting errors

---

### 15. Deployment

#### 15.1 Build for Production
- [ ] Create production build: `npm run build`
- [ ] Verify build output in `build/` directory
- [ ] Test production build locally (serve static files)
- [ ] Verify environment variables set correctly
- [ ] Test API URL configuration

#### 15.2 Set Up S3 Bucket
- [ ] Create S3 bucket for frontend hosting
- [ ] Configure bucket for static website hosting
- [ ] Set up bucket policy for public read access
- [ ] Configure CORS if needed
- [ ] Test S3 bucket configuration

#### 15.3 Set Up CloudFront Distribution
- [ ] Create CloudFront distribution
- [ ] Configure origin (S3 bucket)
- [ ] Set up default root object (index.html)
- [ ] Configure error pages (404 -> index.html for SPA)
- [ ] Set up custom domain (optional)
- [ ] Test CloudFront distribution

#### 15.4 Deploy Frontend
- [ ] Upload build files to S3 bucket
- [ ] Invalidate CloudFront cache
- [ ] Verify deployment accessible via CloudFront URL
- [ ] Test all functionality in production
- [ ] Verify API URL points to production API Gateway

#### 15.5 Test Deployment
- [ ] Run automated tests against deployed frontend
- [ ] Test all pages load correctly
- [ ] Test API integration works
- [ ] Test responsive design
- [ ] Fix any deployment issues

#### 15.6 Update Documentation
- [ ] Update README with frontend deployment instructions
- [ ] Document environment variables
- [ ] Document build process
- [ ] Document deployment process
- [ ] Add frontend URL to project documentation

---

## Success Criteria Checklist

- [ ] React dashboard deployed and accessible
- [ ] Can send events via UI
- [ ] Can view inbox with events
- [ ] Can view event details
- [ ] Can acknowledge events
- [ ] Can delete events
- [ ] API key configuration works
- [ ] Statistics page functional
- [ ] Responsive design works
- [ ] Error handling works
- [ ] All API endpoints integrated
- [ ] Cursor browser tests pass (all UI workflows)
- [ ] Playwright MCP frontend tests pass
- [ ] All frontend tests automated (no manual testing required)
- [ ] Production deployment working

---

## Notes

### API Integration
- API Gateway URL: `https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod`
- Local API URL: `http://localhost:8080/v1`
- All API calls must include `X-API-Key` header
- All API calls should include `X-Request-ID` header (UUID v4)

### Testing Strategy
- Cursor browser tests: Full UI workflow testing using Cursor browser extension MCP
- Playwright MCP tests: UI component and API integration testing
- All tests must be fully automated
- Tests should start/stop dev server automatically
- No manual intervention required

### Deployment
- Frontend deployed to S3 + CloudFront
- Environment variable `REACT_APP_API_URL` set at build time
- CORS already configured in API Gateway (Phase 2)
- No additional CORS setup needed

### Known Limitations
- No real-time WebSocket updates (polling instead)
- No user authentication (uses API key)
- Basic statistics only (no advanced analytics)
- No bulk operations
- No event editing
- No export functionality

---

**Task List Status:** Ready for Implementation  
**Last Updated:** 2025-01-XX

