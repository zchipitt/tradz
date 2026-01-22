/**
 * Main dashboard page - Brutalist design aesthetic.
 * Black/white + yellow accent, hard borders, dot grid background.
 */
import { useEvents, useEventAction, useSystemStatus } from '../hooks/useEvents';
import { useSignals } from '../hooks/useSignals';
import { useLatestBrief } from '../hooks/useDailyBrief';
import { SystemStatus } from '../components/events/SystemStatus';
import { SignalInbox } from '../components/events/SignalInbox';
import { DailyBrief } from '../components/events/DailyBrief';
import { MarketSnapshot } from '../components/events/MarketSnapshot';
import type { Event, Signal } from '../api/types';

interface DashboardProps {
  onEventOpen?: (event: Event) => void;
  onSignalClick?: (signal: Signal) => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function Dashboard({ onEventOpen, onSignalClick, onRefresh, isRefreshing }: DashboardProps) {
  const { data: eventsData, isLoading: eventsLoading, error: eventsError, refetch: refetchEvents } = useEvents();
  const { data: signalsData } = useSignals();
  const { data: systemStatusData, isLoading: statusLoading, error: statusError, refetch: refetchStatus } = useSystemStatus();
  const eventAction = useEventAction();

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

  // Handle opening event details - navigates to event detail page
  const handleOpenEvent = (event: Event) => {
    onEventOpen?.(event);
  };

  // Get events using the events hook
  const events = eventsData?.events ?? [];

  // Get the latest brief using the separate brief API
  const { data: briefData } = useLatestBrief();
  const brief = briefData?.brief;

  return (
    <div className="space-y-8">
      {/* Section 1: System Status Header */}
      <SystemStatus
        systemStatus={systemStatusData}
        isLoading={statusLoading && !systemStatusData}
        isError={!!statusError}
        error={statusError instanceof Error ? statusError : null}
        lastUpdated={eventsData?.generated_at}
        isRefreshing={isRefreshing}
        onRefresh={() => {
          onRefresh?.();
          refetchStatus();
        }}
        onRetry={() => refetchStatus()}
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
        isLoading={eventsLoading && !eventsData}
        isError={!!eventsError}
        error={eventsError instanceof Error ? eventsError : null}
        onRetry={() => refetchEvents()}
        onAction={handleEventAction}
        onOpenEvent={handleOpenEvent}
      />

      {/* Section 3: Daily Brief Snapshot */}
      {brief && (
        <DailyBrief brief={brief} />
      )}

      {/* Section 4: Market Snapshot */}
      {signalsData && signalsData.all_signals.length > 0 && (
        <MarketSnapshot
          signals={signalsData.all_signals}
          onSignalClick={onSignalClick}
          defaultExpanded={false}
        />
      )}
    </div>
  );
}
