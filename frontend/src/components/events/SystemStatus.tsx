/**
 * System Status header component.
 * Shows data quality, source health, and quick actions.
 * Robinhood-style clean design.
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
    <div className="bg-white rounded-xl border border-border p-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {/* Left: Status indicators */}
        <div className="flex flex-wrap items-center gap-4">
          {/* Overall status */}
          <div className="flex items-center gap-2">
            {allOk ? (
              <CheckCircle size={18} className="text-primary" />
            ) : hasErrors ? (
              <AlertCircle size={18} className="text-negative" />
            ) : (
              <AlertTriangle size={18} className="text-amber-500" />
            )}
            <span className="text-sm font-medium text-text">
              Sources: {dataQuality.sources_ok}/{dataQuality.sources_total}
            </span>
          </div>

          {/* Errors */}
          {hasErrors && (
            <div className="flex items-center gap-1.5 text-xs text-negative">
              <AlertCircle size={14} />
              <span>{dataQuality.errors[0]}</span>
              {dataQuality.errors.length > 1 && (
                <span className="text-text-muted">+{dataQuality.errors.length - 1} more</span>
              )}
            </div>
          )}

          {/* Staleness warning */}
          {isStale && (
            <div className="flex items-center gap-1.5 text-xs text-amber-600">
              <Clock size={14} />
              <span>
                {dataQuality.stalest_source}: {dataQuality.stalest_age_hours}h old
              </span>
            </div>
          )}

          {/* Last updated */}
          {lastUpdated && (
            <div className="text-xs text-text-muted">
              Updated: {formatTimeAgo(lastUpdated)}
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
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium',
                'bg-surface text-text hover:bg-gray-200',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'transition-colors cursor-pointer'
              )}
            >
              <RefreshCw size={14} className={cn(isRefreshing && 'animate-spin')} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          )}

          {onGenerateBrief && (
            <button
              onClick={onGenerateBrief}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-surface text-text hover:bg-gray-200 transition-colors cursor-pointer"
            >
              <FileText size={14} />
              <span className="hidden sm:inline">Generate Brief</span>
            </button>
          )}

          {onSendEmail && (
            <button
              onClick={onSendEmail}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-primary text-white hover:bg-primary-dark transition-colors cursor-pointer"
            >
              <Mail size={14} />
              <span className="hidden sm:inline">Send Email</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
