/**
 * React Query hooks for source data.
 *
 * Caching strategy:
 * - Data is considered fresh for 5 minutes (staleTime)
 * - Auto-refresh every 5 minutes (refetchInterval)
 * - Cache persists for 10 minutes (gcTime)
 * - Manual refresh bypasses cache via refresh=true parameter
 * - localStorage persistence for cross-refresh cache
 */
import { useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { useCallback, useState, useEffect } from 'react';
import { getCongress, getHedgeFunds, getPolymarket, getNews } from '../api/client';

const STALE_TIME = 5 * 60 * 1000; // 5 minutes - data is fresh
const GC_TIME = 10 * 60 * 1000; // 10 minutes - cache retention
const REFETCH_INTERVAL = 5 * 60 * 1000; // 5 minutes - auto-refresh
const CACHE_PREFIX = 'tradz_source_';
const CACHE_MAX_AGE = 30 * 60 * 1000; // 30 minutes max cache age

/**
 * localStorage cache utilities for persistent caching across page refreshes.
 */
function getCachedData<T>(key: string): T | undefined {
  try {
    const cached = localStorage.getItem(CACHE_PREFIX + key);
    if (!cached) return undefined;

    const { data, timestamp } = JSON.parse(cached);
    // Check if cache is still valid (within max age)
    if (Date.now() - timestamp > CACHE_MAX_AGE) {
      localStorage.removeItem(CACHE_PREFIX + key);
      return undefined;
    }
    return data as T;
  } catch {
    return undefined;
  }
}

function setCachedData<T>(key: string, data: T): void {
  try {
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify({
      data,
      timestamp: Date.now(),
    }));
  } catch {
    // Ignore storage errors (quota exceeded, etc.)
  }
}

/**
 * Common query options for all source hooks.
 */
const sourceQueryOptions = {
  staleTime: STALE_TIME,
  gcTime: GC_TIME,
  refetchInterval: REFETCH_INTERVAL,
  refetchOnWindowFocus: false, // Don't refetch on window focus
  refetchOnMount: true, // Refetch on mount but show cached data
  refetchIntervalInBackground: false, // Don't refetch when tab is hidden
  placeholderData: keepPreviousData, // Show cached data while fetching new data
};

/**
 * Hook to fetch congress trading data with localStorage persistence.
 */
export function useCongress(enabled = true) {
  const query = useQuery({
    queryKey: ['sources', 'congress'],
    queryFn: () => getCongress(false),
    enabled,
    initialData: getCachedData('congress'),
    ...sourceQueryOptions,
  });

  // Persist to localStorage when data changes
  useEffect(() => {
    if (query.data && !query.isPlaceholderData) {
      setCachedData('congress', query.data);
    }
  }, [query.data, query.isPlaceholderData]);

  return query;
}

/**
 * Hook to fetch hedge fund data with localStorage persistence.
 */
export function useHedgeFunds(enabled = true) {
  const query = useQuery({
    queryKey: ['sources', 'hedgefunds'],
    queryFn: () => getHedgeFunds(false),
    enabled,
    initialData: getCachedData('hedgefunds'),
    ...sourceQueryOptions,
  });

  useEffect(() => {
    if (query.data && !query.isPlaceholderData) {
      setCachedData('hedgefunds', query.data);
    }
  }, [query.data, query.isPlaceholderData]);

  return query;
}

/**
 * Hook to fetch Polymarket data with localStorage persistence.
 */
export function usePolymarket(enabled = true) {
  const query = useQuery({
    queryKey: ['sources', 'polymarket'],
    queryFn: () => getPolymarket(false),
    enabled,
    initialData: getCachedData('polymarket'),
    ...sourceQueryOptions,
  });

  useEffect(() => {
    if (query.data && !query.isPlaceholderData) {
      setCachedData('polymarket', query.data);
    }
  }, [query.data, query.isPlaceholderData]);

  return query;
}

/**
 * Hook to fetch news data with localStorage persistence.
 */
export function useNews(enabled = true) {
  const query = useQuery({
    queryKey: ['sources', 'news'],
    queryFn: () => getNews(false),
    enabled,
    initialData: getCachedData('news'),
    ...sourceQueryOptions,
  });

  useEffect(() => {
    if (query.data && !query.isPlaceholderData) {
      setCachedData('news', query.data);
    }
  }, [query.data, query.isPlaceholderData]);

  return query;
}

/**
 * Hook to manage all sources with unified refresh capability.
 * Returns combined state and a function to force refresh all sources.
 */
export function useSourcesManager() {
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const congress = useCongress();
  const hedgeFunds = useHedgeFunds();
  const polymarket = usePolymarket();
  const news = useNews();

  // Get the most recent dataUpdatedAt from all queries
  const lastUpdated = Math.max(
    congress.dataUpdatedAt || 0,
    hedgeFunds.dataUpdatedAt || 0,
    polymarket.dataUpdatedAt || 0,
    news.dataUpdatedAt || 0
  );

  // Force refresh all sources (bypasses cache)
  const forceRefreshAll = useCallback(async () => {
    setIsRefreshing(true);
    try {
      // Invalidate all source queries and refetch with refresh=true
      await Promise.all([
        queryClient.fetchQuery({
          queryKey: ['sources', 'congress'],
          queryFn: () => getCongress(true),
        }),
        queryClient.fetchQuery({
          queryKey: ['sources', 'hedgefunds'],
          queryFn: () => getHedgeFunds(true),
        }),
        queryClient.fetchQuery({
          queryKey: ['sources', 'polymarket'],
          queryFn: () => getPolymarket(true),
        }),
        queryClient.fetchQuery({
          queryKey: ['sources', 'news'],
          queryFn: () => getNews(true),
        }),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  }, [queryClient]);

  // Check if any source is currently fetching
  const isFetching = congress.isFetching || hedgeFunds.isFetching ||
                     polymarket.isFetching || news.isFetching;

  return {
    congress,
    hedgeFunds,
    polymarket,
    news,
    lastUpdated,
    isFetching,
    isRefreshing,
    forceRefreshAll,
  };
}
