/**
 * Card component for displaying a single signal.
 * Robinhood-style clean design.
 */
import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import type { Signal } from '../../api/types';
import { cn, getScoreColor, getScoreColorHex, formatPercent, formatPrice, getPriceColor } from '../../lib/utils';

interface SignalCardProps {
  signal: Signal;
  showCaveats?: boolean;
}

export function SignalCard({ signal, showCaveats = false }: SignalCardProps) {
  const { symbol, score, asset_type, metrics, why, caveats } = signal;
  const isPositive = metrics.day_return >= 0;

  return (
    <div className="bg-white rounded-xl border border-border p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-lg text-text">{symbol}</h3>
            <span className="text-xs px-2 py-0.5 bg-surface text-text-muted rounded-full uppercase font-medium">
              {asset_type}
            </span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <div className={cn(
              "flex items-center gap-1 text-sm font-semibold",
              isPositive ? "text-positive" : "text-negative"
            )}>
              {isPositive ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              <span>{formatPercent(metrics.day_return)}</span>
            </div>
            <span className="text-text-light">·</span>
            <span className="text-text-muted text-sm">${formatPrice(metrics.last_price)}</span>
          </div>
        </div>

        {/* Score badge */}
        <div
          className="flex items-center justify-center w-12 h-12 rounded-full font-bold text-lg text-white"
          style={{ backgroundColor: getScoreColorHex(score) }}
        >
          {score}
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-3 gap-2 py-3 border-y border-border">
        <div className="text-center">
          <div className={cn('font-semibold text-sm', getPriceColor(metrics.week_return))}>
            {formatPercent(metrics.week_return)}
          </div>
          <div className="text-xs text-text-muted">7d Return</div>
        </div>
        <div className="text-center">
          <div className="font-semibold text-sm text-text">
            {metrics.volatility_7d.toFixed(1)}%
          </div>
          <div className="text-xs text-text-muted">Volatility</div>
        </div>
        <div className="text-center">
          <div className="font-semibold text-sm text-text">
            {metrics.volume_ratio.toFixed(1)}x
          </div>
          <div className="text-xs text-text-muted">Volume</div>
        </div>
      </div>

      {/* Rationale */}
      {why.length > 0 && (
        <div className="mt-3">
          <ul className="space-y-1">
            {why.map((reason, i) => (
              <li key={i} className="text-sm text-text-muted flex items-start gap-2">
                <span className="text-primary mt-1.5 w-1 h-1 rounded-full bg-primary flex-shrink-0" />
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Caveats */}
      {showCaveats && caveats.length > 0 && (
        <div className="mt-3 pt-3 border-t border-border">
          <div className="flex items-center gap-1 text-amber-600 text-xs mb-1">
            <AlertTriangle size={12} />
            <span className="font-medium">Caveats</span>
          </div>
          <ul className="space-y-0.5">
            {caveats.map((caveat, i) => (
              <li key={i} className="text-xs text-text-muted">
                {caveat}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
