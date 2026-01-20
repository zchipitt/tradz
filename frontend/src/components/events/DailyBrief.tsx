/**
 * Daily Brief snapshot component.
 * Shows executive summary, top trade ideas, and open loops.
 * Robinhood-style clean design.
 */
import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  FileText,
  Download,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  Clock,
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
    <div className="bg-surface rounded-lg p-3 border border-border">
      <div className="flex items-center gap-2 mb-2">
        <TrendingUp size={14} className="text-primary" />
        <span
          className={cn(
            'px-1.5 py-0.5 rounded text-xs font-medium',
            plan.risk_level === 'low'
              ? 'bg-green-100 text-green-700'
              : plan.risk_level === 'medium'
              ? 'bg-amber-100 text-amber-700'
              : 'bg-red-100 text-red-700'
          )}
        >
          {plan.risk_level} risk
        </span>
        <span className="text-xs text-text-muted">{plan.timeframe}</span>
      </div>
      <p className="text-sm font-medium text-text mb-1">{plan.thesis}</p>
      <p className="text-xs text-text-muted">
        <span className="font-medium">Exit:</span> {plan.invalidation}
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
    <div className="bg-white rounded-xl border border-border overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 border-b border-border flex items-center justify-between hover:bg-surface/50 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-3">
          <FileText size={20} className="text-text-muted" />
          <h2 className="font-semibold text-text">Daily Brief</h2>
          <span className="text-xs text-text-muted">{brief.date}</span>
        </div>
        {expanded ? (
          <ChevronUp size={18} className="text-text-muted" />
        ) : (
          <ChevronDown size={18} className="text-text-muted" />
        )}
      </button>

      {/* Content */}
      {expanded && (
        <div className="p-4">
          {/* Two Column Layout on Desktop */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Left Column: Executive Summary */}
            <div>
              <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-3">
                Executive Summary
              </h3>
              <ul className="space-y-2">
                {brief.executive_summary.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-text">
                    <ArrowRight size={14} className="mt-0.5 text-primary flex-shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>

              {/* Open Loops */}
              {hasOpenLoops && (
                <div className="mt-4 pt-4 border-t border-border">
                  <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-2 flex items-center gap-2">
                    <Clock size={14} />
                    Open Loops
                  </h3>
                  <ul className="space-y-1">
                    {brief.open_loops.map((loop, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-text-muted">
                        <AlertCircle size={12} className="mt-1 flex-shrink-0" />
                        <span>{loop}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Right Column: Trade Ideas */}
            <div>
              <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-3">
                {hasTradeIdeas ? 'Top Trade Ideas' : 'Research Ideas'}
              </h3>

              {hasTradeIdeas ? (
                <div className="space-y-3">
                  {brief.trade_ideas.slice(0, 3).map((plan, i) => (
                    <TradeIdeaCard key={i} plan={plan} />
                  ))}
                </div>
              ) : (
                <div className="bg-surface rounded-lg p-4 text-center">
                  <AlertCircle size={24} className="mx-auto mb-2 text-text-muted" />
                  <p className="text-sm text-text-muted">
                    No high-confidence trade ideas today.
                  </p>
                  <p className="text-xs text-text-light mt-1">
                    Review events manually for research opportunities.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Actions Row */}
          <div className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-border">
            {onOpenFullReport && (
              <button
                onClick={onOpenFullReport}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-primary text-white hover:bg-primary-dark transition-colors cursor-pointer"
              >
                <FileText size={14} />
                Open Full Report
              </button>
            )}
            {onDownloadJson && (
              <button
                onClick={onDownloadJson}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-surface text-text hover:bg-gray-200 transition-colors cursor-pointer"
              >
                <Download size={14} />
                Download JSON
              </button>
            )}
            {onCompareYesterday && (
              <button
                onClick={onCompareYesterday}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-surface text-text hover:bg-gray-200 transition-colors cursor-pointer"
              >
                Compare with Yesterday
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
