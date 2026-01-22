/**
 * Reports page - Historical daily briefs archive.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import { Calendar, FileText, Download, ChevronRight, Archive, ArchiveIcon } from 'lucide-react';
import { cn } from '../lib/utils';
import { useAvailableBriefs } from '../hooks/useDailyBrief';
import { formatDate } from '../lib/utils';
import { ControlGroup } from '../components/common/ControlGroup';
import { Button } from '../components/common/Button';
import type { BriefSummaryItem } from '../api/types';

interface MarkdownViewerProps {
  content: string;
  onClose: () => void;
  date: string;
}

function MarkdownViewer({ content, onClose, date }: MarkdownViewerProps) {
  // Simple markdown rendering for code blocks
  const renderMarkdown = (markdown: string) => {
    const lines = markdown.split('\n');
    const elements: JSX.Element[] = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];

      // Headers
      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={i} className="text-2xl font-bold mb-4">
            {line.substring(2)}
          </h1>
        );
      } else if (line.startsWith('## ')) {
        elements.push(
          <h2 key={i} className="text-xl font-bold mb-3 mt-4 border-b-2 border-black">
            {line.substring(3)}
          </h2>
        );
      } else if (line.startsWith('### ')) {
        elements.push(
          <h3 key={i} className="text-lg font-bold mb-2 mt-3">
            {line.substring(4)}
          </h3>
        );
      }
      // Code blocks
      else if (line.startsWith('```')) {
        const codeLines: string[] = [];
        i++; // skip the opening ```
        while (i < lines.length && !lines[i].startsWith('```')) {
          codeLines.push(lines[i]);
          i++;
        }
        elements.push(
          <pre key={i} className="bg-gray-100 border-2 border-black p-4 mb-4 overflow-x-auto">
            <code className="text-sm font-mono">{codeLines.join('\n')}</code>
          </pre>
        );
      }
      // Lists
      else if (line.startsWith('- ')) {
        elements.push(
          <li key={i} className="ml-4 mb-1">
            {line.substring(2)}
          </li>
        );
      }
      // Empty lines
      else if (line.trim() === '') {
        elements.push(<div key={i} className="h-2" />);
      }
      // Regular text
      else {
        elements.push(
          <p key={i} className="mb-2">
            {line}
          </p>
        );
      }

      i++;
    }

    return <div>{elements}</div>;
  };

  return (
    <div className="fixed inset-0 bg-white z-50 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b-2 border-black p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            size="sm"
            onClick={onClose}
            leftIcon={<ChevronRight className="rotate-180" />}
          >
            BACK
          </Button>
          <h1 className="text-lg font-bold">
            Daily Brief - {formatDate(date)}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const blob = new Blob([content], { type: 'text/markdown' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `brief-${date}.md`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            leftIcon={<Download />}
          >
            Download
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto p-8">
        {renderMarkdown(content)}
      </div>
    </div>
  );
}

interface BriefListItemProps {
  brief: BriefSummaryItem;
  onOpen: (date: string) => void;
  onDownload: (date: string, format: 'md' | 'json') => void;
}

function BriefListItem({ brief, onOpen, onDownload }: BriefListItemProps) {
  const statusClass = brief.generation_method === 'claude' ? 'bg-primary' : 'bg-gray-200';
  const statusTextClass = brief.generation_method === 'claude' ? 'text-black' : 'text-gray-600';

  return (
    <div className="p-4 hover:bg-gray-50 transition-colors border-b-2 border-gray-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Date */}
          <div className="flex items-center gap-2 min-w-[120px]">
            <Calendar size={14} className="text-gray-500" />
            <span className="font-bold text-sm">{formatDate(brief.date)}</span>
          </div>

          {/* Generation method */}
          <span className={cn('px-2 py-0.5 text-xs font-bold border-2', statusClass, statusTextClass)}>
            {brief.generation_method === 'claude' ? 'LLM' : 'TEMPLATE'}
          </span>

          {/* Event count */}
          <span className="px-2 py-0.5 text-xs font-bold bg-gray-100 border-2 border-black">
            {brief.event_count} EVENTS
          </span>

          {/* Top entity */}
          {brief.top_entity && (
            <span className="px-2 py-0.5 text-xs font-bold bg-gray-100 border-2 border-black">
              TOP: {brief.top_entity}
            </span>
          )}

          {/* Trade ideas count */}
          {brief.trade_idea_count > 0 && (
            <span className="px-2 py-0.5 text-xs font-bold bg-gray-100 border-2 border-black">
              TRADE IDEAS: {brief.trade_idea_count}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => onDownload(brief.date, 'md')}
            className="p-2 text-gray-500 hover:text-black hover:bg-gray-100 transition-colors cursor-pointer border border-transparent hover:border-black"
            title="Download Markdown"
          >
            <FileText size={14} />
          </button>
          <button
            onClick={() => onDownload(brief.date, 'json')}
            className="p-2 text-gray-500 hover:text-black hover:bg-gray-100 transition-colors cursor-pointer border border-transparent hover:border-black"
            title="Download JSON"
          >
            <Download size={14} />
          </button>
          <button
            onClick={() => onOpen(brief.date)}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold uppercase tracking-wide bg-white border-2 border-black text-black hover:bg-primary transition-colors cursor-pointer"
          >
            OPEN
            <ChevronRight size={12} />
          </button>
        </div>
      </div>
    </div>
  );
}

