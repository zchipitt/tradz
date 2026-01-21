/**
 * Main dashboard page - Brutalist design aesthetic.
 * Black/white + yellow accent, hard borders, dot grid background.
 */
import { useState } from 'react';
import { useEvents, useEventAction } from '../hooks/useEvents';
import { useSignals } from '../hooks/useSignals';
import { SystemStatus } from '../components/events/SystemStatus';
import { SignalInbox } from '../components/events/SignalInbox';
import { DailyBrief } from '../components/events/DailyBrief';
import { MarketSnapshot } from '../components/events/MarketSnapshot';
import { AlertCircle, Loader2, X, ExternalLink } from 'lucide-react';
import { cn } from '../lib/utils';
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

  // Loading state - Brutalist style
  if (eventsLoading && !eventsData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="bg-white border-2 border-black p-8 shadow-brutal">
          <div className="flex items-center gap-4 font-mono">
            <Loader2 className="animate-spin text-black" size={24} />
            <span className="text-lg font-bold">Loading events...</span>
          </div>
        </div>
      </div>
    );
  }

  // Error state - Brutalist style
  if (eventsError) {
    return (
      <div className="bg-white border-2 border-black p-6 shadow-brutal">
        <div className="flex items-center gap-4">
          <AlertCircle className="text-status-error" size={24} />
          <div className="font-mono">
            <p className="font-bold text-lg text-black">ERROR: Event load failed</p>
            <p className="text-gray-600 text-sm mt-1">
              {eventsError instanceof Error ? eventsError.message : 'Unknown error'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!eventsData) {
    return null;
  }

  const { events, daily_brief } = eventsData;

  return (
    <div className="space-y-8">
      {/* Section 1: System Status Header */}
      <SystemStatus
        dataQuality={daily_brief.data_quality}
        lastUpdated={eventsData.generated_at}
        isRefreshing={isRefreshing}
        onRefresh={onRefresh}
        onGenerateBrief={() => {
          console.log('Generate brief');
        }}
        onSendEmail={() => {
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
          console.log('Open full report');
        }}
        onDownloadJson={() => {
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
          console.log('Compare with yesterday');
        }}
      />

      {/* Section 4: Market Snapshot */}
      {signalsData && signalsData.all_signals.length > 0 && (
        <MarketSnapshot
          signals={signalsData.all_signals}
          onSignalClick={onSignalClick}
          defaultExpanded={false}
        />
      )}

      {/* Event Detail Modal */}
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
 * Event Detail Modal - Brutalist design.
 */
interface EventDetailModalProps {
  event: Event;
  onClose: () => void;
  onAction: (eventId: string, action: 'dismiss' | 'snooze' | 'pin' | 'unpin' | 'resolve') => void;
}

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

function EventDetailModal({ event, onClose, onAction }: EventDetailModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
      <div className="bg-white border-2 border-black shadow-brutal max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col font-mono">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-gray-100 border-b-2 border-black flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold uppercase tracking-wide">
              Event Details
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-2 border border-black hover:bg-gray-200 transition-colors cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Event Header */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <span className="badge-brutal badge-brutal-yellow uppercase">
                {event.state}
              </span>
              <span className="badge-brutal badge-brutal-outline uppercase">
                {event.category.replace('_', ' ')}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-black mb-3">{event.title}</h1>
            <div className="flex flex-wrap items-center gap-2">
              {event.assets.map((asset) => (
                <span
                  key={asset}
                  className="px-3 py-1 bg-gray-100 border border-black font-mono text-sm font-bold"
                >
                  ${asset}
                </span>
              ))}
            </div>
          </div>

          {/* Score Grid */}
          <div className="grid grid-cols-5 gap-4 mb-6 p-4 bg-gray-50 border-2 border-black">
            {[
              { label: 'ATT', score: event.attention_score },
              { label: 'ANM', score: event.anomaly_score },
              { label: 'CAT', score: event.catalyst_score },
              { label: 'FLW', score: event.flow_score },
              { label: 'CNF', score: event.confidence_score },
            ].map(({ label, score }) => (
              <div key={label} className="text-center">
                <div className={cn('text-3xl font-bold', getScoreColor(score))}>
                  {score}
                </div>
                <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">{label}</div>
                <div className="w-full h-1 bg-gray-200 border border-black mt-2">
                  <div
                    className={cn('h-full', getScoreBg(score))}
                    style={{ width: `${score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="mb-6">
            <h3 className="text-sm font-bold uppercase tracking-wider mb-2 text-black">
              Summary
            </h3>
            <p className="text-gray-700">{event.summary}</p>
          </div>

          {/* Trade Plan */}
          {event.trade_plan && (
            <div className="mb-6 p-4 bg-primary/20 border-2 border-black">
              <h3 className="text-sm font-bold uppercase tracking-wider mb-3 text-black">
                Trade Plan
              </h3>
              <div className="space-y-3">
                <div>
                  <span className="text-xs font-bold text-gray-500 uppercase">Thesis:</span>
                  <p className="text-gray-800 mt-1">{event.trade_plan.thesis}</p>
                </div>
                <div>
                  <span className="text-xs font-bold text-status-error uppercase">Invalidation:</span>
                  <p className="text-gray-700 mt-1">{event.trade_plan.invalidation}</p>
                </div>
                <div className="flex items-center gap-6">
                  <div>
                    <span className="text-xs font-bold text-gray-500 uppercase">Timeframe:</span>
                    <p className="text-gray-800">{event.trade_plan.timeframe}</p>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-gray-500 uppercase">Risk:</span>
                    <span className={cn(
                      'ml-2 px-2 py-0.5 text-xs font-bold uppercase border border-black',
                      event.trade_plan.risk_level === 'low'
                        ? 'bg-status-success text-white'
                        : event.trade_plan.risk_level === 'medium'
                        ? 'bg-status-warning text-black'
                        : 'bg-status-error text-white'
                    )}>
                      {event.trade_plan.risk_level}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Evidence Timeline */}
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider mb-3 text-black">
              Evidence Timeline
            </h3>
            <div className="space-y-3">
              {event.evidence.map((ev, i) => (
                <div
                  key={i}
                  className="p-4 bg-white border-2 border-gray-300 hover:border-black transition-colors"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-bold text-sm text-black">[{ev.source}]</span>
                    <span className="text-xs text-gray-500">
                      {new Date(ev.timestamp).toLocaleString()}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-gray-100 border border-gray-300 font-bold">
                      CONF: {ev.confidence}%
                    </span>
                  </div>
                  <p className="text-sm text-gray-700">{ev.summary}</p>
                  {ev.url && (
                    <a
                      href={ev.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-black font-bold hover:underline mt-2"
                    >
                      <ExternalLink size={12} />
                      VIEW SOURCE
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-gray-100 border-t-2 border-black flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => onAction(event.id, event.pinned ? 'unpin' : 'pin')}
              className="btn-brutal-outline text-xs"
            >
              {event.pinned ? 'Unpin' : 'Pin'}
            </button>
            <button
              onClick={() => onAction(event.id, 'snooze')}
              className="btn-brutal-outline text-xs"
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
              className="px-4 py-2 border-2 border-black text-status-error font-bold text-xs uppercase hover:bg-status-error hover:text-white transition-colors cursor-pointer"
            >
              Dismiss
            </button>
            <button
              onClick={() => {
                onAction(event.id, 'resolve');
                onClose();
              }}
              className="btn-brutal text-xs"
            >
              Mark Resolved
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
