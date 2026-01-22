/**
 * React Query hooks for events data.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getEvents, updateEventAction, getSystemStatus } from '../api/client';
import type { EventAction } from '../api/types';

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
 * Hook to perform event actions (dismiss, snooze, pin, etc).
 */
export function useEventAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (action: EventAction) => updateEventAction(action),
    onSuccess: () => {
      // Invalidate events query to refetch
      queryClient.invalidateQueries({ queryKey: EVENTS_QUERY_KEY });
    },
  });
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
