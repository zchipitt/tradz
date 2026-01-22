/**
 * TypeScript types matching backend Pydantic schemas.
 */

export type AssetType = 'equity' | 'crypto' | 'polymarket' | 'index' | 'commodity';

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
  event_title?: string;
  event_id?: string;
  event_slug?: string;  // Correct slug for event URL
  event_image?: string;
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

// Event-centric types for the new dashboard (matches backend EventListItem schema)

export type EventState = 'new' | 'ongoing' | 'stale' | 'resolved' | 'dismissed';

export type EventType =
  | 'catalyst'
  | 'risk'
  | 'flow'
  | 'macro'
  | 'market_anomaly'
  | 'catalyst_news'
  | 'catalyst_filing'
  | 'flow_congress'
  | 'flow_13f'
  | 'prediction_shift'
  | 'mixed'
  | 'uncertain';

// Legacy category mapping for UI components
export type EventCategory =
  | 'congress_trade'
  | 'hedgefund_filing'
  | 'polymarket_shift'
  | 'news_cluster'
  | 'price_anomaly'
  | 'volume_spike'
  | 'sec_filing';

export interface FourDScores {
  anomaly_score: number;
  catalyst_score: number;
  flow_score: number;
  confidence_score: number;
}

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

/**
 * EventListItem matches backend GET /api/events response.
 */
export interface EventListItem {
  event_id: string;
  entity_id: string | null;
  ticker: string | null;
  title: string;
  event_type: EventType;
  status: EventState;
  attention_score: number;
  scores: FourDScores;
  observation_count: number;
  last_update_at: string;
  start_at: string;
  pinned: boolean;
  snoozed_until: string | null;
}

/**
 * API response for GET /api/events endpoint.
 */
export interface EventsListResponse {
  events: EventListItem[];
  total_count: number;
  offset: number;
  limit: number;
}

/**
 * Legacy Event interface for backwards compatibility with existing UI.
 * Maps from EventListItem for display in SignalInbox/EventCard.
 */
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

export type EventActionType = 'pin' | 'unpin' | 'snooze' | 'dismiss' | 'resolve';

export interface EventAction {
  event_id: string;
  action: EventActionType;
  snooze_hours?: number;
  reason?: string;
}

/**
 * Request body for POST /api/events/{event_id}/actions
 */
export interface EventActionRequest {
  action: EventActionType;
  duration_hours?: number;
  reason?: string;
}

/**
 * Response from POST /api/events/{event_id}/actions
 */
