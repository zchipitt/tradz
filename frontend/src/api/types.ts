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
