import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  TextField,
  IconButton,
  Box,
  Typography,
  CircularProgress,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import ClearIcon from '@mui/icons-material/Clear';
import { useApiKey } from '../../hooks/useApiKey';
import { healthCheck } from '../../services/api';

const Header = () => {
  const { apiKey, setApiKey, clearApiKey } = useApiKey();
  const [validationStatus, setValidationStatus] = useState('idle'); // 'idle', 'checking', 'valid', 'invalid'
  const [debounceTimer, setDebounceTimer] = useState(null);
  const [isFocused, setIsFocused] = useState(false);

  // Validate API key when it changes (debounced)
  useEffect(() => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    if (!apiKey) {
      setValidationStatus('idle');
      return;
    }

    setValidationStatus('checking');

    const timer = setTimeout(async () => {
      try {
        await healthCheck();
        setValidationStatus('valid');
      } catch (error) {
        setValidationStatus('invalid');
      }
    }, 500); // 500ms debounce

    setDebounceTimer(timer);

    return () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
    };
  }, [apiKey]);

  const handleApiKeyChange = (event) => {
    setApiKey(event.target.value);
  };

  const handleClearApiKey = () => {
    clearApiKey();
    setValidationStatus('idle');
  };

  const getValidationIcon = () => {
    switch (validationStatus) {
      case 'checking':
        return <CircularProgress size={20} />;
      case 'valid':
        return <CheckCircleIcon color="success" />;
      case 'invalid':
        return <ErrorIcon color="error" />;
      default:
        return null;
    }
  };

  return (
    <AppBar position="static" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1, height: 64 }}>
      <Toolbar sx={{ width: '100%', px: { xs: 2, sm: 3 }, height: 64, minHeight: '64px !important', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" component="div" sx={{ flexGrow: 0, fontWeight: 600 }}>
          Triggers API
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TextField
            label={isFocused || apiKey ? '' : 'API Key'}
            type="password"
            value={apiKey}
            onChange={handleApiKeyChange}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={isFocused || apiKey ? 'API Key' : ''}
            size="small"
            sx={{
              minWidth: { xs: 200, sm: 300 },
              maxWidth: 400,
              '& .MuiOutlinedInput-root': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                },
                '&.Mui-focused': {
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.5)',
                    borderWidth: '1px',
                  },
                },
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.3)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.4)',
                },
              },
              '& .MuiInputLabel-root': {
                color: 'rgba(255, 255, 255, 0.7)',
                display: (isFocused || apiKey) ? 'none' : 'block',
              },
              '& .MuiInputBase-input': {
                color: 'white',
                '&::placeholder': {
                  color: 'rgba(255, 255, 255, 0.5)',
                  opacity: 1,
                },
              },
            }}
            InputProps={{
              endAdornment: (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getValidationIcon()}
                  {apiKey && (
                    <IconButton
                      size="small"
                      onClick={handleClearApiKey}
                      sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
                    >
                      <ClearIcon fontSize="small" />
                    </IconButton>
                  )}
                </Box>
              ),
            }}
          />
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;

