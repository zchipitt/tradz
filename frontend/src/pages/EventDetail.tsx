/**
 * Event Detail page - Full event information with header, scores, and sidebar.
 * Brutalist design aesthetic - black/white + yellow accent.
 *
 * Features:
 * - Header with title, entity badges, status badge, last updated time
 * - 4D score breakdown with progress bars
 * - Right sidebar with action buttons (responsive: below main on mobile)
 * - Loading skeleton state
 * - 404 state when event not found
 */
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Pin,
  PinOff,
  Clock,
  CheckCircle,
  X,
  AlertTriangle,
  ExternalLink,
  TrendingUp,
  BarChart3,
  Zap,
  Shield,
  FileText,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { useEventDetail, useEventActions } from '../hooks/useEvents';
import type { EventState, EventType, ObservationSummary } from '../api/types';

// State badge configuration
const stateConfig: Record<EventState, { label: string; bg: string; text: string }> = {
  new: { label: 'NEW', bg: 'bg-primary', text: 'text-black' },
  ongoing: { label: 'ONGOING', bg: 'bg-status-success/20', text: 'text-status-success' },
  stale: { label: 'STALE', bg: 'bg-status-error/20', text: 'text-status-error' },
  resolved: { label: 'RESOLVED', bg: 'bg-gray-200', text: 'text-gray-600' },
  dismissed: { label: 'DISMISSED', bg: 'bg-gray-200', text: 'text-gray-600' },
};

// Event type configuration
const eventTypeConfig: Record<EventType, { label: string; icon: React.ElementType }> = {
  market_anomaly: { label: 'MARKET ANOMALY', icon: TrendingUp },
  catalyst_news: { label: 'CATALYST NEWS', icon: FileText },
  catalyst_filing: { label: 'SEC FILING', icon: Shield },
  flow_congress: { label: 'CONGRESS FLOW', icon: TrendingUp },
  flow_13f: { label: '13F FILING', icon: BarChart3 },
  prediction_shift: { label: 'PREDICTION SHIFT', icon: Zap },
  mixed: { label: 'MIXED', icon: BarChart3 },
  uncertain: { label: 'UNCERTAIN', icon: AlertTriangle },
  catalyst: { label: 'CATALYST', icon: Zap },
  risk: { label: 'RISK', icon: AlertTriangle },
  flow: { label: 'FLOW', icon: TrendingUp },
  macro: { label: 'MACRO', icon: BarChart3 },
};

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-status-success';
  if (score >= 60) return 'text-score-good';
  if (score >= 40) return 'text-status-warning';
  return 'text-gray-500';
}

function getScoreBg(score: number): string {
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

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Source icon mapping
function getSourceIcon(source: string): React.ElementType {
  switch (source.toLowerCase()) {
    case 'equities':
    case 'crypto':
      return TrendingUp;
    case 'news':
      return FileText;
    case 'sec':
      return Shield;
    case 'congress':
      return TrendingUp;
    case 'hedgefund':
      return BarChart3;
    case 'polymarket':
      return Zap;
    default:
      return FileText;
  }
}

/**
 * Loading skeleton for the event detail page.
 */
function EventDetailSkeleton() {
  return (
    <div className="animate-pulse">
      {/* Header skeleton */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <div className="h-8 w-8 bg-gray-200 rounded" />
          <div className="h-6 w-24 bg-gray-200 rounded" />
          <div className="h-6 w-32 bg-gray-200 rounded" />
        </div>
        <div className="h-10 w-3/4 bg-gray-200 rounded mb-4" />
        <div className="flex gap-2">
          <div className="h-8 w-20 bg-gray-200 rounded" />
          <div className="h-8 w-20 bg-gray-200 rounded" />
        </div>
      </div>

      {/* Main content skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Score grid */}
          <div className="p-4 bg-gray-50 border-2 border-gray-200">
            <div className="grid grid-cols-5 gap-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="text-center">
                  <div className="h-10 w-12 mx-auto bg-gray-200 rounded mb-2" />
                  <div className="h-3 w-8 mx-auto bg-gray-200 rounded" />
                </div>
              ))}
            </div>
          </div>

          {/* Observations skeleton */}
          <div>
            <div className="h-6 w-40 bg-gray-200 rounded mb-4" />
            {[...Array(3)].map((_, i) => (
              <div key={i} className="p-4 bg-gray-50 border-2 border-gray-200 mb-3">
                <div className="h-4 w-1/2 bg-gray-200 rounded mb-2" />
                <div className="h-3 w-full bg-gray-200 rounded" />
              </div>
            ))}
          </div>
        </div>

        {/* Right sidebar skeleton */}
        <div className="lg:col-span-1">
          <div className="p-4 bg-gray-50 border-2 border-gray-200">
            <div className="h-6 w-24 bg-gray-200 rounded mb-4" />
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-10 w-full bg-gray-200 rounded" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 404 Not Found state.
 */
function EventNotFound({ eventId }: { eventId: string }) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="w-20 h-20 border-4 border-black flex items-center justify-center mb-6">
        <AlertTriangle size={40} className="text-status-error" />
      </div>
      <h1 className="text-2xl font-bold text-black mb-2">Event Not Found</h1>
      <p className="text-gray-600 mb-6 text-center max-w-md">
        The event with ID <code className="bg-gray-100 px-2 py-1 text-sm">{eventId}</code> could not be found.
        It may have been deleted or the ID is invalid.
      </p>
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 px-6 py-2 bg-primary border-2 border-black font-bold uppercase text-sm hover:shadow-brutal-sm transition-all cursor-pointer"
      >
        <ArrowLeft size={16} />
        Back to Dashboard
      </button>
    </div>
  );
}

