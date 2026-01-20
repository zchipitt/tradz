/**
 * Market Snapshot - Collapsible heatmap component.
 * Secondary view showing market overview at a glance.
 * Robinhood-style clean design.
 */
import { useState } from 'react';
import { ChevronDown, ChevronUp, BarChart3 } from 'lucide-react';
import { cn, getScoreColorHex, formatPercent } from '../../lib/utils';
import type { Signal } from '../../api/types';

interface MarketSnapshotProps {
  signals: Signal[];
  onSignalClick?: (signal: Signal) => void;
  defaultExpanded?: boolean;
}

export function MarketSnapshot({
  signals,
  onSignalClick,
  defaultExpanded = false,
}: MarketSnapshotProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const equities = signals.filter((s) => s.asset_type === 'equity');
  const crypto = signals.filter((s) => s.asset_type === 'crypto');

  const avgScore = signals.length > 0
    ? Math.round(signals.reduce((sum, s) => sum + s.score, 0) / signals.length)
    : 0;

  const topMover = signals.length > 0
    ? signals.reduce((top, s) =>
        Math.abs(s.metrics.day_return) > Math.abs(top.metrics.day_return) ? s : top
      )
    : null;

  if (signals.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl border border-border overflow-hidden">
      {/* Header - Always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface/50 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-3">
          <BarChart3 size={20} className="text-text-muted" />
          <h2 className="font-semibold text-text">Market Snapshot</h2>

          {/* Quick stats */}
          <div className="flex items-center gap-3 ml-2 text-xs">
            <span className="text-text-muted">
              {equities.length} equities, {crypto.length} crypto
            </span>
            <span className={cn('font-medium', avgScore >= 60 ? 'text-primary' : 'text-text-muted')}>
              Avg: {avgScore}
            </span>
            {topMover && (
              <span
                className={cn(
                  'font-medium',
                  topMover.metrics.day_return > 0 ? 'text-positive' : 'text-negative'
                )}
              >
                Top: {topMover.symbol.replace('/USDT', '')} {formatPercent(topMover.metrics.day_return)}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted">
            {expanded ? 'Collapse' : 'Expand'}
          </span>
          {expanded ? (
            <ChevronUp size={18} className="text-text-muted" />
          ) : (
            <ChevronDown size={18} className="text-text-muted" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-border pt-4">
          {/* Heatmap Grid */}
          <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-12 gap-1.5">
            {signals.map((signal) => (
              <button
                key={signal.symbol}
                onClick={() => onSignalClick?.(signal)}
                className={cn(
                  'aspect-square rounded-lg p-1 flex flex-col items-center justify-center',
                  'hover:scale-105 hover:shadow-md hover:z-10',
                  'transition-all duration-150 cursor-pointer',
                  'text-white text-xs'
                )}
                style={{ backgroundColor: getScoreColorHex(signal.score) }}
                title={`${signal.symbol}: Score ${signal.score}, ${formatPercent(signal.metrics.day_return)}`}
              >
                <span className="font-bold truncate w-full text-center text-[10px]">
                  {signal.symbol.replace('/USDT', '')}
                </span>
                <span className="opacity-80 text-[9px]">{signal.score}</span>
              </button>
            ))}
          </div>

          {/* Legend */}
          <div className="mt-3 pt-3 border-t border-border">
            <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-text-muted">
              <span className="font-medium">Attention Score:</span>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: '#ef4444' }} />
                <span>0-19</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: '#f97316' }} />
                <span>20-39</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: '#eab308' }} />
                <span>40-59</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: '#84cc16' }} />
                <span>60-79</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: '#22c55e' }} />
                <span>80+</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
