/**
 * React Query hooks for signals data.
 *
 * Caching strategy:
 * - Data is considered fresh for 5 minutes (staleTime)
 * - Auto-refresh every 5 minutes (refetchInterval)
 * - Cache persists for 10 minutes (gcTime)
 * - Manual refresh bypasses cache via refresh=true parameter
 */
import { useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import { getSignals, getTopSignals, getSignalBySymbol } from '../api/client';

export const SIGNALS_QUERY_KEY = ['signals'];
export const TOP_SIGNALS_QUERY_KEY = ['signals', 'top'];

const STALE_TIME = 5 * 60 * 1000; // 5 minutes - data is fresh
const GC_TIME = 10 * 60 * 1000; // 10 minutes - cache retention
const REFETCH_INTERVAL = 5 * 60 * 1000; // 5 minutes - auto-refresh

/**
 * Common query options for signal hooks.
 */
const signalQueryOptions = {
  staleTime: STALE_TIME,
  gcTime: GC_TIME,
  refetchInterval: REFETCH_INTERVAL,
  refetchOnWindowFocus: false,
  refetchOnMount: false,
  refetchIntervalInBackground: false,
  placeholderData: keepPreviousData, // Show cached data while fetching new data
};

/**
 * Hook to fetch all signals.
 */
export function useSignals(enabled = true) {
  return useQuery({
    queryKey: SIGNALS_QUERY_KEY,
    queryFn: () => getSignals(false),
    enabled,
    ...signalQueryOptions,
  });
}

/**
 * Hook to fetch top signals only.
 */
export function useTopSignals(enabled = true) {
  return useQuery({
    queryKey: TOP_SIGNALS_QUERY_KEY,
    queryFn: () => getTopSignals(false),
    enabled,
    ...signalQueryOptions,
  });
}

/**
 * Hook to fetch signal for a specific symbol.
 */
export function useSignal(symbol: string, enabled = true) {
  return useQuery({
    queryKey: ['signals', symbol],
    queryFn: () => getSignalBySymbol(symbol, false),
    enabled: enabled && !!symbol,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook to manually refresh signals.
 */
export function useRefreshSignals() {
  const queryClient = useQueryClient();

  return async () => {
    // Fetch with refresh=true and update cache
    const freshData = await getSignals(true);
    queryClient.setQueryData(SIGNALS_QUERY_KEY, freshData);
    return freshData;
  };
}

/**
 * Hook to manage signals with unified refresh capability.
 * Returns combined state and a function to force refresh.
 */
export function useSignalsManager() {
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const signals = useSignals();
  const topSignals = useTopSignals();

  const lastUpdated = Math.max(
    signals.dataUpdatedAt || 0,
    topSignals.dataUpdatedAt || 0
  );

  const forceRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        queryClient.fetchQuery({
          queryKey: SIGNALS_QUERY_KEY,
          queryFn: () => getSignals(true),
        }),
        queryClient.fetchQuery({
          queryKey: TOP_SIGNALS_QUERY_KEY,
          queryFn: () => getTopSignals(true),
        }),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  }, [queryClient]);

  const isFetching = signals.isFetching || topSignals.isFetching;

  return {
    signals,
    topSignals,
    lastUpdated,
    isFetching,
    isRefreshing,
    forceRefresh,
  };
}
