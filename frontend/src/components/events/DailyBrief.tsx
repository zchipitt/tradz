/**
 * Daily Brief snapshot component.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  FileText,
  Download,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { DailyBrief as DailyBriefType, TradePlan } from '../../api/types';

interface DailyBriefProps {
  brief: DailyBriefType;
  onOpenFullReport?: () => void;
  onDownloadJson?: () => void;
  onCompareYesterday?: () => void;
}

function TradeIdeaCard({ plan }: { plan: TradePlan }) {
  return (
    <div className="bg-white border-2 border-gray-300 p-3">
      <div className="flex items-center gap-2 mb-2">
        <span
          className={cn(
            'px-2 py-0.5 text-[10px] font-bold uppercase border border-black',
            plan.risk_level === 'low'
              ? 'bg-status-success text-white'
              : plan.risk_level === 'medium'
              ? 'bg-status-warning text-black'
              : 'bg-status-error text-white'
          )}
        >
          {plan.risk_level} risk
        </span>
        <span className="text-xs text-gray-500">{plan.timeframe}</span>
      </div>
      <p className="text-xs text-gray-800 mb-1">{plan.thesis}</p>
      <p className="text-xs text-gray-600">
        <span className="text-status-error font-bold">Exit:</span> {plan.invalidation}
      </p>
    </div>
  );
}

export function DailyBrief({
  brief,
  onOpenFullReport,
  onDownloadJson,
  onCompareYesterday,
}: DailyBriefProps) {
  const [expanded, setExpanded] = useState(true);

  const hasTradeIdeas = brief.trade_ideas.length > 0;
  const hasOpenLoops = brief.open_loops.length > 0;

  return (
    <div className="bg-white border-2 border-black font-mono">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between hover:bg-gray-200 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-3">
          <FileText size={16} className="text-black" />
          <span className="text-sm font-bold uppercase tracking-wider">
            Daily Brief
          </span>
          <span className="text-xs text-gray-500">[{brief.date}]</span>
        </div>
        <div className="flex items-center gap-2">
          {expanded ? (
            <ChevronUp size={16} className="text-gray-600" />
          ) : (
            <ChevronDown size={16} className="text-gray-600" />
          )}
        </div>
      </button>

      {/* Content */}
      {expanded && (
        <div className="p-4">
          {/* Two Column Layout on Desktop */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Left Column: Executive Summary */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider mb-3 border-b border-gray-200 pb-2">
                Executive Summary
              </h3>
              <ul className="space-y-2">
                {brief.executive_summary.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-gray-700">
                    <span className="w-2 h-2 bg-black mt-1.5 flex-shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>

              {/* Open Loops */}
              {hasOpenLoops && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h3 className="text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2 text-status-warning">
                    <Clock size={12} />
                    Open Loops
                  </h3>
                  <ul className="space-y-1">
                    {brief.open_loops.map((loop, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                        <span className="text-status-warning font-bold">!</span>
                        <span>{loop}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Right Column: Trade Ideas */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider mb-3 border-b border-gray-200 pb-2">
                {hasTradeIdeas ? 'Trade Ideas' : 'Research Ideas'}
              </h3>

              {hasTradeIdeas ? (
                <div className="space-y-3">
                  {brief.trade_ideas.slice(0, 3).map((plan, i) => (
                    <TradeIdeaCard key={i} plan={plan} />
                  ))}
                </div>
              ) : (
                <div className="bg-gray-50 border-2 border-gray-200 p-4 text-center">
                  <AlertCircle size={20} className="mx-auto mb-2 text-gray-400" />
                  <p className="text-xs text-gray-500">
                    No high-confidence trade ideas today.
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    Review events manually for opportunities.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Actions Row */}
          <div className="flex flex-wrap items-center gap-2 mt-6 pt-4 border-t-2 border-gray-200">
            {onOpenFullReport && (
              <button
                onClick={onOpenFullReport}
                className="flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase tracking-wide bg-primary border-2 border-black text-black cursor-pointer transition-all"
               
              >
                <FileText size={14} />
                Open Report
              </button>
            )}
            {onDownloadJson && (
              <button
                onClick={onDownloadJson}
                className="flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase tracking-wide bg-white border-2 border-black text-black hover:bg-gray-100 cursor-pointer transition-all"
               
              >
                <Download size={14} />
                Download JSON
              </button>
            )}
            {onCompareYesterday && (
              <button
                onClick={onCompareYesterday}
                className="flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase tracking-wide bg-white border-2 border-black text-black hover:bg-gray-100 cursor-pointer transition-all"
               
              >
                Compare Yesterday
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