export interface EventActionResponse {
  event_id: string;
  action: EventActionType;
  success: boolean;
  message: string;
  new_status: EventState | null;
  pinned: boolean | null;
  snoozed_until: string | null;
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

/**
 * Source health status from GET /api/system/status
 */
export type SourceStatus = 'ok' | 'degraded' | 'error';

export interface SourceHealth {
  name: string;
  display_name: string;
  status: SourceStatus;
  last_success_at: string | null;
  last_error: string | null;
  record_count_24h: number;
  freshness_indicator: 'fresh' | 'stale' | 'unknown';
}

export interface OverallHealth {
  total_sources: number;
  healthy_count: number;
  degraded_count: number;
  error_count: number;
}

export interface SystemStatusResponse {
  overall: OverallHealth;
  sources: SourceHealth[];
  last_check_at: string;
}

/**
 * Entity brief information for event detail.
 */
export interface EntityBrief {
  entity_id: string | null;
  ticker: string | null;
  name: string | null;
  asset_type?: AssetType;
}

/**
 * Fact entry from observations.
 */
export interface FactEntry {
  fact_id: string;
  fact_type: string;
  label: string;
  value: unknown;
  unit: string | null;
  source: string;
  timestamp: string | null;
}

/**
 * Observation summary for event detail.
 */
export interface ObservationSummary {
  observation_id: string;
  source: string;
  title: string | null;
  summary: string;
  timestamp: string;
  source_url: string | null;
  fact_entries: FactEntry[];
}

/**
 * Event detail response from GET /api/events/{event_id}.
 */
export interface EventDetailResponse {
  event_id: string;
  entity: EntityBrief;
  title: string;
  event_type: EventType;
  status: EventState;
  attention_score: number;
  scores: FourDScores;
  start_at: string;
  last_update_at: string;
  resolved_at: string | null;
  pinned: boolean;
  snoozed_until: string | null;
  dismissed_reason: string | null;
  title_source: string;
  parent_event_id: string | null;
  observation_count: number;
  observations: ObservationSummary[];
}

/**
 * Timeline source filter options for GET /api/events/{event_id}/timeline.
 */
export type TimelineSourceFilter = 'all' | 'market' | 'news' | 'sec' | 'congress' | '13f' | 'polymarket';

/**
 * Timeline observation item from GET /api/events/{event_id}/timeline.
 */
export interface TimelineObservation {
  observation_id: string;
  source: string;
  observation_type: string;
  timestamp: string;
  title: string | null;
  summary: string;
  fact_entries: FactEntry[];
  source_url: string | null;
}

/**
 * Response from GET /api/events/{event_id}/timeline.
 */
export interface TimelineResponse {
  event_id: string;
  observations: TimelineObservation[];
  total_count: number;
  offset: number;
  limit: number;
}

// =====================================================
// Quality Gate and Recommendation Types (US-012)
// =====================================================

/**
 * Trade direction for trade ideas.
 */
export type TradeDirection = 'long' | 'short' | 'neutral';

/**
 * Time horizon for trade ideas.
 */
export type TimeHorizon = 'intraday' | 'swing' | 'position' | 'investment';

/**
 * Result of a single quality gate evaluation.
 */
export interface GateResult {
  gate_name: string;
  passed: boolean;
  actual_value: number | boolean;
  threshold_value: number | boolean;
  improvement_suggestion: string | null;
}

/**
 * Result of quality gate evaluation for an event.
 */
export interface QualityGateEvaluation {
  passed: boolean;
  gate_score: number;
  failed_gates: string[];
  improvement_suggestions: string[];
  gate_results: GateResult[];
}

/**
 * Trade idea for events passing quality gates.
 */
export interface TradeIdea {
  id: string;
  event_id: string | null;
  direction: TradeDirection;
  entry_zone: string;
  target: string;
  stop_loss: string;
  invalidation: string;
  time_horizon: TimeHorizon;
  confidence_level: number;
  rationale: string;
  key_catalysts: string[];
  risk_factors: string[];
  created_at: string;
}

/**
 * Research plan for events failing quality gates.
 */
export interface ResearchPlan {
  id: string;
  event_id: string | null;
  questions_to_verify: string[];
  evidence_to_watch: string[];
  next_check_date: string | null;
  current_score: number;
  gaps_identified: string[];
  created_at: string;
}

/**
 * Recommendation type.
 */
export type RecommendationType = 'trade_idea' | 'research_plan';

/**
 * Unified recommendation response from GET /api/events/{event_id}/recommendation.
 */
export interface RecommendationResponse {
  type: RecommendationType;
  trade_idea: TradeIdea | null;
  research_plan: ResearchPlan | null;
  gate_evaluation: QualityGateEvaluation | null;
}

/**
 * Daily Brief Summary Item.
 * Response from GET /api/briefs (list briefs endpoint)
 */
export interface BriefSummaryItem {
  id: string;
  date: string;
  generation_method: string;
  created_at: string;
  event_count: number;
  trade_idea_count: number;
  top_entity: string | null;
  report_path_md: string | null;
  report_path_json: string | null;
  run_id: string | null;
}

export interface BriefSummaryResponse {
  briefs: BriefSummaryItem[];
  total_count: number;
}

/**
 * Daily Brief Detail
 * Response from GET /api/briefs/{date} or GET /api/briefs/latest
 */
export interface EventSummaryItem {
  event_id: string;
  title: string;
  ticker: string | null;
  event_type: string;
  attention_score: number;
  anomaly_score: number;
  catalyst_score: number;
  flow_score: number;
  confidence_score: number;
  observation_count: number;
  last_update_at: string | null;
}

export interface TradeIdeaItem {
  event_id: string;
  ticker: string | null;
  direction: string;
  entry_zone: string;
  target: string;
  stop_loss: string;
  confidence_level: number;
  rationale: string;
}

export interface ResearchIdeaItem {
  event_id: string;
  ticker: string | null;
  questions: string[];
  evidence_to_watch: string[];
  current_score: number;
  potential_score: number;
}

export interface OpenLoopItem {
  loop_id: string;
  event_id: string | null;
  question: string;
  created_at: string;
  status: string;
}

export interface SourceHealthItem {
  name: string;
  display_name: string;
  status: string;
  record_count_24h: number;
  freshness_indicator: string;
}

export interface DataQualitySection {
  total_sources: number;
  healthy_count: number;
  degraded_count: number;
  error_count: number;
  sources: SourceHealthItem[];
  overall_status: string;
  quality_message: string;
}

export interface BriefDetail {
  id: string;
  date: string;
  executive_summary: string;
  top_events: EventSummaryItem[];
  trade_ideas: TradeIdeaItem[];
  research_ideas: ResearchIdeaItem[];
  open_loops: OpenLoopItem[];
  data_quality: DataQualitySection | null;
  generation_method: string;
  created_at: string;
  run_id: string | null;
}

// =====================================================
// Brief Diff Types (US-021)
// =====================================================

/**
 * Summary of an event that appeared in the current brief but not baseline.
 */
export interface NewEventSummary {
  event_id: string;
  title: string;
  ticker: string | null;
  event_type: string;
  attention_score: number;
}

/**
 * Summary of an event that was resolved between baseline and current.
 */
export interface ResolvedEventSummary {
  event_id: string;
  title: string;
  ticker: string | null;
  resolution_type: string;
  final_score: number;
}

/**
 * Score change for an event between two dates.
 */
export interface EventScoreChange {
  event_id: string;
  title: string;
  ticker: string | null;
  previous_score: number;
  current_score: number;
  delta: number;
  direction: 'up' | 'down' | 'unchanged';
}

/**
 * Summary of a new trade idea that appeared since baseline.
 */
export interface NewTradeIdeaSummary {
  event_id: string;
  ticker: string | null;
  direction: string;
  entry_zone: string;
  target: string;
}

/**
 * Summary of an open loop that was closed since baseline.
 */
export interface ClosedLoopSummary {
  loop_id: string;
  question: string;
  event_id: string | null;
  resolution: string;
}

/**
 * Response for GET /api/reports/diff comparing two briefs.
 */
export interface BriefDiffResponse {
  date: string;
  baseline: string;
  has_baseline: boolean;

