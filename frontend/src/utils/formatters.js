import { format, formatDistanceToNow } from 'date-fns';

/**
 * Format ISO 8601 timestamp to readable date string
 * @param {string} isoString - ISO 8601 timestamp
 * @returns {string} Formatted date string
 */
export const formatDate = (isoString) => {
  if (!isoString) return 'N/A';
  try {
    return format(new Date(isoString), 'PPpp');
  } catch (error) {
    return isoString;
  }
};

/**
 * Format ISO 8601 timestamp to relative time (e.g., "2 hours ago")
 * @param {string} isoString - ISO 8601 timestamp
 * @returns {string} Relative time string
 */
export const formatRelativeTime = (isoString) => {
  if (!isoString) return 'N/A';
  try {
    return formatDistanceToNow(new Date(isoString), { addSuffix: true });
  } catch (error) {
    return isoString;
  }
};

/**
 * Truncate string to specified length
 * @param {string} str - String to truncate
 * @param {number} length - Maximum length
 * @returns {string} Truncated string
 */
export const truncate = (str, length = 50) => {
  if (!str) return '';
  if (str.length <= length) return str;
  return str.substring(0, length) + '...';
};

/**
 * Truncate event ID for display
 * @param {string} eventId - Event ID
 * @returns {string} Truncated event ID
 */
export const truncateEventId = (eventId) => {
  if (!eventId) return '';
  return eventId.substring(0, 8) + '...';
};

/**
 * Capitalize first letter of a string
 * @param {string} str - String to capitalize
 * @returns {string} String with first letter capitalized
 */
export const capitalize = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
};

