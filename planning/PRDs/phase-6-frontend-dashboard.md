# Phase 6: Frontend Dashboard - PRD

**Phase:** 6 of 6  
**Priority:** P2 (Nice to Have)  
**Estimated Duration:** 3-4 hours  
**Dependencies:** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5

---

## 1. Executive Summary

Phase 6 delivers a React-based web dashboard with Material-UI for testing and managing events. The dashboard provides a visual interface to send events, view the inbox, acknowledge/delete events, and view event details.

**Goal:** Functional web dashboard for testing and managing events.

---

## 2. Scope

### In Scope
- React application with Material-UI
- Event ingestion form
- Inbox viewer with real-time updates
- Event details view
- Acknowledge/delete actions
- Basic event statistics
- API key configuration
- Responsive design
- Error handling and notifications
- **Automated browser tests using Cursor browser extension**
- **Playwright MCP tests for frontend workflows**
- **E2E frontend tests (fully automated)**

### Out of Scope
- User authentication (uses API key)
- Advanced analytics (basic stats only)
- Real-time WebSocket updates (polling instead)
- Multi-tenant support
- Event editing
- Bulk operations

---

## 3. Functional Requirements

### 3.1 Dashboard Layout

**Main Components:**
- Header with API key input
- Navigation sidebar
- Main content area
- Event statistics panel

**Pages:**
1. **Send Event:** Form to create new events
2. **Inbox:** List of pending events
3. **Event Details:** View individual event details
4. **Statistics:** Basic event statistics

### 3.2 Send Event Page

**Form Fields:**
- Source (text input, required)
- Event Type (text input, required)
- Payload (JSON editor, required)
- Metadata (optional):
  - Correlation ID (text input)
  - Priority (dropdown: low/normal/high)

**Features:**
- JSON payload editor with syntax highlighting
- Form validation
- Success/error notifications
- Clear form after successful submission

**Example:**
```json
{
  "source": "my-app",
  "event_type": "user.created",
  "payload": {
    "user_id": "123",
    "name": "John Doe"
  },
  "metadata": {
    "correlation_id": "corr-123",
    "priority": "normal"
  }
}
```

### 3.3 Inbox Page

**Features:**
- List of pending events
- Pagination support
- Filter by source and event_type
- Refresh button
- Auto-refresh (every 30 seconds)
- Event cards with key information
- Actions: View Details, Acknowledge, Delete

**Event Card Display:**
- Event ID (truncated)
- Source
- Event Type
- Timestamp
- Payload preview
- Quick actions

**Pagination:**
- Show total count
- Previous/Next buttons
- Cursor-based pagination
- Limit selector (10, 25, 50, 100)

### 3.4 Event Details Page

**Display:**
- Full event information
- Formatted JSON payload
- Status badge
- Timestamps (created, acknowledged)
- Metadata display
- Actions: Acknowledge, Delete

**Features:**
- Copy event ID button
- Copy payload button
- JSON syntax highlighting
- Responsive layout

### 3.5 Statistics Page

**Basic Statistics:**
- Total events (all time)
- Pending events count
- Acknowledged events count
- Events by source (chart)
- Events by type (chart)
- Recent activity timeline

**Features:**
- Auto-refresh statistics
- Simple charts (bar/line)
- Time range selector (last hour, day, week)

### 3.6 API Key Configuration

**Features:**
- API key input field in header
- Store in localStorage
- Validation
- Clear button
- Status indicator (valid/invalid)

---

## 4. Technical Requirements

### 4.1 Technology Stack

**Frontend Framework:**
- React 18+
- Material-UI (MUI) v5
- React Router v6
- Axios for HTTP client
- React Query for state management

**Additional Libraries:**
- `react-json-view` or `react-json-pretty` (JSON viewer)
- `date-fns` (date formatting)
- `recharts` or `chart.js` (charts, optional)

