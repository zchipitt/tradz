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
