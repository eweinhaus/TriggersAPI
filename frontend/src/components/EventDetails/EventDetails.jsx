import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import JsonView from '@uiw/react-json-view';
import { useEvent, useAcknowledgeEvent, useDeleteEvent } from '../../hooks/useEvents';
import { useNotification } from '../../contexts/NotificationContext';
import { formatDate } from '../../utils/formatters';

const EventDetails = () => {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();
  const { data, isLoading, error } = useEvent(eventId);
  const acknowledgeMutation = useAcknowledgeEvent();
  const deleteMutation = useDeleteEvent();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [copied, setCopied] = useState({ eventId: false, payload: false });

  const handleCopy = async (text, type) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied((prev) => ({ ...prev, [type]: true }));
      showSuccess(`${type === 'eventId' ? 'Event ID' : 'Payload'} copied to clipboard`);
      setTimeout(() => {
        setCopied((prev) => ({ ...prev, [type]: false }));
      }, 2000);
    } catch (error) {
      showError('Failed to copy to clipboard');
    }
  };

  const handleAcknowledge = async () => {
    try {
      await acknowledgeMutation.mutateAsync(eventId);
      showSuccess('Event acknowledged successfully');
      navigate('/inbox');
    } catch (error) {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to acknowledge event';
      showError(errorMessage);
    }
  };

  const handleDelete = async () => {
    setDeleteDialogOpen(false);
    try {
      await deleteMutation.mutateAsync(eventId);
      showSuccess('Event deleted successfully');
      navigate('/inbox');
    } catch (error) {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to delete event';
      showError(errorMessage);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error.formattedError?.message || error.message || 'Failed to load event'}
        <Button sx={{ ml: 2 }} onClick={() => navigate('/inbox')}>
          Back to Inbox
        </Button>
      </Alert>
    );
  }

  if (!data?.data) {
    return (
      <Alert severity="warning">
        Event not found
        <Button sx={{ ml: 2 }} onClick={() => navigate('/inbox')}>
          Back to Inbox
        </Button>
      </Alert>
    );
  }

  const event = data.data;

  return (
    <Box>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/inbox')}
        sx={{ mb: 2 }}
      >
        Back to Inbox
      </Button>

      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 3 }}>
          <Box>
            <Typography variant="h5" gutterBottom>
              Event Details
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
              <Chip
                label={event.status}
                color={event.status === 'pending' ? 'warning' : 'success'}
              />
              <Typography variant="body2" color="text.secondary">
                Created: {formatDate(event.created_at)}
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {event.status === 'pending' && (
              <Button
                variant="contained"
                startIcon={<CheckCircleIcon />}
                onClick={handleAcknowledge}
                disabled={acknowledgeMutation.isPending}
              >
                Acknowledge
              </Button>
            )}
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setDeleteDialogOpen(true)}
              disabled={deleteMutation.isPending}
            >
              Delete
            </Button>
          </Box>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="text.secondary">
            Event ID
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
              {event.event_id}
            </Typography>
            <IconButton
              size="small"
              onClick={() => handleCopy(event.event_id, 'eventId')}
              color={copied.eventId ? 'success' : 'default'}
            >
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="text.secondary">
            Source
          </Typography>
          <Typography variant="body1">{event.source}</Typography>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="text.secondary">
            Event Type
          </Typography>
          <Typography variant="body1">{event.event_type}</Typography>
        </Box>

        {event.acknowledged_at && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Acknowledged At
            </Typography>
            <Typography variant="body1">{formatDate(event.acknowledged_at)}</Typography>
          </Box>
        )}

        {event.metadata && Object.keys(event.metadata).length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Metadata
            </Typography>
            <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
              <JsonView value={event.metadata} />
            </Paper>
          </Box>
        )}

        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Payload
            </Typography>
            <Button
              size="small"
              startIcon={<ContentCopyIcon />}
              onClick={() => handleCopy(JSON.stringify(event.payload, null, 2), 'payload')}
            >
              {copied.payload ? 'Copied!' : 'Copy Payload'}
            </Button>
          </Box>
          <Paper sx={{ p: 2, backgroundColor: 'grey.50', maxHeight: 500, overflow: 'auto' }}>
            <JsonView value={event.payload} />
          </Paper>
        </Box>
      </Paper>

      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Event</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this event? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EventDetails;

