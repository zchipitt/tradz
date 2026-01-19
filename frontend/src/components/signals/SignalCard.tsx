/**
 * Card component for displaying a single signal.
 */
import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import type { Signal } from '../../api/types';
import { cn, getScoreColor, formatPercent, formatPrice, getPriceColor } from '../../lib/utils';

interface SignalCardProps {
  signal: Signal;
  showCaveats?: boolean;
}

export function SignalCard({ signal, showCaveats = false }: SignalCardProps) {
  const { symbol, score, asset_type, metrics, why, caveats } = signal;
  const isPositive = metrics.day_return >= 0;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-lg">{symbol}</h3>
            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full uppercase">
              {asset_type}
            </span>
          </div>
          <div className="flex items-center gap-1 mt-1">
            {isPositive ? (
              <TrendingUp className="h-4 w-4 text-positive" />
            ) : (
              <TrendingDown className="h-4 w-4 text-negative" />
            )}
            <span className={cn('font-medium', getPriceColor(metrics.day_return))}>
              {formatPercent(metrics.day_return)}
            </span>
            <span className="text-gray-400 mx-1">·</span>
            <span className="text-gray-600">${formatPrice(metrics.last_price)}</span>
          </div>
        </div>

        {/* Score badge */}
        <div
          className={cn(
            'flex items-center justify-center',
            'w-12 h-12 rounded-full font-bold text-lg',
            getScoreColor(score)
          )}
        >
          {score}
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-3 gap-2 py-3 border-y border-gray-100">
        <div className="text-center">
          <div className={cn('font-medium', getPriceColor(metrics.week_return))}>
            {formatPercent(metrics.week_return)}
          </div>
          <div className="text-xs text-gray-500">7d Return</div>
        </div>
        <div className="text-center">
          <div className="font-medium text-gray-900">
            {metrics.volatility_7d.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">Volatility</div>
        </div>
        <div className="text-center">
          <div className="font-medium text-gray-900">
            {metrics.volume_ratio.toFixed(1)}x
          </div>
          <div className="text-xs text-gray-500">Volume</div>
        </div>
      </div>

      {/* Rationale */}
      {why.length > 0 && (
        <div className="mt-3">
          <ul className="space-y-1">
            {why.map((reason, i) => (
              <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Caveats */}
      {showCaveats && caveats.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex items-center gap-1 text-amber-600 text-xs mb-1">
            <AlertTriangle size={12} />
            <span className="font-medium">Caveats</span>
          </div>
          <ul className="space-y-0.5">
            {caveats.map((caveat, i) => (
              <li key={i} className="text-xs text-gray-500">
                {caveat}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
