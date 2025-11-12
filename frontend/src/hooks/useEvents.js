import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createEvent,
  getInbox,
  getEvent,
  acknowledgeEvent,
  deleteEvent,
} from '../services/api';

/**
 * Hook to create a new event
 */
export const useCreateEvent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createEvent,
    onSuccess: () => {
      // Invalidate inbox query to refresh the list
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
    },
  });
};

/**
 * Hook to fetch inbox (pending events)
 * @param {Object} params - Query parameters
 */
export const useInbox = (params = {}) => {
  return useQuery({
    queryKey: ['inbox', params.limit, params.cursor, params.source, params.event_type, params.priority],
    queryFn: () => getInbox(params),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    refetchOnWindowFocus: false,
    retry: 1,
  });
};

/**
 * Hook to fetch a single event
 * @param {string} eventId - Event ID
 */
export const useEvent = (eventId) => {
  return useQuery({
    queryKey: ['event', eventId],
    queryFn: () => getEvent(eventId),
    enabled: !!eventId, // Only fetch if eventId is provided
    refetchOnWindowFocus: false,
    retry: 1,
  });
};

/**
 * Hook to acknowledge an event
 */
export const useAcknowledgeEvent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: acknowledgeEvent,
    onSuccess: (data, eventId) => {
      // Invalidate inbox and event queries
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
      queryClient.invalidateQueries({ queryKey: ['event', eventId] });
    },
  });
};

/**
 * Hook to delete an event
 */
export const useDeleteEvent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteEvent,
    onSuccess: (data, eventId) => {
      // Invalidate inbox and event queries
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
      queryClient.invalidateQueries({ queryKey: ['event', eventId] });
    },
  });
};

