/**
 * Panel showing Polymarket prediction data.
 */
import { LineChart, ExternalLink, AlertCircle } from 'lucide-react';
import { usePolymarket } from '../../hooks/useSources';
import { cn, formatCompact } from '../../lib/utils';
import type { PolymarketMarket } from '../../api/types';

export function PolymarketPanel() {
  const { data, isLoading, error } = usePolymarket();

  if (isLoading) {
    return <LoadingState />;
  }

  if (error || data?.error) {
    return <ErrorState message={data?.error || 'Failed to load Polymarket data'} />;
  }

  const markets = data?.markets || [];
  const highProbEvents = data?.high_probability_events || [];

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-4">
          <LineChart className="text-indigo-600" size={20} />
          <h3 className="font-semibold">Prediction Markets</h3>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-indigo-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-indigo-700">
              {data?.total_markets || 0}
            </div>
            <div className="text-sm text-indigo-600">Markets Tracked</div>
          </div>
          <div className="bg-indigo-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-indigo-700">
              {highProbEvents.length}
            </div>
            <div className="text-sm text-indigo-600">High Probability Events</div>
          </div>
        </div>
      </div>

      {/* Markets list */}
      <div>
        <h3 className="font-semibold mb-3">Active Markets</h3>
        {markets.length === 0 ? (
          <p className="text-gray-500 text-sm">No markets available</p>
        ) : (
          <div className="space-y-3">
            {markets.slice(0, 10).map((market) => (
              <MarketCard key={market.id} market={market} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function MarketCard({ market }: { market: PolymarketMarket }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="font-medium text-gray-900 pr-4">{market.question}</h4>
          {market.category && (
            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full mt-1 inline-block">
              {market.category}
            </span>
          )}
        </div>
        {market.url && (
          <a
            href={market.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:text-indigo-700 shrink-0"
          >
            <ExternalLink size={16} />
          </a>
        )}
      </div>

      {/* Outcomes */}
      {market.outcomes.length > 0 && (
        <div className="space-y-2">
          {market.outcomes.slice(0, 3).map((outcome, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-700">{outcome.name}</span>
                  <span className="text-sm font-medium">
                    {outcome.probability_pct.toFixed(0)}%
                  </span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full rounded-full',
                      outcome.probability_pct >= 70
                        ? 'bg-green-500'
                        : outcome.probability_pct >= 40
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    )}
                    style={{ width: `${outcome.probability_pct}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Volume */}
      {market.volume && (
        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
          Volume: ${formatCompact(market.volume)}
        </div>
      )}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-32 bg-gray-200 rounded-xl" />
      <div className="h-48 bg-gray-200 rounded-xl" />
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-center gap-3">
      <AlertCircle className="text-red-500" />
      <div>
        <p className="font-medium text-red-800">Error loading data</p>
        <p className="text-sm text-red-600">{message}</p>
      </div>
    </div>
  );
}
