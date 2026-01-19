/**
 * Heatmap grid showing all signals colored by score.
 */
import type { Signal } from '../../api/types';
import { cn, getScoreColorHex, formatPercent } from '../../lib/utils';

interface SignalHeatmapProps {
  signals: Signal[];
  onSignalClick?: (signal: Signal) => void;
}

export function SignalHeatmap({ signals, onSignalClick }: SignalHeatmapProps) {
  if (signals.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 text-center text-gray-500">
        No signals available
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <h2 className="text-lg font-semibold mb-4">Signal Heatmap</h2>
      <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 gap-2">
        {signals.map((signal) => (
          <button
            key={signal.symbol}
            onClick={() => onSignalClick?.(signal)}
            className={cn(
              'aspect-square rounded-lg p-2 flex flex-col items-center justify-center',
              'hover:opacity-90 transition-opacity cursor-pointer',
              'text-white'
            )}
            style={{ backgroundColor: getScoreColorHex(signal.score) }}
            title={`${signal.symbol}: Score ${signal.score}, ${formatPercent(signal.metrics.day_return)}`}
          >
            <span className="font-bold text-sm truncate w-full text-center">
              {signal.symbol.replace('/USDT', '')}
            </span>
            <span className="text-xs font-medium opacity-90">{signal.score}</span>
          </button>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-center gap-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#ef4444' }} />
            <span>0-19</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f97316' }} />
            <span>20-39</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#eab308' }} />
            <span>40-59</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#84cc16' }} />
            <span>60-79</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#22c55e' }} />
            <span>80-100</span>
          </div>
        </div>
      </div>
    </div>
  );
}
