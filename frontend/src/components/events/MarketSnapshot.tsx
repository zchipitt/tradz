/**
 * Market Snapshot - Collapsible heatmap with asset type sections.
 * Shows top 5 per asset type (Equity, Crypto, Polymarket) with individual expand/collapse.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import { ChevronDown, ChevronUp, BarChart3, TrendingUp, Bitcoin, PieChart } from 'lucide-react';
import { cn, formatPercent } from '../../lib/utils';
import type { Signal, AssetType } from '../../api/types';

interface MarketSnapshotProps {
  signals: Signal[];
  onSignalClick?: (signal: Signal) => void;
  defaultExpanded?: boolean;
}

interface AssetSectionProps {
  title: string;
  icon: React.ElementType;
  signals: Signal[];
  color: string;
  bgColor: string;
  borderColor: string;
  onSignalClick?: (signal: Signal) => void;
  defaultExpanded?: boolean;
}

// Brutalist score color - high contrast
function getScoreColor(score: number): string {
  if (score >= 80) return '#22C55E';
  if (score >= 60) return '#4ADE80';
  if (score >= 40) return '#F59E0B';
  if (score >= 20) return '#F97316';
  return '#EF4444';
}

function getScoreBg(score: number): string {
  if (score >= 80) return 'rgba(34, 197, 94, 0.15)';
  if (score >= 60) return 'rgba(74, 222, 128, 0.15)';
  if (score >= 40) return 'rgba(245, 158, 11, 0.15)';
  if (score >= 20) return 'rgba(249, 115, 22, 0.15)';
  return 'rgba(239, 68, 68, 0.15)';
}

/**
 * Individual asset type section with its own expand/collapse.
 */
