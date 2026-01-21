/**
 * Market Snapshot - Collapsible heatmap component.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import { ChevronDown, ChevronUp, BarChart3 } from 'lucide-react';
import { cn, formatPercent } from '../../lib/utils';
import type { Signal } from '../../api/types';

interface MarketSnapshotProps {
  signals: Signal[];
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
          <div className="flex items-center gap-4 text-xs">
            <span className="text-gray-500">
              {equities.length} Equities | {crypto.length} Crypto
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

      {/* Expanded Content */}
      {expanded && (
        <div className="p-4">
          {/* Heatmap Grid */}
          <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-12 gap-2">
            {signals.map((signal) => (
              <button
                key={signal.symbol}
                onClick={() => onSignalClick?.(signal)}
                className={cn(
                  'aspect-square p-1 flex flex-col items-center justify-center',
                  'border border-black hover:border-2 hover:z-10',
                  'transition-all duration-100 cursor-pointer'
                )}
                style={{
                  backgroundColor: getScoreBg(signal.score),
                  color: getScoreColor(signal.score)
                }}
                title={`${signal.symbol}: Score ${signal.score}, ${formatPercent(signal.metrics.day_return)}`}
              >
                <span className="font-bold truncate w-full text-center text-[10px]">
                  {signal.symbol.replace('/USDT', '')}
                </span>
                <span className="opacity-80 text-[9px] font-bold">{signal.score}</span>
              </button>
            ))}
          </div>

          {/* Legend */}
          <div className="mt-4 pt-4 border-t-2 border-gray-200">
            <div className="flex flex-wrap items-center justify-center gap-4 text-xs">
              <span className="font-bold uppercase tracking-wide text-gray-600">Attention Score:</span>
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-4 border border-black" style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)' }} />
                <span className="text-status-error font-bold">0-19</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-4 border border-black" style={{ backgroundColor: 'rgba(249, 115, 22, 0.15)' }} />
                <span className="text-score-low font-bold">20-39</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-4 border border-black" style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)' }} />
                <span className="text-status-warning font-bold">40-59</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-4 border border-black" style={{ backgroundColor: 'rgba(74, 222, 128, 0.15)' }} />
                <span className="text-score-good font-bold">60-79</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-4 border border-black" style={{ backgroundColor: 'rgba(34, 197, 94, 0.15)' }} />
                <span className="text-status-success font-bold">80+</span>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-4 text-xs text-gray-500 text-center">
            Displaying {signals.length} assets sorted by attention score
          </div>
        </div>
      )}
    </div>
  );
}
