import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout/Layout';
import EventForm from './components/EventForm/EventForm';
import InboxList from './components/Inbox/InboxList';
import EventDetails from './components/EventDetails/EventDetails';
import Statistics from './components/Statistics/Statistics';
import WebhookList from './components/Webhooks/WebhookList';
import ErrorBoundary from './components/ErrorBoundary';
import { NotificationProvider } from './contexts/NotificationContext';
import theme from './theme';

// Create QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <NotificationProvider>
            <BrowserRouter>
              <Layout>
                <Routes>
                  <Route path="/" element={<Navigate to="/inbox" replace />} />
                  <Route path="/send-event" element={<EventForm />} />
                  <Route path="/inbox" element={<InboxList />} />
                  <Route path="/webhooks" element={<WebhookList />} />
                  <Route path="/events/:eventId" element={<EventDetails />} />
                  <Route path="/statistics" element={<Statistics />} />
                </Routes>
              </Layout>
            </BrowserRouter>
          </NotificationProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
