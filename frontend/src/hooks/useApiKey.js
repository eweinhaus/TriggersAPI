import { useState, useEffect } from 'react';

/**
 * Hook to manage API key in localStorage
 * @returns {Object} { apiKey, setApiKey, clearApiKey }
 */
export const useApiKey = () => {
  const [apiKey, setApiKeyState] = useState(() => {
    // Load from localStorage on mount
    try {
      return localStorage.getItem('apiKey') || '';
    } catch (error) {
      console.error('Error loading API key from localStorage:', error);
      return '';
    }
  });

  const setApiKey = (key) => {
    try {
      if (key) {
        localStorage.setItem('apiKey', key);
      } else {
        localStorage.removeItem('apiKey');
      }
      setApiKeyState(key || '');
    } catch (error) {
      console.error('Error saving API key to localStorage:', error);
      setApiKeyState(key || '');
    }
  };

  const clearApiKey = () => {
    try {
      localStorage.removeItem('apiKey');
      setApiKeyState('');
    } catch (error) {
      console.error('Error clearing API key from localStorage:', error);
      setApiKeyState('');
    }
  };

  return { apiKey, setApiKey, clearApiKey };
};

