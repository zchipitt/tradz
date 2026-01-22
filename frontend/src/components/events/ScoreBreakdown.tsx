/**
 * ScoreBreakdown component - Displays detailed 4D score breakdown with contributing factors.
 * Shows attention score prominently with formula tooltip, and each dimension with progress bars.
 *
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import {
  TrendingUp,
  Zap,
  BarChart3,
  Shield,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Newspaper,
  FileText,
  Building2,
  Activity,
  Target,
  Clock,
  Database,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { FourDScores, ObservationSummary } from '../../api/types';

interface ScoreBreakdownProps {
  attentionScore: number;
  scores: FourDScores;
  observations: ObservationSummary[];
  className?: string;
}

interface ScoreFactor {
  label: string;
  value: string | number;
  unit?: string;
  icon: React.ElementType;
}

interface DimensionConfig {
  key: keyof FourDScores;
  label: string;
  abbreviation: string;
  description: string;
  color: string;
  bgColor: string;
  borderColor: string;
  icon: React.ElementType;
}

const DIMENSION_CONFIG: DimensionConfig[] = [
  {
    key: 'anomaly_score',
    label: 'Anomaly',
    abbreviation: 'ANM',
    description: 'Price movement, volume spikes, and volatility changes',
    color: 'text-red-600',
    bgColor: 'bg-red-500',
    borderColor: 'border-red-500',
    icon: TrendingUp,
  },
  {
    key: 'catalyst_score',
    label: 'Catalyst',
    abbreviation: 'CAT',
    description: 'News events, SEC filings, and prediction market shifts',
    color: 'text-blue-600',
    bgColor: 'bg-blue-500',
    borderColor: 'border-blue-500',
    icon: Zap,
  },
  {
    key: 'flow_score',
    label: 'Flow',
    abbreviation: 'FLW',
    description: 'Congressional trades, 13F filings, and institutional activity',
    color: 'text-green-600',
    bgColor: 'bg-green-500',
    borderColor: 'border-green-500',
    icon: BarChart3,
  },
  {
    key: 'confidence_score',
    label: 'Confidence',
    abbreviation: 'CNF',
    description: 'Data quality, source diversity, and information freshness',
    color: 'text-gray-600',
    bgColor: 'bg-gray-500',
    borderColor: 'border-gray-500',
    icon: Shield,
  },
];

/**
 * Calculate contributing factors from observations for each dimension.
 */