### 4.2 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Header.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── Layout.jsx
│   │   ├── EventForm/
│   │   │   └── EventForm.jsx
│   │   ├── Inbox/
│   │   │   ├── InboxList.jsx
│   │   │   └── EventCard.jsx
│   │   ├── EventDetails/
│   │   │   └── EventDetails.jsx
│   │   └── Statistics/
│   │       └── Statistics.jsx
│   ├── services/
│   │   └── api.js          # API client
│   ├── hooks/
│   │   ├── useApiKey.js
│   │   └── useEvents.js
│   ├── utils/
│   │   └── formatters.js
│   ├── App.jsx
│   └── index.jsx
├── public/
├── package.json
└── README.md
```

### 4.3 API Integration

**API Client:**
```javascript
// src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'https://api.example.com/v1',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add API key and request ID to requests
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('apiKey');
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  // Generate request ID for tracking
  config.headers['X-Request-ID'] = crypto.randomUUID();
  return config;
});

export default api;
```

**API Methods:**
- `createEvent(data)` - POST /v1/events
- `getInbox(params)` - GET /v1/inbox
- `getEvent(eventId)` - GET /v1/events/{id}
- `acknowledgeEvent(eventId)` - POST /v1/events/{id}/ack
- `deleteEvent(eventId)` - DELETE /v1/events/{id}
- `healthCheck()` - GET /v1/health

### 4.4 State Management

**React Query Setup:**
```javascript
import { QueryClient, QueryClientProvider } from 'react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});
```

**Custom Hooks:**
- `useEvents()` - Manage event queries
- `useApiKey()` - Manage API key
- `useInbox()` - Manage inbox queries

### 4.5 Styling

**Material-UI Theme:**
- Light theme (default)
- Responsive breakpoints
- Custom color scheme
- Consistent spacing

**Components:**
- Use MUI components throughout
- Custom styling where needed
- Responsive design
- Mobile-friendly

---

## 5. Implementation Steps

1. **Project Setup**
   - Create React app
   - Install dependencies
   - Set up project structure
   - Configure routing

2. **API Client**
   - Create API service
   - Set up axios interceptors
   - Create API methods
   - Add error handling

3. **Layout Components**
   - Create Header component
   - Create Sidebar component
   - Create Layout wrapper
   - Add navigation

4. **Send Event Page**
   - Create EventForm component
   - Add form validation
   - Integrate with API
   - Add success/error handling

5. **Inbox Page**
   - Create InboxList component
   - Create EventCard component
   - Add pagination
   - Add filtering
   - Add auto-refresh

6. **Event Details Page**
   - Create EventDetails component
   - Add JSON viewer
   - Add actions (ack/delete)
   - Add copy functionality

7. **Statistics Page**
   - Create Statistics component
   - Add charts
   - Add statistics queries
   - Add time range selector

8. **API Key Management**
   - Create API key input
   - Add localStorage persistence
   - Add validation
   - Add status indicator

9. **Error Handling**
   - Add error boundaries
   - Add error notifications
   - Handle API errors
   - Add loading states

10. **Automated Testing**
    - Create Cursor browser tests for all UI workflows
    - Create Playwright MCP tests for frontend
    - Test all features automatically
    - No manual testing required

11. **Testing & Polish**
    - Run automated tests
    - Fix bugs found by tests
    - Improve UX
    - Add loading states
    - Improve error messages

12. **Deployment**
    - Build for production
    - Deploy to S3 + CloudFront
    - Configure CORS
    - Test deployment with automated tests

---

## 6. Success Criteria

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
- [ ] **Cursor browser tests pass (all UI workflows)**
- [ ] **Playwright MCP frontend tests pass**
- [ ] **All frontend tests automated (no manual testing)**

---

## 7. UI/UX Requirements

### 7.1 Design Principles

**Material Design:**
- Follow Material Design guidelines
- Use MUI components
- Consistent spacing and typography
- Clear visual hierarchy

**User Experience:**
- Intuitive navigation
- Clear feedback on actions
- Loading states
- Error messages
- Success confirmations

### 7.2 Key Screens

**Send Event Screen:**
- Clean form layout
- JSON editor with syntax highlighting
- Clear submit button
- Success message

**Inbox Screen:**
- Card-based layout
- Easy-to-scan information
- Quick actions
- Pagination controls

**Event Details Screen:**
- Clear information hierarchy
- Readable JSON display
- Prominent action buttons
- Copy functionality

**Statistics Screen:**
- Visual charts
- Clear metrics
- Time range selector
- Auto-refresh

---

## 8. Frontend Testing

### 8.1 Cursor Browser Tests

**Purpose:** Automated browser tests using Cursor's browser extension for full UI workflow testing.

**Test Structure:**
```
frontend/
├── tests/
│   ├── browser/
│   │   ├── test_send_event.js      # Test event creation UI
│   │   ├── test_inbox.js           # Test inbox viewing
│   │   ├── test_event_details.js   # Test event details page
│   │   ├── test_acknowledge.js     # Test acknowledgment flow
│   │   └── test_statistics.js      # Test statistics page
│   └── helpers/
│       └── browser_helpers.js      # Helper functions
```

**Cursor Browser Test Scenarios:**
1. **Event Creation Flow:**
   - Navigate to send event page
   - Fill in form fields (source, event_type, payload)
   - Submit form
   - Verify success message
   - Verify event appears in inbox

2. **Inbox Viewing:**
   - Navigate to inbox page
   - Verify events are displayed
   - Test pagination
   - Test filtering
   - Verify event cards render correctly

3. **Event Details:**
   - Click on event card
   - Verify event details page loads
   - Verify all event data displayed
   - Test acknowledge button
   - Test delete button

4. **Full Workflow:**
   - Create event via UI
   - View in inbox
   - View details
   - Acknowledge event
   - Verify removed from inbox

**Cursor Browser Test Implementation:**
- Use Cursor browser extension MCP tools
- Tests run automatically
- No manual intervention required
- AI can execute all tests

### 8.2 Playwright MCP Frontend Tests

**Purpose:** Automated frontend tests using Playwright MCP for UI interaction testing.

**Playwright MCP Test Scenarios:**
1. **UI Component Tests:**
   - Test form validation
   - Test button clicks
   - Test navigation
   - Test error messages

2. **API Integration Tests:**
   - Test API calls from frontend
   - Verify request/response handling
   - Test error handling in UI

3. **User Flow Tests:**
   - Complete user workflows
   - Test all user interactions
   - Verify state changes

### 8.3 Test Automation

**Running Frontend Tests:**
```bash
# Run all frontend tests (Cursor browser + Playwright MCP)
cd frontend
npm run test:browser