/**
 * Observation item component.
 */
function ObservationItem({ observation }: { observation: ObservationSummary }) {
  const SourceIcon = getSourceIcon(observation.source);

  return (
    <div className="p-4 bg-white border-2 border-gray-300 hover:border-black transition-colors">
      <div className="flex items-center gap-3 mb-2">
        <SourceIcon size={16} className="text-gray-600" />
        <span className="font-bold text-sm text-black uppercase">[{observation.source}]</span>
        <span className="text-xs text-gray-500">{formatTimeAgo(observation.timestamp)}</span>
      </div>
      {observation.title && (
        <h4 className="font-bold text-gray-800 mb-1">{observation.title}</h4>
      )}
      <p className="text-sm text-gray-700">{observation.summary || 'No summary available'}</p>
      {observation.source_url && (
        <a
          href={observation.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-black font-bold hover:underline mt-2"
        >
          <ExternalLink size={12} />
          VIEW SOURCE
        </a>
      )}
      {observation.fact_entries.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <span className="text-xs font-bold text-gray-500 uppercase mb-2 block">Facts:</span>
          <div className="flex flex-wrap gap-2">
            {observation.fact_entries.slice(0, 5).map((fact) => (
              <span
                key={fact.fact_id}
                className="px-2 py-1 text-xs bg-gray-100 border border-gray-300"
              >
                <span className="font-bold">{fact.label}:</span> {String(fact.value)}
                {fact.unit && ` ${fact.unit}`}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function EventDetail() {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();
  const { data: event, isLoading, isError, error } = useEventDetail(eventId);
  const { pin, unpin, snooze, dismiss, resolve, isPending } = useEventActions();

  // Handle back navigation
  const handleBack = () => {
    navigate('/');
  };

  // Handle actions
  const handleAction = async (action: 'pin' | 'unpin' | 'snooze' | 'dismiss' | 'resolve') => {
    if (!eventId) return;
    try {
      switch (action) {
        case 'pin':
          await pin(eventId);
          break;
        case 'unpin':
          await unpin(eventId);
          break;
        case 'snooze':
          await snooze(eventId, 24);
          break;
        case 'dismiss':
          await dismiss(eventId);
          break;
        case 'resolve':
          await resolve(eventId);
          navigate('/');
          break;
      }
    } catch (err) {
      console.error('Action failed:', err);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto p-6 lg:p-8">
        <EventDetailSkeleton />
      </div>
    );
  }

  // Error/404 state
  if (isError || !event) {
    const is404 = error instanceof Error && (
      error.message.includes('404') ||
      error.message.includes('not found')
    );
    if (is404 || !event) {
      return (
        <div className="max-w-7xl mx-auto p-6 lg:p-8">
          <EventNotFound eventId={eventId ?? 'unknown'} />
        </div>
      );
    }
    // Other errors
    return (
      <div className="max-w-7xl mx-auto p-6 lg:p-8">
        <div className="flex flex-col items-center justify-center py-16">
          <AlertTriangle size={40} className="text-status-error mb-4" />
          <h1 className="text-xl font-bold text-black mb-2">Error Loading Event</h1>
          <p className="text-gray-600 mb-6">{error?.message || 'An unexpected error occurred.'}</p>
          <button
            onClick={handleBack}
            className="flex items-center gap-2 px-6 py-2 bg-primary border-2 border-black font-bold uppercase text-sm cursor-pointer"
          >
            <ArrowLeft size={16} />
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const state = stateConfig[event.status] || stateConfig.new;
  const eventType = eventTypeConfig[event.event_type] || eventTypeConfig.uncertain;
  const TypeIcon = eventType.icon;
  const isActionable = event.status !== 'resolved' && event.status !== 'dismissed';

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8">
      {/* Back Button + Header */}
      <div className="mb-8">
        {/* Back button */}
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-black transition-colors mb-4 cursor-pointer"
        >
          <ArrowLeft size={16} />
          <span className="font-bold uppercase">Back to Dashboard</span>
        </button>

        {/* Status badges */}
        <div className="flex items-center gap-3 mb-4">
          <span className={cn('px-3 py-1 text-xs font-bold uppercase border border-black', state.bg, state.text)}>
            {state.label}
          </span>
          <span className="flex items-center gap-1 px-3 py-1 text-xs font-bold uppercase border border-gray-300 bg-gray-50">
            <TypeIcon size={12} />
            {eventType.label}
          </span>
          {event.pinned && (
            <span className="flex items-center gap-1 px-2 py-1 text-xs font-bold text-primary">
              <Pin size={12} />
              PINNED
            </span>
          )}
        </div>

        {/* Title */}
        <h1 className="text-2xl lg:text-3xl font-bold text-black mb-4">{event.title}</h1>

        {/* Entity badges + last updated */}
        <div className="flex flex-wrap items-center gap-4">
          {event.entity.ticker && (
            <span className="px-3 py-1 bg-gray-100 border-2 border-black text-sm font-bold">
              ${event.entity.ticker}
            </span>
          )}
          {event.entity.name && (
            <span className="text-sm text-gray-600">{event.entity.name}</span>
          )}
          <span className="text-sm text-gray-500">
            Last updated: {formatDateTime(event.last_update_at)}
          </span>
        </div>
      </div>

      {/* Main Content Grid - Responsive */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* 4D Score Grid */}
          <div className="p-4 bg-gray-50 border-2 border-black">
            <h3 className="text-sm font-bold uppercase tracking-wider mb-4 text-black">
              Score Breakdown
            </h3>
            <div className="grid grid-cols-5 gap-4">
              {[
                { label: 'ATT', score: Math.round(event.attention_score) },
                { label: 'ANM', score: Math.round(event.scores.anomaly_score) },
                { label: 'CAT', score: Math.round(event.scores.catalyst_score) },
                { label: 'FLW', score: Math.round(event.scores.flow_score) },
                { label: 'CNF', score: Math.round(event.scores.confidence_score) },
              ].map(({ label, score }) => (
                <div key={label} className="text-center">
                  <div className={cn('text-2xl lg:text-3xl font-bold', getScoreColor(score))}>
                    {score}
                  </div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">{label}</div>
                  <div className="w-full h-1.5 bg-gray-200 border border-black mt-2">
                    <div
                      className={cn('h-full', getScoreBg(score))}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Event Timeline/Observations */}
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider mb-4 text-black">
              Evidence Timeline ({event.observation_count} sources)
            </h3>
            {event.observations.length > 0 ? (
              <div className="space-y-3">
                {event.observations.map((obs) => (
                  <ObservationItem key={obs.observation_id} observation={obs} />
                ))}
              </div>
            ) : (
              <div className="p-8 bg-gray-50 border-2 border-gray-200 text-center">
                <FileText size={32} className="text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600">No observations available for this event.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right: Sidebar - Actions */}
        <div className="lg:col-span-1">
          <div className="p-4 bg-gray-50 border-2 border-black sticky top-20">
            <h3 className="text-sm font-bold uppercase tracking-wider mb-4 text-black">
              Actions
            </h3>
            {isActionable ? (
              <div className="space-y-3">
                <button
                  onClick={() => handleAction(event.pinned ? 'unpin' : 'pin')}
                  disabled={isPending}
                  className={cn(
                    'w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold uppercase',
                    'border-2 border-black transition-all cursor-pointer',
                    event.pinned
                      ? 'bg-primary hover:bg-primary/80'
                      : 'bg-white hover:bg-gray-100',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  {event.pinned ? <PinOff size={16} /> : <Pin size={16} />}
                  {event.pinned ? 'Unpin Event' : 'Pin Event'}
                </button>

                <button
                  onClick={() => handleAction('snooze')}
                  disabled={isPending}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold uppercase border-2 border-black bg-white hover:bg-status-warning/20 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Clock size={16} />
                  Snooze 24h
                </button>

                <button
                  onClick={() => handleAction('resolve')}
                  disabled={isPending}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold uppercase border-2 border-black bg-status-success text-white hover:bg-status-success/90 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <CheckCircle size={16} />
                  Mark Resolved
                </button>

                <button
                  onClick={() => handleAction('dismiss')}
                  disabled={isPending}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold uppercase border-2 border-black bg-white text-status-error hover:bg-status-error hover:text-white transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <X size={16} />
                  Dismiss
                </button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-gray-600 text-sm">
                  This event has been {event.status}.
                </p>
                {event.dismissed_reason && (
                  <p className="text-xs text-gray-500 mt-2">
                    Reason: {event.dismissed_reason}
                  </p>
                )}
              </div>
            )}

            {/* Event Metadata */}
            <div className="mt-6 pt-4 border-t border-gray-300">
              <h4 className="text-xs font-bold text-gray-500 uppercase mb-3">Event Info</h4>
              <div className="space-y-2 text-xs text-gray-600">
                <div className="flex justify-between">
                  <span>Started:</span>
                  <span className="text-black">{formatDateTime(event.start_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Title source:</span>
                  <span className="text-black uppercase">{event.title_source}</span>
                </div>
                {event.resolved_at && (
                  <div className="flex justify-between">
                    <span>Resolved:</span>
                    <span className="text-black">{formatDateTime(event.resolved_at)}</span>
                  </div>
                )}
                {event.snoozed_until && (
                  <div className="flex justify-between">
                    <span>Snoozed until:</span>
                    <span className="text-black">{formatDateTime(event.snoozed_until)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
