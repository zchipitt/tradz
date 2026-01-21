/**
 * Sources page with tabbed panels for different data sources.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import { Users, Building2, LineChart, Newspaper, RefreshCw, Clock, Server } from 'lucide-react';
import { cn, formatRelativeTime } from '../lib/utils';
import { CongressPanel } from '../components/sources/CongressPanel';
import { HedgeFundPanel } from '../components/sources/HedgeFundPanel';
import { PolymarketPanel } from '../components/sources/PolymarketPanel';
import { NewsPanel } from '../components/sources/NewsPanel';
import { useSourcesManager } from '../hooks/useSources';

type SourceTab = 'congress' | 'hedgefunds' | 'polymarket' | 'news';

const tabs: { id: SourceTab; label: string; icon: React.ElementType }[] = [
  { id: 'congress', label: 'CONGRESS', icon: Users },
  { id: 'hedgefunds', label: '13F FILINGS', icon: Building2 },
  { id: 'polymarket', label: 'POLYMARKET', icon: LineChart },
  { id: 'news', label: 'NEWS', icon: Newspaper },
];

export function Sources() {
  const [activeTab, setActiveTab] = useState<SourceTab>('congress');
  const { lastUpdated, isFetching, isRefreshing, forceRefreshAll } = useSourcesManager();

  return (
    <div className="space-y-6 font-mono">
      {/* Main Container */}
      <div className="bg-white border-2 border-black overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Server size={16} />
            <span className="text-sm font-bold uppercase tracking-wider">
              Data Sources
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Clock size={12} />
              {lastUpdated > 0 ? (
                <span>Sync: {formatRelativeTime(lastUpdated)} ago</span>
              ) : (
                <span>Sync: Pending</span>
              )}
              {isFetching && !isRefreshing && (
                <span className="text-status-info">(Refreshing...)</span>
              )}
            </div>
            <button
              onClick={forceRefreshAll}
              disabled={isRefreshing}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold uppercase tracking-wide',
                'border-2 border-black transition-all cursor-pointer',
                isRefreshing
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-primary text-black hover:shadow-brutal'
              )}
            >
              <RefreshCw size={12} className={cn(isRefreshing && 'animate-spin')} />
              {isRefreshing ? 'SYNCING...' : 'REFRESH ALL'}
            </button>
          </div>
        </div>

        {/* Tab navigation */}
        <div className="p-2 bg-gray-50 border-b-2 border-black flex gap-1 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 whitespace-nowrap',
                  'transition-all duration-150 text-xs font-bold uppercase tracking-wide cursor-pointer border-2',
                  isActive
                    ? 'bg-black text-white border-black'
                    : 'bg-white text-black border-gray-300 hover:border-black'
                )}
              >
                <Icon size={14} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        <div className="p-4">
          {activeTab === 'congress' && <CongressPanel />}
          {activeTab === 'hedgefunds' && <HedgeFundPanel />}
          {activeTab === 'polymarket' && <PolymarketPanel />}
          {activeTab === 'news' && <NewsPanel />}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 bg-gray-50 border-t-2 border-black text-xs text-gray-600">
          Active source: {activeTab.toUpperCase()}
        </div>
      </div>
    </div>
  );
}
