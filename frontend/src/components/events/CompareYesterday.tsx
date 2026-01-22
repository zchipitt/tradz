/**
 * CompareYesterday component - shows changes since yesterday's brief.
 * Displays new events, resolved events, and score changes.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  TrendingUp,
  TrendingDown,
  Plus,
  Check,
  AlertCircle,
  Minus,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type {
  BriefDiffResponse,
  NewEventSummary,
  ResolvedEventSummary,
  EventScoreChange,
} from '../../api/types';

interface CompareYesterdayProps {
  diff?: BriefDiffResponse | null;
  isLoading?: boolean;
  isError?: boolean;
  error?: Error | null;
  onRetry?: () => void;
}

/**
 * Loading skeleton for comparison section.
 */
function ComparisonSkeleton() {
  return (
    <div className="animate-pulse space-y-3">
      <div className="flex gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex-1 p-3 bg-gray-100 border-2 border-gray-200">
            <div className="w-12 h-6 bg-gray-200 rounded mb-2" />
            <div className="w-24 h-3 bg-gray-200 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Summary stat card showing count and label.
 */
interface StatCardProps {
  count: number;
  label: string;
  icon: React.ElementType;
  colorClass: string;
  bgClass: string;
}

function StatCard({ count, label, icon: Icon, colorClass, bgClass }: StatCardProps) {
  return (
    <div className={cn('p-3 border-2 border-black', bgClass)}>
      <div className="flex items-center gap-2 mb-1">
        <Icon size={16} className={colorClass} />
        <span className={cn('text-2xl font-bold', colorClass)}>{count}</span>
      </div>
      <span className="text-xs font-bold uppercase tracking-wide text-gray-600">
        {label}
      </span>
    </div>
  );
}

/**
 * New event item with NEW badge.
 */
function NewEventItem({ event }: { event: NewEventSummary }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0">
      <div className="flex items-center gap-2 min-w-0">
        <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide bg-primary border border-black">
          NEW
        </span>
        {event.ticker && (
          <span className="text-xs font-bold uppercase text-black">
            {event.ticker}
          </span>
        )}
        <span className="text-xs text-gray-600 truncate">{event.title}</span>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0 ml-2">
        <span className="text-xs font-bold text-black">
          {Math.round(event.attention_score)}
        </span>
      </div>
    </div>
  );
}

/**
 * Resolved event item with strikethrough.
 */
function ResolvedEventItem({ event }: { event: ResolvedEventSummary }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0 opacity-60">
      <div className="flex items-center gap-2 min-w-0">
        <Check size={14} className="text-status-success flex-shrink-0" />
        {event.ticker && (
          <span className="text-xs font-bold uppercase text-gray-400 line-through">
            {event.ticker}
          </span>
        )}
        <span className="text-xs text-gray-400 truncate line-through">{event.title}</span>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0 ml-2">
        <span className="text-[10px] uppercase text-gray-400">
          {event.resolution_type}
        </span>
      </div>
    </div>
  );
}

/**
 * Score change item with up/down arrow and delta.
 */
function ScoreChangeItem({ change }: { change: EventScoreChange }) {
  const isUp = change.direction === 'up';
  const isDown = change.direction === 'down';

  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0">
      <div className="flex items-center gap-2 min-w-0">
        {isUp && <TrendingUp size={14} className="text-status-success flex-shrink-0" />}
        {isDown && <TrendingDown size={14} className="text-status-error flex-shrink-0" />}
        {!isUp && !isDown && <Minus size={14} className="text-gray-400 flex-shrink-0" />}
        {change.ticker && (
          <span className="text-xs font-bold uppercase text-black">
            {change.ticker}
          </span>
        )}
        <span className="text-xs text-gray-600 truncate">{change.title}</span>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0 ml-2">
        <span
          className={cn(
            'text-xs font-bold',
            isUp && 'text-status-success',
            isDown && 'text-status-error',
            !isUp && !isDown && 'text-gray-400'
          )}
        >
          {isUp && '+'}
          {Math.round(change.delta)}
        </span>
        <span className="text-xs text-gray-400">
          ({Math.round(change.current_score)})
        </span>
      </div>
    </div>
  );
}

