# Zapier Triggers API - Frontend Dashboard

React-based web dashboard for testing and managing events in the Zapier Triggers API.

## Features

- **Send Events**: Create new events via a user-friendly form with JSON editor
- **Inbox Viewer**: View pending events with pagination and filtering
- **Event Details**: View full event details with JSON viewer
- **Statistics**: View event statistics with charts
- **API Key Management**: Configure and validate API keys
- **Responsive Design**: Works on mobile, tablet, and desktop

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API running (local or production)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The app will be available at `http://localhost:3000`

### Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
# Local development
REACT_APP_API_URL=http://localhost:8080/v1

# Production
REACT_APP_API_URL=https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod
```

### Building for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/        # React components
│   │   ├── Layout/       # Header, Sidebar, Layout
│   │   ├── EventForm/    # Event creation form
│   │   ├── Inbox/        # Inbox list and event cards
│   │   ├── EventDetails/ # Event details page
│   │   └── Statistics/   # Statistics page
│   ├── services/         # API client
│   ├── hooks/            # Custom React hooks
│   ├── utils/            # Utility functions
│   ├── contexts/         # React contexts
│   ├── App.jsx           # Main app component
│   └── main.jsx          # Entry point
├── tests/                # Test files
└── package.json
```

## Usage

1. **Configure API Key**: Enter your API key in the header. The key will be validated automatically.
2. **Send Events**: Navigate to "Send Event" page and fill in the form.
3. **View Inbox**: Navigate to "Inbox" to see pending events.
4. **View Details**: Click "View Details" on any event card.
5. **Statistics**: Navigate to "Statistics" to see event analytics.

## Technologies

- **React 19** - UI framework
- **Material-UI (MUI) v5** - Component library
- **React Router v6** - Routing
- **Axios** - HTTP client
- **React Query** - State management and data fetching
- **Recharts** - Charts
- **date-fns** - Date formatting
- **@uiw/react-json-view** - JSON viewer

## Development

### Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm run test:browser` - Run browser tests (when implemented)
- `npm run test:cursor` - Run Cursor browser tests (when implemented)
- `npm run test:playwright` - Run Playwright MCP tests (when implemented)

## Deployment

The frontend is deployed to AWS S3 + CloudFront. See deployment documentation for details.
