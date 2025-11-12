import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Paper,
  Pagination,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import EventCard from './EventCard';
import { useInbox } from '../../hooks/useEvents';
import { useAcknowledgeEvent, useDeleteEvent } from '../../hooks/useEvents';
import { useNotification } from '../../contexts/NotificationContext';

const InboxList = () => {
  const { showSuccess, showError } = useNotification();
  const [limit, setLimit] = useState(10);
  const [cursor, setCursor] = useState(null);
  const [sourceFilter, setSourceFilter] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');

  const { data, isLoading, error, refetch } = useInbox({
    limit,
    cursor,
    source: sourceFilter || undefined,
    event_type: eventTypeFilter || undefined,
  });

  const acknowledgeMutation = useAcknowledgeEvent();
  const deleteMutation = useDeleteEvent();

  const handleAcknowledge = async (eventId) => {
    try {
      await acknowledgeMutation.mutateAsync(eventId);
      showSuccess('Event acknowledged successfully');
    } catch (error) {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to acknowledge event';
      showError(errorMessage);
    }
  };

  const handleDelete = async (eventId) => {
    if (!window.confirm('Are you sure you want to delete this event?')) {
      return;
    }
    try {
      await deleteMutation.mutateAsync(eventId);
      showSuccess('Event deleted successfully');
    } catch (error) {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to delete event';
      showError(errorMessage);
    }
  };

  const handleNext = () => {
    if (data?.data?.next_cursor) {
      setCursor(data.data.next_cursor);
    }
  };

  const handlePrevious = () => {
    // For previous, we'd need to maintain cursor history
    // For simplicity, reset to first page
    setCursor(null);
  };

  const handleFilterChange = () => {
    // Reset cursor when filters change
    setCursor(null);
  };

  const handleResetFilters = () => {
    setSourceFilter('');
    setEventTypeFilter('');
    setCursor(null);
  };

  if (isLoading && !data) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error.formattedError?.message || error.message || 'Failed to load inbox'}
      </Alert>
    );
  }

  const events = data?.data?.events || [];
  const hasNext = !!data?.data?.next_cursor;
  const hasPrevious = cursor !== null;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexShrink: 0 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Inbox</Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
          disabled={isLoading}
        >
          Refresh
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 2, flexShrink: 0 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            label="Filter by Source"
            value={sourceFilter}
            onChange={(e) => {
              setSourceFilter(e.target.value);
              handleFilterChange();
            }}
            size="small"
            sx={{ minWidth: 200 }}
          />
          <TextField
            label="Filter by Event Type"
            value={eventTypeFilter}
            onChange={(e) => {
              setEventTypeFilter(e.target.value);
              handleFilterChange();
            }}
            size="small"
            sx={{ minWidth: 200 }}
          />
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Limit</InputLabel>
            <Select
              value={limit}
              onChange={(e) => {
                setLimit(e.target.value);
                setCursor(null);
              }}
              label="Limit"
            >
              <MenuItem value={10}>10</MenuItem>
              <MenuItem value={25}>25</MenuItem>
              <MenuItem value={50}>50</MenuItem>
              <MenuItem value={100}>100</MenuItem>
            </Select>
          </FormControl>
          <Button variant="outlined" onClick={handleResetFilters}>
            Reset Filters
          </Button>
        </Box>
      </Paper>

      <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
        {events.length === 0 ? (
          <Alert severity="info">No events found</Alert>
        ) : (
          <>
            {events.map((event) => (
              <EventCard
                key={event.event_id}
                event={event}
                onAcknowledge={handleAcknowledge}
                onDelete={handleDelete}
              />
            ))}
          </>
        )}
      </Box>

      {events.length > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2, pt: 2, flexShrink: 0, borderTop: '1px solid', borderColor: 'divider' }}>
          <Button
            variant="outlined"
            onClick={handlePrevious}
            disabled={!hasPrevious || isLoading}
          >
            Previous
          </Button>
          <Button
            variant="outlined"
            onClick={handleNext}
            disabled={!hasNext || isLoading}
          >
            Next
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default InboxList;

