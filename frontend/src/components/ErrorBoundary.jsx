import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            p: 3,
          }}
        >
          <Paper sx={{ p: 4, maxWidth: 600 }}>
            <Typography variant="h5" gutterBottom color="error">
              Something went wrong
            </Typography>
            <Typography variant="body1" sx={{ mb: 3 }}>
              An unexpected error occurred. Please try refreshing the page.
            </Typography>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Typography
                variant="body2"
                sx={{
                  fontFamily: 'monospace',
                  backgroundColor: 'grey.100',
                  p: 2,
                  borderRadius: 1,
                  mb: 3,
                  overflow: 'auto',
                }}
              >
                {this.state.error.toString()}
              </Typography>
            )}
            <Button variant="contained" onClick={this.handleReset}>
              Go to Home
            </Button>
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

