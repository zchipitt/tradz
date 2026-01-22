/**
 * Event card component for the Signal Inbox.
 * Brutalist design aesthetic - black/white + yellow accent.
 *
 * Features:
 * - 4D score bars (anomaly/catalyst/flow/confidence) with distinct colors
 * - Action label (Act/Investigate/Monitor) based on confidence score
 * - Clickable entity chips with exchange info
 * - Hover elevation effect
 * - Full card clickable to open event detail
 */
import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Pin,
  PinOff,
  Clock,
  X,
  CheckCircle,
  ExternalLink,
  TrendingUp,
  AlertTriangle,
  Zap,
  BarChart3,
  Shield,
  Play,
  Search,
  Eye,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { Event, EventState, EventCategory, AssetType } from '../../api/types';

interface EventCardProps {
  event: Event;
  onAction?: (eventId: string, action: 'dismiss' | 'snooze' | 'pin' | 'unpin' | 'resolve') => void;
  onOpen?: (event: Event) => void;
  onEntityClick?: (asset: string, assetType?: AssetType) => void;
}

const stateConfig: Record<EventState, { label: string; bg: string; text: string }> = {
  new: { label: 'NEW', bg: 'bg-primary', text: 'text-black' },
  ongoing: { label: 'ONGOING', bg: 'bg-status-success/20', text: 'text-status-success' },
  stale: { label: 'STALE', bg: 'bg-status-error/20', text: 'text-status-error' },
  resolved: { label: 'RESOLVED', bg: 'bg-gray-200', text: 'text-gray-600' },
  dismissed: { label: 'DISMISSED', bg: 'bg-gray-200', text: 'text-gray-600' },
};

const categoryConfig: Record<EventCategory, { label: string; icon: React.ElementType }> = {
  congress_trade: { label: 'CONGRESS', icon: TrendingUp },
  hedgefund_filing: { label: '13F FILING', icon: BarChart3 },
  polymarket_shift: { label: 'POLYMARKET', icon: Zap },
  news_cluster: { label: 'NEWS', icon: AlertTriangle },
  price_anomaly: { label: 'PRICE', icon: TrendingUp },
  volume_spike: { label: 'VOLUME', icon: BarChart3 },
  sec_filing: { label: 'SEC', icon: Shield },
};

// 4D Score bar colors matching the acceptance criteria
const scoreBarConfig = {
  anomaly: { label: 'ANM', color: 'bg-red-500', bgColor: 'bg-red-100' },
  catalyst: { label: 'CAT', color: 'bg-blue-500', bgColor: 'bg-blue-100' },
  flow: { label: 'FLW', color: 'bg-green-500', bgColor: 'bg-green-100' },
  confidence: { label: 'CNF', color: 'bg-gray-500', bgColor: 'bg-gray-200' },
};

// Action label configuration based on confidence score
type ActionLabel = 'act' | 'investigate' | 'monitor';

function getActionLabel(confidenceScore: number): ActionLabel {
  if (confidenceScore >= 70) return 'act';
  if (confidenceScore >= 40) return 'investigate';
  return 'monitor';
}

const actionLabelConfig: Record<ActionLabel, { label: string; icon: React.ElementType; bg: string; text: string }> = {
  act: { label: 'ACT', icon: Play, bg: 'bg-green-500', text: 'text-white' },
  investigate: { label: 'INVESTIGATE', icon: Search, bg: 'bg-yellow-400', text: 'text-black' },
  monitor: { label: 'MONITOR', icon: Eye, bg: 'bg-gray-400', text: 'text-white' },
};

/**
 * 4D Score Bar component - displays a labeled progress bar with specific color.
 */
function ScoreBar({ label, value, color, bgColor }: { label: string; value: number; color: string; bgColor: string }) {
  return (
    <div className="flex-1 min-w-0">
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-[10px] text-gray-500 font-medium">{label}</span>
        <span className="text-[10px] font-bold text-gray-700">{value}</span>
      </div>
      <div className={cn('h-1.5 rounded-full', bgColor)}>
        <div
          className={cn('h-full rounded-full transition-all duration-300', color)}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
    </div>
  );
}

/**
 * Entity chip component - clickable badge showing symbol + exchange/rank.
 */
function EntityChip({
  asset,
  assetType,
  index,
  onClick
}: {
  asset: string;
  assetType?: AssetType;
  index: number;
  onClick?: () => void;
}) {
  // Determine exchange or rank info based on asset type
  const getExchangeInfo = () => {
    if (assetType === 'crypto') {
      // For crypto, show rank placeholder (would come from API in real implementation)
      return `#${index + 1}`;
    }
    // For equities, show exchange (simplified - in reality would come from API)
    if (['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'].includes(asset)) {
      return 'NASDAQ';
    }
    if (['JPM', 'BAC', 'GS', 'JNJ', 'UNH'].includes(asset)) {
      return 'NYSE';
    }
    return 'US';
  };

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onClick?.();
      }}
      className={cn(
        'px-2 py-1 text-xs font-bold border border-black transition-all duration-100',
        'hover:bg-primary hover:border-primary cursor-pointer',
        'flex items-center gap-1'
      )}
      title={`View ${asset} details`}
    >
      <span>${asset}</span>
      <span className="text-[10px] text-gray-500 font-normal">{getExchangeInfo()}</span>
    </button>
  );
}

