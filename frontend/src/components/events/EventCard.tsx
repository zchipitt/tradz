/**
 * Event card component for the Signal Inbox.
 * Displays event summary, scores, evidence, and actions.
 * Robinhood-style clean design with event state badges.
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
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { Event, EventState, EventCategory } from '../../api/types';

interface EventCardProps {
  event: Event;
  onAction?: (eventId: string, action: 'dismiss' | 'snooze' | 'pin' | 'unpin' | 'resolve') => void;
  onOpen?: (event: Event) => void;
}

const stateConfig: Record<EventState, { label: string; color: string; bgColor: string }> = {
  new: { label: 'New', color: 'text-primary', bgColor: 'bg-primary/10' },
  ongoing: { label: 'Ongoing', color: 'text-blue-600', bgColor: 'bg-blue-50' },
  stale: { label: 'Stale', color: 'text-amber-600', bgColor: 'bg-amber-50' },
  resolved: { label: 'Resolved', color: 'text-text-muted', bgColor: 'bg-gray-100' },
  dismissed: { label: 'Dismissed', color: 'text-text-muted', bgColor: 'bg-gray-100' },
};

const categoryConfig: Record<EventCategory, { label: string; icon: React.ElementType }> = {
  congress_trade: { label: 'Congress', icon: TrendingUp },
  hedgefund_filing: { label: '13F Filing', icon: BarChart3 },
  polymarket_shift: { label: 'Polymarket', icon: Zap },
  news_cluster: { label: 'News', icon: AlertTriangle },
  price_anomaly: { label: 'Price', icon: TrendingUp },
  volume_spike: { label: 'Volume', icon: BarChart3 },
  sec_filing: { label: 'SEC', icon: Shield },
};

function ScorePill({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-1 text-xs">
      <span className="text-text-muted">{label}</span>
      <span className={cn('font-semibold', color)}>{value}</span>
    </div>
  );
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-primary';
  if (score >= 60) return 'text-score-good';
  if (score >= 40) return 'text-score-moderate';
  return 'text-text-muted';
}

function getAttentionBgColor(score: number): string {
  if (score >= 80) return 'bg-primary';
  if (score >= 60) return 'bg-score-good';
  if (score >= 40) return 'bg-score-moderate';
  return 'bg-gray-400';
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

export function EventCard({ event, onAction, onOpen }: EventCardProps) {
  const [expanded, setExpanded] = useState(false);
  const state = stateConfig[event.state];
  const category = categoryConfig[event.category];
  const CategoryIcon = category.icon;

  const isActionable = event.state !== 'resolved' && event.state !== 'dismissed';

  return (
    <div
      className={cn(
        'bg-white rounded-xl border border-border',
        'transition-all duration-200',
        'hover:shadow-md hover:border-gray-300',
        event.pinned && 'ring-2 ring-primary/20 border-primary/30',
        !isActionable && 'opacity-60'
      )}
    >
      {/* Main Card Content */}
      <div className="p-4">
        {/* Header Row: State + Category + Time + Pin */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            {/* State Badge */}
            <span
              className={cn(
                'px-2 py-0.5 rounded-full text-xs font-medium',
                state.bgColor,
                state.color
              )}
            >
              {state.label}
            </span>

            {/* Category Badge */}
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-surface text-text-muted">
              <CategoryIcon size={12} />
              {category.label}
            </span>

            {/* Evidence Count */}
            <span className="text-xs text-text-muted">
              {event.evidence_count} evidence
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Time */}
            <span className="text-xs text-text-muted">{formatTimeAgo(event.last_updated)}</span>

            {/* Pin indicator */}
            {event.pinned && <Pin size={14} className="text-primary" />}
          </div>
        </div>

        {/* Title + Attention Score Row */}
        <div className="flex items-start gap-3 mb-3">
          {/* Attention Score Circle */}
          <div
            className={cn(
              'flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center',
              getAttentionBgColor(event.attention_score)
            )}
          >
            <span className="text-white font-bold text-lg">{event.attention_score}</span>
          </div>

          {/* Title + Assets */}
          <div className="flex-1 min-w-0">
            <h3
              className="font-semibold text-text leading-tight cursor-pointer hover:text-primary transition-colors"
              onClick={() => onOpen?.(event)}
            >
              {event.title}
            </h3>
            <div className="flex flex-wrap items-center gap-1.5 mt-1">
              {event.assets.map((asset) => (
                <span
                  key={asset}
                  className="px-1.5 py-0.5 rounded text-xs font-medium bg-surface text-text"
                >
                  {asset}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* 4D Score Pills */}
        <div className="flex items-center gap-4 mb-3 pb-3 border-b border-border">
          <ScorePill label="A" value={event.anomaly_score} color={getScoreColor(event.anomaly_score)} />
          <ScorePill label="C" value={event.catalyst_score} color={getScoreColor(event.catalyst_score)} />
          <ScorePill label="F" value={event.flow_score} color={getScoreColor(event.flow_score)} />
          <ScorePill label="Conf" value={event.confidence_score} color={getScoreColor(event.confidence_score)} />
        </div>

        {/* Summary */}
        <p className="text-sm text-text-muted mb-3 line-clamp-2">{event.summary}</p>

        {/* Latest Evidence Preview */}
        {event.evidence.length > 0 && (
          <div className="text-xs text-text-muted mb-3">
            <span className="font-medium">{event.evidence[0].source}:</span>{' '}
            {event.evidence[0].summary}
          </div>
        )}

        {/* Trade Plan Preview (if high confidence) */}
        {event.trade_plan && event.confidence_score >= 70 && (
          <div className="bg-primary/5 rounded-lg p-3 mb-3 border border-primary/10">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp size={14} className="text-primary" />
              <span className="text-xs font-semibold text-primary">Trade Idea</span>
              <span
                className={cn(
                  'px-1.5 py-0.5 rounded text-xs font-medium',
                  event.trade_plan.risk_level === 'low'
                    ? 'bg-green-100 text-green-700'
                    : event.trade_plan.risk_level === 'medium'
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-red-100 text-red-700'
                )}
              >
                {event.trade_plan.risk_level} risk
              </span>
            </div>
            <p className="text-sm text-text">{event.trade_plan.thesis}</p>
            <p className="text-xs text-text-muted mt-1">
              <span className="font-medium">Invalidation:</span> {event.trade_plan.invalidation}
            </p>
          </div>
        )}

        {/* Expand/Collapse + Actions */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs text-text-muted hover:text-text transition-colors cursor-pointer"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {expanded ? 'Less' : 'More'}
          </button>

          {isActionable && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => onAction?.(event.id, event.pinned ? 'unpin' : 'pin')}
                className="p-1.5 rounded-lg hover:bg-surface text-text-muted hover:text-text transition-colors cursor-pointer"
                title={event.pinned ? 'Unpin' : 'Pin'}
              >
                {event.pinned ? <PinOff size={16} /> : <Pin size={16} />}
              </button>
              <button
                onClick={() => onAction?.(event.id, 'snooze')}
                className="p-1.5 rounded-lg hover:bg-surface text-text-muted hover:text-text transition-colors cursor-pointer"
                title="Snooze 24h"
              >
                <Clock size={16} />
              </button>
              <button
                onClick={() => onAction?.(event.id, 'resolve')}
                className="p-1.5 rounded-lg hover:bg-surface text-text-muted hover:text-primary transition-colors cursor-pointer"
                title="Mark Resolved"
              >
                <CheckCircle size={16} />
              </button>
              <button
                onClick={() => onAction?.(event.id, 'dismiss')}
                className="p-1.5 rounded-lg hover:bg-surface text-text-muted hover:text-negative transition-colors cursor-pointer"
                title="Dismiss"
              >
                <X size={16} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Expanded Evidence Timeline */}
      {expanded && (
        <div className="border-t border-border px-4 py-3 bg-surface/50">
          <h4 className="text-xs font-semibold text-text-muted mb-2 uppercase tracking-wide">
            Evidence Timeline
          </h4>
          <div className="space-y-2">
            {event.evidence.map((ev, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-text-muted mt-2 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-text">{ev.source}</span>
                    <span className="text-xs text-text-light">{formatTimeAgo(ev.timestamp)}</span>
                    {ev.url && (
                      <a
                        href={ev.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                  <p className="text-text-muted">{ev.summary}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Open Full Event Button */}
          <button
            onClick={() => onOpen?.(event)}
            className="mt-3 w-full py-2 rounded-lg border border-border text-sm font-medium text-text hover:bg-white transition-colors cursor-pointer"
          >
            Open Event Details
          </button>
        </div>
      )}
    </div>
  );
}
