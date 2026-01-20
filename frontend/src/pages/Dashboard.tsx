/**
 * Main dashboard page - Event-centric design.
 * Three-section layout: System Status, Signal Inbox, Daily Brief, Market Snapshot.
 * Robinhood-style clean design.
 */
import { useState } from 'react';
import { useEvents, useEventAction } from '../hooks/useEvents';
import { useSignals } from '../hooks/useSignals';
import { SystemStatus } from '../components/events/SystemStatus';
import { SignalInbox } from '../components/events/SignalInbox';
import { DailyBrief } from '../components/events/DailyBrief';
import { MarketSnapshot } from '../components/events/MarketSnapshot';
import { AlertCircle, Loader2 } from 'lucide-react';
import type { Event, Signal } from '../api/types';

interface DashboardProps {
  onEventOpen?: (event: Event) => void;
  onSignalClick?: (signal: Signal) => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function Dashboard({ onEventOpen, onSignalClick, onRefresh, isRefreshing }: DashboardProps) {
  const { data: eventsData, isLoading: eventsLoading, error: eventsError } = useEvents();
  const { data: signalsData } = useSignals();
  const eventAction = useEventAction();

  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);

  // Handle event actions
  const handleEventAction = async (
    eventId: string,
    action: 'dismiss' | 'snooze' | 'pin' | 'unpin' | 'resolve'
  ) => {
    try {
      await eventAction.mutateAsync({
        event_id: eventId,
        action,
        snooze_hours: action === 'snooze' ? 24 : undefined,
      });
    } catch (error) {
      console.error('Event action failed:', error);
    }
  };

  // Handle opening event details
  const handleOpenEvent = (event: Event) => {
    setSelectedEvent(event);
    onEventOpen?.(event);
  };

