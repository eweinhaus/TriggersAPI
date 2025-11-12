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
    <Card sx={{ mb: 2, transition: 'box-shadow 0.2s ease-in-out' }}>
      <CardContent sx={{ pb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
          <Box>
            <Typography variant="h6" component="div" sx={{ fontWeight: 600, mb: 0.5 }}>
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
            sx={{ fontWeight: 500 }}
          />
        </Box>

        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
            <strong>Source:</strong> {event.source}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
            <strong>Type:</strong> {event.event_type}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            <strong>Payload:</strong> {truncatedPayload}
          </Typography>
        </Box>
      </CardContent>
      <CardActions sx={{ pt: 0, pb: 2, px: 2 }}>
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

