/**
 * Panel showing Polymarket prediction data.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { ExternalLink, AlertCircle, Loader2, TrendingUp } from 'lucide-react';
import { usePolymarket } from '../../hooks/useSources';
import { cn, formatCompact } from '../../lib/utils';
import type { PolymarketMarket } from '../../api/types';

export function PolymarketPanel() {
  const { data, isLoading, isFetching, error } = usePolymarket();

  // Only show full loading state on initial load (no cached data)
  if (isLoading && !data) {
    return <LoadingState />;
  }

  if (error || data?.error) {
    return <ErrorState message={data?.error || 'Failed to load Polymarket data'} />;
  }

  const markets = data?.markets || [];
  const highProbEvents = data?.high_probability_events || [];
  const isRefreshing = isFetching && !!data;

  return (
    <div className="space-y-4 font-mono relative">
      {/* Refreshing indicator */}
      {isRefreshing && (
        <div className="absolute top-0 right-0 flex items-center gap-2 text-xs text-gray-500">
          <Loader2 className="animate-spin" size={12} />
          <span>REFRESHING...</span>
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white border-2 border-black p-4 text-center" style={{ boxShadow: '2px 2px 0 0 #000000' }}>
          <div className="text-3xl font-bold">
            {data?.total_markets || 0}
          </div>
          <div className="text-[10px] uppercase tracking-wide font-bold text-gray-600">Markets Tracked</div>
        </div>
        <div className="bg-primary/20 border-2 border-black p-4 text-center" style={{ boxShadow: '2px 2px 0 0 #000000' }}>
          <div className="text-3xl font-bold">
            {highProbEvents.length}
          </div>
          <div className="text-xs uppercase tracking-wide font-bold text-gray-600">High Prob Events</div>
        </div>
      </div>

      {/* Markets list */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider mb-3 border-b-2 border-black pb-2">
          Active Markets
        </h3>
        {markets.length === 0 ? (
          <div className="text-gray-500 text-sm py-4 border-2 border-gray-200 p-4 text-center">
            No markets available
          </div>
        ) : (
          <div className="space-y-3">
            {markets.slice(0, 10).map((market) => (
              <MarketCard key={market.id} market={market} />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="text-xs text-gray-500 border-t-2 border-gray-200 pt-3">
        Displaying {Math.min(markets.length, 10)} of {markets.length} markets
      </div>
    </div>
  );
}

function MarketCard({ market }: { market: PolymarketMarket }) {
  return (
    <div className="bg-white border-2 border-black p-4 hover:bg-gray-50 transition-colors cursor-pointer">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h4 className="font-bold text-sm pr-4 leading-snug">{market.question}</h4>
          {market.category && (
            <span className="inline-block text-[10px] px-2 py-0.5 bg-gray-100 border border-black mt-2 uppercase font-bold">
              {market.category}
            </span>
          )}
        </div>
        {market.url && (
          <a
            href={market.url}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 p-2 border border-black hover:bg-primary transition-colors"
          >
            <ExternalLink size={14} />
          </a>
        )}
      </div>

      {/* Outcomes */}
      {market.outcomes.length > 0 && (
        <div className="space-y-2">
          {market.outcomes.slice(0, 3).map((outcome, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-600">{outcome.name}</span>
                  <span className={cn(
                    'text-xs font-bold',
                    outcome.probability_pct >= 70
                      ? 'text-status-success'
                      : outcome.probability_pct >= 40
                      ? 'text-status-warning'
                      : 'text-status-error'
                  )}>
                    {outcome.probability_pct.toFixed(0)}%
                  </span>
                </div>
                <div className="h-2 bg-gray-100 border border-black overflow-hidden">
                  <div
                    className={cn(
                      'h-full transition-all',
                      outcome.probability_pct >= 70
                        ? 'bg-status-success'
                        : outcome.probability_pct >= 40
                        ? 'bg-status-warning'
                        : 'bg-status-error'
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
        <div className="mt-3 pt-3 border-t-2 border-gray-200 text-[10px] text-gray-600 flex items-center gap-1 font-bold">
          <TrendingUp size={10} />
          VOL: ${formatCompact(market.volume)}
        </div>
      )}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="flex items-center gap-3 font-mono border-2 border-black px-6 py-4 bg-gray-50">
        <Loader2 className="animate-spin" size={16} />
        <span className="text-sm font-bold uppercase">Loading Polymarket Data...</span>
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-status-error/10 border-2 border-status-error p-4 flex items-center gap-3 font-mono">
      <AlertCircle className="text-status-error" size={16} />
      <div>
        <p className="font-bold text-status-error text-sm uppercase">Error: Polymarket Data Load Failed</p>
        <p className="text-xs text-gray-600">{message}</p>
      </div>
    </div>
  );
}
