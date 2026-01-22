/**
 * Asset-specific metrics components for different asset types.
 * Each component shows the most relevant metrics for that asset class.
 *
 * - EquityMetrics: Price, volume, volatility, market cap
 * - CryptoMetrics: Price, volume, 24h change, market cap rank
 * - PolymarketMetrics: Probability, volume, liquidity, time to resolution
 *
 * Brutalist design aesthetic with hard borders and data-focused display.
 */
import { TrendingUp, TrendingDown, Minus, Clock, DollarSign, BarChart2, Users, Droplets } from 'lucide-react';
import { cn } from '../../lib/utils';

// ============================================================================
// Shared Metric Display Components
// ============================================================================

interface MetricItemProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

function MetricItem({ label, value, unit, trend, className }: MetricItemProps) {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-500';

  return (
    <div className={cn('flex flex-col', className)}>
      <span className="text-[10px] text-gray-500 uppercase tracking-wide">{label}</span>
      <div className="flex items-center gap-1">
        <span className="text-sm font-bold text-black">{value}</span>
        {unit && <span className="text-[10px] text-gray-500">{unit}</span>}
        {trend && <TrendIcon size={12} className={trendColor} />}
      </div>
    </div>
  );
}

interface MetricBarProps {
  label: string;
  value: number;
  max?: number;
  color?: string;
  className?: string;
}

function MetricBar({ label, value, max = 100, color = 'bg-blue-500', className }: MetricBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn('flex flex-col gap-0.5', className)}>
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-gray-500 uppercase">{label}</span>
        <span className="text-[10px] font-bold">{value.toFixed(1)}%</span>
      </div>
      <div className="h-1 bg-gray-200 rounded-full">
        <div
          className={cn('h-full rounded-full transition-all duration-300', color)}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Equity Metrics
// ============================================================================

export interface EquityMetricsData {
  price: number;
  change24h: number;
  changePercent24h: number;
  volume: number;
  volumeVsAvg: number;
  volatility7d: number;
  volatility30d: number;
  marketCap?: number;
  peRatio?: number;
  sector?: string;
  exchange?: string;
}

interface EquityMetricsProps {
  data: EquityMetricsData;
  compact?: boolean;
  className?: string;
}

