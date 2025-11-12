import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Box,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import { useNavigate } from 'react-router-dom';
import { formatRelativeTime, truncateEventId, truncate, capitalize } from '../../utils/formatters';

const EventCard = ({ event, onAcknowledge, onDelete }) => {
  const navigate = useNavigate();
  const [payloadExpanded, setPayloadExpanded] = useState(false);

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
  const truncatedPayload = truncate(payloadPreview, 50);

  return (
    <Card sx={{ mb: 1, transition: 'box-shadow 0.2s ease-in-out', border: '1px solid', borderColor: 'divider' }}>
      <CardContent sx={{ pb: 1 }}>
        {/* Compact single-line header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1, gap: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1, minWidth: 0 }}>
            <Chip
              label={capitalize(event.status)}
              color={event.status === 'pending' ? 'warning' : 'success'}
              size="small"
              sx={{ fontWeight: 500, flexShrink: 0 }}
            />
            <Typography variant="body2" component="div" sx={{ fontWeight: 600, flex: 1, minWidth: 0 }}>
              {truncateEventId(event.event_id)}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ flexShrink: 0 }}>
              {formatRelativeTime(event.created_at)}
            </Typography>
          </Box>
        </Box>

        {/* Inline metadata */}
        <Box sx={{ mt: 1, mb: 1 }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Source:</strong> {event.source} · <strong>Type:</strong> {event.event_type}
          </Typography>

          {/* Collapsible payload */}
          {payloadExpanded ? (
            <Box sx={{ mt: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                <strong>Payload:</strong>
              </Typography>
              <Typography
                variant="caption"
                component="pre"
                sx={{
                  mt: 0.5,
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                  fontSize: '0.7rem',
                  backgroundColor: 'action.hover',
                  p: 0.5,
                  borderRadius: 0.5,
                }}
              >
                {payloadPreview}
              </Typography>
              <Button
                size="small"
                onClick={() => setPayloadExpanded(false)}
                sx={{ mt: 0.5, p: 0, minWidth: 'auto', fontSize: '0.7rem', textTransform: 'none' }}
              >
                Show less
              </Button>
            </Box>
          ) : (
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mt: 0.5, display: 'block', cursor: 'pointer' }}
              onClick={() => setPayloadExpanded(true)}
            >
              <strong>Payload:</strong> {truncatedPayload}{' '}
              <Box component="span" sx={{ color: 'primary.main', textDecoration: 'underline' }}>
                Show more
              </Box>
            </Typography>
          )}
        </Box>
      </CardContent>
      <CardActions sx={{ pt: 0, pb: 1, px: 1.5, gap: 0.5 }}>
        <Tooltip title="View Details">
          <IconButton size="small" onClick={handleViewDetails}>
            <VisibilityIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        {event.status === 'pending' && (
          <Tooltip title="Acknowledge">
            <IconButton size="small" color="primary" onClick={handleAcknowledge}>
              <CheckCircleIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
        <Tooltip title="Delete">
          <IconButton size="small" color="error" onClick={handleDelete}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </CardActions>
    </Card>
  );
};

export default EventCard;

