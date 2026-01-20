/**
 * Component showing top signals for a category (equities or crypto).
 * Robinhood-style clean design.
 */
import type { Signal } from '../../api/types';
import { SignalCard } from './SignalCard';

interface TopSignalsProps {
  title: string;
  signals: Signal[];
  emptyMessage?: string;
}

export function TopSignals({ title, signals, emptyMessage = 'No signals available' }: TopSignalsProps) {
  return (
    <div>
      <h2 className="text-lg font-semibold mb-4 text-text">{title}</h2>
      {signals.length === 0 ? (
        <div className="bg-white rounded-xl border border-border p-6 text-center text-text-muted">
          {emptyMessage}
        </div>
      ) : (
        <div className="space-y-3">
          {signals.map((signal) => (
            <SignalCard key={signal.symbol} signal={signal} />
          ))}
        </div>
      )}
    </div>
  );
}
