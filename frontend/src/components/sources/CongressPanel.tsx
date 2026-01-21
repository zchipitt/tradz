/**
 * Panel showing Congress member trading activity.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { AlertCircle, Loader2 } from 'lucide-react';
import { useCongress } from '../../hooks/useSources';
import { cn, formatDate } from '../../lib/utils';
import type { CongressTrade } from '../../api/types';

// Helper to parse trade amount range into a numeric value for sorting
function parseAmount(amountStr: string): number {
  if (!amountStr) return 0;

  // Clean string (remove $, K, M, etc)
  const clean = amountStr.toUpperCase().replace(/[$,]/g, '').trim();

  // Handle "+" suffix (e.g. "1000000+")
  if (clean.endsWith('+')) {
    return parseFloat(clean) || 0;
  }

  // Handle ranges "15K-50K" - take the lower bound usually
  const parts = clean.split('-');
  let valStr = parts[0].trim();

  let multiplier = 1;
  if (valStr.endsWith('K')) {
    multiplier = 1000;
    valStr = valStr.slice(0, -1);
  } else if (valStr.endsWith('M')) {
    multiplier = 1000000;
    valStr = valStr.slice(0, -1);
  } else if (valStr.endsWith('B')) {
    multiplier = 1000000000;
    valStr = valStr.slice(0, -1);
  }

  return (parseFloat(valStr) || 0) * multiplier;
}

export function CongressPanel() {
  const { data, isLoading, isFetching, error } = useCongress();

  // Only show full loading state on initial load (no cached data)
  if (isLoading && !data) {
    return <LoadingState />;
  }

  if (error || data?.error) {
    return <ErrorState message={data?.error || 'Failed to load congress data'} />;
  }

  const trades = data?.trades || [];
  // Sort trades by amount (descending)
  const sortedTrades = [...trades].sort((a, b) => {
    return parseAmount(b.amount_str) - parseAmount(a.amount_str);
  });

  const isRefreshing = isFetching && !!data;

  return (
    <div className="space-y-4 relative">
      {/* Refreshing indicator */}
      {isRefreshing && (
        <div className="absolute top-0 right-0 flex items-center gap-2 text-xs text-gray-500">
          <Loader2 className="animate-spin" size={12} />
          <span>REFRESHING...</span>
        </div>
      )}

      {/* All trades */}
      <div>
        <div className="flex items-center justify-between mb-3 border-b-2 border-black pb-2">
          <h3 className="text-xs font-bold uppercase tracking-wider">
            Recent Trades [{trades.length}]
          </h3>
          <span className="text-[10px] text-gray-500 font-bold uppercase">Sorted by Value (High → Low)</span>
        </div>

        {sortedTrades.length === 0 ? (
          <div className="text-gray-500 text-sm py-4 border-2 border-gray-200 p-4 text-center">
            No recent trades found
          </div>
        ) : (
          <div className="bg-white border-2 border-black overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 border-b-2 border-black">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wide">Member</th>
                    <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wide">Ticker</th>
                    <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wide">Type</th>
                    <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wide">Amount</th>
                    <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wide">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {sortedTrades.slice(0, 20).map((trade, i) => (
                    <TradeTableRow key={i} trade={trade} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="text-xs text-gray-500 border-t-2 border-gray-200 pt-3">
        Displaying {Math.min(trades.length, 20)} of {trades.length} trades
      </div>
    </div>
  );
}

// TradeRow component removed

function TradeTableRow({ trade }: { trade: CongressTrade }) {
  const isPurchase = trade.type === 'purchase';

  return (
    <tr className="hover:bg-gray-50 transition-colors">
      <td className="px-4 py-3">
        <div className="font-bold">{trade.member}</div>
        <div className="text-xs text-gray-500">
          {trade.chamber} {trade.party && `(${trade.party})`} {trade.state && `- ${trade.state}`}
        </div>
      </td>
      <td className="px-4 py-3 font-bold">${trade.ticker}</td>
      <td className="px-4 py-3">
        <span
          className={cn(
            'px-2 py-0.5 text-[10px] font-bold uppercase border',
            isPurchase
              ? 'bg-status-success/10 text-status-success border-status-success'
              : 'bg-status-error/10 text-status-error border-status-error'
          )}
        >
          {trade.type}
        </span>
      </td>
      <td className="px-4 py-3 text-gray-600 text-xs">{trade.amount_str}</td>
      <td className="px-4 py-3 text-xs">
        {trade.transaction_date && formatDate(trade.transaction_date)}
      </td>
    </tr>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="flex items-center gap-3 border-2 border-black px-6 py-4 bg-gray-50">
        <Loader2 className="animate-spin" size={16} />
        <span className="text-sm font-bold uppercase">Loading Congress Data...</span>
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-status-error/10 border-2 border-status-error p-4 flex items-center gap-3 font-mono">
      <AlertCircle className="text-status-error" size={16} />
      <div>
        <p className="font-bold text-status-error text-sm uppercase">Error: Congress Data Load Failed</p>
        <p className="text-xs text-gray-600">{message}</p>
      </div>
    </div>
  );
}
