import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getWebhooks, deleteWebhook, testWebhook } from '../../services/api';
import { useNotification } from '../../contexts/NotificationContext';
import WebhookForm from './WebhookForm';

const WebhookList = () => {
  const { showSuccess, showError } = useNotification();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [webhookToDelete, setWebhookToDelete] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState(null);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['webhooks'],
    queryFn: () => getWebhooks({ limit: 50 }),
  });

  const deleteMutation = useMutation({
    mutationFn: (webhookId) => deleteWebhook(webhookId),
    onSuccess: () => {
      queryClient.invalidateQueries(['webhooks']);
      showSuccess('Webhook deleted successfully');
      setDeleteDialogOpen(false);
      setWebhookToDelete(null);
    },
    onError: (error) => {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to delete webhook';
      showError(errorMessage);
    },
  });

  const testMutation = useMutation({
    mutationFn: (webhookId) => testWebhook(webhookId),
    onSuccess: (response) => {
      const status = response.data.status;
      if (status === 'success') {
        showSuccess('Webhook test successful');
      } else {
        showError(`Webhook test failed: ${response.data.message}`);
      }
    },
    onError: (error) => {
      const errorMessage =
        error.formattedError?.message || error.message || 'Failed to test webhook';
      showError(errorMessage);
    },
  });

  const handleDelete = (webhook) => {
    setWebhookToDelete(webhook);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (webhookToDelete) {
      deleteMutation.mutate(webhookToDelete.webhook_id);
    }
  };

  const handleEdit = (webhook) => {
    setEditingWebhook(webhook);
    setFormOpen(true);
  };

  const handleTest = (webhookId) => {
    testMutation.mutate(webhookId);
  };

  const handleCreate = () => {
    setEditingWebhook(null);
    setFormOpen(true);
  };

  const handleFormClose = () => {
    setFormOpen(false);
    setEditingWebhook(null);
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error.formattedError?.message || error.message || 'Failed to load webhooks'}
      </Alert>
    );
  }

  const webhooks = data?.data?.webhooks || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Webhooks
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreate}
        >
          Create Webhook
        </Button>
      </Box>

      {webhooks.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            No webhooks found
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
            sx={{ mt: 2 }}
          >
            Create Your First Webhook
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>URL</TableCell>
                <TableCell>Events</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {webhooks.map((webhook) => (
                <TableRow key={webhook.webhook_id} hover>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                      {webhook.url}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {webhook.events?.includes('*') ? (
                      <Chip label="All Events" size="small" color="primary" />
                    ) : (
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {webhook.events?.slice(0, 2).map((event, idx) => (
                          <Chip key={idx} label={event} size="small" />
                        ))}
                        {webhook.events?.length > 2 && (
                          <Chip label={`+${webhook.events.length - 2}`} size="small" />
                        )}
                      </Box>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={webhook.is_active ? 'Active' : 'Inactive'}
                      color={webhook.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(webhook.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => handleTest(webhook.webhook_id)}
                      title="Test webhook"
                    >
                      <PlayArrowIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleEdit(webhook)}
                      title="Edit webhook"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(webhook)}
                      title="Delete webhook"
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Webhook</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this webhook? This action cannot be undone.
          </Typography>
          {webhookToDelete && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              URL: {webhookToDelete.url}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmDelete}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? <CircularProgress size={20} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      <WebhookForm
        open={formOpen}
        onClose={handleFormClose}
        webhook={editingWebhook}
        onSuccess={() => {
          queryClient.invalidateQueries(['webhooks']);
          handleFormClose();
        }}
      />
    </Box>
  );
};

export default WebhookList;

