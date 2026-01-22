/**
 * OpenLoops component with interactive checklist for tracking open questions.
 * Features: status indicators, resolve checkbox, progress notes, event links.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Clock, ChevronDown, ChevronUp, Plus, AlertCircle, Check, ExternalLink, MessageSquare } from 'lucide-react';
import { useOpenLoops, useOpenLoopActions } from '../../hooks/useOpenLoops';
import type { OpenLoopAPIItem, OpenLoopStatusValue } from '../../api/types';

interface OpenLoopsProps {
  /** Filter to specific status. Default shows all non-resolved. */
  statusFilter?: OpenLoopStatusValue | 'all';
  /** Whether to show in compact mode (for Daily Brief). */
  compact?: boolean;
  /** Maximum number of loops to display. */
  maxItems?: number;
  /** Whether to show the create form. */
  showCreateForm?: boolean;
}

/**
 * Check if a loop is stale (>7 days old with no resolution).
 */
function isStale(loop: OpenLoopAPIItem): boolean {
  if (loop.status === 'resolved') return false;
  const createdAt = new Date(loop.created_at);
  const now = new Date();
  const diffDays = (now.getTime() - createdAt.getTime()) / (1000 * 60 * 60 * 24);
  return diffDays > 7;
}

/**
 * Format relative time for display.
 */
function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'today';
  if (diffDays === 1) return 'yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
  return `${Math.floor(diffDays / 30)}mo ago`;
}

function getStatusBadge(status: OpenLoopStatusValue, isStaleLoop: boolean) {
  if (isStaleLoop) {
    return {
      className: 'bg-yellow-100 text-yellow-800 border-yellow-800',
      label: 'STALE',
    };
  }
  switch (status) {
    case 'open':
      return {
        className: 'bg-gray-100 text-gray-700 border-gray-700',
        label: 'OPEN',
      };
    case 'in_progress':
      return {
        className: 'bg-blue-100 text-blue-800 border-blue-800',
        label: 'IN PROGRESS',
      };
    case 'resolved':
      return {
        className: 'bg-green-100 text-green-800 border-green-800',
        label: 'RESOLVED',
      };
    case 'stale':
      return {
        className: 'bg-yellow-100 text-yellow-800 border-yellow-800',
        label: 'STALE',
      };
  }
}

interface OpenLoopItemProps {
  loop: OpenLoopAPIItem;
  compact?: boolean;
  onResolve: (loopId: string) => void;
  onAddNote: (loopId: string, note: string) => void;
  isUpdating?: boolean;
}

