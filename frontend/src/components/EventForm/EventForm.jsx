import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  MenuItem,
  Typography,
  Paper,
  Alert,
  InputAdornment,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import CategoryIcon from '@mui/icons-material/Category';
import CodeIcon from '@mui/icons-material/Code';
import LinkIcon from '@mui/icons-material/Link';
import PriorityHighIcon from '@mui/icons-material/PriorityHigh';
import SendIcon from '@mui/icons-material/Send';
import ClearIcon from '@mui/icons-material/Clear';
import FormatIndentIncreaseIcon from '@mui/icons-material/FormatIndentIncrease';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import AceEditor from 'react-ace';
import 'ace-builds/src-noconflict/mode-json';
import 'ace-builds/src-noconflict/theme-github';
import 'ace-builds/src-noconflict/ext-language_tools';
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
  const [isJsonValid, setIsJsonValid] = useState(false);
  const aceEditorRef = useRef(null);

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
      // Validate JSON in real-time
      validateJsonPayload(value);
    }
  };

  const handlePayloadChange = (value) => {
    setFormData((prev) => ({
      ...prev,
      payload: value,
    }));
    validateJsonPayload(value);
    if (payloadError) {
      setPayloadError('');
    }
  };

  const validateJsonPayload = (jsonString) => {
    try {
      const parsed = JSON.parse(jsonString);
      if (typeof parsed === 'object' && !Array.isArray(parsed) && Object.keys(parsed).length > 0) {
        setIsJsonValid(true);
        setPayloadError('');
      } else {
        setIsJsonValid(false);
        if (Object.keys(parsed).length === 0) {
          setPayloadError('Payload cannot be empty');
        } else {
          setPayloadError('Payload must be a JSON object');
        }
      }
    } catch (error) {
      setIsJsonValid(false);
      // Don't set error on empty string (user is still typing)
      if (jsonString.trim() !== '' && jsonString !== '{}') {
        setPayloadError('Invalid JSON: ' + error.message);
      }
    }
  };

  const handleFormatJson = () => {
    try {
      const parsed = JSON.parse(formData.payload);
      const formatted = JSON.stringify(parsed, null, 2);
      setFormData((prev) => ({
        ...prev,
        payload: formatted,
      }));
      validateJsonPayload(formatted);
    } catch (error) {
      showError('Cannot format invalid JSON');
    }
  };

  // Validate JSON on mount
  useEffect(() => {
    if (formData.payload && formData.payload !== '{}') {
      validateJsonPayload(formData.payload);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
        priority: 'med',
      },
    });
    setErrors({});
    setPayloadError('');
  };

  // Character counter helper
  const getCharCountColor = (length, maxLength) => {
    if (length > maxLength * 0.95) return 'error.main';
    if (length > maxLength * 0.8) return 'warning.main';
    return 'text.secondary';
  };

  // Priority color mapping
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'low':
        return 'info';
      case 'normal':
        return 'default';
      case 'high':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', minHeight: 0 }}>
      <Paper
        sx={{
          pt: 2.5,
          px: 3,
          pb: 2.5,
          display: 'flex',
          flexDirection: 'column',
          width: '100%',
          height: '100%',
          boxShadow: 2,
          borderRadius: 2,
          minHeight: 0,
          overflow: 'visible',
        }}
      >
        <Box sx={{ flexShrink: 0, mb: 2 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 0.75, fontSize: '1.1rem' }}>
            Send Event
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
            Create a new event to send to the API
          </Typography>
        </Box>

        <Box
          component="form"
          onSubmit={handleSubmit}
          sx={{
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            minHeight: 0,
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* Required Fields Section */}
          <Typography
            variant="subtitle2"
            sx={{
              fontWeight: 600,
              color: 'text.secondary',
              mb: 1.5,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              fontSize: '0.7rem',
            }}
          >
            Required Fields
          </Typography>

          {/* Two-column layout for Source and Event Type */}
          <Box sx={{ display: 'flex', gap: 2.5, mb: 2, flexShrink: 0 }}>
            <TextField
              fullWidth
              label="Source"
              value={formData.source}
              onChange={handleChange('source')}
              required
              error={!!errors.source}
              helperText={errors.source}
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LocationOnIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <Typography
                      variant="caption"
                      sx={{
                        color: getCharCountColor(formData.source.length, 100),
                        fontSize: '0.7rem',
                      }}
                    >
                      {formData.source.length}/100
                    </Typography>
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiInputBase-input': {
                  fontSize: '1rem',
                  py: 0.75,
                },
                '& .MuiOutlinedInput-root': {
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'primary.light',
                    },
                  },
                  '&.Mui-focused': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderWidth: 2,
                      borderColor: 'primary.main',
                    },
                  },
                },
              }}
            />

            <TextField
              fullWidth
              label="Event Type"
              value={formData.event_type}
              onChange={handleChange('event_type')}
              required
              error={!!errors.event_type}
              helperText={errors.event_type}
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <CategoryIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <Typography
                      variant="caption"
                      sx={{
                        color: getCharCountColor(formData.event_type.length, 100),
                        fontSize: '0.7rem',
                      }}
                    >
                      {formData.event_type.length}/100
                    </Typography>
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiInputBase-input': {
                  fontSize: '1rem',
                  py: 0.75,
                },
                '& .MuiOutlinedInput-root': {
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'primary.light',
                    },
                  },
                  '&.Mui-focused': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderWidth: 2,
                      borderColor: 'primary.main',
                    },
                  },
                },
              }}
            />
          </Box>

          <Box sx={{ mb: 2, flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', flexShrink: 1 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                mb: 1.25,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                <CodeIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 500,
                    color: 'text.primary',
                    fontSize: '0.875rem',
                  }}
                >
                  Payload (JSON) *
                </Typography>
                {formData.payload && formData.payload !== '{}' && (
                  <Box sx={{ display: 'flex', alignItems: 'center', ml: 0.75 }}>
                    {isJsonValid ? (
                      <Tooltip title="Valid JSON">
                        <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main' }} />
                      </Tooltip>
                    ) : (
                      <Tooltip title={payloadError || 'Invalid JSON'}>
                        <ErrorIcon sx={{ fontSize: 16, color: 'error.main' }} />
                      </Tooltip>
                    )}
                  </Box>
                )}
              </Box>
              <Tooltip title="Format JSON">
                <IconButton
                  size="small"
                  onClick={handleFormatJson}
                  sx={{
                    color: 'text.secondary',
                    padding: 0.5,
                    '&:hover': {
                      color: 'primary.main',
                    },
                  }}
                >
                  <FormatIndentIncreaseIcon sx={{ fontSize: 16 }} />
                </IconButton>
              </Tooltip>
            </Box>
            <Box
              sx={{
                border: payloadError
                  ? '2px solid'
                  : isJsonValid && formData.payload && formData.payload !== '{}'
                  ? '2px solid'
                  : '1px solid',
                borderColor: payloadError
                  ? 'error.main'
                  : isJsonValid && formData.payload && formData.payload !== '{}'
                  ? 'success.main'
                  : 'divider',
                borderRadius: 1,
                overflow: 'hidden',
                transition: 'all 0.2s ease-in-out',
                minHeight: 120,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                '&:hover': {
                  borderColor: payloadError ? 'error.main' : 'primary.light',
                },
                '&:focus-within': {
                  borderColor: payloadError ? 'error.main' : 'primary.main',
                  borderWidth: 2,
                },
              }}
            >
              <AceEditor
                ref={aceEditorRef}
                mode="json"
                theme="github"
                value={formData.payload}
                onChange={handlePayloadChange}
                name="payload-editor"
                editorProps={{ $blockScrolling: true }}
                width="100%"
                height="100%"
                fontSize={14}
                showPrintMargin={false}
                setOptions={{
                  enableBasicAutocompletion: true,
                  enableLiveAutocompletion: true,
                  enableSnippets: true,
                  showLineNumbers: true,
                  tabSize: 2,
                }}
                style={{
                  fontFamily: 'monospace',
                }}
              />
            </Box>
            {payloadError && (
              <Typography variant="caption" color="error" sx={{ mt: 0.75, display: 'block', fontSize: '0.7rem' }}>
                {payloadError}
              </Typography>
            )}
            {!payloadError && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.75, display: 'block', fontSize: '0.7rem' }}>
                Enter a valid JSON object
              </Typography>
            )}
          </Box>

          {/* Optional Fields Section */}
          <Divider sx={{ my: 2 }} />
          <Typography
            variant="subtitle2"
            sx={{
              fontWeight: 600,
              color: 'text.secondary',
              mb: 1.5,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              fontSize: '0.7rem',
            }}
          >
            Optional Fields
          </Typography>

          {/* Two-column layout for optional fields */}
          <Box
            sx={{
              backgroundColor: 'action.hover',
              borderRadius: 1,
              p: 2,
              mb: 2,
              display: 'flex',
              gap: 2.5,
              flexShrink: 0,
            }}
          >
            <TextField
              fullWidth
              label="Correlation ID (Optional)"
              value={formData.metadata.correlation_id}
              onChange={handleChange('correlation_id')}
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LinkIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiInputBase-input': {
                  fontSize: '1rem',
                  py: 0.75,
                },
                '& .MuiOutlinedInput-root': {
                  backgroundColor: 'background.paper',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'primary.light',
                    },
                  },
                  '&.Mui-focused': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderWidth: 2,
                      borderColor: 'primary.main',
                    },
                  },
                },
              }}
            />

            <TextField
              fullWidth
              select
              label="Priority (Optional)"
              value={formData.metadata.priority}
              onChange={handleChange('priority')}
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PriorityHighIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiInputBase-input': {
                  fontSize: '1rem',
                  py: 0.75,
                },
                '& .MuiOutlinedInput-root': {
                  backgroundColor: 'background.paper',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'primary.light',
                    },
                  },
                  '&.Mui-focused': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderWidth: 2,
                      borderColor: 'primary.main',
                    },
                  },
                },
              }}
              renderValue={(value) => {
                const displayMap = {
                  'low': 'Low',
                  'normal': 'Medium',
                  'high': 'High'
                };
                return displayMap[value] || value;
              }}
            >
              <MenuItem value="low" sx={{ fontSize: '1rem' }}>Low</MenuItem>
              <MenuItem value="normal" sx={{ fontSize: '1rem' }}>Medium</MenuItem>
              <MenuItem value="high" sx={{ fontSize: '1rem' }}>High</MenuItem>
            </TextField>
          </Box>

          <Box sx={{ display: 'flex', gap: 2, mt: 2, flexShrink: 0 }}>
            <Button
              type="submit"
              variant="contained"
              disabled={createEventMutation.isPending}
              startIcon={<SendIcon sx={{ fontSize: 16 }} />}
              sx={{
                flex: 1,
                py: 0.875,
                px: 2,
                fontWeight: 600,
                textTransform: 'none',
                fontSize: '0.875rem',
                boxShadow: 2,
                '&:hover': {
                  boxShadow: 4,
                },
              }}
            >
              {createEventMutation.isPending ? 'Creating...' : 'Create Event'}
            </Button>
            <Button
              variant="outlined"
              onClick={handleClear}
              startIcon={<ClearIcon sx={{ fontSize: 16 }} />}
              sx={{
                py: 0.875,
                px: 2,
                fontWeight: 600,
                textTransform: 'none',
                fontSize: '0.875rem',
              }}
            >
              Clear
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default EventForm;

