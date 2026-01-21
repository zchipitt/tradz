/**
 * Signal Inbox component - Event list with filtering.
 * Brutalist design aesthetic - black/white + yellow accent.
 *
 * US-004b: Displays events from GET /api/events with:
 * - Tab switcher for Active/Resolved/All views
 * - Loading state with skeleton placeholders
 * - Error state with retry button
 * - Empty state with helpful message
 * - Auto-refresh every 5 minutes via TanStack Query
 */
import { useState } from 'react';
import { Inbox, Eye, EyeOff, RefreshCw, AlertCircle } from 'lucide-react';
import { cn } from '../../lib/utils';
import { EventCard } from './EventCard';
import type { Event } from '../../api/types';

interface SignalInboxProps {
  events: Event[];
  isLoading?: boolean;
  isError?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  onAction?: (eventId: string, action: 'dismiss' | 'snooze' | 'pin' | 'unpin' | 'resolve') => void;
  onOpenEvent?: (event: Event) => void;
}

type FilterState = 'active' | 'all' | 'resolved';

/**
 * Skeleton placeholder for loading state.
 */
function EventCardSkeleton() {
  return (
    <div className="bg-white border-2 border-black overflow-hidden animate-pulse">
      {/* Header */}
      <div className="px-4 py-2 bg-gray-100 border-b border-black flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-5 w-16 bg-gray-300" />
          <div className="h-4 w-20 bg-gray-200" />
          <div className="h-4 w-16 bg-gray-200" />
        </div>
        <div className="h-4 w-12 bg-gray-200" />
      </div>

      {/* Main Content */}
      <div className="p-4">
        <div className="flex items-start gap-4 mb-4">
          {/* Score box */}
          <div className="flex-shrink-0 w-14 h-14 border-2 border-gray-200 bg-gray-100" />
          {/* Title + assets */}
          <div className="flex-1 min-w-0">
            <div className="h-6 w-3/4 bg-gray-300 mb-2" />
            <div className="flex items-center gap-2 mt-2">
              <div className="h-5 w-16 bg-gray-200" />
              <div className="h-5 w-16 bg-gray-200" />
            </div>
          </div>
        </div>

        {/* Score pills */}
        <div className="flex items-center gap-6 mb-4 pb-3 border-b border-gray-200">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-4 w-12 bg-gray-200" />
          ))}
        </div>

        {/* Summary */}
        <div className="h-4 w-full bg-gray-200 mb-2" />
        <div className="h-4 w-2/3 bg-gray-200" />
      </div>
    </div>
  );
}

