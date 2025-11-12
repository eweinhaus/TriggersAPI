import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Chip,
  IconButton,
  Tooltip,
  ToggleButton,
  ToggleButtonGroup,
  Checkbox,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import ViewListIcon from '@mui/icons-material/ViewList';
import ViewModuleIcon from '@mui/icons-material/ViewModule';
import SearchIcon from '@mui/icons-material/Search';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import EventCard from './EventCard';
import { useInbox } from '../../hooks/useEvents';
import { useAcknowledgeEvent, useDeleteEvent } from '../../hooks/useEvents';
import { useNotification } from '../../contexts/NotificationContext';
import { formatRelativeTime, capitalize } from '../../utils/formatters';

const InboxList = () => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();
  const [limit, setLimit] = useState(25);
  const [cursor, setCursor] = useState(null);
  const [sourceFilter, setSourceFilter] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'card'
  const [selectedEvents, setSelectedEvents] = useState(new Set());

  const { data, isLoading, error, refetch } = useInbox({
    limit,
    cursor,
    source: sourceFilter || undefined,
    event_type: eventTypeFilter || undefined,
    priority: priorityFilter || undefined,
  });

  const acknowledgeMutation = useAcknowledgeEvent();
  const deleteMutation = useDeleteEvent();

  // Calculate summary stats
  const stats = useMemo(() => {
    const events = data?.data?.events || [];
    const total = events.length;
    const pending = events.filter((e) => e.status === 'pending').length;
    const acknowledged = events.filter((e) => e.status === 'acknowledged').length;
    
    // Count by source
    const sourceCounts = {};
    events.forEach((e) => {
      sourceCounts[e.source] = (sourceCounts[e.source] || 0) + 1;
    });
    
    // Count by priority
    const priorityCounts = { low: 0, normal: 0, high: 0 };
    events.forEach((e) => {
      const priority = e.metadata?.priority || 'normal';
      if (priorityCounts[priority] !== undefined) {
        priorityCounts[priority]++;
      }
    });

    return { total, pending, acknowledged, sourceCounts, priorityCounts };
  }, [data]);

  // Filter events by search query
  const filteredEvents = useMemo(() => {
    const events = data?.data?.events || [];
    if (!searchQuery.trim()) return events;
    
    const query = searchQuery.toLowerCase();
    return events.filter((event) => {
      return (
        event.event_id.toLowerCase().includes(query) ||
        event.source.toLowerCase().includes(query) ||
        event.event_type.toLowerCase().includes(query) ||
        JSON.stringify(event.payload).toLowerCase().includes(query)
      );
    });
  }, [data, searchQuery]);

  const handleAcknowledge = async (eventId) => {
    try {
      await acknowledgeMutation.mutateAsync(eventId);
      showSuccess('Event acknowledged successfully');
      setSelectedEvents((prev) => {
        const next = new Set(prev);
        next.delete(eventId);
        return next;
      });
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
      setSelectedEvents((prev) => {
        const next = new Set(prev);
        next.delete(eventId);
        return next;
      });
    } catch (error) {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to delete event';
      showError(errorMessage);
    }
  };

  const handleBulkAcknowledge = async () => {
    if (selectedEvents.size === 0) return;
    
    const eventIds = Array.from(selectedEvents);
    const pendingEvents = eventIds.filter((id) => {
      const event = filteredEvents.find((e) => e.event_id === id);
      return event?.status === 'pending';
    });

    if (pendingEvents.length === 0) {
      showError('No pending events selected');
      return;
    }

    try {
      await Promise.all(pendingEvents.map((id) => acknowledgeMutation.mutateAsync(id)));
      showSuccess(`Acknowledged ${pendingEvents.length} event(s) successfully`);
      setSelectedEvents(new Set());
    } catch (error) {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to acknowledge events';
      showError(errorMessage);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedEvents.size === 0) return;
    
    if (!window.confirm(`Are you sure you want to delete ${selectedEvents.size} event(s)?`)) {
      return;
    }

    try {
      await Promise.all(Array.from(selectedEvents).map((id) => deleteMutation.mutateAsync(id)));
      showSuccess(`Deleted ${selectedEvents.size} event(s) successfully`);
      setSelectedEvents(new Set());
    } catch (error) {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to delete events';
      showError(errorMessage);
    }
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedEvents(new Set(filteredEvents.map((e) => e.event_id)));
    } else {
      setSelectedEvents(new Set());
    }
  };

  const handleSelectEvent = (eventId, checked) => {
    setSelectedEvents((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(eventId);
      } else {
        next.delete(eventId);
      }
      return next;
    });
  };

  const handleNext = () => {
    if (data?.data?.next_cursor) {
      setCursor(data.data.next_cursor);
    }
  };

  const handlePrevious = () => {
    setCursor(null);
  };

  const handleFilterChange = () => {
    setCursor(null);
    setSelectedEvents(new Set());
  };

  const handleResetFilters = () => {
    setSourceFilter('');
    setEventTypeFilter('');
    setPriorityFilter('');
    setSearchQuery('');
    setCursor(null);
    setSelectedEvents(new Set());
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

  const events = filteredEvents;
  const hasNext = !!data?.data?.next_cursor;
  const hasPrevious = cursor !== null;
  const allSelected = events.length > 0 && selectedEvents.size === events.length;
  const someSelected = selectedEvents.size > 0 && selectedEvents.size < events.length;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', gap: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Inbox
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
            size="small"
          >
            <ToggleButton value="table">
              <ViewListIcon fontSize="small" />
            </ToggleButton>
            <ToggleButton value="card">
              <ViewModuleIcon fontSize="small" />
            </ToggleButton>
          </ToggleButtonGroup>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            disabled={isLoading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Summary Stats */}
      <Box sx={{ display: 'flex', gap: 2, flexShrink: 0 }}>
        <Card sx={{ flex: 1, p: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            Total Events
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            {stats.total}
          </Typography>
        </Card>
        <Card sx={{ flex: 1, p: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            Pending
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 600, color: 'warning.main' }}>
            {stats.pending}
          </Typography>
        </Card>
        <Card sx={{ flex: 1, p: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            Acknowledged
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 600, color: 'success.main' }}>
            {stats.acknowledged}
          </Typography>
        </Card>
        {stats.priorityCounts.high > 0 && (
          <Card sx={{ flex: 1, p: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              High Priority
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 600, color: 'error.main' }}>
              {stats.priorityCounts.high}
            </Typography>
          </Card>
        )}
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, flexShrink: 0 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <TextField
            label="Search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            size="small"
            sx={{ minWidth: 200, flex: 1 }}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
            placeholder="Search by ID, source, type, or payload..."
          />
          <TextField
            label="Source"
            value={sourceFilter}
            onChange={(e) => {
              setSourceFilter(e.target.value);
              handleFilterChange();
            }}
            size="small"
            sx={{ minWidth: 150 }}
          />
          <TextField
            label="Event Type"
            value={eventTypeFilter}
            onChange={(e) => {
              setEventTypeFilter(e.target.value);
              handleFilterChange();
            }}
            size="small"
            sx={{ minWidth: 150 }}
          />
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Priority</InputLabel>
            <Select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value);
                handleFilterChange();
              }}
              label="Priority"
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="normal">Normal</MenuItem>
              <MenuItem value="high">High</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 100 }}>
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
          <Button variant="outlined" onClick={handleResetFilters} size="small">
            Reset
          </Button>
        </Box>
      </Paper>

      {/* Bulk Actions */}
      {selectedEvents.size > 0 && (
        <Paper sx={{ p: 1.5, flexShrink: 0, bgcolor: 'action.selected' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {selectedEvents.size} event(s) selected
            </Typography>
            <Button
              size="small"
              variant="contained"
              startIcon={<CheckCircleIcon />}
              onClick={handleBulkAcknowledge}
              disabled={acknowledgeMutation.isPending}
            >
              Acknowledge Selected
            </Button>
            <Button
              size="small"
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleBulkDelete}
              disabled={deleteMutation.isPending}
            >
              Delete Selected
            </Button>
            <Button size="small" onClick={() => setSelectedEvents(new Set())}>
              Clear Selection
            </Button>
          </Box>
        </Paper>
      )}

      {/* Events List */}
      <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
        {events.length === 0 ? (
          <Alert severity="info">No events found</Alert>
        ) : viewMode === 'table' ? (
          <TableContainer component={Paper} variant="outlined">
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: 'grey.200' }}>
                  <TableCell padding="checkbox" sx={{ width: 48 }}>
                    <Checkbox
                      checked={allSelected}
                      indeterminate={someSelected}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                    />
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 600, minWidth: 300 }}>ID</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Source</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Priority</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Created</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Payload Preview</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: 120 }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {events.map((event) => {
                  const priority = event.metadata?.priority || 'normal';
                  const isSelected = selectedEvents.has(event.event_id);
                  return (
                    <TableRow
                      key={event.event_id}
                      hover
                      selected={isSelected}
                      onClick={() => navigate(`/events/${event.event_id}`)}
                      sx={{
                        cursor: 'pointer',
                        bgcolor: 'background.paper',
                      }}
                    >
                      <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                        <Checkbox
                          checked={isSelected}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleSelectEvent(event.event_id, e.target.checked);
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={capitalize(event.status)}
                          color={event.status === 'pending' ? 'warning' : 'success'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {event.event_id}
                        </Typography>
                      </TableCell>
                      <TableCell>{event.source}</TableCell>
                      <TableCell>{event.event_type}</TableCell>
                      <TableCell>
                        {priority !== 'normal' && (
                          <Chip
                            label={capitalize(priority)}
                            size="small"
                            color={priority === 'high' ? 'error' : 'default'}
                            variant={priority === 'high' ? 'filled' : 'outlined'}
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary">
                          {formatRelativeTime(event.created_at)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="caption"
                          sx={{
                            fontFamily: 'monospace',
                            fontSize: '0.7rem',
                            display: 'block',
                            maxWidth: 200,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {JSON.stringify(event.payload).substring(0, 50)}...
                        </Typography>
                      </TableCell>
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          {event.status === 'pending' && (
                            <Tooltip title="Acknowledge">
                              <IconButton
                                size="small"
                                color="primary"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleAcknowledge(event.event_id);
                                }}
                              >
                                <CheckCircleIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(event.event_id);
                              }}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {events.map((event) => (
              <EventCard
                key={event.event_id}
                event={event}
                onAcknowledge={handleAcknowledge}
                onDelete={handleDelete}
              />
            ))}
          </Box>
        )}
      </Box>

      {/* Pagination */}
      {events.length > 0 && (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            pt: 2,
            flexShrink: 0,
            borderTop: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Showing {events.length} event(s)
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button variant="outlined" onClick={handlePrevious} disabled={!hasPrevious || isLoading}>
              Previous
            </Button>
            <Button variant="outlined" onClick={handleNext} disabled={!hasNext || isLoading}>
              Next
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default InboxList;
