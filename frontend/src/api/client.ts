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

// Events API (with mock data fallback until backend is ready)
import type { EventsResponse, Event, EventAction, SourceHealth } from './types';

// Mock data for events until backend endpoint is ready
const mockEvents: Event[] = [
  {
    id: 'evt-001',
    title: 'Rep. Pelosi purchases NVDA calls ahead of chip bill vote',
    category: 'congress_trade',
    state: 'new',
    attention_score: 87,
    anomaly_score: 45,
    catalyst_score: 92,
    flow_score: 85,
    confidence_score: 78,
    assets: ['NVDA'],
    asset_types: ['equity'],
    evidence: [
      {
        source: 'Congress',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        summary: 'Disclosure filed: $500K-$1M in NVDA call options',
        confidence: 95,
      },
      {
        source: 'News',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        summary: 'CHIPS Act vote scheduled for next week',
        url: 'https://example.com/chips-act',
        confidence: 85,
      },
    ],
    evidence_count: 2,
    first_seen: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    last_updated: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    summary: 'Congressional trade detected with high catalyst alignment to upcoming legislation',
    trade_plan: {
      thesis: 'Follow smart money into NVDA ahead of potential chip subsidies catalyst',
      invalidation: 'CHIPS Act vote delayed or fails, NVDA breaks below $800',
      timeframe: '1-2 weeks',
      risk_level: 'medium',
    },
  },
  {
    id: 'evt-002',
    title: 'Polymarket: Fed rate cut probability surges to 78%',
    category: 'polymarket_shift',
    state: 'ongoing',
    attention_score: 79,
    anomaly_score: 72,
    catalyst_score: 88,
    flow_score: 15,
    confidence_score: 65,
    assets: ['SPY', 'QQQ', 'TLT'],
    asset_types: ['equity'],
    evidence: [
      {
        source: 'Polymarket',
        timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        summary: 'March rate cut probability: 78% (+12% in 24h)',
        url: 'https://polymarket.com/event/fed-rate-cut',
        confidence: 90,
      },
      {
        source: 'News',
        timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
        summary: 'Fed minutes show dovish tilt, inflation cooling',
        confidence: 75,
      },
    ],
    evidence_count: 3,
    first_seen: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    last_updated: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    summary: 'Prediction market showing strong shift toward March rate cut expectation',
  },
  {
    id: 'evt-003',
    title: 'BTC volume spike: 3.2x average with price consolidation',
    category: 'volume_spike',
    state: 'new',
    attention_score: 73,
    anomaly_score: 88,
    catalyst_score: 25,
    flow_score: 45,
    confidence_score: 82,
    assets: ['BTC/USDT'],
    asset_types: ['crypto'],
    evidence: [
      {
        source: 'Market',
        timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        summary: 'Volume z-score: 3.2, Price stable at $42,500',
        confidence: 95,
      },
    ],
    evidence_count: 1,
    first_seen: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    last_updated: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    summary: 'Unusual volume accumulation without significant price movement - potential breakout setup',
  },
  {
    id: 'evt-004',
    title: 'Bridgewater increases AAPL position by 340%',
    category: 'hedgefund_filing',
    state: 'stale',
    attention_score: 65,
    anomaly_score: 55,
    catalyst_score: 40,
    flow_score: 92,
    confidence_score: 88,
    assets: ['AAPL'],
    asset_types: ['equity'],
    evidence: [
      {
        source: '13F Filing',
        timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        summary: '13F shows $2.1B AAPL position, up from $480M',
        confidence: 98,
      },
    ],
    evidence_count: 1,
    first_seen: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    last_updated: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    summary: 'Major institutional accumulation detected in 13F filing',
  },
  {
    id: 'evt-005',
    title: 'TSLA earnings miss: -8% after hours',
    category: 'price_anomaly',
    state: 'resolved',
    attention_score: 82,
    anomaly_score: 95,
    catalyst_score: 85,
    flow_score: 30,
    confidence_score: 92,
    assets: ['TSLA'],
    asset_types: ['equity'],
    evidence: [
      {
        source: 'Market',
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        summary: 'Price drop -8.2% AH, volume 4.5x average',
        confidence: 98,
      },
      {
        source: 'News',
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        summary: 'Q4 earnings miss, margin compression concerns',
        confidence: 95,
      },
    ],
    evidence_count: 4,
    first_seen: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    last_updated: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    summary: 'Earnings catalyst resolved - price discovery complete',
  },
];

const mockDailyBrief = {
  date: new Date().toISOString().split('T')[0],
  executive_summary: [
    'Congressional trading activity elevated: 3 new disclosures from committee members',
    'Rate cut expectations shifted significantly - Polymarket now pricing 78% March cut',
    'Crypto showing accumulation patterns despite headline uncertainty',
    'Earnings season catalyst resolved for major tech names',
  ],
  top_events: mockEvents.filter((e) => e.state !== 'resolved' && e.state !== 'dismissed').slice(0, 3),
  trade_ideas: mockEvents.filter((e) => e.trade_plan && e.confidence_score >= 70).map((e) => e.trade_plan!),
  data_quality: {
    sources_ok: 6,
    sources_total: 7,
    errors: ['NewsAPI: rate limit exceeded'],
    stalest_source: 'Congress',
    stalest_age_hours: 48,
  },
  open_loops: [
    'Monitor NVDA price action around CHIPS Act vote',
    'Fed meeting March 20 - key catalyst for rate expectations',
  ],
};

export const getEvents = async (_refresh = false): Promise<EventsResponse> => {
  // TODO: Replace with actual API call when backend is ready
  // const { data } = await apiClient.get<EventsResponse>('/events', { params: { refresh } });
  // return data;

  // Return mock data for now
  await new Promise((resolve) => setTimeout(resolve, 500)); // Simulate network delay
  return {
    events: mockEvents,
    daily_brief: mockDailyBrief,
    generated_at: new Date().toISOString(),
  };
};

export const updateEventAction = async (action: EventAction): Promise<Event> => {
  // TODO: Replace with actual API call when backend is ready
  // const { data } = await apiClient.post<Event>('/events/action', action);
  // return data;

  await new Promise((resolve) => setTimeout(resolve, 300));
  const event = mockEvents.find((e) => e.id === action.event_id);
  if (!event) throw new Error('Event not found');

  // Apply action to mock data
  switch (action.action) {
    case 'dismiss':
      event.state = 'dismissed';
      break;
    case 'resolve':
      event.state = 'resolved';
      break;
    case 'pin':
      event.pinned = true;
      break;
    case 'unpin':
      event.pinned = false;
      break;
    case 'snooze':
      event.snoozed_until = new Date(Date.now() + (action.snooze_hours || 24) * 60 * 60 * 1000).toISOString();
      break;
  }
  return event;
};

export const getSourcesHealth = async (): Promise<SourceHealth[]> => {
  // TODO: Replace with actual API call
  await new Promise((resolve) => setTimeout(resolve, 200));
  return [
    { name: 'Equities', status: 'ok', records_count: 45 },
    { name: 'Crypto', status: 'ok', records_count: 12 },
    { name: 'Congress', status: 'warning', last_success: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString() },
    { name: 'HedgeFunds', status: 'ok', records_count: 8 },
    { name: 'Polymarket', status: 'ok', records_count: 25 },
    { name: 'News', status: 'error', error_message: 'Rate limit exceeded' },
    { name: 'SEC', status: 'ok', records_count: 15 },
  ];
};