# Run Cursor browser tests only
npm run test:cursor

# Run Playwright MCP tests only
npm run test:playwright
```

**Test Requirements:**
- All tests must be fully automated
- Tests should start frontend dev server automatically
- Tests should clean up after themselves
- No manual intervention required
- AI can run with single command

**Test Dependencies:**
- `@playwright/test` (for Playwright MCP)
- Cursor browser extension MCP server
- Test server setup (start React dev server)

**Cursor Browser Test Implementation:**
- Use Cursor browser extension MCP tools
- Navigate to frontend URL
- Interact with UI elements (click, type, etc.)
- Verify UI state and responses
- Test complete user workflows
- Fully automated - AI can execute all tests
- Example workflow:
  1. Navigate to dashboard
  2. Fill event creation form
  3. Submit form
  4. Verify success message
  5. Navigate to inbox
  6. Verify event appears
  7. Click event to view details
  8. Acknowledge event
  9. Verify event removed from inbox

## 9. Deployment

### 9.1 Build Process

**Build Command:**
```bash
npm run build
```

**Build Output:**
- Static files in `build/` directory
- Optimized for production
- Minified JavaScript/CSS

### 9.2 AWS Deployment

**S3 + CloudFront:**
- Upload build to S3 bucket
- Configure CloudFront distribution
- Set up custom domain (optional)
- Configure CORS

**Environment Variables:**
- `REACT_APP_API_URL`: API Gateway URL
- Set in build time

### 9.3 Configuration

**API URL:**
- Configurable via environment variable
- Default to API Gateway URL
- Can be changed in build

**CORS:**
- Already configured in API Gateway (Phase 2)
- No additional CORS setup needed

---

## 10. Known Limitations (Phase 6)

- No real-time WebSocket updates (polling instead)
- No user authentication (uses API key)
- Basic statistics only (no advanced analytics)
- No bulk operations
- No event editing
- No export functionality

---

## 11. Next Steps

After Phase 6 completion:
- Project complete!
- Gather user feedback
- Plan future enhancements
- Consider additional features

---

**Phase Status:** Not Started  
**Completion Date:** TBD

