/**
 * Reports page - Historical daily briefs archive.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { Calendar, FileText, Download, ChevronRight, Archive } from 'lucide-react';
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
    <div className="space-y-6 font-mono">
      {/* Main Container */}
      <div className="bg-white border-2 border-black overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Archive size={16} />
            <span className="text-sm font-bold uppercase tracking-wider">
              Report Archive
            </span>
            <span className="text-xs text-gray-500">
              [{reports.length} entries]
            </span>
          </div>
        </div>

        {/* Reports List */}
        {reports.length > 0 ? (
          <div className="divide-y-2 divide-gray-200">
            {reports.map((report) => (
              <div
                key={report.date}
                className="p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {/* Date */}
                    <div className="flex items-center gap-2">
                      <Calendar size={14} />
                      <span className="font-bold">{report.date}</span>
                    </div>

                    {/* Event count */}
                    <span className="px-2 py-0.5 text-xs font-bold bg-gray-100 border-2 border-black">
                      {report.eventCount} EVENTS
                    </span>

                    {/* Data quality */}
                    <span
                      className={cn(
                        'px-2 py-0.5 text-xs font-bold border-2',
                        report.dataQuality.sourcesOk === report.dataQuality.sourcesTotal
                          ? 'text-status-success bg-status-success/10 border-status-success'
                          : 'text-status-warning bg-status-warning/10 border-status-warning'
                      )}
                    >
                      SOURCES: {report.dataQuality.sourcesOk}/{report.dataQuality.sourcesTotal}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleDownload(report.date, 'md')}
                      className="p-2 text-gray-500 hover:text-black hover:bg-gray-100 transition-colors cursor-pointer border border-transparent hover:border-black"
                      title="Download Markdown"
                    >
                      <FileText size={14} />
                    </button>
                    <button
                      onClick={() => handleDownload(report.date, 'json')}
                      className="p-2 text-gray-500 hover:text-black hover:bg-gray-100 transition-colors cursor-pointer border border-transparent hover:border-black"
                      title="Download JSON"
                    >
                      <Download size={14} />
                    </button>
                    <button
                      onClick={() => handleOpenReport(report.date)}
                      className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold uppercase tracking-wide bg-white border-2 border-black text-black hover:bg-primary transition-colors cursor-pointer"
                    >
                      OPEN
                      <ChevronRight size={12} />
                    </button>
                  </div>
                </div>

                {/* Top events preview */}
                <div className="mt-2 text-xs text-gray-600 pl-6 border-l-2 border-gray-300">
                  {report.topEvents.join(' | ')}
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* Empty state */
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-16 h-16 border-2 border-black mb-4">
              <Archive size={32} className="text-gray-400" />
            </div>
            <p className="text-sm font-bold uppercase tracking-wider">
              No Reports Found
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Reports will appear here after nightly runs complete.
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="px-4 py-3 bg-gray-50 border-t-2 border-black flex items-center justify-between text-xs text-gray-600">
          <span>
            Sorted by date (newest first)
          </span>
          <span>
            Page: 1/1 | Total: {reports.length}
          </span>
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-center gap-2">
        <button className="px-3 py-1.5 text-xs font-bold uppercase tracking-wide bg-white border-2 border-gray-300 text-gray-400 cursor-not-allowed">
          [ PREV ]
        </button>
        <span className="text-xs text-gray-500">Page 1 of 1</span>
        <button className="px-3 py-1.5 text-xs font-bold uppercase tracking-wide bg-white border-2 border-gray-300 text-gray-400 cursor-not-allowed">
          [ NEXT ]
        </button>
      </div>
    </div>
  );
}