export function Reports() {
  const [selectedBrief, setSelectedBrief] = useState<{ date: string; content: string } | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [dateFilter, setDateFilter] = useState<string>('');
  const itemsPerPage = 20;

  // Fetch available briefs - will auto-refetch after 5 minutes to show new reports
   const { data, isLoading, error, refetch } = useAvailableBriefs(itemsPerPage, (currentPage - 1) * itemsPerPage);

  const handleOpenBrief = async (date: string) => {
    try {
      // Fetch the actual markdown file from the reports directory
      const response = await fetch(`/reports/${date}.md`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const content = await response.text();
      setSelectedBrief({ date, content });
    } catch (err) {
      console.error('Failed to load brief:', err);
    }
  };

  const handleDownload = async (date: string, format: 'md' | 'json') => {
    try {
      // Fetch the actual file from the file system
      const response = await fetch(`/reports/${date}.${format}`);
      const content = await response.text();

      const blob = new Blob([content], {
        type: format === 'md' ? 'text/markdown' : 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `brief-${date}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download brief:', err);
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    refetch();
  };

  const filteredBriefs = data?.briefs || [];
  const totalCount = data?.total_count || 0;
  const totalPages = Math.ceil(totalCount / itemsPerPage);

  if (selectedBrief) {
    return (
      <MarkdownViewer
        content={selectedBrief.content}
        onClose={() => setSelectedBrief(null)}
        date={selectedBrief.date}
      />
    );
  }

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Report Archive</h1>
          <p className="text-sm text-gray-600 mt-1">
            Browse historical daily briefs and trade ideas
          </p>
        </div>
      </div>

      {/* Date Filter */}
      <ControlGroup label="Filter by Date">
        <input
          type="date"
          value={dateFilter}
          onChange={(e) => {
            setDateFilter(e.target.value);
            if (e.target.value) {
              handleOpenBrief(e.target.value);
            }
          }}
          className="px-3 py-2 border-2 border-black text-sm bg-white"
        />
      </ControlGroup>

      {/* Reports List */}
      <div className="bg-white border-2 border-black overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Archive size={16} />
            <span className="text-sm font-bold uppercase tracking-wider">
              Available Reports
            </span>
            {!isLoading && (
              <span className="text-xs text-gray-500">
                [{totalCount} entries]
              </span>
            )}
          </div>
          {isLoading && (
            <span className="text-xs text-gray-500">Loading...</span>
          )}
        </div>

        {/* List or Empty State */}
        {isLoading ? (
          <div className="p-8">
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 border-2 border-gray-300" />
              ))}
            </div>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-sm text-red-600 border-2 border-red-600 bg-red-50">
            <strong>Error loading reports:</strong> {error.message}
          </div>
        ) : filteredBriefs.length > 0 ? (
          <div>
            {filteredBriefs.map((brief) => (
              <BriefListItem
                key={brief.date}
                brief={brief}
                onOpen={handleOpenBrief}
                onDownload={handleDownload}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-16 h-16 border-2 border-black mb-4">
              <ArchiveIcon size={32} className="text-gray-400" />
            </div>
            <p className="text-sm font-bold uppercase tracking-wider">
              No Reports Found
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Reports will appear here after nightly runs complete.
            </p>
            <button
              onClick={() => refetch()}
              className="mt-4 px-4 py-2 text-sm font-bold uppercase tracking-wide bg-primary border-2 border-black hover:bg-primary-dark transition-colors"
            >
              Refresh
            </button>
          </div>
        )}

        {/* Footer */}
        {!isLoading && !error && totalCount > 0 && (
          <div className="px-4 py-3 bg-gray-50 border-t-2 border-black flex items-center justify-between text-xs text-gray-600">
            <span>
              Sorted by date (newest first)
            </span>
            <span>
              Page: {currentPage}/{totalPages} | Total: {totalCount}
            </span>
          </div>
        )}
      </div>

      {/* Pagination */}
      {!isLoading && !error && totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className={cn(
              'px-3 py-1.5 text-xs font-bold uppercase tracking-wide bg-white border-2 transition-colors',
              currentPage === 1
                ? 'border-gray-300 text-gray-400 cursor-not-allowed'
                : 'border-black text-black hover:bg-gray-100 cursor-pointer'
            )}
          >
            [ PREV ]
          </button>
          <span className="text-xs text-gray-500">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className={cn(
              'px-3 py-1.5 text-xs font-bold uppercase tracking-wide bg-white border-2 transition-colors',
              currentPage >= totalPages
                ? 'border-gray-300 text-gray-400 cursor-not-allowed'
                : 'border-black text-black hover:bg-gray-100 cursor-pointer'
            )}
          >
            [ NEXT ]
          </button>
        </div>
      )}
    </div>
  );
}
