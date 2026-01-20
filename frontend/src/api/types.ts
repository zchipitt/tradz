/**
 * TypeScript types matching backend Pydantic schemas.
 */

export type AssetType = 'equity' | 'crypto';

export interface SignalMetrics {
  day_return: number;
  week_return: number;
  volatility_7d: number;
  volatility_30d: number;
  volatility_change: number;
  volume_ratio: number;
  last_price: number;
}

export interface Signal {
  symbol: string;
  score: number;
  asset_type: AssetType;
  metrics: SignalMetrics;
  why: string[];
  caveats: string[];
}

export interface SignalsResponse {
  top_equities: Signal[];
  top_crypto: Signal[];
  all_signals: Signal[];
  generated_at: string;
}

export interface TopSignalsResponse {
  top_equities: Signal[];
  top_crypto: Signal[];
  generated_at: string;
}

// Source data types

export interface EquityData {
  symbol: string;
  last_price: number;
  day_return: number;
  week_return: number;
  volume: number;
  data_points: number;
}

export interface CryptoData {
  symbol: string;
  last_price: number;
  day_return: number;
  week_return: number;
  volume: number;
  data_points: number;
}

export interface CongressTrade {
  ticker: string;
  member: string;
  chamber: 'House' | 'Senate';
  party?: string;
  state?: string;
  type: 'purchase' | 'sale' | 'exchange';
  amount_str: string;
  transaction_date?: string;
  disclosure_date?: string;
  description?: string;
}

export interface CongressResponse {
  trades: CongressTrade[];
  summary?: Record<string, unknown>;
  watchlist_overlap: CongressTrade[];
  count: number;
  error?: string;
}

export interface HedgeFundFiling {
  cik: string;
  fund_name: string;
  accession_number?: string;
  filing_date?: string;
}

export interface HedgeFundResponse {
  filings: HedgeFundFiling[];
  filings_found: number;
  notable_funds: string[];
  error?: string;
}

export interface PolymarketOutcome {
  name: string;
  price: number;
  probability_pct: number;
}

export interface PolymarketMarket {
  id: string;
  question: string;
  category?: string;
  outcomes: PolymarketOutcome[];
  volume?: number;
  url?: string;
}

export interface PolymarketResponse {
  markets: PolymarketMarket[];
  high_probability_events: Record<string, unknown>[];
  total_markets: number;
  error?: string;
}

export interface NewsArticle {
  title: string;
  source?: string;
  url?: string;
  published_at?: string;
  ticker?: string;
}

export interface NewsResponse {
  by_ticker: Record<string, NewsArticle[]>;
  headlines: NewsArticle[];
  total_articles: number;
  error?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
}

// Event-centric types for the new dashboard

export type EventState = 'new' | 'ongoing' | 'stale' | 'resolved' | 'dismissed';

export type EventCategory =
  | 'congress_trade'
  | 'hedgefund_filing'
  | 'polymarket_shift'
  | 'news_cluster'
  | 'price_anomaly'
  | 'volume_spike'
  | 'sec_filing';

export interface EventEvidence {
  source: string;
  timestamp: string;
  summary: string;
  url?: string;
  confidence: number;
}

export interface TradePlan {
  thesis: string;
  invalidation: string;
  timeframe: string;
  risk_level: 'low' | 'medium' | 'high';
}

export interface Event {
  id: string;
  title: string;
  category: EventCategory;
  state: EventState;
  attention_score: number;
  anomaly_score: number;
  catalyst_score: number;
  flow_score: number;
  confidence_score: number;
  assets: string[];
  asset_types: AssetType[];
  evidence: EventEvidence[];
  evidence_count: number;
  first_seen: string;
  last_updated: string;
  summary: string;
  trade_plan?: TradePlan;
  pinned?: boolean;
  snoozed_until?: string;
}

export interface EventAction {
  event_id: string;
  action: 'dismiss' | 'snooze' | 'pin' | 'unpin' | 'resolve';
  snooze_hours?: number;
}

export interface DailyBrief {
  date: string;
  executive_summary: string[];
  top_events: Event[];
  trade_ideas: TradePlan[];
  data_quality: {
    sources_ok: number;
    sources_total: number;
    errors: string[];
    stalest_source: string;
    stalest_age_hours: number;
  };
  open_loops: string[];
}

export interface EventsResponse {
  events: Event[];
  daily_brief: DailyBrief;
  generated_at: string;
}

export interface SourceHealth {
  name: string;
  status: 'ok' | 'warning' | 'error';
  last_success?: string;
  error_message?: string;
  records_count?: number;
}