function OpenLoopItemCard({ loop, compact, onResolve, onAddNote, isUpdating }: OpenLoopItemProps) {
  const [showNoteInput, setShowNoteInput] = useState(false);
  const [noteText, setNoteText] = useState('');
  const stale = isStale(loop);
  const statusBadge = getStatusBadge(loop.status, stale);
  const isResolved = loop.status === 'resolved';

  const handleSubmitNote = () => {
    if (noteText.trim()) {
      onAddNote(loop.loop_id, noteText.trim());
      setNoteText('');
      setShowNoteInput(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmitNote();
    }
    if (e.key === 'Escape') {
      setShowNoteInput(false);
      setNoteText('');
    }
  };

  return (
    <div
      className={`border-2 rounded-lg p-3 transition-all ${
        stale
          ? 'border-yellow-500 bg-yellow-50'
          : isResolved
          ? 'border-green-400 bg-green-50 opacity-75'
          : 'border-gray-400 bg-white hover:border-black'
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox for resolving */}
        <button
          onClick={() => !isResolved && onResolve(loop.loop_id)}
          disabled={isResolved || isUpdating}
          className={`mt-0.5 w-5 h-5 flex-shrink-0 border-2 rounded flex items-center justify-center transition-colors ${
            isResolved
              ? 'bg-green-500 border-green-500 text-white cursor-default'
              : 'border-gray-400 hover:border-black hover:bg-gray-100 cursor-pointer'
          } ${isUpdating ? 'opacity-50 cursor-wait' : ''}`}
          title={isResolved ? 'Resolved' : 'Mark as resolved'}
        >
          {isResolved && <Check size={12} strokeWidth={3} />}
        </button>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`text-sm ${isResolved ? 'line-through text-gray-500' : 'text-gray-800'}`}
            >
              {loop.question}
            </span>
            <span
              className={`px-1.5 py-0.5 text-[10px] font-bold border ${statusBadge.className}`}
            >
              {statusBadge.label}
            </span>
          </div>

          {/* Meta info */}
          <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500">
            <span>{formatRelativeTime(loop.created_at)}</span>
            {loop.progress_notes_count > 0 && (
              <span className="flex items-center gap-1">
                <MessageSquare size={10} />
                {loop.progress_notes_count} note{loop.progress_notes_count !== 1 ? 's' : ''}
              </span>
            )}
            {loop.event_summary && (
              <Link
                to={`/events/${loop.event_id}`}
                className="flex items-center gap-1 text-blue-600 hover:text-blue-800 hover:underline"
              >
                <ExternalLink size={10} />
                {loop.event_summary.title || 'View event'}
              </Link>
            )}
          </div>

          {/* Add note section */}
          {!compact && !isResolved && (
            <div className="mt-2">
              {showNoteInput ? (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Add progress note..."
                    className="flex-1 px-2 py-1 text-xs border-2 border-gray-300 rounded focus:border-black focus:outline-none"
                    autoFocus
                    disabled={isUpdating}
                  />
                  <button
                    onClick={handleSubmitNote}
                    disabled={!noteText.trim() || isUpdating}
                    className="px-2 py-1 text-xs font-bold bg-black text-white rounded hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Add
                  </button>
                  <button
                    onClick={() => {
                      setShowNoteInput(false);
                      setNoteText('');
                    }}
                    className="px-2 py-1 text-xs text-gray-600 hover:text-black"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowNoteInput(true)}
                  className="text-xs text-gray-500 hover:text-black flex items-center gap-1"
                >
                  <Plus size={10} />
                  Add note
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface CreateLoopFormProps {
  onCreate: (question: string, eventId?: string) => void;
  isCreating: boolean;
}

function CreateLoopForm({ onCreate, isCreating }: CreateLoopFormProps) {
  const [question, setQuestion] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim()) {
      onCreate(question.trim());
      setQuestion('');
      setIsOpen(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="w-full p-2 text-xs text-gray-600 border-2 border-dashed border-gray-300 rounded-lg hover:border-gray-500 hover:text-gray-800 flex items-center justify-center gap-1"
      >
        <Plus size={12} />
        Add open question
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="border-2 border-black rounded-lg p-3 bg-gray-50">
      <input
        type="text"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="What question needs to be resolved?"
        className="w-full px-2 py-1.5 text-sm border-2 border-gray-300 rounded focus:border-black focus:outline-none"
        autoFocus
        disabled={isCreating}
      />
      <div className="flex gap-2 mt-2">
        <button
          type="submit"
          disabled={!question.trim() || isCreating}
          className="px-3 py-1 text-xs font-bold bg-black text-white rounded hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCreating ? 'Creating...' : 'Add Loop'}
        </button>
        <button
          type="button"
          onClick={() => {
            setIsOpen(false);
            setQuestion('');
          }}
          className="px-3 py-1 text-xs text-gray-600 hover:text-black"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export function OpenLoops({
  statusFilter = 'all',
  compact = false,
  maxItems,
  showCreateForm = true,
}: OpenLoopsProps) {
  const [expanded, setExpanded] = useState(true);

  // Fetch loops - for UI we want to exclude resolved by default unless explicitly requested
  const effectiveFilter = statusFilter === 'all' ? 'all' : statusFilter;
  const { data, isLoading, error } = useOpenLoops(effectiveFilter);
  const actions = useOpenLoopActions();

  // Filter out resolved loops from 'all' view for cleaner default display
  const loops = data?.loops.filter((loop) =>
    statusFilter === 'resolved' ? true : loop.status !== 'resolved'
  ) || [];

  const displayLoops = maxItems ? loops.slice(0, maxItems) : loops;
  const openCount = loops.filter((l) => l.status !== 'resolved').length;
  const staleCount = loops.filter((l) => isStale(l)).length;

  const handleResolve = async (loopId: string) => {
    try {
      await actions.resolve(loopId);
    } catch (err) {
      console.error('Failed to resolve loop:', err);
    }
  };

  const handleAddNote = async (loopId: string, note: string) => {
    try {
      await actions.addNote(loopId, note);
    } catch (err) {
      console.error('Failed to add note:', err);
    }
  };

  const handleCreate = async (question: string, eventId?: string) => {
    try {
      await actions.create(question, eventId);
    } catch (err) {
      console.error('Failed to create loop:', err);
    }
  };

  if (error) {
    return (
      <div className="p-4 border-2 border-red-300 bg-red-50 rounded-lg text-center">
        <AlertCircle className="mx-auto mb-2 text-red-500" size={20} />
        <p className="text-sm text-red-700">Failed to load open loops</p>
      </div>
    );
  }

  return (
    <div className="bg-white border-2 border-black rounded-lg font-mono">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between hover:bg-gray-200 transition-colors cursor-pointer rounded-t-lg"
      >
        <div className="flex items-center gap-3">
          <Clock size={16} className={staleCount > 0 ? 'text-yellow-600' : 'text-gray-600'} />
          <span className="text-sm font-bold uppercase tracking-wider">Open Loops</span>
          {openCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-bold bg-black text-white rounded-full">
              {openCount}
            </span>
          )}
          {staleCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-bold bg-yellow-500 text-white rounded-full">
              {staleCount} stale
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {/* Content */}
      {expanded && (
        <div className="p-4">
          {isLoading ? (
            <div className="text-center py-4">
              <div className="animate-pulse text-sm text-gray-500">Loading...</div>
            </div>
          ) : displayLoops.length === 0 ? (
            <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-gray-200">
              <Clock size={24} className="mx-auto mb-2 text-gray-400" />
              <p className="text-sm text-gray-600">No open questions to track</p>
              <p className="text-xs text-gray-400 mt-1">
                Add questions that need resolution over time
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {displayLoops.map((loop) => (
                <OpenLoopItemCard
                  key={loop.loop_id}
                  loop={loop}
                  compact={compact}
                  onResolve={handleResolve}
                  onAddNote={handleAddNote}
                  isUpdating={actions.isUpdating}
                />
              ))}
            </div>
          )}

          {/* Show more link if truncated */}
          {maxItems && loops.length > maxItems && (
            <div className="mt-3 text-center">
              <span className="text-xs text-gray-500">
                +{loops.length - maxItems} more loops
              </span>
            </div>
          )}

          {/* Create form */}
          {showCreateForm && !compact && (
            <div className="mt-4">
              <CreateLoopForm onCreate={handleCreate} isCreating={actions.isCreating} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default OpenLoops;
