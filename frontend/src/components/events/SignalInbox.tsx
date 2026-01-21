/**
 * Signal Inbox component - Event list with filtering.
 * Brutalist design aesthetic - black/white + yellow accent.
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
    <div className="bg-white border-2 border-black font-mono" style={{ boxShadow: '4px 4px 0 0 #000000' }}>
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