function AssetSection({
  title,
  icon: Icon,
  signals,
  color,
  bgColor,
  borderColor,
  onSignalClick,
  defaultExpanded = true,
}: AssetSectionProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  // Show top 5 by score when collapsed, all when expanded
  const topSignals = signals.slice(0, 5);
  const displayedSignals = expanded ? signals : topSignals;
  const hasMore = signals.length > 5;

  if (signals.length === 0) {
    return null;
  }

  const avgScore = Math.round(signals.reduce((sum, s) => sum + s.score, 0) / signals.length);
  const topMover = signals.reduce((top, s) =>
    Math.abs(s.metrics.day_return) > Math.abs(top.metrics.day_return) ? s : top
  );

  return (
    <div className={cn('border-2', borderColor)}>
      {/* Section Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'w-full px-3 py-2 flex items-center justify-between',
          'hover:opacity-80 transition-opacity cursor-pointer',
          bgColor
        )}
      >
        <div className="flex items-center gap-3">
          <Icon size={14} className={color} />
          <span className={cn('text-xs font-bold uppercase tracking-wide', color)}>
            {title}
          </span>
          <span className="text-xs text-gray-500">
            ({signals.length})
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Quick stats */}
          <span className={cn(
            'text-[10px] px-1.5 py-0.5 border font-bold',
            borderColor,
            avgScore >= 60 ? 'bg-status-success/20 text-status-success' : 'bg-gray-100 text-gray-600'
          )}>
            AVG: {avgScore}
          </span>
          <span className={cn(
            'text-[10px] px-1.5 py-0.5 border font-bold',
            borderColor,
            topMover.metrics.day_return > 0
              ? 'bg-status-success/20 text-status-success'
              : 'bg-status-error/20 text-status-error'
          )}>
            TOP: {topMover.symbol.replace('/USDT', '')} {formatPercent(topMover.metrics.day_return)}
          </span>

          {hasMore && (
            <span className="text-[10px] text-gray-400">
              {expanded ? `Showing all ${signals.length}` : `+${signals.length - 5} more`}
            </span>
          )}

          {expanded ? (
            <ChevronUp size={12} className="text-gray-500" />
          ) : (
            <ChevronDown size={12} className="text-gray-500" />
          )}
        </div>
      </button>

      {/* Signal Grid */}
      <div className="p-2 bg-white">
        <div className="grid grid-cols-5 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-1.5">
          {displayedSignals.map((signal) => (
            <button
              key={signal.symbol}
              onClick={() => onSignalClick?.(signal)}
              className={cn(
                'aspect-square p-0.5 flex flex-col items-center justify-center',
                'border border-black hover:border-2 hover:z-10',
                'transition-all duration-100 cursor-pointer'
              )}
              style={{
                backgroundColor: getScoreBg(signal.score),
                color: getScoreColor(signal.score)
              }}
              title={`${signal.symbol}: Score ${signal.score}, ${formatPercent(signal.metrics.day_return)}`}
            >
              <span className="font-bold truncate w-full text-center text-[9px]">
                {signal.symbol.replace('/USDT', '')}
              </span>
              <span className="opacity-80 text-[8px] font-bold">{signal.score}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Asset section configuration.
 */
const ASSET_SECTIONS: Array<{
  type: AssetType;
  title: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  borderColor: string;
}> = [
  {
    type: 'equity',
    title: 'Equities',
    icon: TrendingUp,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-300',
  },
  {
    type: 'crypto',
    title: 'Crypto',
    icon: Bitcoin,
    color: 'text-orange-500',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-300',
  },
  {
    type: 'polymarket',
    title: 'Polymarket',
    icon: PieChart,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-300',
  },
];

export function MarketSnapshot({
  signals,
  onSignalClick,
  defaultExpanded = false,
}: MarketSnapshotProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  // Group signals by asset type and sort by score
  const signalsByType = ASSET_SECTIONS.reduce((acc, section) => {
    acc[section.type] = signals
      .filter((s) => s.asset_type === section.type)
      .sort((a, b) => b.score - a.score);
    return acc;
  }, {} as Record<AssetType, Signal[]>);

  const totalSignals = signals.length;
  const avgScore = totalSignals > 0
    ? Math.round(signals.reduce((sum, s) => sum + s.score, 0) / totalSignals)
    : 0;

  const topMover = totalSignals > 0
    ? signals.reduce((top, s) =>
        Math.abs(s.metrics.day_return) > Math.abs(top.metrics.day_return) ? s : top
      )
    : null;

  if (totalSignals === 0) {
    return null;
  }

  // Count per asset type
  const counts = ASSET_SECTIONS.map((s) => ({
    title: s.title.charAt(0),
    count: signalsByType[s.type].length,
  })).filter((c) => c.count > 0);

  return (
    <div className="bg-white border-2 border-black font-mono">
      {/* Header - Always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between hover:bg-gray-200 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-4">
          <BarChart3 size={16} className="text-black" />
          <span className="text-sm font-bold uppercase tracking-wider">
            Market Snapshot
          </span>

          {/* Quick stats */}
          <div className="flex items-center gap-3 text-xs">
            <span className="text-gray-500">
              {counts.map((c) => `${c.count}${c.title}`).join(' | ')}
            </span>
            <span className={cn(
              'px-2 py-0.5 border border-black font-bold',
              avgScore >= 60 ? 'bg-status-success/20 text-status-success' : 'bg-gray-100 text-gray-600'
            )}>
              AVG: {avgScore}
            </span>
            {topMover && (
              <span
                className={cn(
                  'px-2 py-0.5 border border-black font-bold',
                  topMover.metrics.day_return > 0 ? 'bg-status-success/20 text-status-success' : 'bg-status-error/20 text-status-error'
                )}
              >
                TOP: {topMover.symbol.replace('/USDT', '')} {formatPercent(topMover.metrics.day_return)}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 uppercase">
            [{expanded ? 'Collapse' : 'Expand'}]
          </span>
          {expanded ? (
            <ChevronUp size={16} className="text-gray-600" />
          ) : (
            <ChevronDown size={16} className="text-gray-600" />
          )}
        </div>
      </button>

      {/* Expanded Content - Asset Type Sections */}
      {expanded && (
        <div className="p-3 space-y-3">
          {ASSET_SECTIONS.map((section) => {
            const sectionSignals = signalsByType[section.type];
            if (sectionSignals.length === 0) return null;

            return (
              <AssetSection
                key={section.type}
                title={section.title}
                icon={section.icon}
                signals={sectionSignals}
                color={section.color}
                bgColor={section.bgColor}
                borderColor={section.borderColor}
                onSignalClick={onSignalClick}
                defaultExpanded={sectionSignals.length <= 5}
              />
            );
          })}

          {/* Legend */}
          <div className="pt-3 border-t-2 border-gray-200">
            <div className="flex flex-wrap items-center justify-center gap-3 text-xs">
              <span className="font-bold uppercase tracking-wide text-gray-600">Score:</span>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 border border-black" style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)' }} />
                <span className="text-status-error font-bold text-[10px]">0-19</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 border border-black" style={{ backgroundColor: 'rgba(249, 115, 22, 0.15)' }} />
                <span className="text-score-low font-bold text-[10px]">20-39</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 border border-black" style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)' }} />
                <span className="text-status-warning font-bold text-[10px]">40-59</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 border border-black" style={{ backgroundColor: 'rgba(74, 222, 128, 0.15)' }} />
                <span className="text-score-good font-bold text-[10px]">60-79</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 border border-black" style={{ backgroundColor: 'rgba(34, 197, 94, 0.15)' }} />
                <span className="text-status-success font-bold text-[10px]">80+</span>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="text-xs text-gray-500 text-center">
            {totalSignals} assets across {counts.length} asset types
          </div>
        </div>
      )}
    </div>
  );
}
