/**
 * Sources page with tabbed panels for different data sources.
 * Robinhood-style clean design.
 */
import { useState } from 'react';
import { Users, Building2, LineChart, Newspaper } from 'lucide-react';
import { cn } from '../lib/utils';
import { CongressPanel } from '../components/sources/CongressPanel';
import { HedgeFundPanel } from '../components/sources/HedgeFundPanel';
import { PolymarketPanel } from '../components/sources/PolymarketPanel';
import { NewsPanel } from '../components/sources/NewsPanel';

type SourceTab = 'congress' | 'hedgefunds' | 'polymarket' | 'news';

const tabs: { id: SourceTab; label: string; icon: React.ElementType }[] = [
  { id: 'congress', label: 'Congress', icon: Users },
  { id: 'hedgefunds', label: 'Hedge Funds', icon: Building2 },
  { id: 'polymarket', label: 'Polymarket', icon: LineChart },
  { id: 'news', label: 'News', icon: Newspaper },
];

export function Sources() {
  const [activeTab, setActiveTab] = useState<SourceTab>('congress');

  return (
    <div className="space-y-6">
      {/* Tab navigation */}
      <div className="bg-white rounded-xl border border-border p-1 flex gap-1 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap',
                'transition-all duration-150 text-sm font-medium',
                isActive
                  ? 'bg-primary-light text-primary'
                  : 'text-text-muted hover:text-text hover:bg-surface'
              )}
            >
              <Icon size={18} className={cn(isActive ? "text-primary" : "text-text-muted")} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'congress' && <CongressPanel />}
        {activeTab === 'hedgefunds' && <HedgeFundPanel />}
        {activeTab === 'polymarket' && <PolymarketPanel />}
        {activeTab === 'news' && <NewsPanel />}
      </div>
    </div>
  );
}
