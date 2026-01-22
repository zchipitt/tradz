/**
 * FactSpotlight component - Displays key facts extracted from evidence.
 * Groups facts by category and shows citations with clickable observation links.
 *
 * IMPORTANT: This component only displays deterministic, extracted facts.
 * NO LLM-generated content is shown here - only structured data from observations.
 *
 * Brutalist design aesthetic - black/white + yellow accent.
 *
 * Groups:
 * - Price & Volume: price, price_change, volume, volume_vs_avg, volatility
 * - Filings: filing_type, filed_date, form_url, key_item
 * - News: headline, publisher, published_at, sentiment_score
 * - Insider Activity: politician, party, trade_type, amount_range, trade_date
 * - Predictions: market_question, probability, probability_change
 */
import { useState, useCallback } from 'react';
import {
  TrendingUp,
  FileText,
  Newspaper,
  Building2,
  Target,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Clock,
  Database,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { FactEntry, ObservationSummary } from '../../api/types';

interface FactSpotlightProps {
  observations: ObservationSummary[];
  onHighlightObservation?: (observationId: string) => void;
  className?: string;
}

// Fact type to group mapping
const FACT_TYPE_GROUPS: Record<string, string> = {
  // Price & Volume
  price: 'price_volume',
  price_change: 'price_volume',
  volume: 'price_volume',
  volume_vs_avg: 'price_volume',
  volatility: 'price_volume',
  // Filings
  filing_type: 'filings',
  filed_date: 'filings',
  form_url: 'filings',
  key_item: 'filings',
  // News
  headline: 'news',
  publisher: 'news',
  published_at: 'news',
  sentiment_score: 'news',
  // Insider Activity (Congress, 13F)
  politician: 'insider',
  party: 'insider',
  trade_type: 'insider',
  amount_range: 'insider',
  trade_date: 'insider',
  // Predictions (Polymarket)
  market_question: 'predictions',
  probability: 'predictions',
  probability_change: 'predictions',
  // Ticker is shared across multiple groups
  ticker: 'shared',
  // Other
  other: 'other',
};

interface FactGroup {
  id: string;
  label: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  borderColor: string;
}

const FACT_GROUPS: FactGroup[] = [
  {
    id: 'price_volume',
    label: 'Price & Volume',
    icon: TrendingUp,
    color: 'text-red-600',
    bgColor: 'bg-red-500',
    borderColor: 'border-red-500',
  },
  {
    id: 'filings',
    label: 'Filings',
    icon: FileText,
    color: 'text-blue-600',
    bgColor: 'bg-blue-500',
    borderColor: 'border-blue-500',
  },
  {
    id: 'news',
    label: 'News',
    icon: Newspaper,
    color: 'text-purple-600',
    bgColor: 'bg-purple-500',
    borderColor: 'border-purple-500',
  },
  {
    id: 'insider',
    label: 'Insider Activity',
    icon: Building2,
    color: 'text-green-600',
    bgColor: 'bg-green-500',
    borderColor: 'border-green-500',
  },
  {
    id: 'predictions',
    label: 'Predictions',
    icon: Target,
    color: 'text-orange-600',
    bgColor: 'bg-orange-500',
    borderColor: 'border-orange-500',
  },
];

interface EnrichedFact extends FactEntry {
  observation_id: string;
  source_url: string | null;
}

/**
 * Format timestamp as relative time.
 */
function formatTimeAgo(dateString: string | null): string {
  if (!dateString) return '';
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

/**
 * Format fact value for display.
 */
function formatFactValue(value: unknown, unit: string | null): string {
  if (value === null || value === undefined) return '—';

  // Handle numbers
  if (typeof value === 'number') {
    if (unit === '%') {
      return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
    }
    if (unit === 'x') {
      return `${value.toFixed(1)}x`;
    }
    if (unit === '$') {
      // Format currency
      if (value >= 1000000) {
        return `$${(value / 1000000).toFixed(1)}M`;
      }
      if (value >= 1000) {
        return `$${(value / 1000).toFixed(1)}K`;
      }
      return `$${value.toFixed(2)}`;
    }
    if (unit === 'shares') {
      if (value >= 1000000) {
        return `${(value / 1000000).toFixed(1)}M shares`;
      }
      if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K shares`;
      }
      return `${value.toLocaleString()} shares`;
    }
    return value.toLocaleString();
  }

  // Handle strings
  if (typeof value === 'string') {
    // Truncate long strings
    if (value.length > 100) {
      return value.substring(0, 97) + '...';
    }
    return value;
  }

  return String(value);
}

/**
 * Single fact card component.
 */
function FactCard({
  fact,
  onHighlight,
}: {
  fact: EnrichedFact;
  onHighlight?: (observationId: string) => void;
}) {
  const handleClick = useCallback(() => {
    if (onHighlight && fact.observation_id) {
      onHighlight(fact.observation_id);
    }
  }, [fact.observation_id, onHighlight]);

  const hasLink = !!fact.source_url;
  const isClickable = !!onHighlight || hasLink;

  return (
    <div
      className={cn(
        'p-3 bg-white border-2 transition-all',
        isClickable
          ? 'border-gray-200 hover:border-black cursor-pointer'
          : 'border-gray-200'
      )}
      onClick={isClickable ? handleClick : undefined}
    >
      {/* Fact label */}
      <div className="text-xs text-gray-500 uppercase mb-1">{fact.label}</div>

      {/* Fact value */}
      <div className="text-sm font-bold text-black mb-2">
        {formatFactValue(fact.value, fact.unit)}
      </div>

      {/* Citation: [source, timestamp] */}
      <div className="flex items-center justify-between text-[10px] text-gray-400">
        <span className="flex items-center gap-1">
          <Database size={10} />
          [{fact.source}
          {fact.timestamp && `, ${formatTimeAgo(fact.timestamp)}`}]
        </span>
        {hasLink && (
          <a
            href={fact.source_url!}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-black"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink size={10} />
          </a>
        )}
      </div>
    </div>
  );
}

/**
 * Fact group section component.
 */
function FactGroupSection({
  group,
  facts,
  onHighlightObservation,
}: {
  group: FactGroup;
  facts: EnrichedFact[];
  onHighlightObservation?: (observationId: string) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(true);
  const Icon = group.icon;

  if (facts.length === 0) return null;

  return (
    <div className="border-2 border-gray-200">
      {/* Group header - clickable to expand/collapse */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-2">
          <div className={cn('p-1.5 border border-black', group.bgColor)}>
            <Icon size={12} className="text-white" />
          </div>
          <span className="font-bold text-sm uppercase text-black">
            {group.label}
          </span>
          <span className="text-xs text-gray-500">({facts.length})</span>
        </div>
        <div className="text-gray-400">
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {/* Facts grid */}
      {isExpanded && (
        <div className="p-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {facts.map((fact, idx) => (
              <FactCard
                key={`${fact.fact_id}-${idx}`}
                fact={fact}
                onHighlight={onHighlightObservation}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Empty state when no facts are available.
 */
function EmptyState() {
  return (
    <div className="p-8 bg-gray-50 border-2 border-gray-200 text-center">
      <Database size={32} className="text-gray-400 mx-auto mb-3" />
      <p className="text-gray-600 font-bold mb-1">No facts extracted</p>
      <p className="text-sm text-gray-500">
        There are no verified facts from the observations yet.
      </p>
    </div>
  );
}

export function FactSpotlight({
  observations,
  onHighlightObservation,
  className,
}: FactSpotlightProps) {
  // Extract all facts from observations and enrich with observation context
  const enrichedFacts: EnrichedFact[] = observations.flatMap((obs) =>
    obs.fact_entries.map((fact) => ({
      ...fact,
      observation_id: obs.observation_id,
      source_url: obs.source_url,
    }))
  );

  // Group facts by category
  const factsByGroup: Record<string, EnrichedFact[]> = {};

  for (const fact of enrichedFacts) {
    const groupId = FACT_TYPE_GROUPS[fact.fact_type] || 'other';

    // Skip shared types (like ticker) that appear in multiple groups
    if (groupId === 'shared') continue;

    if (!factsByGroup[groupId]) {
      factsByGroup[groupId] = [];
    }
    factsByGroup[groupId].push(fact);
  }

  // Calculate total facts for display
  const totalFacts = enrichedFacts.filter(
    (f) => FACT_TYPE_GROUPS[f.fact_type] !== 'shared'
  ).length;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold uppercase tracking-wider text-black">
            Fact Spotlight
          </h3>
          <span className="text-xs text-gray-500">
            ({totalFacts} verified fact{totalFacts !== 1 ? 's' : ''})
          </span>
        </div>
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Clock size={12} />
          <span>No LLM content</span>
        </div>
      </div>

      {/* Fact groups */}
      {totalFacts > 0 ? (
        <div className="space-y-3">
          {FACT_GROUPS.map((group) => (
            <FactGroupSection
              key={group.id}
              group={group}
              facts={factsByGroup[group.id] || []}
              onHighlightObservation={onHighlightObservation}
            />
          ))}
        </div>
      ) : (
        <EmptyState />
      )}
    </div>
  );
}
