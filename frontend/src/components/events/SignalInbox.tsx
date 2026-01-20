/**
 * Signal Inbox component - Event list with filtering.
 * Main component for displaying all events sorted by attention score.
 */
import { useState } from 'react';
import { Inbox, Eye, EyeOff } from 'lucide-react';
import { cn } from '../../lib/utils';
import { EventCard } from './EventCard';
import type { Event } from '../../api/types';

interface SignalInboxProps {
  events: Event[];
  onAction?: (eventId: string, action: 'dismiss' | 'snooze' | 'pin' | 'unpin' | 'resolve') => void;
  onOpenEvent?: (event: Event) => void;
}

type FilterState = 'active' | 'all' | 'resolved';

export function SignalInbox({ events, onAction, onOpenEvent }: SignalInboxProps) {
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

  return (
    <div className="bg-white rounded-xl border border-border">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Inbox size={20} className="text-text-muted" />
          <h2 className="font-semibold text-text">Signal Inbox</h2>

          {/* State counts */}
          <div className="flex items-center gap-2 ml-2">
            {stateCounts.new > 0 && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                {stateCounts.new} new
              </span>
            )}
            {stateCounts.ongoing > 0 && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600">
                {stateCounts.ongoing} ongoing
              </span>
            )}
            {stateCounts.stale > 0 && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-600">
                {stateCounts.stale} stale
              </span>
            )}
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-surface rounded-lg p-0.5">
            <button
              onClick={() => setFilter('active')}
              className={cn(
                'px-3 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer',
                filter === 'active'
                  ? 'bg-white text-text shadow-sm'
                  : 'text-text-muted hover:text-text'
              )}
            >
              Active ({activeCount})
            </button>
            <button
              onClick={() => setFilter('resolved')}
              className={cn(
                'px-3 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer',
                filter === 'resolved'
                  ? 'bg-white text-text shadow-sm'
                  : 'text-text-muted hover:text-text'
              )}
            >
              Resolved
            </button>
            <button
              onClick={() => setFilter('all')}
              className={cn(
                'px-3 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer',
                filter === 'all'
                  ? 'bg-white text-text shadow-sm'
                  : 'text-text-muted hover:text-text'
              )}
            >
              All
            </button>
          </div>

          <button
            onClick={() => setShowResolved(!showResolved)}
            className="p-2 rounded-lg hover:bg-surface text-text-muted hover:text-text transition-colors cursor-pointer"
            title={showResolved ? 'Hide resolved' : 'Show resolved'}
          >
            {showResolved ? <Eye size={16} /> : <EyeOff size={16} />}
          </button>
        </div>
      </div>

      {/* Event List */}
      <div className="p-4 space-y-4">
        {sortedEvents.length === 0 ? (
          <div className="text-center py-12 text-text-muted">
            <Inbox size={40} className="mx-auto mb-3 opacity-50" />
            <p className="font-medium">No events to show</p>
            <p className="text-sm mt-1">
              {filter === 'active'
                ? 'All caught up! No active events right now.'
                : filter === 'resolved'
                ? 'No resolved events yet.'
                : 'No events available.'}
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
    </div>
  );
}
