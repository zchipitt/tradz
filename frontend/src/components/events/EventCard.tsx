/**
 * Event card component for the Signal Inbox.
 * Brutalist design aesthetic - black/white + yellow accent.
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

function ScorePill({ label, value }: { label: string; value: number }) {
  const getColor = (score: number) => {
    if (score >= 80) return 'text-status-success';
    if (score >= 60) return 'text-score-good';
    if (score >= 40) return 'text-status-warning';
    return 'text-gray-500';
  };

  return (
    <div className="flex items-center gap-1 font-mono text-xs">
      <span className="text-gray-500">{label}:</span>
      <span className={cn('font-bold', getColor(value))}>{value}</span>
    </div>
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

export function EventCard({ event, onAction, onOpen }: EventCardProps) {
  const [expanded, setExpanded] = useState(false);
  const state = stateConfig[event.state];
  const category = categoryConfig[event.category];
  const CategoryIcon = category.icon;

  const isActionable = event.state !== 'resolved' && event.state !== 'dismissed';

  return (
    <div
      className={cn(
        'bg-white border-2 border-black overflow-hidden font-mono transition-all duration-100',
        event.pinned && 'border-primary',
        !isActionable && 'opacity-60'
      )}
      style={{ boxShadow: event.pinned ? '4px 4px 0 0 #FFEB3B' : '2px 2px 0 0 #000000' }}
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
              onClick={() => onOpen?.(event)}
            >
              {event.title}
            </h3>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              {event.assets.map((asset) => (
                <span
                  key={asset}
                  className="px-2 py-0.5 text-xs font-bold bg-gray-100 border border-black"
                >
                  ${asset}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* 4D Score Pills */}
        <div className="flex items-center gap-6 mb-4 pb-3 border-b border-gray-200">
          <ScorePill label="ANM" value={event.anomaly_score} />
          <ScorePill label="CAT" value={event.catalyst_score} />
          <ScorePill label="FLW" value={event.flow_score} />
          <ScorePill label="CNF" value={event.confidence_score} />
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
