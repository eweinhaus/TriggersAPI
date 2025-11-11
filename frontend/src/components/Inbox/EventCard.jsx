import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Box,
  Chip,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { formatRelativeTime, truncateEventId, truncate } from '../../utils/formatters';

const EventCard = ({ event, onAcknowledge, onDelete }) => {
  const navigate = useNavigate();

  const handleViewDetails = () => {
    navigate(`/events/${event.event_id}`);
  };

  const handleAcknowledge = () => {
    if (onAcknowledge) {
      onAcknowledge(event.event_id);
    }
  };

  const handleDelete = () => {
    if (onDelete) {
      onDelete(event.event_id);
    }
  };

  const payloadPreview = JSON.stringify(event.payload);
  const truncatedPayload = truncate(payloadPreview, 100);

  return (
    <Card sx={{ mb: 2, '&:hover': { boxShadow: 4 } }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
          <Box>
            <Typography variant="h6" component="div">
              {truncateEventId(event.event_id)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {formatRelativeTime(event.created_at)}
            </Typography>
          </Box>
          <Chip
            label={event.status}
            color={event.status === 'pending' ? 'warning' : 'success'}
            size="small"
          />
        </Box>

        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            <strong>Source:</strong> {event.source}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            <strong>Type:</strong> {event.event_type}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            <strong>Payload:</strong> {truncatedPayload}
          </Typography>
        </Box>
      </CardContent>
      <CardActions>
        <Button size="small" onClick={handleViewDetails}>
          View Details
        </Button>
        {event.status === 'pending' && (
          <Button size="small" color="primary" onClick={handleAcknowledge}>
            Acknowledge
          </Button>
        )}
        <Button size="small" color="error" onClick={handleDelete}>
          Delete
        </Button>
      </CardActions>
    </Card>
  );
};

export default EventCard;

