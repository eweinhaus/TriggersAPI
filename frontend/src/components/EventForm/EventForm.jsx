import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Typography,
  Paper,
  Alert,
} from '@mui/material';
import { useCreateEvent } from '../../hooks/useEvents';
import { useNotification } from '../../contexts/NotificationContext';
import { useNavigate } from 'react-router-dom';

const EventForm = () => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();
  const createEventMutation = useCreateEvent();

  const [formData, setFormData] = useState({
    source: '',
    event_type: '',
    payload: '{}',
    metadata: {
      correlation_id: '',
      priority: 'normal',
    },
  });

  const [errors, setErrors] = useState({});
  const [payloadError, setPayloadError] = useState('');

  const handleChange = (field) => (event) => {
    const value = event.target.value;
    if (field === 'correlation_id' || field === 'priority') {
      setFormData((prev) => ({
        ...prev,
        metadata: {
          ...prev.metadata,
          [field]: value,
        },
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [field]: value,
      }));
    }
    // Clear errors when user types
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
    if (field === 'payload' && payloadError) {
      setPayloadError('');
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.source.trim()) {
      newErrors.source = 'Source is required';
    } else if (formData.source.length > 100) {
      newErrors.source = 'Source must be 100 characters or less';
    }

    if (!formData.event_type.trim()) {
      newErrors.event_type = 'Event type is required';
    } else if (formData.event_type.length > 100) {
      newErrors.event_type = 'Event type must be 100 characters or less';
    }

    // Validate JSON payload
    try {
      const parsed = JSON.parse(formData.payload);
      if (typeof parsed !== 'object' || Array.isArray(parsed)) {
        setPayloadError('Payload must be a JSON object');
        return false;
      }
      if (Object.keys(parsed).length === 0) {
        setPayloadError('Payload cannot be empty');
        return false;
      }
    } catch (error) {
      setPayloadError('Invalid JSON: ' + error.message);
      return false;
    }

    setErrors(newErrors);
    setPayloadError('');
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      const payload = JSON.parse(formData.payload);
      const requestData = {
        source: formData.source.trim(),
        event_type: formData.event_type.trim(),
        payload,
      };

      // Add metadata if provided
      if (formData.metadata.correlation_id || formData.metadata.priority !== 'normal') {
        requestData.metadata = {};
        if (formData.metadata.correlation_id) {
          requestData.metadata.correlation_id = formData.metadata.correlation_id.trim();
        }
        if (formData.metadata.priority !== 'normal') {
          requestData.metadata.priority = formData.metadata.priority;
        }
      }

      const response = await createEventMutation.mutateAsync(requestData);
      showSuccess('Event created successfully!');
      
      // Clear form
      setFormData({
        source: '',
        event_type: '',
        payload: '{}',
        metadata: {
          correlation_id: '',
          priority: 'normal',
        },
      });

      // Optionally navigate to inbox
      setTimeout(() => {
        navigate('/inbox');
      }, 1000);
    } catch (error) {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to create event';
      showError(errorMessage);
    }
  };

  const handleClear = () => {
    setFormData({
      source: '',
      event_type: '',
      payload: '{}',
      metadata: {
        correlation_id: '',
        priority: 'normal',
      },
    });
    setErrors({});
    setPayloadError('');
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Send Event
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Create a new event to send to the API
      </Typography>

      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          fullWidth
          label="Source"
          value={formData.source}
          onChange={handleChange('source')}
          required
          error={!!errors.source}
          helperText={errors.source}
          margin="normal"
        />

        <TextField
          fullWidth
          label="Event Type"
          value={formData.event_type}
          onChange={handleChange('event_type')}
          required
          error={!!errors.event_type}
          helperText={errors.event_type}
          margin="normal"
        />

        <TextField
          fullWidth
          label="Payload (JSON)"
          value={formData.payload}
          onChange={handleChange('payload')}
          required
          error={!!payloadError}
          helperText={payloadError || 'Enter a valid JSON object'}
          margin="normal"
          multiline
          rows={8}
          sx={{
            '& .MuiInputBase-input': {
              fontFamily: 'monospace',
              fontSize: '0.875rem',
            },
          }}
        />

        <TextField
          fullWidth
          label="Correlation ID (Optional)"
          value={formData.metadata.correlation_id}
          onChange={handleChange('correlation_id')}
          margin="normal"
        />

        <FormControl fullWidth margin="normal">
          <InputLabel>Priority (Optional)</InputLabel>
          <Select
            value={formData.metadata.priority}
            onChange={handleChange('priority')}
            label="Priority (Optional)"
          >
            <MenuItem value="low">Low</MenuItem>
            <MenuItem value="normal">Normal</MenuItem>
            <MenuItem value="high">High</MenuItem>
          </Select>
        </FormControl>

        <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
          <Button
            type="submit"
            variant="contained"
            disabled={createEventMutation.isPending}
          >
            {createEventMutation.isPending ? 'Creating...' : 'Create Event'}
          </Button>
          <Button variant="outlined" onClick={handleClear}>
            Clear
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default EventForm;

