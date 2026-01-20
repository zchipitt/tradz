/**
 * Panel showing Congress member trading activity.
 * Robinhood-style clean design.
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
        <div className="bg-primary-light border border-primary/20 rounded-xl p-4">
          <h3 className="font-semibold text-primary mb-3 flex items-center gap-2">
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
        <h3 className="font-semibold mb-3 text-text">Recent Trades ({trades.length})</h3>
        {trades.length === 0 ? (
          <p className="text-text-muted text-sm">No recent trades found</p>
        ) : (
          <div className="bg-white border border-border rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-surface border-b border-border">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-text-muted">Member</th>
                    <th className="px-4 py-3 text-left font-medium text-text-muted">Ticker</th>
                    <th className="px-4 py-3 text-left font-medium text-text-muted">Type</th>
                    <th className="px-4 py-3 text-left font-medium text-text-muted">Amount</th>
                    <th className="px-4 py-3 text-left font-medium text-text-muted">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
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
        highlight ? 'bg-white' : 'bg-surface'
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            'p-2 rounded-lg',
            isPurchase ? 'bg-green-100 text-positive' : 'bg-red-100 text-negative'
          )}
        >
          {isPurchase ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
        </div>
        <div>
          <div className="font-medium text-text">{trade.ticker}</div>
          <div className="text-xs text-text-muted">
            {trade.member} ({trade.chamber})
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className={cn('font-medium', isPurchase ? 'text-positive' : 'text-negative')}>
          {trade.type}
        </div>
        <div className="text-xs text-text-muted">{trade.amount_str}</div>
      </div>
    </div>
  );
}

function TradeTableRow({ trade }: { trade: CongressTrade }) {
  const isPurchase = trade.type === 'purchase';

  return (
    <tr className="hover:bg-surface transition-colors">
      <td className="px-4 py-3">
        <div className="font-medium text-text">{trade.member}</div>
        <div className="text-xs text-text-muted">
          {trade.chamber} {trade.party && `(${trade.party})`} {trade.state && `- ${trade.state}`}
        </div>
      </td>
      <td className="px-4 py-3 font-medium text-text">{trade.ticker}</td>
      <td className="px-4 py-3">
        <span
          className={cn(
            'px-2 py-1 rounded text-xs font-medium',
            isPurchase ? 'bg-green-100 text-positive' : 'bg-red-100 text-negative'
          )}
        >
          {trade.type}
        </span>
      </td>
      <td className="px-4 py-3 text-text-muted">{trade.amount_str}</td>
      <td className="px-4 py-3 text-text-muted text-xs">
        {trade.transaction_date && formatDate(trade.transaction_date)}
      </td>
    </tr>
  );
}

function LoadingState() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-32 bg-surface rounded-xl" />
      <div className="h-64 bg-surface rounded-xl" />
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-center gap-3">
      <AlertCircle className="text-negative" />
      <div>
        <p className="font-medium text-red-800">Error loading data</p>
        <p className="text-sm text-red-600">{message}</p>
      </div>
    </div>
  );
}
