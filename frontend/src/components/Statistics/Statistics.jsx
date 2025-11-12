import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  CircularProgress,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { subHours, subDays, subWeeks } from 'date-fns';
import { getInbox } from '../../services/api';

// Color palettes for pie charts - diverse colors across the spectrum
const SOURCE_COLORS = [
  '#1976d2', // Blue
  '#4caf50', // Green
  '#ff9800', // Orange
  '#9c27b0', // Purple
  '#f44336', // Red
  '#00bcd4', // Cyan
  '#ffeb3b', // Yellow
  '#795548', // Brown
  '#607d8b', // Blue Grey
  '#e91e63', // Pink
  '#3f51b5', // Indigo
  '#009688', // Teal
  '#ff5722', // Deep Orange
  '#673ab7', // Deep Purple
  '#8bc34a', // Light Green
];

const TYPE_COLORS = [
  '#dc004e', // Red
  '#2196f3', // Blue
  '#4caf50', // Green
  '#ff9800', // Orange
  '#9c27b0', // Purple
  '#00bcd4', // Cyan
  '#ffeb3b', // Yellow
  '#795548', // Brown
  '#607d8b', // Blue Grey
  '#e91e63', // Pink
  '#3f51b5', // Indigo
  '#009688', // Teal
  '#ff5722', // Deep Orange
  '#673ab7', // Deep Purple
  '#8bc34a', // Light Green
];
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const Statistics = () => {
  const [timeRange, setTimeRange] = useState('day'); // 'hour', 'day', 'week'
  const [allEvents, setAllEvents] = useState([]);
  const [isLoadingAll, setIsLoadingAll] = useState(false);

  // Fetch all events for statistics (with pagination)
  const fetchAllEvents = async () => {
    setIsLoadingAll(true);
    const events = [];
    let cursor = null;
    let hasMore = true;

    while (hasMore) {
      try {
        const response = await getInbox({ limit: 100, cursor });
        const data = response.data;

        if (data.events) {
          events.push(...data.events);
        }

        cursor = data.next_cursor || null;
        hasMore = !!cursor;
      } catch (error) {
        console.error('Error fetching events for statistics:', error);
        hasMore = false;
      }
    }

    setAllEvents(events);
    setIsLoadingAll(false);
  };

  // Load all events on mount
  React.useEffect(() => {
    fetchAllEvents();
  }, []);

  // Filter events by time range
  const filteredEvents = useMemo(() => {
    if (!allEvents.length) return [];

    const now = new Date();
    let cutoffDate;

    switch (timeRange) {
      case 'hour':
        cutoffDate = subHours(now, 1);
        break;
      case 'day':
        cutoffDate = subDays(now, 1);
        break;
      case 'week':
        cutoffDate = subWeeks(now, 1);
        break;
      default:
        cutoffDate = subDays(now, 1);
    }

    return allEvents.filter((event) => {
      const eventDate = new Date(event.created_at);
      return eventDate >= cutoffDate;
    });
  }, [allEvents, timeRange]);

  // Calculate statistics
  const stats = useMemo(() => {
    const total = filteredEvents.length;
    const pending = filteredEvents.filter((e) => e.status === 'pending').length;
    const acknowledged = filteredEvents.filter((e) => e.status === 'acknowledged').length;

    // Events by source
    const bySource = {};
    filteredEvents.forEach((event) => {
      bySource[event.source] = (bySource[event.source] || 0) + 1;
    });
    const sourceData = Object.entries(bySource)
      .map(([source, count]) => ({ name: source, value: count }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10); // Top 10

    // Events by type
    const byType = {};
    filteredEvents.forEach((event) => {
      byType[event.event_type] = (byType[event.event_type] || 0) + 1;
    });
    const typeData = Object.entries(byType)
      .map(([type, count]) => ({ name: type, value: count }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10); // Top 10

    return {
      total,
      pending,
      acknowledged,
      sourceData,
      typeData,
    };
  }, [filteredEvents]);

  if (isLoadingAll) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexShrink: 0, pt: 1 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Statistics</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              label="Time Range"
            >
              <MenuItem value="hour">Last Hour</MenuItem>
              <MenuItem value="day">Last Day</MenuItem>
              <MenuItem value="week">Last Week</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchAllEvents}
            disabled={isLoadingAll}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      <Grid container spacing={2} sx={{ mb: 2, flexShrink: 0 }}>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
              {stats.total}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
              Total Events
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h3" color="warning.main" sx={{ fontWeight: 700, mb: 1 }}>
              {stats.pending}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
              Pending Events
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h3" color="success.main" sx={{ fontWeight: 700, mb: 1 }}>
              {stats.acknowledged}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
              Acknowledged Events
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0, display: 'flex', flexDirection: 'row', gap: 2 }}>
        {stats.sourceData.length > 0 && (
          <Paper sx={{ p: 3, flexShrink: 0, flex: '1 1 50%', display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Events by Source
            </Typography>
            <Box sx={{ flex: 1, width: '100%', minHeight: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.sourceData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => (percent > 0.05 ? `${(percent * 100).toFixed(0)}%` : '')}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {stats.sourceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={SOURCE_COLORS[index % SOURCE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        )}

        {stats.typeData.length > 0 && (
          <Paper sx={{ p: 3, flexShrink: 0, flex: '1 1 50%', display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Events by Type
            </Typography>
            <Box sx={{ flex: 1, width: '100%', minHeight: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.typeData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => (percent > 0.05 ? `${(percent * 100).toFixed(0)}%` : '')}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {stats.typeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={TYPE_COLORS[index % TYPE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        )}

        {stats.total === 0 && (
          <Alert severity="info" sx={{ flex: '1 1 100%' }}>No events found for the selected time range</Alert>
        )}
      </Box>
    </Box>
  );
};

export default Statistics;

