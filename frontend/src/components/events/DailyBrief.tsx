/**
 * Daily Brief component with structured sections and collapsible interface.
 * Replaces the old DailyBrief.tsx with updated types.
 */
import { useState } from 'react';
import { ChevronDown, ChevronUp, FileText, Copy, Check, AlertCircle, Clock } from 'lucide-react';
import type { BriefDetail, TradeIdeaItem, ResearchIdeaItem, OpenLoopItem } from '../../api/types';

interface DailyBriefProps {
  brief: BriefDetail;
}

function TradeIdeaCard({ idea }: { idea: TradeIdeaItem }) {
  const getDirectionBadgeColor = (direction: string) => {
    switch (direction.toLowerCase()) {
      case 'long':
        return 'bg-green-100 text-green-800 border-green-800';
      case 'short':
        return 'bg-red-100 text-red-800 border-red-800';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-800';
    }
  };

  return (
    <div className="border-2 border-black rounded-lg p-4 bg-white hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,0.8)] hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {idea.ticker && <span className="font-bold text-lg">{idea.ticker}</span>}
          <span className={`px-2 py-1 text-xs font-bold uppercase border ${getDirectionBadgeColor(idea.direction)}`}>
            {idea.direction}
          </span>
          <span className="text-xs text-gray-500">{idea.confidence_level}% confidence</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-3">
        <div className="bg-gray-50 rounded p-2">
          <div className="text-xs text-gray-600 uppercase tracking-wide">Entry</div>
          <div className="font-semibold text-green-700">{idea.entry_zone}</div>
        </div>
        <div className="bg-gray-50 rounded p-2">
          <div className="text-xs text-gray-600 uppercase tracking-wide">Target</div>
          <div className="font-semibold text-blue-700">{idea.target}</div>
        </div>
        <div className="bg-gray-50 rounded p-2">
          <div className="text-xs text-gray-600 uppercase tracking-wide">Stop</div>
          <div className="font-semibold text-red-700">{idea.stop_loss}</div>
        </div>
      </div>

      <div className="bg-gray-50 rounded p-3">
        <div className="text-xs text-gray-600 uppercase tracking-wide mb-1">Rationale</div>
        <div className="text-sm text-gray-700">{idea.rationale}</div>
      </div>
    </div>
  );
}

