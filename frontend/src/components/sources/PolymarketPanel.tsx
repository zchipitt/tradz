/**
 * Panel showing Polymarket prediction data in a visually rich card layout.
 * Mimics the official Polymarket design with Brutalist touches.
 */
import { ExternalLink, AlertCircle, Loader2, TrendingUp } from 'lucide-react';
import { usePolymarket } from '../../hooks/useSources';
import { formatCompact } from '../../lib/utils';
import type { PolymarketMarket, PolymarketOutcome } from '../../api/types';

export function PolymarketPanel() {
  const { data, isLoading, isFetching, error } = usePolymarket();

  // Only show full loading state on initial load (no cached data)
  if (isLoading && !data) {
    return <LoadingState />;
  }

  if (error || data?.error) {
    return <ErrorState message={data?.error || 'Failed to load Polymarket data'} />;
  }

  const markets = Array.isArray(data?.markets) ? data.markets : [];
  const highProbEvents = data?.high_probability_events || [];
  const isRefreshing = isFetching && !!data;

  // Group markets by Event ID (preferred) or fallback to text similarity
  const groupedMarkets: Record<string, PolymarketMarket[]> = {};
  markets.forEach(market => {
    let key = market.event_id || market.event_title;

    // Fallback if no event metadata (e.g. legacy data)
    if (!key) {
      // Heuristic: Use first 6 words as "Theme" or "Series"
      const words = market.question.split(' ');
      key = words.length > 5 ? words.slice(0, 5).join(' ') + '...' : market.question;
    }

    if (!groupedMarkets[key]) {
      groupedMarkets[key] = [];
    }
    groupedMarkets[key].push(market);
  });

  const sortedGroups = Object.entries(groupedMarkets).sort((a, b) => b[1].length - a[1].length);

  return (
    <div className="space-y-4 relative">
      {/* Refreshing indicator */}
      {isRefreshing && (
        <div className="absolute top-0 right-0 flex items-center gap-2 text-xs text-gray-500">
          <Loader2 className="animate-spin" size={12} />
          <span>REFRESHING...</span>
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white border-2 border-black p-4 text-center">
          <div className="text-3xl font-bold">
            {data?.total_markets || 0}
          </div>
          <div className="text-[10px] uppercase tracking-wide font-bold text-gray-600">Markets Tracked</div>
        </div>
        <div className="bg-primary/20 border-2 border-black p-4 text-center">
          <div className="text-3xl font-bold">
            {highProbEvents.length}
          </div>
          <div className="text-xs uppercase tracking-wide font-bold text-gray-600">High Prob Events</div>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sortedGroups.map(([key, groupMarkets]) => (
          <EventCard key={key} markets={groupMarkets} />
        ))}
      </div>

      {/* Footer */}
      <div className="text-xs text-center text-gray-500 border-t-2 border-dashed border-gray-200 pt-4">
        Displaying {sortedGroups.length} events from {markets.length} markets
      </div>
    </div>
  );
}

function EventCard({ markets }: { markets: PolymarketMarket[] }) {
  if (!markets || !Array.isArray(markets) || markets.length === 0) return null;

  const mainMarket = markets[0];
  if (!mainMarket) return null;

  const title = mainMarket.event_title || mainMarket.question || 'Unknown Event';
  const image = mainMarket.event_image;
  const isMulti = markets.length > 1;

  // Calculate total volume for the event (volume may come as string from API)
  const totalVolume = markets.reduce((sum, m) => {
    const vol = typeof m.volume === 'string' ? parseFloat(m.volume) : (m.volume || 0);
    return sum + (isNaN(vol) ? 0 : vol);
  }, 0);

  // Get the best available URL for the event
  // Use event_slug from API (correct slug from Polymarket), fall back to url field
  const eventUrl = mainMarket.event_slug
    ? `https://polymarket.com/event/${mainMarket.event_slug}`
    : mainMarket.url;

  return (
    <div className="bg-white border-2 border-black rounded-sm shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-[-2px] hover:shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] transition-all duration-200 overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="p-4 pb-2 flex items-start gap-3 border-b-2 border-gray-100">
        {image ? (
          <img
            src={image}
            alt="Event"
            className="w-10 h-10 object-cover rounded-sm border-2 border-black shrink-0"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        ) : (
          <div className="w-10 h-10 bg-gray-100 rounded-sm border-2 border-black flex items-center justify-center shrink-0">
            <span className="text-xs font-bold text-gray-400">?</span>
          </div>
        )}

        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-bold leading-tight line-clamp-3 text-black">
            {title}
          </h3>
          {isMulti && (
            <span className="inline-block mt-1 text-[10px] bg-yellow-300 border border-black px-1.5 font-bold text-black uppercase">
              {markets.length} Markets
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-2 flex-1 flex flex-col gap-3">
        {isMulti ? (
          <div className="space-y-3 mt-2 max-h-[200px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
            {markets.map(market => (
              <div key={market.id} className="pt-2 border-t border-dashed border-gray-200 first:border-0 first:pt-0">
                {market.url ? (
                  <a
                    href={market.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] font-bold text-gray-700 mb-1 line-clamp-2 hover:text-blue-600 hover:underline block"
                  >
                    {market.question}
                  </a>
                ) : (
                  <div className="text-[11px] font-bold text-gray-700 mb-1 line-clamp-2">{market.question}</div>
                )}
                <BinaryPredictionBar outcomes={market.outcomes} />
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-2 text-center">
            <BinaryPredictionBar outcomes={mainMarket.outcomes} height="h-10" textSize="text-sm" />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-gray-50 border-t-2 border-black flex items-center justify-between text-[10px] text-gray-600 font-bold uppercase mt-auto">
        <div className="flex items-center gap-1">
          <TrendingUp size={12} className="text-black" />
          <span>${formatCompact(totalVolume)} Vol</span>
        </div>

        {eventUrl && (
          <a
            href={eventUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 hover:text-black hover:underline"
          >
            OPEN <ExternalLink size={10} />
          </a>
        )}
      </div>
    </div>
  );
}

function BinaryPredictionBar({
  outcomes,
  height = "h-6",
  textSize = "text-xs"
}: {
  outcomes: PolymarketOutcome[],
  height?: string,
  textSize?: string
}) {
  if (!outcomes || !Array.isArray(outcomes) || outcomes.length === 0) {
    return (
      <div className={`w-full ${height} bg-gray-100 border border-gray-300 rounded-sm flex items-center justify-center text-[10px] text-gray-400 font-bold uppercase`}>
        NO DATA
      </div>
    );
  }

  const yes = outcomes.find(o => o.name && o.name.toLowerCase() === 'yes');
  const no = outcomes.find(o => o.name && o.name.toLowerCase() === 'no');

  if (!yes || !no) {
    // Non-binary fallback
    return (
      <div className="space-y-1">
        {outcomes.slice(0, 2).map((o, i) => (
          <div key={i} className="flex justify-between items-center text-xs">
            <span className="text-gray-500 font-mono">{o.name || 'Unknown'}</span>
            <span className="font-bold bg-gray-100 px-1 border border-black">{(o.probability_pct || 0).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    );
  }

  // Get safe probability values (handle missing/undefined data)
  const yesPct = yes.probability_pct ?? 0;
  const noPct = no.probability_pct ?? 0;

  // Polymarket style: Green Yes button, Red No button (light backgrounds)
  return (
    <div className={`flex gap-1 w-full ${height}`}>
      {/* Yes Button */}
      <div className="flex-1 bg-green-50 rounded-sm border border-green-600 flex items-center justify-between px-2 relative overflow-hidden group">
        <div
          className="absolute inset-y-0 left-0 bg-green-200/50 transition-all"
          style={{ width: `${yesPct}%` }}
        />
        <span className={`font-bold text-green-700 relative z-10 ${textSize} uppercase`}>Yes</span>
        <span className={`font-bold text-green-700 relative z-10 ${textSize}`}>{yesPct.toFixed(0)}%</span>
      </div>

      {/* No Button */}
      <div className="flex-1 bg-red-50 rounded-sm border border-red-600 flex items-center justify-between px-2 relative overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 bg-red-200/50 transition-all"
          style={{ width: `${noPct}%` }}
        />
        <span className={`font-bold text-red-700 relative z-10 ${textSize} uppercase`}>No</span>
        <span className={`font-bold text-red-700 relative z-10 ${textSize}`}>{noPct.toFixed(0)}%</span>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {[1, 2, 3, 4, 5, 6].map(i => (
        <div key={i} className="bg-white border-2 border-black p-4 h-40 animate-pulse">
          <div className="flex gap-3 mb-4">
            <div className="w-10 h-10 bg-gray-200 rounded-sm border-2 border-black"></div>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
          <div className="flex gap-2 mt-8">
            <div className="h-8 bg-gray-100 rounded border border-black flex-1"></div>
            <div className="h-8 bg-gray-100 rounded border border-black flex-1"></div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-red-50 border-2 border-red-600 p-4 flex items-center gap-3 font-mono">
      <AlertCircle className="text-red-600" size={16} />
      <div>
        <p className="font-bold text-red-600 text-sm uppercase">Error: Polymarket Data Load Failed</p>
        <p className="text-xs text-gray-600">{message}</p>
      </div>
    </div>
  );
}
