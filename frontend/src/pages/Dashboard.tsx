/**
 * Main dashboard page showing signals overview.
 */
import { useSignals } from '../hooks/useSignals';
import { SignalHeatmap } from '../components/signals/SignalHeatmap';
import { TopSignals } from '../components/signals/TopSignals';
import { AlertCircle, Loader2 } from 'lucide-react';
import type { Signal } from '../api/types';

interface DashboardProps {
  onSignalClick?: (signal: Signal) => void;
}

export function Dashboard({ onSignalClick }: DashboardProps) {
  const { data, isLoading, error } = useSignals();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-gray-500">
          <Loader2 className="animate-spin" />
          <span>Loading signals...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-center gap-3">
        <AlertCircle className="text-red-500" />
        <div>
          <p className="font-medium text-red-800">Error loading signals</p>
          <p className="text-sm text-red-600">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Heatmap */}
      <SignalHeatmap signals={data.all_signals} onSignalClick={onSignalClick} />

      {/* Top signals grid */}
      <div className="grid md:grid-cols-2 gap-6">
        <TopSignals
          title="Top Equities"
          signals={data.top_equities}
          emptyMessage="No equity signals available"
        />
        <TopSignals
          title="Top Crypto"
          signals={data.top_crypto}
          emptyMessage="No crypto signals available"
        />
      </div>
    </div>
  );
}