  // Loading state
  if (eventsLoading && !eventsData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-text-muted">
          <Loader2 className="animate-spin" />
          <span>Loading events...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (eventsError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-center gap-3">
        <AlertCircle className="text-negative" />
        <div>
          <p className="font-medium text-red-800">Error loading events</p>
          <p className="text-sm text-red-600">
            {eventsError instanceof Error ? eventsError.message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  if (!eventsData) {
    return null;
  }

  const { events, daily_brief } = eventsData;

  return (
    <div className="space-y-6">
      {/* Section 1: System Status Header */}
      <SystemStatus
        dataQuality={daily_brief.data_quality}
        lastUpdated={eventsData.generated_at}
        isRefreshing={isRefreshing}
        onRefresh={onRefresh}
        onGenerateBrief={() => {
          // TODO: Implement generate brief
          console.log('Generate brief');
        }}
        onSendEmail={() => {
          // TODO: Implement send email
          console.log('Send email');
        }}
      />

      {/* Section 2: Signal Inbox (Primary) */}
      <SignalInbox
        events={events}
        onAction={handleEventAction}
        onOpenEvent={handleOpenEvent}
      />

      {/* Section 3: Daily Brief Snapshot */}
      <DailyBrief
        brief={daily_brief}
        onOpenFullReport={() => {
          // TODO: Navigate to full report
          console.log('Open full report');
        }}
        onDownloadJson={() => {
          // Download events as JSON
          const blob = new Blob([JSON.stringify(eventsData, null, 2)], {
            type: 'application/json',
          });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `tradz-events-${daily_brief.date}.json`;
          a.click();
          URL.revokeObjectURL(url);
        }}
        onCompareYesterday={() => {
          // TODO: Implement comparison
          console.log('Compare with yesterday');
        }}
      />

      {/* Section 4: Market Snapshot (Secondary, Collapsed by Default) */}
      {signalsData && signalsData.all_signals.length > 0 && (
        <MarketSnapshot
          signals={signalsData.all_signals}
          onSignalClick={onSignalClick}
          defaultExpanded={false}
        />
      )}

      {/* Event Detail Modal (if selected) */}
      {selectedEvent && (
        <EventDetailModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
          onAction={handleEventAction}
        />
      )}
    </div>
  );
}

/**
 * Event Detail Modal - Full event view with evidence timeline.
 */
interface EventDetailModalProps {
  event: Event;
  onClose: () => void;
  onAction: (eventId: string, action: 'dismiss' | 'snooze' | 'pin' | 'unpin' | 'resolve') => void;
}

function EventDetailModal({ event, onClose, onAction }: EventDetailModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 className="font-semibold text-lg text-text">Event Details</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-surface text-text-muted hover:text-text transition-colors cursor-pointer"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Event Header */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                {event.state}
              </span>
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-surface text-text-muted">
                {event.category.replace('_', ' ')}
              </span>
            </div>
            <h1 className="text-xl font-bold text-text mb-2">{event.title}</h1>
            <div className="flex flex-wrap items-center gap-2">
              {event.assets.map((asset) => (
                <span
                  key={asset}
                  className="px-2 py-1 rounded-lg text-sm font-medium bg-surface text-text"
                >
                  {asset}
                </span>
              ))}
            </div>
          </div>

          {/* Score Grid */}
          <div className="grid grid-cols-5 gap-4 mb-6 p-4 bg-surface rounded-xl">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{event.attention_score}</div>
              <div className="text-xs text-text-muted">Attention</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-text">{event.anomaly_score}</div>
              <div className="text-xs text-text-muted">Anomaly</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-text">{event.catalyst_score}</div>
              <div className="text-xs text-text-muted">Catalyst</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-text">{event.flow_score}</div>
              <div className="text-xs text-text-muted">Flow</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-text">{event.confidence_score}</div>
              <div className="text-xs text-text-muted">Confidence</div>
            </div>
          </div>

          {/* Summary */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-2">
              Summary
            </h3>
            <p className="text-text">{event.summary}</p>
          </div>

          {/* Trade Plan */}
          {event.trade_plan && (
            <div className="mb-6 p-4 bg-primary/5 rounded-xl border border-primary/10">
              <h3 className="text-sm font-semibold text-primary uppercase tracking-wide mb-3">
                Trade Plan
              </h3>
              <div className="space-y-2">
                <div>
                  <span className="text-xs font-medium text-text-muted">Thesis:</span>
                  <p className="text-text">{event.trade_plan.thesis}</p>
                </div>
                <div>
                  <span className="text-xs font-medium text-text-muted">Invalidation:</span>
                  <p className="text-text">{event.trade_plan.invalidation}</p>
                </div>
                <div className="flex items-center gap-4">
                  <div>
                    <span className="text-xs font-medium text-text-muted">Timeframe:</span>
                    <p className="text-text">{event.trade_plan.timeframe}</p>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-text-muted">Risk:</span>
                    <p className="text-text capitalize">{event.trade_plan.risk_level}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Evidence Timeline */}
          <div>
            <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-3">
              Evidence Timeline
            </h3>
            <div className="space-y-3">
              {event.evidence.map((ev, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 p-3 bg-surface rounded-lg"
                >
                  <div className="w-2 h-2 rounded-full bg-primary mt-2 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-text">{ev.source}</span>
                      <span className="text-xs text-text-muted">
                        {new Date(ev.timestamp).toLocaleString()}
                      </span>
                      <span className="text-xs px-1.5 py-0.5 rounded bg-gray-200 text-text-muted">
                        {ev.confidence}% conf
                      </span>
                    </div>
                    <p className="text-sm text-text">{ev.summary}</p>
                    {ev.url && (
                      <a
                        href={ev.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline mt-1 inline-block"
                      >
                        View source
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => onAction(event.id, event.pinned ? 'unpin' : 'pin')}
              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-surface text-text hover:bg-gray-200 transition-colors cursor-pointer"
            >
              {event.pinned ? 'Unpin' : 'Pin'}
            </button>
            <button
              onClick={() => onAction(event.id, 'snooze')}
              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-surface text-text hover:bg-gray-200 transition-colors cursor-pointer"
            >
              Snooze 24h
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                onAction(event.id, 'dismiss');
                onClose();
              }}
              className="px-3 py-1.5 rounded-lg text-sm font-medium text-negative hover:bg-red-50 transition-colors cursor-pointer"
            >
              Dismiss
            </button>
            <button
              onClick={() => {
                onAction(event.id, 'resolve');
                onClose();
              }}
              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-primary text-white hover:bg-primary-dark transition-colors cursor-pointer"
            >
              Mark Resolved
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
