/**
 * React Query hooks for events data.
 */
import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { getEvents, performEventAction, getSystemStatus, getEventById, getEventTimeline, getEventRecommendation } from '../api/client';
import type { EventAction, EventsResponse, Event, EventState, EventDetailResponse, TimelineResponse, TimelineSourceFilter, RecommendationResponse } from '../api/types';

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

export const EVENT_DETAIL_KEY = (eventId: string) => ['events', eventId];

/**
 * Hook to fetch a single event's details by ID.
 * Returns detailed event data including observations and facts.
 */
export function useEventDetail(eventId: string | undefined, enabled = true) {
  return useQuery<EventDetailResponse>({
    queryKey: EVENT_DETAIL_KEY(eventId ?? ''),
    queryFn: () => getEventById(eventId!),
    enabled: enabled && !!eventId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: (failureCount, error) => {
      // Don't retry on 404 errors
      if (error instanceof Error && error.message.includes('404')) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export const EVENT_TIMELINE_KEY = (eventId: string, source: TimelineSourceFilter) => ['events', eventId, 'timeline', source];

/**
 * Hook to fetch event timeline with infinite scrolling / load more pagination.
 * Returns observations in reverse chronological order.
 */
export function useEventTimeline(
  eventId: string | undefined,
  source: TimelineSourceFilter = 'all',
  enabled = true
) {
  return useInfiniteQuery<TimelineResponse>({
    queryKey: EVENT_TIMELINE_KEY(eventId ?? '', source),
    queryFn: ({ pageParam = 0 }) =>
      getEventTimeline(eventId!, {
        source,
        limit: 20,
        offset: pageParam as number,
      }),
    getNextPageParam: (lastPage) => {
      // If we have more observations, return next offset
      const nextOffset = lastPage.offset + lastPage.limit;
      return nextOffset < lastPage.total_count ? nextOffset : undefined;
    },
    initialPageParam: 0,
    enabled: enabled && !!eventId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export const EVENT_RECOMMENDATION_KEY = (eventId: string) => ['events', eventId, 'recommendation'];

/**
 * Hook to fetch event recommendation (trade idea or research plan).
 * Evaluates quality gates and returns appropriate recommendation.
 */
export function useEventRecommendation(eventId: string | undefined, enabled = true) {
  return useQuery<RecommendationResponse>({
    queryKey: EVENT_RECOMMENDATION_KEY(eventId ?? ''),
    queryFn: () => getEventRecommendation(eventId!),
    enabled: enabled && !!eventId,
    staleTime: 5 * 60 * 1000, // 5 minutes (recommendations don't change often)
    retry: (failureCount, error) => {
      // Don't retry on 404 errors
      if (error instanceof Error && error.message.includes('404')) {
        return false;
      }
      return failureCount < 2;
    },
  });
}
