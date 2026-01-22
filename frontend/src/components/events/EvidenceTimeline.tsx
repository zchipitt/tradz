/**
 * Evidence Timeline component - chronological timeline of observations supporting an event.
 * Brutalist design aesthetic - black/white + yellow accent.
 *
 * Features:
 * - Reverse chronological order of observations
 * - Source filter chips (All, Market, News, SEC, Congress, 13F, Polymarket)
 * - Expandable entries showing full details and facts
 * - Source URL links open in new tab
 * - Load more button for pagination
 * - Empty state when no observations match filter
 */
import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  TrendingUp,
  FileText,
  Shield,
  BarChart3,
  Zap,
  Newspaper,
  Filter,
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useEventTimeline } from '../../hooks/useEvents';
import type { TimelineSourceFilter, TimelineObservation, FactEntry } from '../../api/types';

interface EvidenceTimelineProps {
  eventId: string;
}

// Source filter chip configuration
const sourceFilters: { value: TimelineSourceFilter; label: string; icon: React.ElementType }[] = [
  { value: 'all', label: 'All', icon: Filter },
  { value: 'market', label: 'Market', icon: TrendingUp },
  { value: 'news', label: 'News', icon: Newspaper },
  { value: 'sec', label: 'SEC', icon: Shield },
  { value: 'congress', label: 'Congress', icon: TrendingUp },
  { value: '13f', label: '13F', icon: BarChart3 },
  { value: 'polymarket', label: 'Polymarket', icon: Zap },
];

// Source icon mapping
function getSourceIcon(source: string): React.ElementType {
  switch (source.toLowerCase()) {
    case 'equities':
    case 'crypto':
      return TrendingUp;
    case 'news':
      return Newspaper;
    case 'sec':
      return Shield;
    case 'congress':
      return TrendingUp;
    case 'hedgefund':
    case '13f':
      return BarChart3;
    case 'polymarket':
      return Zap;
    default:
      return FileText;
  }
}

// Format timestamp to relative time
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

// Format timestamp to full date/time
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
 * Filter chip component for selecting source type.
 */
function FilterChip({
  filter,
  isActive,
  onClick,
  count,
}: {
  filter: { value: TimelineSourceFilter; label: string; icon: React.ElementType };
  isActive: boolean;
  onClick: () => void;
  count?: number;
}) {
  const Icon = filter.icon;
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold uppercase border-2 transition-all cursor-pointer',
        isActive
          ? 'bg-primary border-black text-black'
          : 'bg-white border-gray-300 text-gray-600 hover:border-black hover:text-black'
      )}
    >
      <Icon size={12} />
      <span>{filter.label}</span>
      {count !== undefined && (
        <span className={cn(
          'ml-1 px-1.5 py-0.5 text-[10px] rounded-sm',
          isActive ? 'bg-black text-white' : 'bg-gray-200 text-gray-600'
        )}>
          {count}
        </span>
      )}
    </button>
  );
}

/**
 * Single observation entry in the timeline.
 */
