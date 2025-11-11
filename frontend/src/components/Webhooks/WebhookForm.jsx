import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { createWebhook, updateWebhook } from '../../services/api';
import { useNotification } from '../../contexts/NotificationContext';

const WebhookForm = ({ open, onClose, webhook, onSuccess }) => {
  const { showSuccess, showError } = useNotification();
  const [url, setUrl] = useState('');
  const [events, setEvents] = useState('');
  const [secret, setSecret] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (webhook) {
      setUrl(webhook.url || '');
      setEvents(webhook.events?.join(', ') || '');
      setSecret(''); // Don't populate secret for security
      setIsActive(webhook.is_active !== false);
    } else {
      setUrl('');
      setEvents('');
      setSecret('');
      setIsActive(true);
    }
    setErrors({});
  }, [webhook, open]);

  const createMutation = useMutation({
    mutationFn: (data) => createWebhook(data),
    onSuccess: () => {
      showSuccess('Webhook created successfully');
      onSuccess?.();
    },
    onError: (error) => {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to create webhook';
      showError(errorMessage);
      if (error.formattedError?.details) {
        setErrors(error.formattedError.details);
      }
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data) => updateWebhook(webhook.webhook_id, data),
    onSuccess: () => {
      showSuccess('Webhook updated successfully');
      onSuccess?.();
    },
    onError: (error) => {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to update webhook';
      showError(errorMessage);
      if (error.formattedError?.details) {
        setErrors(error.formattedError.details);
      }
    },
  });

  const validate = () => {
    const newErrors = {};
    
    if (!url.trim()) {
      newErrors.url = 'URL is required';
    } else if (!url.startsWith('http://') && !url.startsWith('https://')) {
      newErrors.url = 'URL must start with http:// or https://';
    }
    
    if (!events.trim()) {
      newErrors.events = 'Events are required';
    }
    
    if (!webhook && !secret.trim()) {
      newErrors.secret = 'Secret is required';
    } else if (secret && secret.length < 16) {
      newErrors.secret = 'Secret must be at least 16 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) {
      return;
    }

    const eventsList = events
      .split(',')
      .map((e) => e.trim())
      .filter((e) => e.length > 0);

    const data = {
      url: url.trim(),
      events: eventsList,
      is_active: isActive,
    };

    if (!webhook) {
      // Creating new webhook - secret required
      data.secret = secret;
      createMutation.mutate(data);
    } else {
      // Updating webhook - secret optional
      if (secret.trim()) {
        data.secret = secret;
      }
      updateMutation.mutate(data);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{webhook ? 'Edit Webhook' : 'Create Webhook'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField
            label="Webhook URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            fullWidth
            required
            error={!!errors.url}
            helperText={errors.url || 'HTTPS URL to receive webhook events'}
            disabled={isLoading}
          />

          <TextField
            label="Event Types"
            value={events}
            onChange={(e) => setEvents(e.target.value)}
            fullWidth
            required
            error={!!errors.events}
            helperText={
              errors.events ||
              'Comma-separated list of event types (e.g., "user.created, order.completed") or "*" for all events'
            }
            disabled={isLoading}
            placeholder="*"
          />

          <TextField
            label="Secret"
            type="password"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
            fullWidth
            required={!webhook}
            error={!!errors.secret}
            helperText={
              errors.secret ||
              (webhook
                ? 'Leave empty to keep current secret. Minimum 16 characters if updating.'
                : 'Secret for HMAC signature verification (minimum 16 characters)')
            }
            disabled={isLoading}
          />

          {webhook && (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Status
              </Typography>
              <Chip
                label={isActive ? 'Active' : 'Inactive'}
                color={isActive ? 'success' : 'default'}
                onClick={() => setIsActive(!isActive)}
                sx={{ cursor: 'pointer' }}
              />
            </Box>
          )}

          {Object.keys(errors).length > 0 && (
            <Alert severity="error">
              Please fix the errors above before submitting.
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={isLoading}
        >
          {isLoading ? <CircularProgress size={20} /> : webhook ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default WebhookForm;

