/**
 * React Query hooks for source data.
 */
import { useQuery } from '@tanstack/react-query';
import { getCongress, getHedgeFunds, getPolymarket, getNews } from '../api/client';

const STALE_TIME = 5 * 60 * 1000; // 5 minutes

/**
 * Hook to fetch congress trading data.
 */
export function useCongress(enabled = true) {
  return useQuery({
    queryKey: ['sources', 'congress'],
    queryFn: () => getCongress(),
    enabled,
    staleTime: STALE_TIME,
  });
}

/**
 * Hook to fetch hedge fund data.
 */
export function useHedgeFunds(enabled = true) {
  return useQuery({
    queryKey: ['sources', 'hedgefunds'],
    queryFn: () => getHedgeFunds(),
    enabled,
    staleTime: STALE_TIME,
  });
}

/**
 * Hook to fetch Polymarket data.
 */
export function usePolymarket(enabled = true) {
  return useQuery({
    queryKey: ['sources', 'polymarket'],
    queryFn: () => getPolymarket(),
    enabled,
    staleTime: STALE_TIME,
  });
}

/**
 * Hook to fetch news data.
 */
export function useNews(enabled = true) {
  return useQuery({
    queryKey: ['sources', 'news'],
    queryFn: () => getNews(),
    enabled,
    staleTime: STALE_TIME,
  });
}