export function SignalInbox({
  events,
  isLoading = false,
  isError = false,
  error = null,
  onRetry,
  onAction,
  onOpenEvent,
}: SignalInboxProps) {
  const [filter, setFilter] = useState<FilterState>('active');
  const [showResolved, setShowResolved] = useState(false);

  // Filter events based on current filter
  const filteredEvents = events.filter((event) => {
    // Don't show snoozed events
    if (event.snoozed_until && new Date(event.snoozed_until) > new Date()) {
      return false;
    }

    switch (filter) {
      case 'active':
        return event.state !== 'resolved' && event.state !== 'dismissed';
      case 'resolved':
        return event.state === 'resolved';
      case 'all':
        return event.state !== 'dismissed';
      default:
        return true;
    }
  });

  // Sort: pinned first, then by attention score
  const sortedEvents = [...filteredEvents].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1;
    if (!a.pinned && b.pinned) return 1;
    return b.attention_score - a.attention_score;
  });

  // Count by state
  const stateCounts = events.reduce(
    (acc, event) => {
      if (event.state === 'new') acc.new++;
      else if (event.state === 'ongoing') acc.ongoing++;
      else if (event.state === 'stale') acc.stale++;
      else if (event.state === 'resolved') acc.resolved++;
      return acc;
    },
    { new: 0, ongoing: 0, stale: 0, resolved: 0 }
  );

  const activeCount = stateCounts.new + stateCounts.ongoing + stateCounts.stale;

  // Error state
  if (isError) {
    return (
      <div className="bg-white border-2 border-black font-mono">
        {/* Header */}
        <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
          <span className="text-sm font-bold uppercase tracking-wider">
            Signal Inbox
          </span>
        </div>

        {/* Error content */}
        <div className="p-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 border-2 border-status-error mb-4">
            <AlertCircle size={32} className="text-status-error" />
          </div>
          <p className="text-lg font-bold uppercase tracking-wider text-status-error">
            Failed to Load Events
          </p>
          <p className="text-sm text-gray-500 mt-2 mb-6">
            {error?.message || 'Unable to fetch events from the server. Please try again.'}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center gap-2 px-4 py-2 border-2 border-black font-bold text-sm uppercase tracking-wider hover:bg-primary transition-colors cursor-pointer"
            >
              <RefreshCw size={14} />
              Retry
            </button>
          )}
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white border-2 border-black font-mono">
        {/* Header */}
        <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm font-bold uppercase tracking-wider">
              Signal Inbox
            </span>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <RefreshCw size={12} className="animate-spin" />
              Loading...
            </div>
          </div>

          {/* Disabled filter controls during loading */}
          <div className="flex items-center gap-3">
            <div className="flex items-center border-2 border-gray-300 opacity-50">
              {(['active', 'resolved', 'all'] as FilterState[]).map((f) => (
                <button
                  key={f}
                  disabled
                  className="px-3 py-1.5 text-xs font-bold uppercase tracking-wide bg-white text-gray-400 cursor-not-allowed"
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Skeleton placeholders */}
        <div className="p-4 space-y-4">
          {[...Array(3)].map((_, i) => (
            <EventCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border-2 border-black font-mono">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-sm font-bold uppercase tracking-wider">
            Signal Inbox
          </span>

          {/* State counts */}
          <div className="flex items-center gap-2">
            {stateCounts.new > 0 && (
              <span className="px-2 py-0.5 text-xs font-bold bg-primary border border-black">
                {stateCounts.new} NEW
              </span>
            )}
            {stateCounts.ongoing > 0 && (
              <span className="px-2 py-0.5 text-xs font-bold bg-status-success/20 border border-status-success text-status-success">
                {stateCounts.ongoing} ONGOING
              </span>
            )}
            {stateCounts.stale > 0 && (
              <span className="px-2 py-0.5 text-xs font-bold bg-status-error/20 border border-status-error text-status-error">
                {stateCounts.stale} STALE
              </span>
            )}
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center border-2 border-black">
            {(['active', 'resolved', 'all'] as FilterState[]).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  'px-3 py-1.5 text-xs font-bold uppercase tracking-wide transition-colors cursor-pointer',
                  filter === f
                    ? 'bg-black text-white'
                    : 'bg-white text-black hover:bg-gray-100'
                )}
              >
                {f === 'active' ? `Active (${activeCount})` : f}
              </button>
            ))}
          </div>

          <button
            onClick={() => setShowResolved(!showResolved)}
            className="p-2 border border-black hover:bg-gray-100 transition-colors cursor-pointer"
            title={showResolved ? 'Hide resolved' : 'Show resolved'}
          >
            {showResolved ? <Eye size={14} /> : <EyeOff size={14} />}
          </button>
        </div>
      </div>

      {/* Event List */}
      <div className="p-4 space-y-4">
        {sortedEvents.length === 0 ? (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-16 h-16 border-2 border-black mb-4">
              <Inbox size={32} className="text-gray-400" />
            </div>
            <p className="text-lg font-bold uppercase tracking-wider">
              No Events Found
            </p>
            <p className="text-sm text-gray-500 mt-2">
              {filter === 'active'
                ? 'All caught up! No active events right now.'
                : filter === 'resolved'
                ? 'No resolved events in the system.'
                : 'No events available in the database.'}
            </p>
          </div>
        ) : (
          sortedEvents.map((event) => (
            <EventCard
              key={event.id}
              event={event}
              onAction={onAction}
              onOpen={onOpenEvent}
            />
          ))
        )}
      </div>

      {/* Footer status */}
      {sortedEvents.length > 0 && (
        <div className="px-4 py-3 bg-gray-50 border-t-2 border-black flex items-center justify-between text-xs">
          <span className="text-gray-600">
            Showing {sortedEvents.length} of {events.length} events
          </span>
          <span className="text-gray-600">
            Sorted by: <span className="font-bold">Attention Score</span>
          </span>
        </div>
      )}
    </div>
  );
}