export function EquityMetrics({ data, compact = false, className }: EquityMetricsProps) {
  const priceChange = data.changePercent24h;
  const trend: 'up' | 'down' | 'neutral' = priceChange > 0 ? 'up' : priceChange < 0 ? 'down' : 'neutral';

  const formatPrice = (p: number) => p >= 1000 ? `$${(p / 1000).toFixed(1)}K` : `$${p.toFixed(2)}`;
  const formatVolume = (v: number) => {
    if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(1)}B`;
    if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
    if (v >= 1_000) return `${(v / 1_000).toFixed(1)}K`;
    return v.toString();
  };

  if (compact) {
    return (
      <div className={cn('flex items-center gap-3 text-xs', className)}>
        <span className="font-bold">{formatPrice(data.price)}</span>
        <span className={cn('font-medium', trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-500')}>
          {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
        </span>
        <span className="text-gray-500">Vol: {formatVolume(data.volume)}</span>
      </div>
    );
  }

  return (
    <div className={cn('border-2 border-black p-3 bg-white', className)}>
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-200">
        <DollarSign size={14} className="text-blue-600" />
        <span className="text-xs font-bold uppercase tracking-wide">Equity Metrics</span>
        {data.exchange && <span className="text-[10px] text-gray-500">{data.exchange}</span>}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <MetricItem label="Price" value={formatPrice(data.price)} trend={trend} />
        <MetricItem
          label="24h Change"
          value={`${priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)}%`}
          trend={trend}
        />
        <MetricItem label="Volume" value={formatVolume(data.volume)} />
        <MetricItem
          label="Vol vs Avg"
          value={`${data.volumeVsAvg.toFixed(1)}x`}
          trend={data.volumeVsAvg > 1.5 ? 'up' : data.volumeVsAvg < 0.5 ? 'down' : 'neutral'}
        />
      </div>

      <div className="mt-3 pt-2 border-t border-gray-200 space-y-2">
        <MetricBar label="Volatility 7D" value={data.volatility7d} color="bg-red-400" />
        <MetricBar label="Volatility 30D" value={data.volatility30d} color="bg-red-300" />
      </div>

      {data.sector && (
        <div className="mt-2 pt-2 border-t border-gray-200">
          <span className="text-[10px] text-gray-500">Sector: </span>
          <span className="text-[10px] font-bold">{data.sector}</span>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Crypto Metrics
// ============================================================================

export interface CryptoMetricsData {
  price: number;
  change24h: number;
  change7d: number;
  volume24h: number;
  volumeChange: number;
  marketCapRank?: number;
  marketCap?: number;
  circulatingSupply?: number;
  totalSupply?: number;
  athPrice?: number;
  athChangePercent?: number;
  fundingRate?: number;
  exchangeNetflow?: number;
}

interface CryptoMetricsProps {
  data: CryptoMetricsData;
  compact?: boolean;
  className?: string;
}

export function CryptoMetrics({ data, compact = false, className }: CryptoMetricsProps) {
  const trend24h: 'up' | 'down' | 'neutral' = data.change24h > 0 ? 'up' : data.change24h < 0 ? 'down' : 'neutral';

  const formatPrice = (p: number) => {
    if (p >= 1000) return `$${(p / 1000).toFixed(1)}K`;
    if (p >= 1) return `$${p.toFixed(2)}`;
    return `$${p.toFixed(6)}`;
  };
  const formatVolume = (v: number) => {
    if (v >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(1)}B`;
    if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
    return `$${(v / 1_000).toFixed(1)}K`;
  };

  if (compact) {
    return (
      <div className={cn('flex items-center gap-3 text-xs', className)}>
        <span className="font-bold">{formatPrice(data.price)}</span>
        <span className={cn('font-medium', trend24h === 'up' ? 'text-green-600' : trend24h === 'down' ? 'text-red-600' : 'text-gray-500')}>
          {data.change24h >= 0 ? '+' : ''}{data.change24h.toFixed(2)}%
        </span>
        {data.marketCapRank && <span className="text-gray-500">Rank #{data.marketCapRank}</span>}
      </div>
    );
  }

  return (
    <div className={cn('border-2 border-black p-3 bg-white', className)}>
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-200">
        <BarChart2 size={14} className="text-orange-500" />
        <span className="text-xs font-bold uppercase tracking-wide">Crypto Metrics</span>
        {data.marketCapRank && <span className="text-[10px] text-gray-500">Rank #{data.marketCapRank}</span>}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <MetricItem label="Price" value={formatPrice(data.price)} trend={trend24h} />
        <MetricItem
          label="24h Change"
          value={`${data.change24h >= 0 ? '+' : ''}${data.change24h.toFixed(2)}%`}
          trend={trend24h}
        />
        <MetricItem
          label="7d Change"
          value={`${data.change7d >= 0 ? '+' : ''}${data.change7d.toFixed(2)}%`}
          trend={data.change7d > 0 ? 'up' : data.change7d < 0 ? 'down' : 'neutral'}
        />
        <MetricItem label="Volume 24h" value={formatVolume(data.volume24h)} />
      </div>

      {(data.fundingRate !== undefined || data.exchangeNetflow !== undefined) && (
        <div className="mt-3 pt-2 border-t border-gray-200 grid grid-cols-2 gap-3">
          {data.fundingRate !== undefined && (
            <MetricItem
              label="Funding Rate"
              value={`${(data.fundingRate * 100).toFixed(4)}%`}
              trend={data.fundingRate > 0.01 ? 'up' : data.fundingRate < -0.01 ? 'down' : 'neutral'}
            />
          )}
          {data.exchangeNetflow !== undefined && (
            <MetricItem
              label="Exchange Flow"
              value={data.exchangeNetflow > 0 ? 'Inflow' : 'Outflow'}
              trend={data.exchangeNetflow > 0 ? 'down' : 'up'}
            />
          )}
        </div>
      )}

      {data.athPrice && data.athChangePercent !== undefined && (
        <div className="mt-2 pt-2 border-t border-gray-200 flex items-center gap-2 text-[10px]">
          <span className="text-gray-500">ATH:</span>
          <span className="font-bold">{formatPrice(data.athPrice)}</span>
          <span className="text-red-500">({data.athChangePercent.toFixed(1)}%)</span>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Polymarket Metrics
// ============================================================================

export interface PolymarketMetricsData {
  probability: number;
  probabilityChange24h?: number;
  volume24h: number;
  totalVolume?: number;
  liquidity: number;
  endDate?: string;
  outcomes?: { name: string; probability: number }[];
  pollAverage?: number;
  category?: string;
}

interface PolymarketMetricsProps {
  data: PolymarketMetricsData;
  compact?: boolean;
  className?: string;
}

export function PolymarketMetrics({ data, compact = false, className }: PolymarketMetricsProps) {
  const probChange = data.probabilityChange24h || 0;
  const trend: 'up' | 'down' | 'neutral' = probChange > 0 ? 'up' : probChange < 0 ? 'down' : 'neutral';

  const formatMoney = (v: number) => {
    if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
    if (v >= 1_000) return `$${(v / 1_000).toFixed(1)}K`;
    return `$${v.toFixed(0)}`;
  };

  const formatTimeRemaining = (endDateStr?: string) => {
    if (!endDateStr) return null;
    const end = new Date(endDateStr);
    const now = new Date();
    const diffMs = end.getTime() - now.getTime();
    if (diffMs < 0) return 'Ended';
    const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (days > 30) return `${Math.floor(days / 30)}mo`;
    if (days > 0) return `${days}d`;
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    return `${hours}h`;
  };

  if (compact) {
    return (
      <div className={cn('flex items-center gap-3 text-xs', className)}>
        <span className="font-bold">{(data.probability * 100).toFixed(1)}%</span>
        {probChange !== 0 && (
          <span className={cn('font-medium', trend === 'up' ? 'text-green-600' : 'text-red-600')}>
            {probChange > 0 ? '+' : ''}{(probChange * 100).toFixed(1)}%
          </span>
        )}
        <span className="text-gray-500">Vol: {formatMoney(data.volume24h)}</span>
      </div>
    );
  }

  const timeRemaining = formatTimeRemaining(data.endDate);

  return (
    <div className={cn('border-2 border-black p-3 bg-white', className)}>
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Users size={14} className="text-purple-600" />
          <span className="text-xs font-bold uppercase tracking-wide">Prediction Market</span>
          {data.category && <span className="text-[10px] text-gray-500">{data.category}</span>}
        </div>
        {timeRemaining && (
          <div className="flex items-center gap-1 text-[10px] text-gray-500">
            <Clock size={10} />
            <span>{timeRemaining}</span>
          </div>
        )}
      </div>

      {/* Main probability display */}
      <div className="flex items-center justify-center mb-4">
        <div className="text-center">
          <div className="text-3xl font-bold text-black">{(data.probability * 100).toFixed(1)}%</div>
          <div className="text-[10px] text-gray-500 uppercase">Probability</div>
          {probChange !== 0 && (
            <div className={cn('text-xs font-medium mt-1', trend === 'up' ? 'text-green-600' : 'text-red-600')}>
              {probChange > 0 ? '+' : ''}{(probChange * 100).toFixed(1)}% (24h)
            </div>
          )}
        </div>
      </div>

      {/* Probability bar */}
      <div className="mb-4">
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-purple-500 transition-all duration-300"
            style={{ width: `${data.probability * 100}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-gray-500 mt-1">
          <span>No</span>
          <span>Yes</span>
        </div>
      </div>

      {/* Market metrics */}
      <div className="grid grid-cols-2 gap-3">
        <MetricItem label="24h Volume" value={formatMoney(data.volume24h)} />
        <div className="flex items-center gap-1">
          <Droplets size={12} className="text-blue-400" />
          <MetricItem label="Liquidity" value={formatMoney(data.liquidity)} />
        </div>
      </div>

      {/* Poll divergence if available */}
      {data.pollAverage !== undefined && (
        <div className="mt-3 pt-2 border-t border-gray-200">
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-gray-500">Poll Average:</span>
            <span className="font-bold">{(data.pollAverage * 100).toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between text-[10px] mt-1">
            <span className="text-gray-500">Divergence:</span>
            <span className={cn('font-bold', Math.abs(data.probability - data.pollAverage) > 0.1 ? 'text-orange-500' : 'text-gray-600')}>
              {((data.probability - data.pollAverage) * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      )}

      {/* Outcomes list if available */}
      {data.outcomes && data.outcomes.length > 2 && (
        <div className="mt-3 pt-2 border-t border-gray-200">
          <div className="text-[10px] text-gray-500 uppercase mb-2">All Outcomes</div>
          <div className="space-y-1">
            {data.outcomes.map((outcome, i) => (
              <div key={i} className="flex items-center justify-between text-[10px]">
                <span className="truncate max-w-[60%]">{outcome.name}</span>
                <span className="font-bold">{(outcome.probability * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Unified Asset Metrics Component
// ============================================================================

export type AssetMetricsData =
  | { type: 'equity'; data: EquityMetricsData }
  | { type: 'crypto'; data: CryptoMetricsData }
  | { type: 'polymarket'; data: PolymarketMetricsData };

interface AssetMetricsProps {
  metrics: AssetMetricsData;
  compact?: boolean;
  className?: string;
}

export function AssetMetrics({ metrics, compact = false, className }: AssetMetricsProps) {
  switch (metrics.type) {
    case 'equity':
      return <EquityMetrics data={metrics.data} compact={compact} className={className} />;
    case 'crypto':
      return <CryptoMetrics data={metrics.data} compact={compact} className={className} />;
    case 'polymarket':
      return <PolymarketMetrics data={metrics.data} compact={compact} className={className} />;
    default:
      return null;
  }
}
