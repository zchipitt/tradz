/**
 * System Status header component.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import {
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  RefreshCw,
  Mail,
  FileText,
  Clock,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { DailyBrief } from '../../api/types';

interface SystemStatusProps {
  dataQuality: DailyBrief['data_quality'];
  lastUpdated?: string;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  onGenerateBrief?: () => void;
  onSendEmail?: () => void;
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.floor(diffHours / 24)}d ago`;
}

export function SystemStatus({
  dataQuality,
  lastUpdated,
  isRefreshing,
  onRefresh,
  onGenerateBrief,
  onSendEmail,
}: SystemStatusProps) {
  const hasErrors = dataQuality.errors.length > 0;
  const isStale = dataQuality.stalest_age_hours > 24;
  const allOk = !hasErrors && !isStale;

  return (
    <div className="bg-white border-2 border-black font-mono">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
        <span className="text-sm font-bold uppercase tracking-wider">
          System Status
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">
            {dataQuality.sources_ok}/{dataQuality.sources_total} sources
          </span>
        </div>
      </div>

      <div className="p-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          {/* Left: Status indicators */}
          <div className="flex flex-wrap items-center gap-4">
            {/* Overall status */}
            <div className={cn(
              'flex items-center gap-2 px-3 py-1.5 border-2',
              allOk ? 'bg-status-success/10 border-status-success text-status-success' :
              hasErrors ? 'bg-status-error/10 border-status-error text-status-error' :
              'bg-status-warning/10 border-status-warning text-status-warning'
            )}>
              {allOk ? (
                <CheckCircle size={16} />
              ) : hasErrors ? (
                <AlertCircle size={16} />
              ) : (
                <AlertTriangle size={16} />
              )}
              <span className="text-xs font-bold uppercase">
                {allOk ? 'All OK' : hasErrors ? 'Error' : 'Warning'}
              </span>
            </div>

            {/* Errors */}
            {hasErrors && (
              <div className="text-xs text-status-error font-bold">
                {dataQuality.errors[0]}
                {dataQuality.errors.length > 1 && (
                  <span className="text-gray-500 ml-1">+{dataQuality.errors.length - 1} more</span>
                )}
              </div>
            )}

            {/* Staleness warning */}
            {isStale && (
              <div className="flex items-center gap-2 text-xs text-status-warning">
                <Clock size={14} />
                <span className="font-bold">
                  {dataQuality.stalest_source}: {dataQuality.stalest_age_hours}h old
                </span>
              </div>
            )}

            {/* Last updated */}
            {lastUpdated && (
              <div className="text-xs text-gray-500">
                Last sync: {formatTimeAgo(lastUpdated)}
              </div>
            )}
          </div>

          {/* Right: Quick actions */}
          <div className="flex items-center gap-2">
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isRefreshing}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 text-xs font-bold uppercase tracking-wide',
                  'bg-white border-2 border-black text-black',
                  'hover:bg-gray-100 transition-colors cursor-pointer',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
               
              >
                <RefreshCw size={14} className={cn(isRefreshing && 'animate-spin')} />
                <span className="hidden sm:inline">Refresh</span>
              </button>
            )}

            {onGenerateBrief && (
              <button
                onClick={onGenerateBrief}
                className="flex items-center gap-2 px-3 py-2 text-xs font-bold uppercase tracking-wide bg-white border-2 border-black text-black hover:bg-gray-100 transition-colors cursor-pointer"
               
              >
                <FileText size={14} />
                <span className="hidden sm:inline">Brief</span>
              </button>
            )}

            {onSendEmail && (
              <button
                onClick={onSendEmail}
                className="flex items-center gap-2 px-3 py-2 text-xs font-bold uppercase tracking-wide bg-primary border-2 border-black text-black hover:shadow-brutal transition-colors cursor-pointer"
               
              >
                <Mail size={14} />
                <span className="hidden sm:inline">Send</span>
              </button>
            )}
          </div>
        </div>

        {/* Status message */}
        <div className="mt-4 pt-4 border-t-2 border-gray-200 text-xs text-gray-600">
          {allOk ? (
            <span>All systems operational. Data sources connected and syncing.</span>
          ) : hasErrors ? (
            <span className="text-status-error">Errors detected - check source health.</span>
          ) : (
            <span className="text-status-warning">Warning - some data may be stale.</span>
          )}
        </div>
      </div>
    </div>
  );
}
