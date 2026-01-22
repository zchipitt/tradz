/**
 * Asset Type Filter component with multi-select support.
 * Allows filtering events by asset type: All, Equity, Crypto, Polymarket.
 * Shows count per asset type when available.
 *
 * Brutalist design aesthetic with hard borders and yellow accent.
 */
import { TrendingUp, Bitcoin, BarChart3, Globe } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { AssetType } from '../../api/types';

interface AssetTypeFilterProps {
  selected: AssetType[];
  counts?: Record<AssetType | 'all', number>;
  onChange: (types: AssetType[]) => void;
  className?: string;
}

interface FilterConfig {
  type: AssetType | 'all';
  label: string;
  icon: React.ElementType;
  color: string;
  hoverColor: string;
  activeColor: string;
}

const filterConfig: FilterConfig[] = [
  {
    type: 'all',
    label: 'ALL',
    icon: Globe,
    color: 'text-gray-600',
    hoverColor: 'hover:bg-gray-100 hover:border-gray-400',
    activeColor: 'bg-black text-white border-black',
  },
  {
    type: 'equity',
    label: 'EQUITY',
    icon: TrendingUp,
    color: 'text-blue-600',
    hoverColor: 'hover:bg-blue-50 hover:border-blue-400',
    activeColor: 'bg-blue-600 text-white border-blue-600',
  },
  {
    type: 'crypto',
    label: 'CRYPTO',
    icon: Bitcoin,
    color: 'text-orange-500',
    hoverColor: 'hover:bg-orange-50 hover:border-orange-400',
    activeColor: 'bg-orange-500 text-white border-orange-500',
  },
  {
    type: 'polymarket',
    label: 'POLYMARKET',
    icon: BarChart3,
    color: 'text-purple-600',
    hoverColor: 'hover:bg-purple-50 hover:border-purple-400',
    activeColor: 'bg-purple-600 text-white border-purple-600',
  },
];

export function AssetTypeFilter({
  selected,
  counts,
  onChange,
  className,
}: AssetTypeFilterProps) {
  // Check if "all" is effectively selected (no specific types selected or all types selected)
  const isAllSelected = selected.length === 0 || selected.length >= 3;

  const handleClick = (type: AssetType | 'all') => {
    if (type === 'all') {
      // Clear all filters to show all
      onChange([]);
      return;
    }

    // Toggle the specific type
    if (selected.includes(type)) {
      // Remove from selection
      onChange(selected.filter((t) => t !== type));
    } else {
      // Add to selection
      onChange([...selected, type]);
    }
  };

  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {filterConfig.map((config) => {
        const Icon = config.icon;
        const isActive = config.type === 'all' ? isAllSelected : selected.includes(config.type as AssetType);
        const count = counts?.[config.type];

        return (
          <button
            key={config.type}
            onClick={() => handleClick(config.type)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold uppercase',
              'border-2 transition-all duration-100',
              isActive ? config.activeColor : [
                'bg-white border-gray-300',
                config.color,
                config.hoverColor,
              ],
            )}
          >
            <Icon size={14} />
            <span>{config.label}</span>
            {count !== undefined && (
              <span
                className={cn(
                  'ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded-sm',
                  isActive ? 'bg-white/20' : 'bg-gray-100'
                )}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/**
 * Simple single-select asset type pills for compact display.
 */
export function AssetTypePills({
  selected,
  onChange,
  className,
}: {
  selected: AssetType | 'all';
  onChange: (type: AssetType | 'all') => void;
  className?: string;
}) {
  return (
    <div className={cn('flex gap-1', className)}>
      {filterConfig.map((config) => {
        const isActive = selected === config.type || (selected === 'all' && config.type === 'all');

        return (
          <button
            key={config.type}
            onClick={() => onChange(config.type as AssetType | 'all')}
            className={cn(
              'px-2 py-1 text-[10px] font-bold uppercase border transition-all duration-100',
              isActive
                ? 'bg-black text-white border-black'
                : 'bg-white text-gray-600 border-gray-300 hover:border-black'
            )}
          >
            {config.label}
          </button>
        );
      })}
    </div>
  );
}
