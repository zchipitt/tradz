/**
 * Related Assets component.
 * Shows assets related to the current event's entity.
 * Groups by relationship type: same sector, correlated, mentioned together.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Link2,
  TrendingUp,
  Bitcoin,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { cn, formatPercent } from '../../lib/utils';
import type { AssetType } from '../../api/types';

interface RelatedAsset {
  symbol: string;
  name: string;
  asset_type: AssetType;
  relationship: 'sector' | 'correlated' | 'mentioned' | 'holding';
  change_24h: number;
  score?: number;
}

interface RelatedAssetsProps {
  entityId: string;
  ticker?: string;
  assetType: AssetType;
  className?: string;
}

// Asset type icon mapping
const assetTypeIcons: Record<AssetType, React.ElementType> = {
  equity: TrendingUp,
  crypto: Bitcoin,
  polymarket: BarChart3,
  index: TrendingUp,
  commodity: BarChart3,
};

// Asset type color mapping
const assetTypeColors: Record<AssetType, { text: string; bg: string; border: string }> = {
  equity: { text: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-300' },
  crypto: { text: 'text-orange-500', bg: 'bg-orange-50', border: 'border-orange-300' },
  polymarket: { text: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-300' },
  index: { text: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-300' },
  commodity: { text: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-300' },
};

// Relationship labels
const relationshipLabels: Record<string, { label: string; description: string }> = {
  sector: { label: 'SAME SECTOR', description: 'Companies in the same industry' },
  correlated: { label: 'CORRELATED', description: 'Price movements are correlated' },
  mentioned: { label: 'CO-MENTIONED', description: 'Mentioned together in news/filings' },
  holding: { label: 'HOLDING', description: 'Held by same institutional investors' },
};

/**
 * Mock function to get related assets.
 * In production, this would be an API call.
 */
function getRelatedAssets(ticker: string | undefined, assetType: AssetType): RelatedAsset[] {
  if (!ticker) return [];

  // Mock data based on asset type
  if (assetType === 'equity') {
    // Tech sector example for common tickers
    const techTickers = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'NVDA'];
    const financeTickers = ['JPM', 'BAC', 'GS', 'MS', 'WFC', 'C'];

    if (techTickers.includes(ticker)) {
      return techTickers
        .filter((t) => t !== ticker)
        .slice(0, 4)
        .map((t, i) => ({
          symbol: t,
          name: { AAPL: 'Apple Inc.', MSFT: 'Microsoft Corp.', GOOGL: 'Alphabet Inc.', META: 'Meta Platforms', AMZN: 'Amazon.com', NVDA: 'NVIDIA Corp.' }[t] || t,
          asset_type: 'equity' as AssetType,
          relationship: i < 2 ? 'sector' : 'correlated',
          change_24h: (Math.random() - 0.5) * 10,
          score: Math.floor(Math.random() * 40) + 40,
        }));
    }

    if (financeTickers.includes(ticker)) {
      return financeTickers
        .filter((t) => t !== ticker)
        .slice(0, 4)
        .map((t, i) => ({
          symbol: t,
          name: { JPM: 'JPMorgan Chase', BAC: 'Bank of America', GS: 'Goldman Sachs', MS: 'Morgan Stanley', WFC: 'Wells Fargo', C: 'Citigroup' }[t] || t,
          asset_type: 'equity' as AssetType,
          relationship: i < 2 ? 'sector' : 'correlated',
          change_24h: (Math.random() - 0.5) * 8,
          score: Math.floor(Math.random() * 40) + 30,
        }));
    }

    // Default: generic equities
    return [
      { symbol: 'SPY', name: 'SPDR S&P 500 ETF', asset_type: 'equity', relationship: 'correlated', change_24h: 0.5, score: 55 },
      { symbol: 'QQQ', name: 'Invesco QQQ Trust', asset_type: 'equity', relationship: 'correlated', change_24h: 0.8, score: 52 },
    ];
  }

  if (assetType === 'crypto') {
    const cryptoSymbols = ['BTC', 'ETH', 'SOL', 'ADA', 'AVAX', 'DOGE'];
    const tickerBase = ticker.replace('/USDT', '');

    return cryptoSymbols
      .filter((c) => c !== tickerBase)
      .slice(0, 4)
      .map((c, i) => ({
        symbol: `${c}/USDT`,
        name: { BTC: 'Bitcoin', ETH: 'Ethereum', SOL: 'Solana', ADA: 'Cardano', AVAX: 'Avalanche', DOGE: 'Dogecoin' }[c] || c,
        asset_type: 'crypto' as AssetType,
        relationship: i === 0 ? 'correlated' : 'mentioned',
        change_24h: (Math.random() - 0.5) * 15,
        score: Math.floor(Math.random() * 50) + 30,
      }));
  }

  if (assetType === 'polymarket') {
    return [
      { symbol: 'POLY-001', name: 'Related Market A', asset_type: 'polymarket', relationship: 'mentioned', change_24h: 5.2, score: 65 },
      { symbol: 'POLY-002', name: 'Related Market B', asset_type: 'polymarket', relationship: 'correlated', change_24h: -3.1, score: 48 },
    ];
  }

  return [];
}

