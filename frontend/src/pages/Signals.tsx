/**
 * Signals page - Raw signals view for diagnostics/tuning.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useSignalsManager } from '../hooks/useSignals';
import { AlertCircle, Loader2, Download, ArrowUpDown, RefreshCw, Clock, Activity } from 'lucide-react';
import { useState } from 'react';
import { cn, formatPercent, formatPrice, formatRelativeTime } from '../lib/utils';
import type { Signal } from '../api/types';

type SortField = 'symbol' | 'score' | 'day_return' | 'volume_ratio';
type SortDirection = 'asc' | 'desc';

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-status-success';
  if (score >= 60) return 'text-score-good';
  if (score >= 40) return 'text-status-warning';
  return 'text-gray-500';
}

function getScoreBg(score: number): string {
  if (score >= 80) return 'bg-status-success/10 border-status-success';
  if (score >= 60) return 'bg-score-good/10 border-score-good';
  if (score >= 40) return 'bg-status-warning/10 border-status-warning';
  return 'bg-gray-100 border-gray-300';
}

export function Signals() {
  const { signals, lastUpdated, isFetching, isRefreshing, forceRefresh } = useSignalsManager();
  const { data, isLoading, error } = signals;
  const [sortField, setSortField] = useState<SortField>('score');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [filterType, setFilterType] = useState<'all' | 'equity' | 'crypto'>('all');

  // Only show full loading state on initial load (no cached data)
  if (isLoading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 border-2 border-black px-6 py-4 bg-gray-50">
          <Loader2 className="animate-spin" size={16} />
          <span className="text-sm font-bold uppercase">Loading Signals...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-status-error/10 border-2 border-status-error p-6 flex items-center gap-3 font-mono">
        <AlertCircle className="text-status-error" />
        <div>
          <p className="font-bold text-status-error uppercase">Error: Signal Load Failed</p>
          <p className="text-sm text-gray-600">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  // Filter signals
  let filteredSignals = data.all_signals;
  if (filterType !== 'all') {
    filteredSignals = filteredSignals.filter((s) => s.asset_type === filterType);
  }

  // Sort signals
  const sortedSignals = [...filteredSignals].sort((a, b) => {
    let aVal: number;
    let bVal: number;

    switch (sortField) {
      case 'symbol':
        return sortDirection === 'asc'
          ? a.symbol.localeCompare(b.symbol)
          : b.symbol.localeCompare(a.symbol);
      case 'score':
        aVal = a.score;
        bVal = b.score;
        break;
      case 'day_return':
        aVal = a.metrics.day_return;
        bVal = b.metrics.day_return;
        break;
      case 'volume_ratio':
        aVal = a.metrics.volume_ratio;
        bVal = b.metrics.volume_ratio;
        break;
      default:
        return 0;
    }

    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const handleExport = () => {
    const csv = [
      ['Symbol', 'Type', 'Score', 'Day Return', 'Week Return', 'Volume Ratio', 'Price', 'Why', 'Caveats'].join(','),
      ...sortedSignals.map((s) =>
        [
          s.symbol,
          s.asset_type,
          s.score,
          s.metrics.day_return.toFixed(2),
          s.metrics.week_return.toFixed(2),
          s.metrics.volume_ratio.toFixed(2),
          s.metrics.last_price,
          `"${s.why.join('; ')}"`,
          `"${s.caveats.join('; ')}"`,
        ].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tradz-signals-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Main Container */}
      <div className="bg-white border-2 border-black overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity size={16} />
            <span className="text-sm font-bold uppercase tracking-wider">
              Raw Signals
            </span>
            <span className="text-xs text-gray-500">
              [{sortedSignals.length} records]
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
          </div>
        </div>

        {/* Controls */}
        <div className="p-4 border-b-2 border-gray-200 flex flex-wrap items-center justify-between gap-4">
          {/* Filter Tabs */}
          <div className="flex items-center border-2 border-black">
            {(['all', 'equity', 'crypto'] as const).map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={cn(
                  'px-3 py-1.5 text-xs font-bold uppercase tracking-wide transition-colors cursor-pointer',
                  filterType === type
                    ? 'bg-black text-white'
                    : 'bg-white text-black hover:bg-gray-100'
                )}
              >
                {type === 'all' ? 'ALL' : type === 'equity' ? 'EQUITIES' : 'CRYPTO'}
                <span className="ml-1 opacity-60">
                  ({type === 'all'
                    ? data.all_signals.length
                    : data.all_signals.filter((s) => s.asset_type === type).length})
                </span>
              </button>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={forceRefresh}
              disabled={isRefreshing}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold uppercase tracking-wide',
                'border-2 border-black transition-all cursor-pointer',
                isRefreshing
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-black hover:bg-gray-100'
              )}
            >
              <RefreshCw size={12} className={cn(isRefreshing && 'animate-spin')} />
              {isRefreshing ? 'SYNCING...' : 'REFRESH'}
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold uppercase tracking-wide bg-primary border-2 border-black text-black hover:shadow-brutal transition-all cursor-pointer"
            >
              <Download size={12} />
              EXPORT CSV
            </button>
          </div>
        </div>

        {/* Signals Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-black bg-gray-50">
                <th className="text-left px-4 py-3 text-xs font-bold uppercase tracking-wide">
                  <button
                    onClick={() => handleSort('symbol')}
                    className="flex items-center gap-1 cursor-pointer hover:text-primary"
                  >
                    Symbol
                    <ArrowUpDown size={10} />
                  </button>
                </th>
                <th className="text-center px-4 py-3 text-xs font-bold uppercase tracking-wide">
                  <button
                    onClick={() => handleSort('score')}
                    className="flex items-center gap-1 cursor-pointer hover:text-primary mx-auto"
                  >
                    Score
                    <ArrowUpDown size={10} />
                  </button>
                </th>
                <th className="text-right px-4 py-3 text-xs font-bold uppercase tracking-wide">
                  <button
                    onClick={() => handleSort('day_return')}
                    className="flex items-center gap-1 cursor-pointer hover:text-primary ml-auto"
                  >
                    Day %
                    <ArrowUpDown size={10} />
                  </button>
                </th>
                <th className="text-right px-4 py-3 text-xs font-bold uppercase tracking-wide">
                  Week %
                </th>
                <th className="text-right px-4 py-3 text-xs font-bold uppercase tracking-wide">
                  <button
                    onClick={() => handleSort('volume_ratio')}
                    className="flex items-center gap-1 cursor-pointer hover:text-primary ml-auto"
                  >
                    Vol Ratio
                    <ArrowUpDown size={10} />
                  </button>
                </th>
                <th className="text-right px-4 py-3 text-xs font-bold uppercase tracking-wide">
                  Price
                </th>
                <th className="text-left px-4 py-3 text-xs font-bold uppercase tracking-wide">
                  Drivers
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedSignals.map((signal) => (
                <SignalRow key={signal.symbol} signal={signal} />
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="px-4 py-3 bg-gray-50 border-t-2 border-black flex items-center justify-between text-xs">
          <span className="text-gray-600">
            Sort: {sortField.toUpperCase()} | Order: {sortDirection.toUpperCase()}
          </span>
          <span className="text-gray-600">
            Total: {sortedSignals.length} | Filter: {filterType.toUpperCase()}
          </span>
        </div>
      </div>
    </div>
  );
}

function SignalRow({ signal }: { signal: Signal }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr
        className="border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="font-bold">{signal.symbol.replace('/USDT', '')}</span>
            <span className="text-[10px] px-1.5 py-0.5 border border-black uppercase">
              {signal.asset_type}
            </span>
          </div>
        </td>
        <td className="px-4 py-3 text-center">
          <span
            className={cn(
              'inline-flex items-center justify-center w-10 h-10 border-2 font-bold',
              getScoreBg(signal.score),
              getScoreColor(signal.score)
            )}
          >
            {signal.score}
          </span>
        </td>
        <td className={cn(
          'px-4 py-3 text-right font-bold',
          signal.metrics.day_return > 0 ? 'text-status-success' : signal.metrics.day_return < 0 ? 'text-status-error' : 'text-gray-500'
        )}>
          {formatPercent(signal.metrics.day_return)}
        </td>
        <td className={cn(
          'px-4 py-3 text-right',
          signal.metrics.week_return > 0 ? 'text-status-success' : signal.metrics.week_return < 0 ? 'text-status-error' : 'text-gray-500'
        )}>
          {formatPercent(signal.metrics.week_return)}
        </td>
        <td className="px-4 py-3 text-right text-gray-600">
          {signal.metrics.volume_ratio.toFixed(2)}x
        </td>
        <td className="px-4 py-3 text-right font-bold">
          ${formatPrice(signal.metrics.last_price)}
        </td>
        <td className="px-4 py-3">
          <div className="text-xs text-gray-600 truncate max-w-xs">
            {signal.why.slice(0, 2).join(', ')}
            {signal.why.length > 2 && ` +${signal.why.length - 2}`}
          </div>
        </td>
      </tr>
      {expanded && (
        <tr className="bg-gray-50 border-b-2 border-gray-300">
          <td colSpan={7} className="px-4 py-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider mb-2 border-b border-black pb-1">
                  Drivers
                </h4>
                <ul className="space-y-1">
                  {signal.why.map((reason, i) => (
                    <li key={i} className="text-xs text-gray-700 flex items-start gap-2">
                      <span className="font-bold">+</span>
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider mb-2 border-b border-status-warning pb-1 text-status-warning">
                  Caveats
                </h4>
                <ul className="space-y-1">
                  {signal.caveats.length > 0 ? (
                    signal.caveats.map((caveat, i) => (
                      <li key={i} className="text-xs text-gray-600 flex items-start gap-2">
                        <span className="text-status-warning font-bold">!</span>
                        {caveat}
                      </li>
                    ))
                  ) : (
                    <li className="text-xs text-gray-500">No caveats detected</li>
                  )}
                </ul>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