export function CompareYesterday({
  diff,
  isLoading,
  isError,
  error,
  onRetry,
}: CompareYesterdayProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  // Check if there are any changes to show
  const hasChanges = diff && (
    diff.total_new_events > 0 ||
    diff.total_resolved > 0 ||
    diff.total_score_changes > 0
  );

  // Don't show if no baseline exists (yesterday's brief not available)
  const hasBaseline = diff?.has_baseline ?? false;

  return (
    <div className="bg-white border-2 border-black font-mono">
      {/* Header - always visible */}
      <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer"
        >
          <span className="text-sm font-bold uppercase tracking-wider">
            Δ Compare Yesterday
          </span>
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>

        {/* Quick summary badge */}
        {!isLoading && !isError && diff && hasBaseline && (
          <div className="flex items-center gap-3 text-xs">
            {diff.total_new_events > 0 && (
              <span className="flex items-center gap-1 text-black">
                <Plus size={12} />
                <span className="font-bold">{diff.total_new_events}</span>
                <span className="text-gray-500">new</span>
              </span>
            )}
            {diff.total_resolved > 0 && (
              <span className="flex items-center gap-1 text-status-success">
                <Check size={12} />
                <span className="font-bold">{diff.total_resolved}</span>
                <span className="text-gray-500">resolved</span>
              </span>
            )}
            {diff.total_score_changes > 0 && (
              <span className="flex items-center gap-1 text-gray-600">
                <TrendingUp size={12} />
                <span className="font-bold">{diff.total_score_changes}</span>
                <span className="text-gray-500">changes</span>
              </span>
            )}
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <span className="text-xs text-gray-500">Loading...</span>
        )}

        {/* Error state */}
        {isError && (
          <span className="text-xs text-status-error">Failed to load diff</span>
        )}
      </div>

      {/* Collapsible content */}
      {isExpanded && (
        <div className="p-4">
          {/* Error state with retry */}
          {isError && (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <AlertCircle size={32} className="text-status-error mb-3" />
              <p className="text-sm text-gray-600 mb-3">
                {error?.message || 'Failed to compare briefs'}
              </p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="px-4 py-2 text-xs font-bold uppercase bg-white border-2 border-black hover:bg-gray-100 transition-colors cursor-pointer"
                >
                  Retry
                </button>
              )}
            </div>
          )}

          {/* Loading skeleton */}
          {isLoading && <ComparisonSkeleton />}

          {/* No baseline state */}
          {!isLoading && !isError && diff && !hasBaseline && (
            <div className="text-center py-6 text-gray-500">
              <p className="text-sm">No baseline brief available for comparison.</p>
              <p className="text-xs mt-1">Yesterday's brief hasn't been generated yet.</p>
            </div>
          )}

          {/* No changes state */}
          {!isLoading && !isError && diff && hasBaseline && !hasChanges && (
            <div className="text-center py-6 text-gray-500">
              <Check size={24} className="mx-auto mb-2 text-status-success" />
              <p className="text-sm">No significant changes since yesterday.</p>
            </div>
          )}

          {/* Summary stats */}
          {!isLoading && !isError && diff && hasBaseline && hasChanges && (
            <>
              <div className="grid grid-cols-3 gap-3 mb-4">
                <StatCard
                  count={diff.total_new_events}
                  label="New Events"
                  icon={Plus}
                  colorClass="text-black"
                  bgClass="bg-primary/20"
                />
                <StatCard
                  count={diff.total_resolved}
                  label="Resolved"
                  icon={Check}
                  colorClass="text-status-success"
                  bgClass="bg-status-success/10"
                />
                <StatCard
                  count={diff.total_score_changes}
                  label="Score Changes"
                  icon={TrendingUp}
                  colorClass="text-gray-600"
                  bgClass="bg-gray-100"
                />
              </div>

              {/* Toggle for full details */}
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="w-full py-2 text-xs font-bold uppercase tracking-wide text-center border-2 border-dashed border-gray-300 hover:border-black hover:bg-gray-50 transition-colors cursor-pointer"
              >
                {showDetails ? 'Hide Details' : 'Show Full Details'}
                {showDetails ? (
                  <ChevronUp size={14} className="inline ml-1" />
                ) : (
                  <ChevronDown size={14} className="inline ml-1" />
                )}
              </button>

              {/* Detailed sections */}
              {showDetails && (
                <div className="mt-4 space-y-4">
                  {/* New Events */}
                  {diff.new_events.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wide text-black mb-2 flex items-center gap-2">
                        <Plus size={14} />
                        New Events ({diff.new_events.length})
                      </h4>
                      <div className="border-2 border-black p-2">
                        {diff.new_events.map((event) => (
                          <NewEventItem key={event.event_id} event={event} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Score Changes */}
                  {diff.score_changes.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wide text-black mb-2 flex items-center gap-2">
                        <TrendingUp size={14} />
                        Score Changes ({diff.score_changes.length})
                      </h4>
                      <div className="border-2 border-black p-2">
                        {diff.score_changes.map((change) => (
                          <ScoreChangeItem key={change.event_id} change={change} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Resolved Events */}
                  {diff.resolved_events.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wide text-gray-500 mb-2 flex items-center gap-2">
                        <Check size={14} />
                        Resolved Events ({diff.resolved_events.length})
                      </h4>
                      <div className="border-2 border-gray-300 p-2">
                        {diff.resolved_events.map((event) => (
                          <ResolvedEventItem key={event.event_id} event={event} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* New Trade Ideas */}
                  {diff.new_trade_ideas.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wide text-black mb-2 flex items-center gap-2">
                        <TrendingUp size={14} />
                        New Trade Ideas ({diff.new_trade_ideas.length})
                      </h4>
                      <div className="border-2 border-black p-2">
                        {diff.new_trade_ideas.map((idea) => (
                          <div
                            key={idea.event_id}
                            className="flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0"
                          >
                            <div className="flex items-center gap-2">
                              <span
                                className={cn(
                                  'inline-flex items-center px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide border border-black',
                                  idea.direction === 'long'
                                    ? 'bg-status-success/20 text-status-success'
                                    : idea.direction === 'short'
                                    ? 'bg-status-error/20 text-status-error'
                                    : 'bg-gray-100 text-gray-600'
                                )}
                              >
                                {idea.direction}
                              </span>
                              {idea.ticker && (
                                <span className="text-xs font-bold uppercase text-black">
                                  {idea.ticker}
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-gray-500">
                              Entry: {idea.entry_zone} → Target: {idea.target}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Closed Loops */}
                  {diff.closed_loops.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wide text-gray-500 mb-2 flex items-center gap-2">
                        <Check size={14} />
                        Closed Loops ({diff.closed_loops.length})
                      </h4>
                      <div className="border-2 border-gray-300 p-2">
                        {diff.closed_loops.map((loop) => (
                          <div
                            key={loop.loop_id}
                            className="flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0 opacity-60"
                          >
                            <span className="text-xs text-gray-400 line-through truncate">
                              {loop.question}
                            </span>
                            <span className="text-[10px] uppercase text-gray-400 ml-2 flex-shrink-0">
                              {loop.resolution}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Comparison dates */}
              <div className="mt-4 pt-3 border-t border-gray-200 text-xs text-gray-400 text-center">
                Comparing {diff.date} vs {diff.baseline}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
