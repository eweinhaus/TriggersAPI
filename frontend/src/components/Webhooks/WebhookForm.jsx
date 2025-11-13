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
      
      // Debug logging in development
      if (import.meta.env.DEV) {
        console.log('Webhook creation error:', error);
        console.log('Formatted error:', error.formattedError);
      }
      
      if (error.formattedError?.details) {
        // Convert validation_errors array to flat object
        const details = error.formattedError.details;
        if (details.validation_errors && Array.isArray(details.validation_errors)) {
          const fieldErrors = {};
          details.validation_errors.forEach((err) => {
            // Map field names to form field names
            // FastAPI may prefix with "body." so we strip that
            let fieldName = err.field || '';
            if (fieldName.startsWith('body.')) {
              fieldName = fieldName.substring(5); // Remove "body." prefix
            }
            if (fieldName) {
              // Clean up error message - remove "Value error, " prefix if present
              let errorMessage = err.message || err.issue || 'Invalid value';
              if (errorMessage.startsWith('Value error, ')) {
                errorMessage = errorMessage.substring(14); // Remove "Value error, " prefix
              }
              fieldErrors[fieldName] = errorMessage;
            }
          });
          setErrors(fieldErrors);
        } else {
          // Fallback: check if details has direct field mappings
          const fieldErrors = {};
          Object.keys(details).forEach((key) => {
            // Skip non-field keys
            if (key !== 'validation_errors' && key !== 'field' && key !== 'issue' && key !== 'value') {
              fieldErrors[key] = details[key];
            }
          });
          if (Object.keys(fieldErrors).length > 0) {
            setErrors(fieldErrors);
          }
        }
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
        // Convert validation_errors array to flat object
        const details = error.formattedError.details;
        if (details.validation_errors && Array.isArray(details.validation_errors)) {
          const fieldErrors = {};
          details.validation_errors.forEach((err) => {
            // Map field names to form field names
            // FastAPI may prefix with "body." so we strip that
            let fieldName = err.field || '';
            if (fieldName.startsWith('body.')) {
              fieldName = fieldName.substring(5); // Remove "body." prefix
            }
            if (fieldName) {
              // Clean up error message - remove "Value error, " prefix if present
              let errorMessage = err.message || err.issue || 'Invalid value';
              if (errorMessage.startsWith('Value error, ')) {
                errorMessage = errorMessage.substring(14); // Remove "Value error, " prefix
              }
              fieldErrors[fieldName] = errorMessage;
            }
          });
          setErrors(fieldErrors);
        } else {
          // Fallback: check if details has direct field mappings
          const fieldErrors = {};
          Object.keys(details).forEach((key) => {
            // Skip non-field keys
            if (key !== 'validation_errors' && key !== 'field' && key !== 'issue' && key !== 'value') {
              fieldErrors[key] = details[key];
            }
          });
          if (Object.keys(fieldErrors).length > 0) {
            setErrors(fieldErrors);
          }
        }
      }
    },
  });

  const validate = () => {
    const newErrors = {};
    
    const urlTrimmed = url.trim();
    if (!urlTrimmed) {
      newErrors.url = 'URL is required';
    } else {
      // Validate URL format - must start with http:// or https://
      if (!urlTrimmed.startsWith('http://') && !urlTrimmed.startsWith('https://')) {
        newErrors.url = 'URL must start with http:// or https://';
      } else {
        // Basic URL validation - must have a domain
        try {
          const urlObj = new URL(urlTrimmed);
          if (!urlObj.hostname || urlObj.hostname.length === 0) {
            newErrors.url = 'URL must include a valid hostname';
          }
        } catch (e) {
          newErrors.url = 'URL must be a valid HTTP/HTTPS URL';
        }
      }
    }
    
    // Events can be empty (will default to "*" in handleSubmit)
    // But if provided, must be valid
    const eventsTrimmed = events.trim();
    if (eventsTrimmed) {
      const eventsList = eventsTrimmed.split(',').map((e) => e.trim()).filter((e) => e.length > 0);
      if (eventsList.length === 0) {
        newErrors.events = 'Events cannot be empty';
      }
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

    // Process events - default to "*" if empty, otherwise split by comma
    let eventsList;
    const eventsTrimmed = events.trim();
    if (!eventsTrimmed) {
      eventsList = ['*'];
    } else {
      eventsList = eventsTrimmed
        .split(',')
        .map((e) => e.trim())
        .filter((e) => e.length > 0);
      
      // If after filtering we have no events, default to "*"
      if (eventsList.length === 0) {
        eventsList = ['*'];
      }
    }

    const data = {
      url: url.trim(),
      events: eventsList,
      is_active: isActive,
    };

    if (!webhook) {
      // Creating new webhook - secret required
      data.secret = secret.trim();
      createMutation.mutate(data);
    } else {
      // Updating webhook - secret optional
      if (secret.trim()) {
        data.secret = secret.trim();
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
            onChange={(e) => {
              setUrl(e.target.value);
              if (errors.url) {
                setErrors((prev) => {
                  const newErrors = { ...prev };
                  delete newErrors.url;
                  return newErrors;
                });
              }
            }}
            fullWidth
            required
            error={!!errors.url}
            helperText={errors.url || 'HTTPS URL to receive webhook events'}
            disabled={isLoading}
          />

          <TextField
            label="Event Types"
            value={events}
            onChange={(e) => {
              setEvents(e.target.value);
              if (errors.events) {
                setErrors((prev) => {
                  const newErrors = { ...prev };
                  delete newErrors.events;
                  return newErrors;
                });
              }
            }}
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
            onChange={(e) => {
              setSecret(e.target.value);
              if (errors.secret) {
                setErrors((prev) => {
                  const newErrors = { ...prev };
                  delete newErrors.secret;
                  return newErrors;
                });
              }
            }}
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
              {Object.keys(errors).length === 1 
                ? 'Please fix the error above before submitting.'
                : 'Please fix the errors above before submitting.'}
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

