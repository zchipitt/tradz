/**
 * Reports page - Historical daily briefs archive.
 * Shows calendar/list of past reports.
 */
import { Calendar, FileText, Download, ChevronRight } from 'lucide-react';
import { cn } from '../lib/utils';

interface ReportEntry {
  date: string;
  eventCount: number;
  topEvents: string[];
  dataQuality: {
    sourcesOk: number;
    sourcesTotal: number;
  };
}

// Backend reports endpoint not yet implemented
const reports: ReportEntry[] = [];

export function Reports() {
  const handleOpenReport = (date: string) => {
    // TODO: Fetch and display full report
    console.log('Open report for', date);
  };

  const handleDownload = (date: string, format: 'md' | 'json') => {
    // TODO: Implement actual download
    console.log('Download', format, 'for', date);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text">Daily Reports</h1>
        <p className="text-sm text-text-muted mt-1">
          Historical archive of daily briefs and event summaries
        </p>
      </div>

      {/* Reports List */}
      <div className="bg-white rounded-xl border border-border divide-y divide-border">
        {reports.map((report) => (
          <div
            key={report.date}
            className="p-4 hover:bg-surface/50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {/* Date */}
                <div className="flex items-center gap-2">
                  <Calendar size={16} className="text-text-muted" />
                  <span className="font-medium text-text">{report.date}</span>
                </div>

                {/* Event count */}
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                  {report.eventCount} events
                </span>

                {/* Data quality */}
                <span
                  className={cn(
                    'px-2 py-0.5 rounded-full text-xs',
                    report.dataQuality.sourcesOk === report.dataQuality.sourcesTotal
                      ? 'bg-green-50 text-green-700'
                      : 'bg-amber-50 text-amber-700'
                  )}
                >
                  {report.dataQuality.sourcesOk}/{report.dataQuality.sourcesTotal} sources
                </span>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownload(report.date, 'md')}
                  className="p-2 rounded-lg hover:bg-surface text-text-muted hover:text-text transition-colors cursor-pointer"
                  title="Download Markdown"
                >
                  <FileText size={16} />
                </button>
                <button
                  onClick={() => handleDownload(report.date, 'json')}
                  className="p-2 rounded-lg hover:bg-surface text-text-muted hover:text-text transition-colors cursor-pointer"
                  title="Download JSON"
                >
                  <Download size={16} />
                </button>
                <button
                  onClick={() => handleOpenReport(report.date)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium bg-surface text-text hover:bg-gray-200 transition-colors cursor-pointer"
                >
                  View
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>

            {/* Top events preview */}
            <div className="mt-2 text-sm text-text-muted">
              {report.topEvents.join(' • ')}
            </div>
          </div>
        ))}
      </div>

      {/* Empty state */}
      {reports.length === 0 && (
        <div className="text-center py-12 text-text-muted">
          <FileText size={40} className="mx-auto mb-3 opacity-50" />
          <p className="font-medium">No reports yet</p>
          <p className="text-sm mt-1">Reports will appear here after daily runs.</p>
        </div>
      )}

      {/* Pagination placeholder */}
      <div className="flex items-center justify-center gap-2">
        <button className="px-4 py-2 rounded-lg text-sm font-medium bg-surface text-text-muted cursor-not-allowed opacity-50">
          Previous
        </button>
        <span className="text-sm text-text-muted">Page 1 of 1</span>
        <button className="px-4 py-2 rounded-lg text-sm font-medium bg-surface text-text-muted cursor-not-allowed opacity-50">
          Next
        </button>
      </div>
    </div>
  );
}