function calculateContributingFactors(
  dimension: keyof FourDScores,
  observations: ObservationSummary[]
): ScoreFactor[] {
  const factors: ScoreFactor[] = [];

  switch (dimension) {
    case 'anomaly_score': {
      // Extract price and volume data from market observations
      const marketObs = observations.filter(
        (o) => o.source.toLowerCase() === 'equities' || o.source.toLowerCase() === 'crypto'
      );

      // Get price change from facts
      const priceChangeFact = marketObs
        .flatMap((o) => o.fact_entries)
        .find((f) => f.fact_type === 'change_pct' || f.label.toLowerCase().includes('change'));

      if (priceChangeFact) {
        const value = Number(priceChangeFact.value);
        factors.push({
          label: 'Price Change',
          value: `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`,
          icon: TrendingUp,
        });
      }

      // Get volume ratio from facts
      const volumeFact = marketObs
        .flatMap((o) => o.fact_entries)
        .find(
          (f) =>
            f.fact_type === 'volume_vs_avg' ||
            f.label.toLowerCase().includes('volume')
        );

      if (volumeFact) {
        const value = Number(volumeFact.value);
        factors.push({
          label: 'Vol vs Avg',
          value: `${value.toFixed(1)}x`,
          icon: Activity,
        });
      }

      // Get volatility from facts
      const volatilityFact = marketObs
        .flatMap((o) => o.fact_entries)
        .find((f) => f.label.toLowerCase().includes('volatility'));

      if (volatilityFact) {
        factors.push({
          label: 'Volatility',
          value: `${Number(volatilityFact.value).toFixed(1)}%`,
          icon: Activity,
        });
      }

      // If no specific facts, show market observation count
      if (factors.length === 0 && marketObs.length > 0) {
        factors.push({
          label: 'Market Data Points',
          value: marketObs.length,
          icon: TrendingUp,
        });
      }
      break;
    }

    case 'catalyst_score': {
      // Count news observations
      const newsCount = observations.filter(
        (o) => o.source.toLowerCase() === 'news'
      ).length;
      if (newsCount > 0) {
        factors.push({
          label: 'News Articles',
          value: newsCount,
          icon: Newspaper,
        });
      }

      // Count SEC filings
      const secCount = observations.filter(
        (o) => o.source.toLowerCase() === 'sec'
      ).length;
      if (secCount > 0) {
        factors.push({
          label: 'SEC Filings',
          value: secCount,
          icon: FileText,
        });
      }

      // Count Polymarket observations and extract probability changes
      const polyObs = observations.filter(
        (o) => o.source.toLowerCase() === 'polymarket'
      );
      if (polyObs.length > 0) {
        const probChangeFact = polyObs
          .flatMap((o) => o.fact_entries)
          .find((f) => f.fact_type === 'probability_change' || f.label.toLowerCase().includes('change'));

        if (probChangeFact) {
          const value = Number(probChangeFact.value);
          factors.push({
            label: 'Prediction Shift',
            value: `${value >= 0 ? '+' : ''}${value.toFixed(0)}%`,
            icon: Target,
          });
        } else {
          factors.push({
            label: 'Prediction Markets',
            value: polyObs.length,
            icon: Target,
          });
        }
      }
      break;
    }

    case 'flow_score': {
      // Count Congress trades
      const congressObs = observations.filter(
        (o) => o.source.toLowerCase() === 'congress'
      );
      if (congressObs.length > 0) {
        factors.push({
          label: 'Congress Trades',
          value: congressObs.length,
          icon: Building2,
        });

        // Extract trade amounts if available
        const amountFacts = congressObs
          .flatMap((o) => o.fact_entries)
          .filter((f) => f.fact_type === 'amount_range' || f.label.toLowerCase().includes('amount'));

        if (amountFacts.length > 0) {
          factors.push({
            label: 'Trade Activity',
            value: amountFacts[0].value as string,
            icon: BarChart3,
          });
        }
      }

      // Count 13F filings
      const hedgefundObs = observations.filter(
        (o) => o.source.toLowerCase() === 'hedgefund'
      );
      if (hedgefundObs.length > 0) {
        factors.push({
          label: '13F Filings',
          value: hedgefundObs.length,
          icon: FileText,
        });

        // Extract position changes if available
        const positionFacts = hedgefundObs
          .flatMap((o) => o.fact_entries)
          .filter((f) => f.fact_type === 'position_change' || f.label.toLowerCase().includes('position'));

        if (positionFacts.length > 0) {
          factors.push({
            label: 'Position Changes',
            value: positionFacts.length,
            icon: BarChart3,
          });
        }
      }
      break;
    }

    case 'confidence_score': {
      // Count unique sources
      const uniqueSources = new Set(observations.map((o) => o.source.toLowerCase()));
      factors.push({
        label: 'Data Sources',
        value: uniqueSources.size,
        icon: Database,
      });

      // Calculate freshness (based on most recent observation)
      if (observations.length > 0) {
        const mostRecent = observations.reduce((latest, obs) => {
          const obsDate = new Date(obs.timestamp);
          return obsDate > new Date(latest.timestamp) ? obs : latest;
        });

        const hoursAgo = Math.floor(
          (Date.now() - new Date(mostRecent.timestamp).getTime()) / (1000 * 60 * 60)
        );

        let freshnessLabel: string;
        if (hoursAgo < 1) {
          freshnessLabel = 'Just now';
        } else if (hoursAgo < 24) {
          freshnessLabel = `${hoursAgo}h ago`;
        } else {
          freshnessLabel = `${Math.floor(hoursAgo / 24)}d ago`;
        }

        factors.push({
          label: 'Latest Data',
          value: freshnessLabel,
          icon: Clock,
        });
      }

      // Count total facts
      const totalFacts = observations.reduce(
        (sum, obs) => sum + obs.fact_entries.length,
        0
      );
      if (totalFacts > 0) {
        factors.push({
          label: 'Verified Facts',
          value: totalFacts,
          icon: Shield,
        });
      }
      break;
    }
  }

  return factors;
}

/**
 * Get score level label and color.
 */
function getScoreLevel(score: number): { label: string; color: string } {
  if (score >= 80) return { label: 'Very High', color: 'text-status-success' };
  if (score >= 60) return { label: 'High', color: 'text-score-good' };
  if (score >= 40) return { label: 'Moderate', color: 'text-status-warning' };
  if (score >= 20) return { label: 'Low', color: 'text-orange-500' };
  return { label: 'Very Low', color: 'text-gray-500' };
}

/**
 * Dimension row component with expandable factors.
 */
