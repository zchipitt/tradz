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
  TrendingUp,
  BarChart3,
  Zap,
  Shield,
  FileText,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { useEventDetail, useEventActions } from '../hooks/useEvents';
import { ScoreBreakdown } from '../components/events/ScoreBreakdown';
import { EvidenceTimeline } from '../components/events/EvidenceTimeline';
import { FactSpotlight } from '../components/events/FactSpotlight';
import { ActionPanel } from '../components/events/ActionPanel';
import type { EventState, EventType } from '../api/types';

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
          {/* 4D Score Breakdown */}
          <ScoreBreakdown
            attentionScore={event.attention_score}
            scores={event.scores}
            observations={event.observations}
          />

          {/* Fact Spotlight - Extracted facts grouped by type */}
          <FactSpotlight
            observations={event.observations}
          />

          {/* Action Panel - Trade Idea or Research Plan */}
          <ActionPanel eventId={event.event_id} />

          {/* Event Timeline - using the new EvidenceTimeline component */}
          <EvidenceTimeline eventId={event.event_id} />
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