function TimelineEntry({
  observation,
  isExpanded,
  onToggle,
}: {
  observation: TimelineObservation;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const SourceIcon = getSourceIcon(observation.source);

  return (
    <div
      className={cn(
        'bg-white border-2 transition-all',
        isExpanded ? 'border-black shadow-brutal-sm' : 'border-gray-300 hover:border-black'
      )}
    >
      {/* Entry header - always visible */}
      <button
        onClick={onToggle}
        className="w-full p-4 text-left cursor-pointer"
      >
        <div className="flex items-start gap-3">
          {/* Timeline dot and source icon */}
          <div className="flex-shrink-0 w-10 h-10 border-2 border-black flex items-center justify-center bg-gray-50">
            <SourceIcon size={18} className="text-gray-700" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className="font-bold text-sm text-black uppercase">[{observation.source}]</span>
              {observation.observation_type && (
                <span className="text-xs text-gray-500">{observation.observation_type}</span>
              )}
              <span className="text-xs text-gray-400">{formatTimeAgo(observation.timestamp)}</span>
            </div>

            {observation.title ? (
              <h4 className="font-bold text-gray-800 text-sm line-clamp-2">{observation.title}</h4>
            ) : (
              <p className="text-sm text-gray-700 line-clamp-2">
                {observation.summary || 'No summary available'}
              </p>
            )}
          </div>

          {/* Expand/collapse indicator */}
          <div className="flex-shrink-0 p-1">
            {isExpanded ? (
              <ChevronUp size={16} className="text-gray-500" />
            ) : (
              <ChevronDown size={16} className="text-gray-500" />
            )}
          </div>
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-200">
          {/* Full timestamp */}
          <div className="mb-3 text-xs text-gray-500">
            {formatDateTime(observation.timestamp)}
          </div>

          {/* Summary (if title was shown, show summary here) */}
          {observation.title && observation.summary && (
            <p className="text-sm text-gray-700 mb-4">{observation.summary}</p>
          )}

          {/* Fact entries */}
          {observation.fact_entries.length > 0 && (
            <div className="mb-4">
              <h5 className="text-xs font-bold text-gray-500 uppercase mb-2">Extracted Facts</h5>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {observation.fact_entries.map((fact: FactEntry) => (
                  <div
                    key={fact.fact_id}
                    className="p-2 bg-gray-50 border border-gray-200"
                  >
                    <div className="text-[10px] text-gray-500 uppercase mb-0.5">{fact.fact_type}</div>
                    <div className="text-xs">
                      <span className="font-bold text-gray-700">{fact.label}:</span>{' '}
                      <span className="text-gray-900">
                        {String(fact.value)}
                        {fact.unit && ` ${fact.unit}`}
                      </span>
                    </div>
                    {fact.timestamp && (
                      <div className="text-[10px] text-gray-400 mt-1">
                        {formatDateTime(fact.timestamp)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Source URL link */}
          {observation.source_url && (
            <a
              href={observation.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-bold uppercase bg-gray-100 border-2 border-black hover:bg-primary transition-colors"
            >
              <ExternalLink size={12} />
              View Source
            </a>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Loading skeleton for timeline entries.
 */
function TimelineSkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="animate-pulse">
          <div className="p-4 bg-gray-50 border-2 border-gray-200">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-gray-200 rounded" />
              <div className="flex-1">
                <div className="h-4 w-24 bg-gray-200 rounded mb-2" />
                <div className="h-4 w-full bg-gray-200 rounded" />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Empty state when no observations match filter.
 */
function EmptyState({ filter }: { filter: TimelineSourceFilter }) {
  return (
    <div className="p-8 bg-gray-50 border-2 border-gray-200 text-center">
      <FileText size={32} className="text-gray-400 mx-auto mb-3" />
      <p className="text-gray-600 font-bold mb-1">No observations found</p>
      <p className="text-sm text-gray-500">
        {filter === 'all'
          ? 'There are no observations for this event yet.'
          : `No ${filter} observations match this filter. Try selecting "All" to see all sources.`}
      </p>
    </div>
  );
}

/**
 * Error state for timeline loading failure.
 */
function ErrorState({ error, onRetry }: { error: Error; onRetry: () => void }) {
  return (
    <div className="p-8 bg-status-error/10 border-2 border-status-error text-center">
      <AlertTriangle size={32} className="text-status-error mx-auto mb-3" />
      <p className="text-gray-800 font-bold mb-1">Failed to load timeline</p>
      <p className="text-sm text-gray-600 mb-4">{error.message}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 text-xs font-bold uppercase bg-white border-2 border-black hover:bg-primary transition-colors cursor-pointer"
      >
        Try Again
      </button>
    </div>
  );
}

export function EvidenceTimeline({ eventId }: EvidenceTimelineProps) {
  const [sourceFilter, setSourceFilter] = useState<TimelineSourceFilter>('all');
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useEventTimeline(eventId, sourceFilter);

  // Flatten all pages of observations
  const allObservations = data?.pages.flatMap((page) => page.observations) ?? [];
  const totalCount = data?.pages[0]?.total_count ?? 0;

  // Toggle expanded state for an observation
  const toggleExpanded = (observationId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(observationId)) {
        next.delete(observationId);
      } else {
        next.add(observationId);
      }
      return next;
    });
  };

  // Handle filter change - collapse all entries
  const handleFilterChange = (filter: TimelineSourceFilter) => {
    setSourceFilter(filter);
    setExpandedIds(new Set());
  };

  return (
    <div className="space-y-4">
      {/* Header with count */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold uppercase tracking-wider text-black">
          Evidence Timeline
          {totalCount > 0 && (
            <span className="ml-2 text-gray-500 font-normal">({totalCount} total)</span>
          )}
        </h3>
      </div>

      {/* Source filter chips */}
      <div className="flex flex-wrap gap-2">
        {sourceFilters.map((filter) => (
          <FilterChip
            key={filter.value}
            filter={filter}
            isActive={sourceFilter === filter.value}
            onClick={() => handleFilterChange(filter.value)}
          />
        ))}
      </div>

      {/* Timeline content */}
      {isLoading ? (
        <TimelineSkeleton />
      ) : isError && error ? (
        <ErrorState error={error as Error} onRetry={() => refetch()} />
      ) : allObservations.length === 0 ? (
        <EmptyState filter={sourceFilter} />
      ) : (
        <>
          {/* Timeline entries */}
          <div className="space-y-3">
            {allObservations.map((observation) => (
              <TimelineEntry
                key={observation.observation_id}
                observation={observation}
                isExpanded={expandedIds.has(observation.observation_id)}
                onToggle={() => toggleExpanded(observation.observation_id)}
              />
            ))}
          </div>

          {/* Load more button */}
          {hasNextPage && (
            <button
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
              className={cn(
                'w-full py-3 text-sm font-bold uppercase border-2 border-black transition-all cursor-pointer',
                isFetchingNextPage
                  ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                  : 'bg-white hover:bg-primary'
              )}
            >
              {isFetchingNextPage ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 size={16} className="animate-spin" />
                  Loading...
                </span>
              ) : (
                <span>
                  Load More ({allObservations.length} of {totalCount})
                </span>
              )}
            </button>
          )}
        </>
      )}
    </div>
  );
}
