/**
 * Panel showing Congress member trading activity.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { Users, ArrowUpRight, ArrowDownRight, AlertCircle, Loader2 } from 'lucide-react';
import { useCongress } from '../../hooks/useSources';
import { cn, formatDate } from '../../lib/utils';
import type { CongressTrade } from '../../api/types';

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
  const watchlistOverlap = data?.watchlist_overlap || [];
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

      {/* Watchlist overlap section */}
      {watchlistOverlap.length > 0 && (
        <div className="bg-primary/10 border-2 border-primary p-4" style={{ boxShadow: '2px 2px 0 0 #000000' }}>
          <h3 className="text-sm font-bold uppercase tracking-wider mb-3 flex items-center gap-2">
            <Users size={16} />
            WATCHLIST MATCHES [{watchlistOverlap.length}]
          </h3>
          <div className="space-y-2">
            {watchlistOverlap.slice(0, 5).map((trade, i) => (
              <TradeRow key={i} trade={trade} highlight />
            ))}
          </div>
        </div>
      )}

      {/* All trades */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider mb-3 border-b-2 border-black pb-2">
          Recent Trades [{trades.length}]
        </h3>
        {trades.length === 0 ? (
          <div className="text-gray-500 text-sm py-4 border-2 border-gray-200 p-4 text-center">
            No recent trades found
          </div>
        ) : (
          <div className="bg-white border-2 border-black overflow-hidden" style={{ boxShadow: '2px 2px 0 0 #000000' }}>
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
                  {trades.slice(0, 20).map((trade, i) => (
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

function TradeRow({ trade, highlight = false }: { trade: CongressTrade; highlight?: boolean }) {
  const isPurchase = trade.type === 'purchase';

  return (
    <div
      className={cn(
        'flex items-center justify-between p-3 border-2',
        highlight
          ? 'bg-primary/5 border-primary'
          : 'bg-white border-gray-300'
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            'p-2 border-2',
            isPurchase
              ? 'bg-status-success/10 border-status-success text-status-success'
              : 'bg-status-error/10 border-status-error text-status-error'
          )}
        >
          {isPurchase ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
        </div>
        <div>
          <div className="font-bold">${trade.ticker}</div>
          <div className="text-xs text-gray-500">
            {trade.member} ({trade.chamber})
          </div>
        </div>
      </div>
      <div className="text-right">
        <span className={cn(
          'px-2 py-0.5 text-xs font-bold uppercase border-2',
          isPurchase
            ? 'text-status-success bg-status-success/10 border-status-success'
            : 'text-status-error bg-status-error/10 border-status-error'
        )}>
          {trade.type}
        </span>
        <div className="text-xs text-gray-500 mt-1">{trade.amount_str}</div>
      </div>
    </div>
  );
}

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
      <div className="flex items-center gap-3 font-mono border-2 border-black px-6 py-4 bg-gray-50">
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
