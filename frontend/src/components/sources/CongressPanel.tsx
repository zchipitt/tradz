/**
 * Panel showing Congress member trading activity.
 */
import { Users, ArrowUpRight, ArrowDownRight, AlertCircle } from 'lucide-react';
import { useCongress } from '../../hooks/useSources';
import { cn, formatDate } from '../../lib/utils';
import type { CongressTrade } from '../../api/types';

export function CongressPanel() {
  const { data, isLoading, error } = useCongress();

  if (isLoading) {
    return <LoadingState />;
  }

  if (error || data?.error) {
    return <ErrorState message={data?.error || 'Failed to load congress data'} />;
  }

  const trades = data?.trades || [];
  const watchlistOverlap = data?.watchlist_overlap || [];

  return (
    <div className="space-y-6">
      {/* Watchlist overlap section */}
      {watchlistOverlap.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <h3 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
            <Users size={18} />
            Watchlist Matches ({watchlistOverlap.length})
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
        <h3 className="font-semibold mb-3">Recent Trades ({trades.length})</h3>
        {trades.length === 0 ? (
          <p className="text-gray-500 text-sm">No recent trades found</p>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Member</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Ticker</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Type</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Amount</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {trades.slice(0, 20).map((trade, i) => (
                    <TradeTableRow key={i} trade={trade} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function TradeRow({ trade, highlight = false }: { trade: CongressTrade; highlight?: boolean }) {
  const isPurchase = trade.type === 'purchase';

  return (
    <div
      className={cn(
        'flex items-center justify-between p-3 rounded-lg',
        highlight ? 'bg-white' : 'bg-gray-50'
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            'p-2 rounded-lg',
            isPurchase ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          )}
        >
          {isPurchase ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
        </div>
        <div>
          <div className="font-medium">{trade.ticker}</div>
          <div className="text-xs text-gray-500">
            {trade.member} ({trade.chamber})
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className={cn('font-medium', isPurchase ? 'text-green-700' : 'text-red-700')}>
          {trade.type}
        </div>
        <div className="text-xs text-gray-500">{trade.amount_str}</div>
      </div>
    </div>
  );
}

function TradeTableRow({ trade }: { trade: CongressTrade }) {
  const isPurchase = trade.type === 'purchase';

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-3">
        <div className="font-medium">{trade.member}</div>
        <div className="text-xs text-gray-500">
          {trade.chamber} {trade.party && `(${trade.party})`} {trade.state && `- ${trade.state}`}
        </div>
      </td>
      <td className="px-4 py-3 font-medium">{trade.ticker}</td>
      <td className="px-4 py-3">
        <span
          className={cn(
            'px-2 py-1 rounded text-xs font-medium',
            isPurchase ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          )}
        >
          {trade.type}
        </span>
      </td>
      <td className="px-4 py-3 text-gray-600">{trade.amount_str}</td>
      <td className="px-4 py-3 text-gray-500 text-xs">
        {trade.transaction_date && formatDate(trade.transaction_date)}
      </td>
    </tr>
  );
}

function LoadingState() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-32 bg-gray-200 rounded-xl" />
      <div className="h-64 bg-gray-200 rounded-xl" />
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