function ResearchIdeaCard({ idea }: { idea: ResearchIdeaItem }) {
  return (
    <div className="border-2 border-gray-400 rounded-lg p-4 bg-gray-50">
      <div className="flex items-center gap-2 mb-3">
        {idea.ticker && <span className="font-bold text-lg">{idea.ticker}</span>}
        <span className="px-2 py-1 text-xs font-bold uppercase bg-yellow-100 text-yellow-800 border border-yellow-800">
          Research
        </span>
        <span className="text-xs text-gray-500">Potential: {idea.potential_score}</span>
      </div>

      <div className="space-y-3">
        <div className="bg-yellow-50 rounded p-3">
          <div className="text-xs text-gray-600 uppercase tracking-wide mb-1">Questions to Verify</div>
          <ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
            {idea.questions.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </div>

        <div className="bg-gray-50 rounded p-3">
          <div className="text-xs text-gray-600 uppercase tracking-wide mb-1">Evidence to Watch</div>
          <ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
            {idea.evidence_to_watch.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function OpenLoopCard({ loop }: { loop: OpenLoopItem }) {
  const getStatusBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open':
        return 'bg-yellow-100 text-yellow-800 border-yellow-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-800';
      case 'resolved':
        return 'bg-green-100 text-green-800 border-green-800';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-800';
    }
  };

  return (
    <div className="flex items-start gap-2 p-2 bg-gray-50 rounded border">
      <span className="pt-1">⚠️</span>
      <div className="flex-1">
        <div className="text-sm text-gray-700">{loop.question}</div>
        <span className={`inline-block mt-1 px-2 py-0.5 text-xs border ${getStatusBadgeColor(loop.status)}`}>
          {loop.status.replace('_', ' ')}
        </span>
      </div>
    </div>
  );
}

function DataQualityCard({ dataQuality }: { dataQuality: BriefDetail['data_quality'] }) {
  if (!dataQuality) return null;

  const getStatusBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'ok':
        return 'bg-green-100 text-green-800 border-green-800';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 border-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-800';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-800';
    }
  };

  return (
    <div className="border-2 border-black rounded-lg p-4 bg-white">
      <div className="flex items-center gap-2 mb-3">
        <span className={`px-2 py-1 text-xs font-bold border ${getStatusBadgeColor(dataQuality.overall_status)}`}>
          {dataQuality.overall_status.toUpperCase()}
        </span>
        <span className="text-sm font-semibold">{dataQuality.quality_message}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {dataQuality.sources.map((source) => (
          <div key={source.name} className="flex items-center justify-between bg-gray-50 rounded p-2">
            <span className="text-sm font-medium">{source.display_name}</span>
            <span className={`px-2 py-0.5 text-xs border ${getStatusBadgeColor(source.status)}`}>
              {source.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function DailyBrief({ brief }: DailyBriefProps) {
  const [expanded, setExpanded] = useState(true);
  const [copied, setCopied] = useState(false);

  const tradeIdeas = brief.trade_ideas || [];
  const researchIdeas = brief.research_ideas || [];
  const openLoops = brief.open_loops || [];
  const dataQuality = brief.data_quality || null;

  const hasTradeIdeas = tradeIdeas.length > 0;
  const hasResearchIdeas = researchIdeas.length > 0;
  const hasOpenLoops = openLoops.length > 0;
  const hasDataQuality = dataQuality !== null;

  const generationMethodBadge = brief.generation_method === 'claude'
    ? 'bg-purple-100 text-purple-800 border-purple-800'
    : 'bg-gray-100 text-gray-800 border-gray-800';

  const handleCopySummary = async () => {
    try {
      await navigator.clipboard.writeText(brief.executive_summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="bg-white border-2 border-black font-mono">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between hover:bg-gray-200 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-3">
          <FileText size={16} className="text-black" />
          <span className="text-sm font-bold uppercase tracking-wider">Daily Brief</span>
          <span className="text-xs text-gray-500">{brief.date.split('T')[0]}</span>
          <span className={`px-2 py-1 text-xs border ${generationMethodBadge}`}>
            {brief.generation_method.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {/* Content */}
      {expanded && (
        <div className="p-4">
          {/* Executive Summary */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold uppercase tracking-wider border-b border-gray-200 pb-2">
                Executive Summary
              </h3>
              <button
                onClick={handleCopySummary}
                className="flex items-center gap-1 p-1 text-xs bg-gray-100 border border-gray-400 hover:bg-gray-200 transition-colors"
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <p className="text-sm text-gray-700 bg-gray-50 rounded p-3">
              {brief.executive_summary}
            </p>
          </div>

          {/* Two Column Layout */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Left Column: Trade Ideas */}
            <div className="mb-6">
              <h3 className="text-xs font-bold uppercase tracking-wider border-b border-gray-200 pb-2">
                {hasTradeIdeas ? 'Trade Ideas' : 'Research Ideas'}
              </h3>
              {hasTradeIdeas && (
                <div className="mt-4 space-y-4">
                  {tradeIdeas.map((idea) => (
                    <TradeIdeaCard key={idea.event_id} idea={idea} />
                  ))}
                </div>
              )}
              {hasResearchIdeas && !hasTradeIdeas && (
                <div className="mt-4 space-y-4">
                  {researchIdeas.map((idea) => (
                    <ResearchIdeaCard key={idea.event_id} idea={idea} />
                  ))}
                </div>
              )}
              {!hasTradeIdeas && !hasResearchIdeas && (
                <div className="mt-4 p-8 bg-gray-50 border-2 border-gray-300 text-center">
                  <AlertCircle size={20} className="mx-auto mb-2 text-gray-400" />
                  <p className="text-xs text-gray-500">No actionable trade ideas today</p>
                  <p className="text-xs text-gray-400 mt-1">Check Research Ideas or review events manually</p>
                </div>
              )}
            </div>

            {/* Right Column: Top Events */}
            <div className="mb-6">
              <h3 className="text-xs font-bold uppercase tracking-wider border-b border-gray-200 pb-2">
                Top Events
              </h3>
              <div className="mt-4 space-y-3">
                {brief.top_events.map((event) => (
                  <div key={event.event_id} className="border-2 border-gray-400 rounded p-3 bg-white">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm">{event.title}</span>
                        <span className="px-2 py-0.5 text-xs bg-gray-200 text-gray-700">
                          {event.attention_score.toFixed(0)}
                        </span>
                      </div>
                      {event.ticker && (
                        <span className="text-xs font-mono text-gray-600">{event.ticker}</span>
                      )}
                    </div>
                    <div className="grid grid-cols-4 gap-2 text-xs">
                      <div className="bg-red-50 rounded p-1 text-center">
                        <div className="text-red-600 font-semibold">{event.anomaly_score.toFixed(0)}</div>
                        <div className="text-red-500 text-xs">Anomaly</div>
                      </div>
                      <div className="bg-blue-50 rounded p-1 text-center">
                        <div className="text-blue-600 font-semibold">{event.catalyst_score.toFixed(0)}</div>
                        <div className="text-blue-500 text-xs">Catalyst</div>
                      </div>
                      <div className="bg-green-50 rounded p-1 text-center">
                        <div className="text-green-600 font-semibold">{event.flow_score.toFixed(0)}</div>
                        <div className="text-green-500 text-xs">Flow</div>
                      </div>
                      <div className="bg-gray-50 rounded p-1 text-center">
                        <div className="text-gray-600 font-semibold">{event.confidence_score.toFixed(0)}</div>
                        <div className="text-gray-500 text-xs">Confidence</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Open Loops */}
          {hasOpenLoops && (
            <div className="mb-6">
              <h3 className="text-xs font-bold uppercase tracking-wider border-b border-gray-200 pb-2 flex items-center gap-2">
                <Clock size={12} className="text-yellow-600" />
                Open Loops
              </h3>
              <div className="mt-3 space-y-2">
                {openLoops.map((loop) => (
                  <OpenLoopCard key={loop.loop_id} loop={loop} />
                ))}
              </div>
            </div>
          )}

          {/* Data Quality */}
          {hasDataQuality && (
            <div className="mb-6">
              <h3 className="text-xs font-bold uppercase tracking-wider border-b border-gray-200 pb-2">
                Data Quality
              </h3>
              <div className="mt-3">
                <DataQualityCard dataQuality={dataQuality} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
