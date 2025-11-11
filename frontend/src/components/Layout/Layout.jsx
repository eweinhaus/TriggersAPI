import React from 'react';
import { Box } from '@mui/material';
import Header from './Header';
import Sidebar from './Sidebar';

const Layout = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', width: '100%' }}>
      <Header />
      <Box sx={{ display: 'flex', flexGrow: 1, width: '100%', overflow: 'hidden' }}>
        <Sidebar />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            backgroundColor: 'background.default',
            minHeight: 'calc(100vh - 64px)',
            width: '100%',
            overflow: 'auto',
            maxWidth: 'calc(100vw - 240px)', // Account for sidebar width
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;

