/**
 * React Query hooks for Daily Brief API interactions.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLatestBrief, getBriefByDate, getAvailableBriefs } from '../api/client';
import type { BriefDetail, BriefSummaryItem } from '../api/types';

// Query keys
export const DAILY_BRIEF_KEY = ['daily-brief'];
export const LATEST_BRIEF_KEY = ['daily-brief', 'latest'];
export const BRIEFS_LIST_KEY = ['daily-brief', 'list'];

/**
 * Hook to fetch the latest Daily Brief.
 * Data refreshes every 5 minutes and becomes stale after 5 minutes.
 */
export function useLatestBrief(options?: { refresh?: boolean }) {
  const refresh = options?.refresh ?? false;

  return useQuery<{ brief: BriefDetail }>({
    queryKey: [...LATEST_BRIEF_KEY, { refresh }],
    queryFn: () => getLatestBrief(refresh).then(brief => ({ brief })),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
    retry: (failureCount, error) => {
      // Don't retry 404s (brief not generated yet)
      if (error?.message?.includes('404')) {
        return false;
      }
      return failureCount < 2; // Retry 2 times for other errors
    },
  });
}

/**
 * Hook to fetch a Daily Brief by date.
 * Date should be in YYYY-MM-DD format.
 * Data is cached per date and stale after 5 minutes.
 */
export function useBriefByDate(date: string, options?: { refresh?: boolean }) {
  const refresh = options?.refresh ?? false;

  return useQuery<{ brief: BriefDetail }>({
    queryKey: [...DAILY_BRIEF_KEY, date, { refresh }],
    queryFn: () => getBriefByDate(date, refresh).then(brief => ({ brief })),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error) => {
      // Don't retry 404s (brief not found)
      if (error?.message?.includes('404')) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

/**
 * Hook to fetch a list of available Daily Briefs.
 * Supports pagination with limit and offset.
 * Results are cached for 10 minutes.
 */
export function useAvailableBriefs(limit = 20, offset = 0) {
  return useQuery<{ briefs: BriefSummaryItem[]; total_count: number }>({
    queryKey: [...BRIEFS_LIST_KEY, { limit, offset }],
    queryFn: () => getAvailableBriefs(limit, offset),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Convenience hook that returns helper methods for Daily Brief actions.
 * Includes manual refetch and briefs data.
 */
export function useBriefActions() {
  const queryClient = useQueryClient();

  const refetchLatest = () => {
    return queryClient.refetchQueries({ queryKey: LATEST_BRIEF_KEY });
  };

  const refetchByDate = (date: string) => {
    return queryClient.refetchQueries({ queryKey: [...DAILY_BRIEF_KEY, date] });
  };

  const refetchList = () => {
    return queryClient.refetchQueries({ queryKey: BRIEFS_LIST_KEY });
  };

  // Invalidate all brief queries
  const invalidateAll = () => {
    return queryClient.invalidateQueries({ queryKey: DAILY_BRIEF_KEY });
  };

  return {
    refetchLatest,
    refetchByDate,
    refetchList,
    invalidateAll,
  };
}

/**
 * Hook to generate a new Daily Brief (integration with backend generation endpoint).
 * This would typically trigger the Python backend to run the daily brief generation.
 */
export function useGenerateBrief() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params?: { date?: string; refresh?: boolean }) => {
      // This would call the backend generation endpoint
      // Currently using the latest endpoint with refresh flag
      const date = params?.date;
      const refresh = params?.refresh ?? false;

      if (date) {
        return getBriefByDate(date, refresh);
      } else {
        return getLatestBrief(refresh);
      }
    },
    onSuccess: () => {
      // Invalidate all brief-related queries to refresh the data
      queryClient.invalidateQueries({ queryKey: DAILY_BRIEF_KEY });
    },
  });
}