function DimensionRow({
  config,
  score,
  factors,
}: {
  config: DimensionConfig;
  score: number;
  factors: ScoreFactor[];
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const Icon = config.icon;
  const scoreLevel = getScoreLevel(score);

  return (
    <div className="border-2 border-gray-200 hover:border-gray-400 transition-colors">
      {/* Main row - clickable to expand */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-4 p-3 cursor-pointer"
      >
        {/* Icon */}
        <div className={cn('p-2 border-2 border-black', config.bgColor)}>
          <Icon size={16} className="text-white" />
        </div>

        {/* Label and description */}
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2">
            <span className="font-bold text-black uppercase text-sm">
              {config.label}
            </span>
            <span className="text-xs text-gray-500">({config.abbreviation})</span>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">{config.description}</p>
        </div>

        {/* Score */}
        <div className="text-right">
          <div className={cn('text-2xl font-bold', config.color)}>
            {Math.round(score)}
          </div>
          <div className={cn('text-xs uppercase', scoreLevel.color)}>
            {scoreLevel.label}
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-24 hidden sm:block">
          <div className="h-2 bg-gray-200 border border-black">
            <div
              className={cn('h-full transition-all', config.bgColor)}
              style={{ width: `${score}%` }}
            />
          </div>
        </div>

        {/* Expand icon */}
        <div className="text-gray-400">
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {/* Expanded factors */}
      {isExpanded && (
        <div className="px-3 pb-3 border-t border-gray-200">
          <div className="pt-3 text-xs font-bold text-gray-500 uppercase mb-2">
            Contributing Factors
          </div>
          {factors.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {factors.map((factor, idx) => {
                const FactorIcon = factor.icon;
                return (
                  <div
                    key={idx}
                    className="flex items-center gap-2 px-2 py-1.5 bg-gray-50 border border-gray-200"
                  >
                    <FactorIcon size={12} className="text-gray-500 flex-shrink-0" />
                    <div className="min-w-0">
                      <div className="text-xs text-gray-500">{factor.label}</div>
                      <div className="text-sm font-bold text-black truncate">
                        {factor.value}
                        {factor.unit && (
                          <span className="text-gray-500"> {factor.unit}</span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-xs text-gray-500 italic py-2">
              No specific factors available from observations
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Formula tooltip component.
 */
function FormulaTooltip({ isVisible }: { isVisible: boolean }) {
  if (!isVisible) return null;

  return (
    <div className="absolute z-10 top-full mt-2 left-0 right-0 sm:left-auto sm:right-0 sm:w-80 p-4 bg-black text-white text-xs border-2 border-black shadow-brutal-sm">
      <div className="font-bold uppercase mb-2">Attention Score Formula</div>
      <div className="font-mono text-xs leading-relaxed">
        <span className="text-red-400">0.30</span> × Anomaly +{' '}
        <span className="text-blue-400">0.30</span> × Catalyst +{' '}
        <span className="text-green-400">0.25</span> × Flow +{' '}
        <span className="text-gray-400">0.15</span> × Confidence +{' '}
        <span className="text-yellow-400">Coverage Bonus</span>
      </div>
      <div className="mt-2 pt-2 border-t border-gray-700 text-gray-300">
        Coverage Bonus: +5 per unique source (max +20)
      </div>
    </div>
  );
}

export function ScoreBreakdown({
  attentionScore,
  scores,
  observations,
  className,
}: ScoreBreakdownProps) {
  const [showFormula, setShowFormula] = useState(false);
  const attentionLevel = getScoreLevel(attentionScore);

  // Pre-calculate factors for all dimensions
  const factorsByDimension = DIMENSION_CONFIG.reduce(
    (acc, config) => {
      acc[config.key] = calculateContributingFactors(config.key, observations);
      return acc;
    },
    {} as Record<keyof FourDScores, ScoreFactor[]>
  );

  // Calculate coverage bonus (estimated from unique sources)
  const uniqueSources = new Set(observations.map((o) => o.source.toLowerCase()));
  const coverageBonus = Math.min(uniqueSources.size * 5, 20);

  return (
    <div className={cn('space-y-4', className)}>
      {/* Attention Score - Prominent Display */}
      <div className="p-4 bg-primary border-2 border-black relative">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-bold uppercase tracking-wider text-black">
                Attention Score
              </span>
              <button
                onMouseEnter={() => setShowFormula(true)}
                onMouseLeave={() => setShowFormula(false)}
                onClick={() => setShowFormula(!showFormula)}
                className="p-1 hover:bg-black/10 rounded cursor-pointer"
                aria-label="Show formula"
              >
                <HelpCircle size={14} className="text-black/70" />
              </button>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-bold text-black">
                {Math.round(attentionScore)}
              </span>
              <span className="text-sm font-bold uppercase text-black/70">
                / 100
              </span>
            </div>
            <div className={cn('text-sm font-bold uppercase mt-1', attentionLevel.color)}>
              {attentionLevel.label} Priority
            </div>
          </div>

          {/* Coverage bonus indicator */}
          <div className="text-right">
            <div className="text-xs text-black/70 uppercase">Coverage Bonus</div>
            <div className="text-2xl font-bold text-black">+{coverageBonus}</div>
            <div className="text-xs text-black/70">
              {uniqueSources.size} source{uniqueSources.size !== 1 ? 's' : ''}
            </div>
          </div>
        </div>

        {/* Attention score progress bar */}
        <div className="mt-4 h-3 bg-white border-2 border-black">
          <div
            className="h-full bg-black transition-all"
            style={{ width: `${attentionScore}%` }}
          />
        </div>

        <FormulaTooltip isVisible={showFormula} />
      </div>

      {/* 4D Score Dimensions */}
      <div className="space-y-2">
        <h3 className="text-sm font-bold uppercase tracking-wider text-black">
          Score Dimensions
        </h3>
        {DIMENSION_CONFIG.map((config) => (
          <DimensionRow
            key={config.key}
            config={config}
            score={scores[config.key]}
            factors={factorsByDimension[config.key]}
          />
        ))}
      </div>
    </div>
  );
}
