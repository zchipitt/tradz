/**
 * Utility functions for the Tradz frontend.
 */

/**
 * Combine class names conditionally.
 * Simple implementation without external dependencies.
 */
export function cn(...classes: (string | boolean | undefined | null | (string | boolean | undefined | null)[])[]): string {
  return classes
    .flat()
    .filter((c): c is string => typeof c === 'string' && c.length > 0)
    .join(' ');
}

/**
 * Format a date string for display.
 */
export function formatDate(date: string | Date | undefined | null): string {
  if (!date) return 'N/A';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return 'Invalid date';
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format a number as a percentage.
 */
export function formatPercent(value: number | undefined | null, decimals: number = 1): string {
  if (value === undefined || value === null) return 'N/A';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

/**
 * Format a number as a price.
 */
export function formatPrice(value: number | undefined | null, currency: string = 'USD'): string {
  if (value === undefined || value === null) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format a date as relative time (e.g., "2 hours ago").
 */
export function formatRelativeTime(date: string | Date | number | undefined | null): string {
  if (!date && date !== 0) return 'N/A';
  const d = typeof date === 'number' 
    ? new Date(date) 
    : typeof date === 'string' 
      ? new Date(date) 
      : date;
  if (isNaN(d.getTime())) return 'Invalid date';
  
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(d);
}

/**
 * Get a color hex based on score value (0-100).
 */
export function getScoreColorHex(score: number): string {
  if (score >= 80) return '#22c55e'; // green-500
  if (score >= 60) return '#84cc16'; // lime-500
  if (score >= 40) return '#eab308'; // yellow-500
  if (score >= 20) return '#f97316'; // orange-500
  return '#ef4444'; // red-500
}

/**
 * Get color class based on price change.
 */
export function getPriceColor(change: number | undefined | null): string {
  if (change === undefined || change === null) return 'text-gray-500';
  if (change > 0) return 'text-green-600';
  if (change < 0) return 'text-red-600';
  return 'text-gray-500';
}

/**
 * Format a large number in compact notation (e.g., 1.2M, 3.4B).
 */
export function formatCompact(value: number | undefined | null): string {
  if (value === undefined || value === null) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
}
