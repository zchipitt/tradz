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

// Events API - calls backend GET /api/events endpoint
import type {
  EventsResponse,
  EventsListResponse,
  EventListItem,
  Event,
  EventAction,
  EventCategory,
  EventType,
  SystemStatusResponse,
} from './types';

/**
 * Maps backend EventType to legacy UI EventCategory for display.
 */
function mapEventTypeToCategory(eventType: EventType): EventCategory {
  switch (eventType) {
    case 'flow_congress':
      return 'congress_trade';
    case 'flow_13f':
      return 'hedgefund_filing';
    case 'prediction_shift':
      return 'polymarket_shift';
    case 'catalyst_news':
      return 'news_cluster';
    case 'market_anomaly':
      return 'price_anomaly';
    case 'catalyst_filing':
      return 'sec_filing';
    default:
      return 'price_anomaly'; // Default fallback
  }
}

/**
 * Transforms backend EventListItem to legacy Event format for UI components.
 */
function transformEventListItem(item: EventListItem): Event {
  return {
    id: item.event_id,
    title: item.title,
    category: mapEventTypeToCategory(item.event_type),
    state: item.status,
    attention_score: Math.round(item.attention_score),
    anomaly_score: Math.round(item.scores.anomaly_score),
    catalyst_score: Math.round(item.scores.catalyst_score),
    flow_score: Math.round(item.scores.flow_score),
    confidence_score: Math.round(item.scores.confidence_score),
    assets: item.ticker ? [item.ticker] : [],
    asset_types: ['equity'], // Default, can be extended later
    evidence: [], // Detailed evidence requires separate API call
    evidence_count: item.observation_count,
    first_seen: item.start_at,
    last_updated: item.last_update_at,
    summary: '', // Summary requires separate API call to event detail
    pinned: item.pinned,
    snoozed_until: item.snoozed_until ?? undefined,
  };
}

/**
 * Fetches events from backend API with optional status filter.
 */
export const getEventsFromApi = async (
  status: 'active' | 'resolved' | 'dismissed' | 'all' = 'active',
  limit = 50,
  offset = 0
): Promise<EventsListResponse> => {
  const { data } = await apiClient.get<EventsListResponse>('/events', {
    params: { status, limit, offset },
  });
  return data;
};

/**
 * Legacy getEvents function that returns EventsResponse format for backwards compatibility.
 */
export const getEvents = async (_refresh = false): Promise<EventsResponse> => {
  try {
    // Fetch all events (not just active) to support filtering in UI
    const response = await getEventsFromApi('all', 100, 0);
    const events = response.events.map(transformEventListItem);

    return {
      events,
      daily_brief: {
        date: new Date().toISOString().split('T')[0],
        executive_summary: events.length > 0
          ? [`${events.length} active events across your watchlist.`]
          : ['No active events to report.'],
        top_events: events.slice(0, 5),
        trade_ideas: [],
        data_quality: {
          sources_ok: 7,
          sources_total: 7,
          errors: [],
          stalest_source: '',
          stalest_age_hours: 0,
        },
        open_loops: [],
      },
      generated_at: new Date().toISOString(),
    };
  } catch (error) {
    // If API fails, throw error to let React Query handle it
    throw error;
  }
};

export const updateEventAction = async (_action: EventAction): Promise<Event> => {
  // Backend events action endpoint not yet implemented (US-006)
  throw new Error('Events action API not yet implemented');
};

/**
 * Fetches system status from GET /api/system/status endpoint.
 */
export const getSystemStatus = async (): Promise<SystemStatusResponse> => {
  const { data } = await apiClient.get<SystemStatusResponse>('/system/status');
  return data;
};