  // Event changes
  new_events: NewEventSummary[];
  resolved_events: ResolvedEventSummary[];
  score_changes: EventScoreChange[];

  // Trade idea changes
  new_trade_ideas: NewTradeIdeaSummary[];

  // Loop changes
  closed_loops: ClosedLoopSummary[];

  // Summary stats
  total_new_events: number;
  total_resolved: number;
  total_score_changes: number;
  total_new_trade_ideas: number;
  total_closed_loops: number;
}

// =====================================================
// Open Loops API Types (US-024)
// =====================================================

/**
 * Open loop status values.
 */
export type OpenLoopStatusValue = 'open' | 'in_progress' | 'resolved' | 'stale';

/**
 * Brief event summary for open loop responses.
 */
export interface OpenLoopEventSummary {
  event_id: string;
  title: string | null;
  attention_score: number | null;
  status: string | null;
}

/**
 * Open loop item in list responses.
 */
export interface OpenLoopAPIItem {
  loop_id: string;
  event_id: string | null;
  question: string;
  created_at: string;
  status: OpenLoopStatusValue;
  progress_notes_count: number;
  resolved_at: string | null;
  event_summary: OpenLoopEventSummary | null;
}

/**
 * Response for GET /api/loops.
 */
export interface OpenLoopsListResponse {
  loops: OpenLoopAPIItem[];
  total_count: number;
}

/**
 * Detailed open loop with progress notes.
 */
export interface OpenLoopDetail {
  loop_id: string;
  event_id: string | null;
  question: string;
  created_at: string;
  status: OpenLoopStatusValue;
  progress_notes: string[];
  resolved_at: string | null;
  event_summary: OpenLoopEventSummary | null;
}

/**
 * Request body for POST /api/loops.
 */
export interface CreateOpenLoopRequest {
  question: string;
  event_id?: string;
}

/**
 * Response for POST /api/loops.
 */
export interface OpenLoopCreateResponse {
  loop_id: string;
  question: string;
  status: OpenLoopStatusValue;
  created_at: string;
}

/**
 * Request body for PATCH /api/loops/{loop_id}.
 */
export interface UpdateOpenLoopRequest {
  status?: OpenLoopStatusValue;
  progress_note?: string;
}

/**
 * Response for PATCH /api/loops/{loop_id}.
 */
export interface OpenLoopUpdateResponse {
  loop_id: string;
  status: OpenLoopStatusValue;
  progress_notes_count: number;
  updated: boolean;
  message: string;
}

/**
 * Response for DELETE /api/loops/{loop_id}.
 */
export interface OpenLoopDeleteResponse {
  loop_id: string;
  deleted: boolean;
  message: string;
}

// =====================================================
// Quality Gate Settings Types (US-025b)
// =====================================================

/**
 * Quality gate threshold settings.
 */
export interface QualityGateSettings {
  min_confidence: number;
  min_sources: number;
  min_anomaly: number;
  min_catalyst: number;
  require_invalidation: boolean;
}

/**
 * Response for GET /api/settings/gates.
 */
export interface QualityGateSettingsResponse {
  settings: QualityGateSettings;
  defaults: QualityGateSettings;
}

/**
 * Request body for PUT /api/settings/gates.
 * All fields are optional for partial updates.
 */
export interface UpdateQualityGateSettingsRequest {
  min_confidence?: number;
  min_sources?: number;
  min_anomaly?: number;
  min_catalyst?: number;
  require_invalidation?: boolean;
}

/**
 * Response for PUT /api/settings/gates and DELETE /api/settings/gates.
 */
export interface UpdateQualityGateSettingsResponse {
  settings: QualityGateSettings;
  updated_fields: string[];
  message: string;
}
