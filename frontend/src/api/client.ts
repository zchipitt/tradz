/**
 * API client configuration and base functions.
 */
import axios from 'axios';
import type {
  SignalsResponse,
  TopSignalsResponse,
  Signal,
  CongressResponse,
  HedgeFundResponse,
  PolymarketResponse,
  NewsResponse,
  HealthResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export const getHealth = async (): Promise<HealthResponse> => {
  const { data } = await apiClient.get<HealthResponse>('/health');
  return data;
};

// Signals API
export const getSignals = async (refresh = false): Promise<SignalsResponse> => {
  const { data } = await apiClient.get<SignalsResponse>('/signals', {
    params: { refresh },
  });
  return data;
};

export const getTopSignals = async (refresh = false): Promise<TopSignalsResponse> => {
  const { data } = await apiClient.get<TopSignalsResponse>('/signals/top', {
    params: { refresh },
  });
  return data;
};

export const getSignalBySymbol = async (symbol: string, refresh = false): Promise<Signal> => {
  const { data } = await apiClient.get<Signal>(`/signals/${encodeURIComponent(symbol)}`, {
    params: { refresh },
  });
  return data;
};

// Sources API
export const getCongress = async (refresh = false): Promise<CongressResponse> => {
  const { data } = await apiClient.get<CongressResponse>('/sources/congress', {
    params: { refresh },
  });
  return data;
};

export const getHedgeFunds = async (refresh = false): Promise<HedgeFundResponse> => {
  const { data } = await apiClient.get<HedgeFundResponse>('/sources/hedgefunds', {
    params: { refresh },
  });
  return data;
};

export const getPolymarket = async (refresh = false): Promise<PolymarketResponse> => {
  const { data } = await apiClient.get<PolymarketResponse>('/sources/polymarket', {
    params: { refresh },
  });
  return data;
};

export const getNews = async (refresh = false): Promise<NewsResponse> => {
  const { data } = await apiClient.get<NewsResponse>('/sources/news', {
    params: { refresh },
  });
  return data;
};

// Events API (backend not yet implemented, these will return empty data)
import type { EventsResponse, Event, EventAction, SourceHealth } from './types';

export const getEvents = async (_refresh = false): Promise<EventsResponse> => {
  // Backend events endpoint not yet implemented
  // Return empty structure for now
  return {
    events: [],
    daily_brief: {
      date: new Date().toISOString().split('T')[0],
      executive_summary: [],
      top_events: [],
      trade_ideas: [],
      data_quality: {
        sources_ok: 0,
        sources_total: 0,
        errors: [],
        stalest_source: '',
        stalest_age_hours: 0,
      },
      open_loops: [],
    },
    generated_at: new Date().toISOString(),
  };
};

export const updateEventAction = async (_action: EventAction): Promise<Event> => {
  // Backend events endpoint not yet implemented
  throw new Error('Events API not yet implemented');
};

export const getSourcesHealth = async (): Promise<SourceHealth[]> => {
  // Backend source health endpoint not yet implemented
  // Return empty array for now
  return [];
};
