/**
 * Signals page - Raw signals view for diagnostics/tuning.
 * Shows all signals with full score breakdown.
 */
import { useSignals } from '../hooks/useSignals';
import { AlertCircle, Loader2, Download, ArrowUpDown } from 'lucide-react';
import { useState } from 'react';
import { cn, formatPercent, formatPrice, getScoreColorHex } from '../lib/utils';
import type { Signal } from '../api/types';

type SortField = 'symbol' | 'score' | 'day_return' | 'volume_ratio';
type SortDirection = 'asc' | 'desc';

export function Signals() {
  const { data, isLoading, error } = useSignals();
  const [sortField, setSortField] = useState<SortField>('score');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [filterType, setFilterType] = useState<'all' | 'equity' | 'crypto'>('all');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-text-muted">
          <Loader2 className="animate-spin" />
          <span>Loading signals...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-center gap-3">
        <AlertCircle className="text-negative" />
        <div>
          <p className="font-medium text-red-800">Error loading signals</p>
          <p className="text-sm text-red-600">
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text">Raw Signals</h1>
          <p className="text-sm text-text-muted mt-1">
            Full signal data for diagnostics and parameter tuning
          </p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface text-text hover:bg-gray-200 transition-colors cursor-pointer"
        >
          <Download size={16} />
          Export CSV
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2">
        <div className="flex items-center bg-surface rounded-lg p-0.5">
          {(['all', 'equity', 'crypto'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={cn(
                'px-4 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer',
                filterType === type
                  ? 'bg-white text-text shadow-sm'
                  : 'text-text-muted hover:text-text'
              )}
            >
              {type === 'all' ? 'All' : type === 'equity' ? 'Equities' : 'Crypto'}
              <span className="ml-1 text-xs text-text-light">
                ({type === 'all'
                  ? data.all_signals.length
                  : data.all_signals.filter((s) => s.asset_type === type).length})
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Signals Table */}
      <div className="bg-white rounded-xl border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-surface">
                <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wide">
                  <button
                    onClick={() => handleSort('symbol')}
                    className="flex items-center gap-1 cursor-pointer hover:text-text"
                  >
                    Symbol
                    <ArrowUpDown size={12} />
                  </button>
                </th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wide">
                  <button
                    onClick={() => handleSort('score')}
                    className="flex items-center gap-1 cursor-pointer hover:text-text mx-auto"
                  >
                    Score
                    <ArrowUpDown size={12} />
                  </button>
                </th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wide">
                  <button
                    onClick={() => handleSort('day_return')}
                    className="flex items-center gap-1 cursor-pointer hover:text-text ml-auto"
                  >
                    Day
                    <ArrowUpDown size={12} />
                  </button>
                </th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wide">
                  Week
                </th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wide">
                  <button
                    onClick={() => handleSort('volume_ratio')}
                    className="flex items-center gap-1 cursor-pointer hover:text-text ml-auto"
                  >
                    Vol Ratio
                    <ArrowUpDown size={12} />
                  </button>
                </th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wide">
                  Price
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wide">
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
      </div>
    </div>
  );
}

function SignalRow({ signal }: { signal: Signal }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr
        className="border-b border-border hover:bg-surface/50 cursor-pointer transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="font-medium text-text">{signal.symbol.replace('/USDT', '')}</span>
            <span className="text-xs px-1.5 py-0.5 rounded bg-surface text-text-muted">
              {signal.asset_type}
            </span>
          </div>
        </td>
        <td className="px-4 py-3 text-center">
          <span
            className="inline-flex items-center justify-center w-10 h-10 rounded-lg text-white font-bold"
            style={{ backgroundColor: getScoreColorHex(signal.score) }}
          >
            {signal.score}
          </span>
        </td>
        <td className={cn(
          'px-4 py-3 text-right font-medium',
          signal.metrics.day_return > 0 ? 'text-positive' : signal.metrics.day_return < 0 ? 'text-negative' : 'text-text-muted'
        )}>
          {formatPercent(signal.metrics.day_return)}
        </td>
        <td className={cn(
          'px-4 py-3 text-right',
          signal.metrics.week_return > 0 ? 'text-positive' : signal.metrics.week_return < 0 ? 'text-negative' : 'text-text-muted'
        )}>
          {formatPercent(signal.metrics.week_return)}
        </td>
        <td className="px-4 py-3 text-right text-text-muted">
          {signal.metrics.volume_ratio.toFixed(2)}x
        </td>
        <td className="px-4 py-3 text-right font-mono text-sm text-text">
          ${formatPrice(signal.metrics.last_price)}
        </td>
        <td className="px-4 py-3">
          <div className="text-xs text-text-muted truncate max-w-xs">
            {signal.why.slice(0, 2).join(', ')}
            {signal.why.length > 2 && ` +${signal.why.length - 2}`}
          </div>
        </td>
      </tr>
      {expanded && (
        <tr className="bg-surface/30">
          <td colSpan={7} className="px-4 py-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <h4 className="text-xs font-semibold text-text-muted uppercase mb-2">Why (Drivers)</h4>
                <ul className="space-y-1">
                  {signal.why.map((reason, i) => (
                    <li key={i} className="text-sm text-text flex items-start gap-2">
                      <span className="text-primary">•</span>
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="text-xs font-semibold text-text-muted uppercase mb-2">Caveats</h4>
                <ul className="space-y-1">
                  {signal.caveats.length > 0 ? (
                    signal.caveats.map((caveat, i) => (
                      <li key={i} className="text-sm text-text-muted flex items-start gap-2">
                        <span className="text-amber-500">!</span>
                        {caveat}
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-text-muted">No caveats</li>
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
