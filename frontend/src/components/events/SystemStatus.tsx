/**
 * System Status component with health grid.
 * Displays data source health from GET /api/system/status.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import {
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  RefreshCw,
  Mail,
  FileText,
  ChevronDown,
  ChevronUp,
  Database,
  TrendingUp,
  Building2,
  Newspaper,
  BarChart3,
  FileCheck,
  Bitcoin,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { SourceHealth, SourceStatus, SystemStatusResponse } from '../../api/types';

interface SystemStatusProps {
  systemStatus?: SystemStatusResponse | null;
  isLoading?: boolean;
  isError?: boolean;
  error?: Error | null;
  lastUpdated?: string;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  onRetry?: () => void;
  onGenerateBrief?: () => void;
  onSendEmail?: () => void;
}

/**
 * Format timestamp as relative time (e.g., "5m ago", "2h ago").
 */
function formatTimeAgo(dateString: string | null): string {
  if (!dateString) return 'Never';

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.floor(diffHours / 24)}d ago`;
}

/**
 * Get icon for a data source.
 */
function getSourceIcon(sourceName: string) {
  switch (sourceName) {
    case 'equities':
      return TrendingUp;
    case 'crypto':
      return Bitcoin;
    case 'congress':
      return Building2;
    case 'hedgefund':
      return BarChart3;
    case 'polymarket':
      return BarChart3;
    case 'news':
      return Newspaper;
    case 'sec':
      return FileCheck;
    default:
      return Database;
  }
}

/**
 * Get status indicator color based on source status.
 */
function getStatusColor(status: SourceStatus): string {
  switch (status) {
    case 'ok':
      return 'bg-status-success';
    case 'degraded':
      return 'bg-status-warning';
    case 'error':
      return 'bg-status-error';
    default:
      return 'bg-gray-400';
  }
}

/**
 * Get status border color for the source card.
 */
function getStatusBorderColor(status: SourceStatus): string {
  switch (status) {
    case 'ok':
      return 'border-status-success/30';
    case 'degraded':
      return 'border-status-warning/30';
    case 'error':
      return 'border-status-error/30';
    default:
      return 'border-gray-300';
  }
}

/**
 * Individual source health card.
 */
interface SourceHealthCardProps {
  source: SourceHealth;
}

function SourceHealthCard({ source }: SourceHealthCardProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const Icon = getSourceIcon(source.name);
  const hasError = source.status === 'error' || source.status === 'degraded';

  return (
    <div
      className={cn(
        'relative p-3 bg-white border-2 border-black transition-all',
        getStatusBorderColor(source.status),
        hasError && 'cursor-pointer hover:shadow-brutal-sm'
      )}
      onMouseEnter={() => hasError && setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Header: Icon + Name + Status */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon size={16} className="text-gray-600" />
          <span className="text-xs font-bold uppercase tracking-wide text-black">
            {source.display_name}
          </span>
        </div>
        <div
          className={cn(
            'w-3 h-3 rounded-full border border-black',
            getStatusColor(source.status)
          )}
          title={source.status}
        />
      </div>

      {/* Last update time */}
      <div className="text-xs text-gray-500">
        {formatTimeAgo(source.last_success_at)}
      </div>

      {/* Record count */}
      <div className="text-xs text-gray-400 mt-1">
        {source.record_count_24h} records (24h)
      </div>

      {/* Error tooltip for degraded/error sources */}
      {hasError && showTooltip && source.last_error && (
        <div className="absolute left-0 right-0 top-full mt-1 z-10 p-2 bg-black text-white text-xs border-2 border-black shadow-brutal-sm">
          <div className="font-bold uppercase mb-1">
            {source.status === 'error' ? 'Error' : 'Warning'}
          </div>
          <div className="break-words">{source.last_error}</div>
        </div>
      )}
    </div>
  );
}

/**
 * Loading skeleton for the health grid.
 */
function HealthGridSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3 animate-pulse">
      {Array.from({ length: 7 }).map((_, i) => (
        <div key={i} className="p-3 bg-gray-100 border-2 border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gray-200 rounded" />
              <div className="w-16 h-3 bg-gray-200 rounded" />
            </div>
            <div className="w-3 h-3 bg-gray-200 rounded-full" />
          </div>
          <div className="w-12 h-2 bg-gray-200 rounded mt-2" />
          <div className="w-20 h-2 bg-gray-200 rounded mt-1" />
        </div>
      ))}
    </div>
  );
}

export function SystemStatus({
  systemStatus,
  isLoading,
  isError,
  error,
  lastUpdated,
  isRefreshing,
  onRefresh,
  onRetry,
  onGenerateBrief,
  onSendEmail,
}: SystemStatusProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  // Derive summary stats
  const overall = systemStatus?.overall ?? {
    total_sources: 0,
    healthy_count: 0,
    degraded_count: 0,
    error_count: 0,
  };
  const sources = systemStatus?.sources ?? [];

  const allOk = overall.healthy_count === overall.total_sources && overall.total_sources > 0;
  const hasErrors = overall.error_count > 0;
  const hasDegraded = overall.degraded_count > 0;

  return (
    <div className="bg-white border-2 border-black font-mono">
      {/* Header - always visible */}
      <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer"
        >
          <span className="text-sm font-bold uppercase tracking-wider">
            System Status
          </span>
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>

        <div className="flex items-center gap-4">
          {/* Summary badge */}
          {!isLoading && !isError && (
            <div
              className={cn(
                'flex items-center gap-2 px-2 py-1 border text-xs font-bold',
                allOk
                  ? 'bg-status-success/10 border-status-success text-status-success'
                  : hasErrors
                  ? 'bg-status-error/10 border-status-error text-status-error'
                  : hasDegraded
                  ? 'bg-status-warning/10 border-status-warning text-status-warning'
                  : 'bg-gray-100 border-gray-300 text-gray-500'
              )}
            >
              {allOk ? (
                <CheckCircle size={14} />
              ) : hasErrors ? (
                <AlertCircle size={14} />
              ) : hasDegraded ? (
                <AlertTriangle size={14} />
              ) : null}
              <span>
                {overall.healthy_count}/{overall.total_sources} sources healthy
              </span>
            </div>
          )}

          {/* Loading indicator */}
          {isLoading && (
            <span className="text-xs text-gray-500">Loading...</span>
          )}

          {/* Error state */}
          {isError && (
            <span className="text-xs text-status-error">
              Failed to load status
            </span>
          )}
        </div>
      </div>

      {/* Collapsible content */}
      {isExpanded && (
        <div className="p-4">
          {/* Error state with retry */}
          {isError && (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <AlertCircle size={32} className="text-status-error mb-3" />
              <p className="text-sm text-gray-600 mb-3">
                {error?.message || 'Failed to load system status'}
              </p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="px-4 py-2 text-xs font-bold uppercase bg-white border-2 border-black hover:bg-gray-100 transition-colors cursor-pointer"
                >
                  Retry
                </button>
              )}
            </div>
          )}

          {/* Loading skeleton */}
          {isLoading && !systemStatus && <HealthGridSkeleton />}

          {/* Health grid */}
          {!isError && sources.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
              {sources.map((source) => (
                <SourceHealthCard key={source.name} source={source} />
              ))}
            </div>
          )}

          {/* Actions bar */}
          {!isError && (
            <div className="mt-4 pt-4 border-t-2 border-gray-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              {/* Left: Status message + last updated */}
              <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600">
                {allOk ? (
                  <span>All systems operational.</span>
                ) : hasErrors ? (
                  <span className="text-status-error">
                    {overall.error_count} source{overall.error_count !== 1 ? 's' : ''} in error state.
                  </span>
                ) : hasDegraded ? (
                  <span className="text-status-warning">
                    {overall.degraded_count} source{overall.degraded_count !== 1 ? 's' : ''} degraded.
                  </span>
                ) : null}

                {(lastUpdated || systemStatus?.last_check_at) && (
                  <span className="text-gray-400">
                    Last sync: {formatTimeAgo(lastUpdated || systemStatus?.last_check_at || null)}
                  </span>
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
          )}
        </div>
      )}
    </div>
  );
}
