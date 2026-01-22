/**
 * Entity Badge component with asset-specific icons and metadata.
 * Shows symbol with exchange for equity, rank for crypto, category for polymarket.
 *
 * Brutalist design aesthetic with hard borders and yellow accent.
 */
import { TrendingUp, Bitcoin, BarChart3, DollarSign, Package } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { AssetType } from '../../api/types';

interface EntityBadgeProps {
  symbol: string;
  assetType: AssetType;
  metadata?: {
    exchange?: string;
    rank?: number;
    category?: string;
    sector?: string;
    marketCap?: string;
  };
  onClick?: () => void;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

// Asset type icon and color configuration
const assetConfig: Record<AssetType, {
  icon: React.ElementType;
  color: string;
  bgColor: string;
  borderColor: string;
}> = {
  equity: {
    icon: TrendingUp,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200 hover:border-blue-400',
  },
  crypto: {
    icon: Bitcoin,
    color: 'text-orange-500',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200 hover:border-orange-400',
  },
  polymarket: {
    icon: BarChart3,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200 hover:border-purple-400',
  },
  index: {
    icon: DollarSign,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200 hover:border-green-400',
  },
  commodity: {
    icon: Package,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200 hover:border-yellow-400',
  },
};

// Size configuration
const sizeConfig = {
  sm: {
    container: 'px-1.5 py-0.5 text-[10px]',
    icon: 10,
    gap: 'gap-1',
  },
  md: {
    container: 'px-2 py-1 text-xs',
    icon: 12,
    gap: 'gap-1.5',
  },
  lg: {
    container: 'px-3 py-1.5 text-sm',
    icon: 14,
    gap: 'gap-2',
  },
};

/**
 * Get metadata display based on asset type.
 */
function getMetadataDisplay(assetType: AssetType, metadata?: EntityBadgeProps['metadata']): string {
  if (!metadata) {
    // Default fallbacks
    switch (assetType) {
      case 'equity':
        return 'US';
      case 'crypto':
        return '';
      case 'polymarket':
        return '';
      case 'index':
        return 'IDX';
      case 'commodity':
        return 'CMD';
      default:
        return '';
    }
  }

  switch (assetType) {
    case 'equity':
      return metadata.exchange || metadata.sector || 'US';
    case 'crypto':
      return metadata.rank ? `#${metadata.rank}` : '';
    case 'polymarket':
      return metadata.category || '';
    case 'index':
      return metadata.exchange || 'IDX';
    case 'commodity':
      return metadata.category || 'CMD';
    default:
      return '';
  }
}

export function EntityBadge({
  symbol,
  assetType,
  metadata,
  onClick,
  size = 'md',
  className,
}: EntityBadgeProps) {
  const config = assetConfig[assetType];
  const sizes = sizeConfig[size];
  const Icon = config.icon;
  const metadataText = getMetadataDisplay(assetType, metadata);

  const Component = onClick ? 'button' : 'span';

  return (
    <Component
      onClick={onClick}
      className={cn(
        'inline-flex items-center font-bold border transition-all duration-100',
        sizes.container,
        sizes.gap,
        config.bgColor,
        config.borderColor,
        onClick && 'cursor-pointer hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,0.1)]',
        className
      )}
    >
      <Icon size={sizes.icon} className={config.color} />
      <span className="text-black">${symbol}</span>
      {metadataText && (
        <span className="text-gray-500 font-normal">{metadataText}</span>
      )}
    </Component>
  );
}

/**
 * Compact entity chip for lists and inline display.
 */
export function EntityChip({
  symbol,
  assetType,
  onClick,
  className,
}: {
  symbol: string;
  assetType: AssetType;
  onClick?: () => void;
  className?: string;
}) {
  const config = assetConfig[assetType];
  const Icon = config.icon;

  const Component = onClick ? 'button' : 'span';

  return (
    <Component
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-bold',
        'border border-black transition-all duration-100',
        onClick && 'cursor-pointer hover:bg-primary',
        className
      )}
    >
      <Icon size={10} className={config.color} />
      <span>${symbol}</span>
    </Component>
  );
}

/**
 * Entity icon only for compact displays.
 */
export function EntityIcon({
  assetType,
  size = 14,
  className,
}: {
  assetType: AssetType;
  size?: number;
  className?: string;
}) {
  const config = assetConfig[assetType];
  const Icon = config.icon;

  return <Icon size={size} className={cn(config.color, className)} />;
}

/**
 * Get the color class for an asset type.
 */
export function getAssetTypeColor(assetType: AssetType): string {
  return assetConfig[assetType].color;
}

/**
 * Get the background color class for an asset type.
 */
export function getAssetTypeBgColor(assetType: AssetType): string {
  return assetConfig[assetType].bgColor;
}
