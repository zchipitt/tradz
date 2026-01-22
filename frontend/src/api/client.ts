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
  BriefDetail,
  BriefSummaryItem,
  BriefDiffResponse,
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
  EventActionRequest,
  EventActionResponse,
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

/**
 * Performs an action on an event (pin, unpin, snooze, dismiss, resolve).
 * Calls POST /api/events/{event_id}/actions
 */
export const performEventAction = async (
  eventId: string,
  action: EventAction['action'],
  options?: { duration_hours?: number; reason?: string }
): Promise<EventActionResponse> => {
  const request: EventActionRequest = {
    action,
    duration_hours: options?.duration_hours ?? 24,
    reason: options?.reason,
  };
  const { data } = await apiClient.post<EventActionResponse>(
    `/events/${encodeURIComponent(eventId)}/actions`,
    request
  );
  return data;
};

/**
 * Legacy function for backwards compatibility.
 * @deprecated Use performEventAction instead
 */
export const updateEventAction = async (action: EventAction): Promise<EventActionResponse> => {
  return performEventAction(action.event_id, action.action, {
    duration_hours: action.snooze_hours,
    reason: action.reason,
  });
};

/**
 * Fetches system status from GET /api/system/status endpoint.
 */
export const getSystemStatus = async (): Promise<SystemStatusResponse> => {
  const { data } = await apiClient.get<SystemStatusResponse>('/system/status');
  return data;
};

import type { EventDetailResponse, TimelineResponse, TimelineSourceFilter, RecommendationResponse } from './types';

/**
 * Fetches event detail from GET /api/events/{event_id} endpoint.
 */
export const getEventById = async (eventId: string): Promise<EventDetailResponse> => {
  const { data } = await apiClient.get<EventDetailResponse>(`/events/${encodeURIComponent(eventId)}`);
  return data;
};

/**
 * Fetches event timeline from GET /api/events/{event_id}/timeline endpoint.
 * Returns observations sorted by timestamp descending with pagination.
 */
export const getEventTimeline = async (
  eventId: string,
  options?: {
    source?: TimelineSourceFilter;
    limit?: number;
    offset?: number;
  }
): Promise<TimelineResponse> => {
  const { data } = await apiClient.get<TimelineResponse>(
    `/events/${encodeURIComponent(eventId)}/timeline`,
    {
      params: {
        source: options?.source ?? 'all',
        limit: options?.limit ?? 20,
        offset: options?.offset ?? 0,
      },
    }
  );
  return data;
};

/**
 * Fetches event recommendation from GET /api/events/{event_id}/recommendation endpoint.
 * Returns either a TradeIdea (if quality gates pass) or ResearchPlan (if gates fail).
 */
export const getEventRecommendation = async (
  eventId: string
): Promise<RecommendationResponse> => {
  const { data } = await apiClient.get<RecommendationResponse>(
    `/events/${encodeURIComponent(eventId)}/recommendation`
  );
  return data;
};

// Daily Brief API

/**
 * Fetches the latest Daily Brief from GET /api/briefs/latest endpoint.
 */
export const getLatestBrief = async (
  refresh = false
): Promise<BriefDetail> => {
  const { data } = await apiClient.get<{ brief: BriefDetail }>('/briefs/latest', {
    params: { refresh },
  });
  return data.brief;
};

/**
 * Fetches a Daily Brief by date from GET /api/briefs/{date} endpoint.
 * Date should be in YYYY-MM-DD format.
 */
export const getBriefByDate = async (
  date: string,
  refresh = false
): Promise<BriefDetail> => {
  const { data } = await apiClient.get<{ brief: BriefDetail }>(
    `/briefs/${encodeURIComponent(date)}`,
    {
      params: { refresh },
    }
  );
  return data.brief;
};

/**
 * Fetches a list of available Daily Briefs from GET /api/briefs endpoint.
 * Supports pagination with limit and offset.
 */
export const getAvailableBriefs = async (
  limit = 20,
  offset = 0
): Promise<{ briefs: BriefSummaryItem[]; total_count: number }> => {
  const { data } = await apiClient.get<{ briefs: BriefSummaryItem[]; total_count: number }>(
    '/briefs',
    {
      params: { limit, offset },
    }
  );
  return data;
};

/**
 * Fetches brief comparison/diff between two dates from GET /api/reports/diff endpoint.
 * Compares current date's brief with baseline (default: yesterday).
 *
 * @param date - Comparison date in YYYY-MM-DD format (default: today)
 * @param baseline - Baseline date in YYYY-MM-DD format (default: yesterday)
 */
export const getBriefDiff = async (
  date?: string,
  baseline?: string
): Promise<BriefDiffResponse> => {
  const { data } = await apiClient.get<BriefDiffResponse>('/reports/diff', {
    params: {
      ...(date && { date }),
      ...(baseline && { baseline }),
    },
  });
  return data;
};

// Open Loops API
import type {
  OpenLoopsListResponse,
  OpenLoopDetail,
  CreateOpenLoopRequest,
  OpenLoopCreateResponse,
  UpdateOpenLoopRequest,
  OpenLoopUpdateResponse,
  OpenLoopDeleteResponse,
  OpenLoopStatusValue,
} from './types';

/**
 * Fetches open loops from GET /api/loops endpoint.
 * Supports filtering by status.
 */
export const getOpenLoops = async (
  status: OpenLoopStatusValue | 'all' = 'all',
  limit = 50,
  offset = 0
): Promise<OpenLoopsListResponse> => {
  const { data } = await apiClient.get<OpenLoopsListResponse>('/loops', {
    params: { status, limit, offset },
  });
  return data;
};

/**
 * Fetches a single open loop by ID from GET /api/loops/{loop_id} endpoint.
 */
export const getOpenLoopById = async (loopId: string): Promise<OpenLoopDetail> => {
  const { data } = await apiClient.get<OpenLoopDetail>(
    `/loops/${encodeURIComponent(loopId)}`
  );
  return data;
};

/**
 * Creates a new open loop via POST /api/loops endpoint.
 */
export const createOpenLoop = async (
  request: CreateOpenLoopRequest
): Promise<OpenLoopCreateResponse> => {
  const { data } = await apiClient.post<OpenLoopCreateResponse>('/loops', request);
  return data;
};

/**
 * Updates an open loop via PATCH /api/loops/{loop_id} endpoint.
 * Can update status and/or add a progress note.
 */
export const updateOpenLoop = async (
  loopId: string,
  request: UpdateOpenLoopRequest
): Promise<OpenLoopUpdateResponse> => {
  const { data } = await apiClient.patch<OpenLoopUpdateResponse>(
    `/loops/${encodeURIComponent(loopId)}`,
    request
  );
  return data;
};

/**
 * Deletes an open loop via DELETE /api/loops/{loop_id} endpoint.
 */
export const deleteOpenLoop = async (loopId: string): Promise<OpenLoopDeleteResponse> => {
  const { data } = await apiClient.delete<OpenLoopDeleteResponse>(
    `/loops/${encodeURIComponent(loopId)}`
  );
  return data;
};
