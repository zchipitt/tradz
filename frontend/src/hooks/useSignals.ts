/**
 * React Query hooks for signals data.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getSignals, getTopSignals, getSignalBySymbol } from '../api/client';

export const SIGNALS_QUERY_KEY = ['signals'];
export const TOP_SIGNALS_QUERY_KEY = ['signals', 'top'];

/**
 * Hook to fetch all signals.
 */
export function useSignals(enabled = true) {
  return useQuery({
    queryKey: SIGNALS_QUERY_KEY,
    queryFn: () => getSignals(),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  });
}

/**
 * Hook to fetch top signals only.
 */
export function useTopSignals(enabled = true) {
  return useQuery({
    queryKey: TOP_SIGNALS_QUERY_KEY,
    queryFn: () => getTopSignals(),
    enabled,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
  });
}

/**
 * Hook to fetch signal for a specific symbol.
 */
export function useSignal(symbol: string, enabled = true) {
  return useQuery({
    queryKey: ['signals', symbol],
    queryFn: () => getSignalBySymbol(symbol),
    enabled: enabled && !!symbol,
    staleTime: 5 * 60 * 1000,
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