/**
 * Individual related asset row.
 */
function RelatedAssetRow({ asset }: { asset: RelatedAsset }) {
  const Icon = assetTypeIcons[asset.asset_type];
  const colors = assetTypeColors[asset.asset_type];
  const isPositive = asset.change_24h >= 0;

  return (
    <div className="flex items-center justify-between py-2 px-3 hover:bg-gray-50 transition-colors">
      <div className="flex items-center gap-3">
        <div className={cn('w-6 h-6 flex items-center justify-center', colors.bg, 'border', colors.border)}>
          <Icon size={12} className={colors.text} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm text-black">
              {asset.symbol.replace('/USDT', '')}
            </span>
            <span className={cn(
              'text-[9px] px-1 py-0.5 uppercase font-bold',
              'bg-gray-100 text-gray-500 border border-gray-200'
            )}>
              {relationshipLabels[asset.relationship]?.label || asset.relationship}
            </span>
          </div>
          <span className="text-xs text-gray-500">{asset.name}</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {asset.score !== undefined && (
          <span className={cn(
            'text-xs font-bold px-1.5 py-0.5 border border-gray-300',
            asset.score >= 60 ? 'bg-status-success/20 text-status-success' : 'bg-gray-100 text-gray-600'
          )}>
            {asset.score}
          </span>
        )}
        <div className={cn(
          'flex items-center gap-1 text-xs font-bold',
          isPositive ? 'text-status-success' : 'text-status-error'
        )}>
          {isPositive ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
          {formatPercent(asset.change_24h)}
        </div>
      </div>
    </div>
  );
}

export function RelatedAssets({
  ticker,
  assetType,
  className,
}: RelatedAssetsProps) {
  const [expanded, setExpanded] = useState(true);

  // Get related assets (would be API call in production)
  const relatedAssets = getRelatedAssets(ticker, assetType);

  if (relatedAssets.length === 0) {
    return null;
  }

  // Group by relationship type
  const grouped = relatedAssets.reduce((acc, asset) => {
    if (!acc[asset.relationship]) {
      acc[asset.relationship] = [];
    }
    acc[asset.relationship].push(asset);
    return acc;
  }, {} as Record<string, RelatedAsset[]>);

  return (
    <div className={cn('bg-white border-2 border-black font-mono', className)}>
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between hover:bg-gray-200 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-3">
          <Link2 size={16} className="text-black" />
          <span className="text-sm font-bold uppercase tracking-wider">
            Related Assets
          </span>
          <span className="text-xs text-gray-500">
            ({relatedAssets.length})
          </span>
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

      {/* Content */}
      {expanded && (
        <div className="divide-y divide-gray-200">
          {Object.entries(grouped).map(([relationship, assets]) => (
            <div key={relationship}>
              {/* Relationship header */}
              <div className="px-3 py-1.5 bg-gray-50 border-b border-gray-200">
                <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wide">
                  {relationshipLabels[relationship]?.label || relationship}
                </span>
                <span className="text-[10px] text-gray-400 ml-2">
                  {relationshipLabels[relationship]?.description}
                </span>
              </div>

              {/* Assets */}
              {assets.map((asset) => (
                <RelatedAssetRow key={asset.symbol} asset={asset} />
              ))}
            </div>
          ))}

          {/* Footer */}
          <div className="px-3 py-2 text-center">
            <span className="text-[10px] text-gray-400">
              Based on sector, correlation, and co-mention analysis
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