function getAttentionBg(score: number): string {
  if (score >= 80) return 'bg-status-success';
  if (score >= 60) return 'bg-score-good';
  if (score >= 40) return 'bg-status-warning';
  return 'bg-gray-400';
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  return `${diffDays}d`;
}

export function EventCard({ event, onAction, onOpen, onEntityClick }: EventCardProps) {
  const [expanded, setExpanded] = useState(false);
  const state = stateConfig[event.state];
  const category = categoryConfig[event.category];
  const CategoryIcon = category.icon;

  const isActionable = event.state !== 'resolved' && event.state !== 'dismissed';

  // Get action label based on confidence score
  const actionType = getActionLabel(event.confidence_score);
  const actionConfig = actionLabelConfig[actionType];
  const ActionIcon = actionConfig.icon;

  // Handle card click to open event detail
  const handleCardClick = (e: React.MouseEvent) => {
    // Don't trigger if clicking on buttons or interactive elements
    const target = e.target as HTMLElement;
    if (target.closest('button') || target.closest('a')) {
      return;
    }
    onOpen?.(event);
  };

  return (
    <div
      onClick={handleCardClick}
      className={cn(
        'bg-white border-2 border-black overflow-hidden transition-all duration-150 cursor-pointer',
        'hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,0.8)] hover:-translate-x-0.5 hover:-translate-y-0.5',
        event.pinned && 'border-primary',
        !isActionable && 'opacity-60 cursor-default hover:shadow-none hover:translate-x-0 hover:translate-y-0'
      )}
    >
      {/* Header */}
      <div className="px-4 py-2 bg-gray-100 border-b border-black flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* State Badge */}
          <span className={cn('px-2 py-0.5 text-xs font-bold uppercase border border-black', state.bg, state.text)}>
            {state.label}
          </span>

          {/* Category Badge */}
          <span className="flex items-center gap-1 text-xs text-gray-600">
            <CategoryIcon size={12} />
            <span>{category.label}</span>
          </span>

          {/* Evidence Count */}
          <span className="text-xs text-gray-500">
            {event.evidence_count} sources
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Action Label - Act/Investigate/Monitor based on confidence */}
          <span className={cn(
            'px-2 py-0.5 text-[10px] font-bold uppercase flex items-center gap-1',
            actionConfig.bg, actionConfig.text
          )}>
            <ActionIcon size={10} />
            {actionConfig.label}
          </span>

          {/* Time */}
          <span className="text-xs text-gray-500">{formatTimeAgo(event.last_updated)} ago</span>

          {/* Pin indicator */}
          {event.pinned && <Pin size={12} className="text-primary" />}
        </div>
      </div>

      {/* Main Card Content */}
      <div className="p-4">
        {/* Title + Attention Score Row */}
        <div className="flex items-start gap-4 mb-4">
          {/* Attention Score */}
          <div className="flex-shrink-0 w-14 h-14 border-2 border-black flex flex-col items-center justify-center bg-gray-50">
            <span className="text-2xl font-bold">{event.attention_score}</span>
            <span className="text-[10px] text-gray-500 uppercase">ATT</span>
            <div className="w-full h-1 mt-1">
              <div
                className={cn('h-full', getAttentionBg(event.attention_score))}
                style={{ width: `${event.attention_score}%` }}
              />
            </div>
          </div>

          {/* Title + Assets */}
          <div className="flex-1 min-w-0">
            <h3
              className="font-bold text-black text-lg leading-tight cursor-pointer hover:underline hover:underline-offset-4 transition-all"
              onClick={(e) => {
                e.stopPropagation();
                onOpen?.(event);
              }}
            >
              {event.title}
            </h3>
            {/* Entity chips - clickable with symbol + exchange/rank */}
            <div className="flex flex-wrap items-center gap-2 mt-2">
              {event.assets.map((asset, index) => (
                <EntityChip
                  key={asset}
                  asset={asset}
                  assetType={event.asset_types?.[index]}
                  index={index}
                  onClick={() => onEntityClick?.(asset, event.asset_types?.[index])}
                />
              ))}
            </div>
          </div>
        </div>

        {/* 4D Score Bars - anomaly (red), catalyst (blue), flow (green), confidence (gray) */}
        <div className="flex items-center gap-4 mb-4 pb-3 border-b border-gray-200">
          <ScoreBar
            label={scoreBarConfig.anomaly.label}
            value={event.anomaly_score}
            color={scoreBarConfig.anomaly.color}
            bgColor={scoreBarConfig.anomaly.bgColor}
          />
          <ScoreBar
            label={scoreBarConfig.catalyst.label}
            value={event.catalyst_score}
            color={scoreBarConfig.catalyst.color}
            bgColor={scoreBarConfig.catalyst.bgColor}
          />
          <ScoreBar
            label={scoreBarConfig.flow.label}
            value={event.flow_score}
            color={scoreBarConfig.flow.color}
            bgColor={scoreBarConfig.flow.bgColor}
          />
          <ScoreBar
            label={scoreBarConfig.confidence.label}
            value={event.confidence_score}
            color={scoreBarConfig.confidence.color}
            bgColor={scoreBarConfig.confidence.bgColor}
          />
        </div>

        {/* Summary */}
        <div className="mb-3">
          <p className="text-sm text-gray-700 line-clamp-2">{event.summary}</p>
        </div>

        {/* Latest Evidence Preview */}
        {event.evidence.length > 0 && (
          <div className="text-xs text-gray-600 mb-3 pl-4 border-l-2 border-gray-300">
            <span className="font-bold">[{event.evidence[0].source}]</span>{' '}
            <span>{event.evidence[0].summary}</span>
          </div>
        )}

        {/* Trade Plan Preview (if high confidence) */}
        {event.trade_plan && event.confidence_score >= 70 && (
          <div className="bg-primary/20 border-2 border-black p-3 mb-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold uppercase">Trade Idea</span>
              <span
                className={cn(
                  'px-2 py-0.5 text-[10px] font-bold uppercase border border-black',
                  event.trade_plan.risk_level === 'low'
                    ? 'bg-status-success text-white'
                    : event.trade_plan.risk_level === 'medium'
                      ? 'bg-status-warning text-black'
                      : 'bg-status-error text-white'
                )}
              >
                {event.trade_plan.risk_level} risk
              </span>
            </div>
            <p className="text-xs text-gray-800">{event.trade_plan.thesis}</p>
            <p className="text-xs text-gray-600 mt-1">
              <span className="text-status-error font-bold">Invalidation:</span> {event.trade_plan.invalidation}
            </p>
          </div>
        )}

        {/* Expand/Collapse + Actions */}
        <div className="flex items-center justify-between pt-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs text-gray-600 hover:text-black transition-colors cursor-pointer font-bold uppercase"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            <span>{expanded ? 'Collapse' : 'Expand'}</span>
          </button>

          {isActionable && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => onAction?.(event.id, event.pinned ? 'unpin' : 'pin')}
                className="p-2 text-gray-500 hover:text-black hover:bg-gray-100 transition-colors cursor-pointer border border-transparent hover:border-black"
                title={event.pinned ? 'Unpin' : 'Pin'}
              >
                {event.pinned ? <PinOff size={14} /> : <Pin size={14} />}
              </button>
              <button
                onClick={() => onAction?.(event.id, 'snooze')}
                className="p-2 text-gray-500 hover:text-status-warning hover:bg-status-warning/10 transition-colors cursor-pointer border border-transparent hover:border-status-warning"
                title="Snooze 24h"
              >
                <Clock size={14} />
              </button>
              <button
                onClick={() => onAction?.(event.id, 'resolve')}
                className="p-2 text-gray-500 hover:text-status-success hover:bg-status-success/10 transition-colors cursor-pointer border border-transparent hover:border-status-success"
                title="Mark Resolved"
              >
                <CheckCircle size={14} />
              </button>
              <button
                onClick={() => onAction?.(event.id, 'dismiss')}
                className="p-2 text-gray-500 hover:text-status-error hover:bg-status-error/10 transition-colors cursor-pointer border border-transparent hover:border-status-error"
                title="Dismiss"
              >
                <X size={14} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Expanded Evidence Timeline */}
      {expanded && (
        <div className="border-t-2 border-black px-4 py-4 bg-gray-50">
          <h4 className="text-xs font-bold mb-3 uppercase tracking-wider">
            Evidence Timeline
          </h4>
          <div className="space-y-3">
            {event.evidence.map((ev, i) => (
              <div key={i} className="flex items-start gap-3 text-xs p-3 bg-white border border-gray-300">
                <div className="w-2 h-2 bg-black mt-1.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold">[{ev.source}]</span>
                    <span className="text-gray-500">{formatTimeAgo(ev.timestamp)} ago</span>
                    <span className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 text-[10px] font-bold">
                      CONF: {ev.confidence}%
                    </span>
                    {ev.url && (
                      <a
                        href={ev.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-black hover:underline font-bold flex items-center gap-1"
                      >
                        <ExternalLink size={10} />
                        SOURCE
                      </a>
                    )}
                  </div>
                  <p className="text-gray-600 mt-1">{ev.summary}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Open Full Event Button */}
          <button
            onClick={() => onOpen?.(event)}
            className="mt-4 w-full py-2 text-xs font-bold uppercase tracking-wider border-2 border-black hover:bg-primary transition-colors cursor-pointer"
          >
            Open Full Details
          </button>
        </div>
      )}
    </div>
  );
}
