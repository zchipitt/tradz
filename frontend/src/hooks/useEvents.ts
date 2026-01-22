/**
 * React Query hooks for events data.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getEvents, performEventAction, getSystemStatus } from '../api/client';
import type { EventAction, EventsResponse, Event, EventState } from '../api/types';

export const EVENTS_QUERY_KEY = ['events'];

/**
 * Hook to fetch all events and daily brief.
 */
export function useEvents(enabled = true) {
  return useQuery({
    queryKey: EVENTS_QUERY_KEY,
    queryFn: () => getEvents(),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  });
}

/**
 * Hook to perform event actions with optimistic updates.
 * Supports pin, unpin, snooze, dismiss, resolve actions.
 */
export function useEventAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (action: EventAction) =>
      performEventAction(action.event_id, action.action, {
        duration_hours: action.snooze_hours,
        reason: action.reason,
      }),

    // Optimistic update
    onMutate: async (action: EventAction) => {
      // Cancel any outgoing refetches to prevent overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: EVENTS_QUERY_KEY });

      // Snapshot current data for rollback
      const previousData = queryClient.getQueryData<EventsResponse>(EVENTS_QUERY_KEY);

      // Optimistically update the cache
      if (previousData) {
        const updatedEvents = previousData.events.map((event: Event) => {
          if (event.id !== action.event_id) return event;

          // Apply optimistic changes based on action
          switch (action.action) {
            case 'pin':
              return { ...event, pinned: true };
            case 'unpin':
              return { ...event, pinned: false };
            case 'snooze':
              // Calculate snooze until timestamp
              const hours = action.snooze_hours ?? 24;
              const snoozedUntil = new Date();
              snoozedUntil.setHours(snoozedUntil.getHours() + hours);
              return { ...event, snoozed_until: snoozedUntil.toISOString() };
            case 'dismiss':
              return { ...event, state: 'dismissed' as EventState };
            case 'resolve':
              return { ...event, state: 'resolved' as EventState };
            default:
              return event;
          }
        });

        queryClient.setQueryData<EventsResponse>(EVENTS_QUERY_KEY, {
          ...previousData,
          events: updatedEvents,
        });
      }

      // Return context with previous data for rollback
      return { previousData };
    },

    // On error, rollback to previous data
    onError: (_err, _action, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(EVENTS_QUERY_KEY, context.previousData);
      }
    },

    // Always refetch after mutation settles
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: EVENTS_QUERY_KEY });
    },
  });
}

/**
 * Type-safe hook return for useEventAction with additional helpers
 */
export function useEventActions() {
  const mutation = useEventAction();

  return {
    ...mutation,
    pin: (eventId: string) =>
      mutation.mutateAsync({ event_id: eventId, action: 'pin' }),
    unpin: (eventId: string) =>
      mutation.mutateAsync({ event_id: eventId, action: 'unpin' }),
    snooze: (eventId: string, hours = 24) =>
      mutation.mutateAsync({ event_id: eventId, action: 'snooze', snooze_hours: hours }),
    dismiss: (eventId: string, reason?: string) =>
      mutation.mutateAsync({ event_id: eventId, action: 'dismiss', reason }),
    resolve: (eventId: string) =>
      mutation.mutateAsync({ event_id: eventId, action: 'resolve' }),
  };
}

export const SYSTEM_STATUS_KEY = ['system', 'status'];

/**
 * Hook to fetch system status from GET /api/system/status.
 * Auto-refreshes every 5 minutes with 5-minute stale time.
 */
export function useSystemStatus(enabled = true) {
  return useQuery({
    queryKey: SYSTEM_STATUS_KEY,
    queryFn: () => getSystemStatus(),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  });
}

/**
 * Hook to manually refresh events.
 */
export function useRefreshEvents() {
  const queryClient = useQueryClient();

  return async () => {
    const freshData = await getEvents(true);
    queryClient.setQueryData(EVENTS_QUERY_KEY, freshData);
    return freshData;
  };
}
