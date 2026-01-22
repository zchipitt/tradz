/**
 * ActionPanel component - Displays trade ideas or research plans based on quality gate evaluation.
 * Shows either a TradeIdea (if gates pass) or ResearchPlan (if gates fail).
 *
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import {
  ArrowUpRight,
  ArrowDownRight,
  Target,
  Shield,
  AlertTriangle,
  HelpCircle,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  BookOpen,
  TrendingUp,
  Eye,
  Calendar,
  Loader2,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useEventRecommendation } from '../../hooks/useEvents';
import type {
  TradeIdea,
  ResearchPlan,
  QualityGateEvaluation,
  GateResult,
  TradeDirection,
  TimeHorizon,
} from '../../api/types';

interface ActionPanelProps {
  eventId: string;
  className?: string;
}

/**
 * Direction configuration for display.
 */
const directionConfig: Record<TradeDirection, { label: string; icon: React.ElementType; color: string; bgColor: string }> = {
  long: {
    label: 'LONG',
    icon: ArrowUpRight,
    color: 'text-status-success',
    bgColor: 'bg-status-success',
  },
  short: {
    label: 'SHORT',
    icon: ArrowDownRight,
    color: 'text-status-error',
    bgColor: 'bg-status-error',
  },
  neutral: {
    label: 'NEUTRAL',
    icon: TrendingUp,
    color: 'text-gray-600',
    bgColor: 'bg-gray-500',
  },
};

/**
 * Time horizon configuration for display.
 */
const horizonConfig: Record<TimeHorizon, { label: string; description: string }> = {
  intraday: { label: 'Intraday', description: 'Same day' },
  swing: { label: 'Swing', description: '2-10 days' },
  position: { label: 'Position', description: '2-8 weeks' },
  investment: { label: 'Investment', description: '3+ months' },
};

/**
 * Get confidence level styling.
 */
function getConfidenceStyle(level: number): { label: string; color: string; bgColor: string } {
  if (level >= 80) return { label: 'Very High', color: 'text-status-success', bgColor: 'bg-status-success' };
  if (level >= 70) return { label: 'High', color: 'text-score-good', bgColor: 'bg-score-good' };
  if (level >= 60) return { label: 'Moderate', color: 'text-status-warning', bgColor: 'bg-status-warning' };
  if (level >= 50) return { label: 'Low', color: 'text-orange-500', bgColor: 'bg-orange-500' };
  return { label: 'Very Low', color: 'text-gray-500', bgColor: 'bg-gray-500' };
}

/**
 * Quality Gate result row.
 */
function GateResultRow({ result }: { result: GateResult }) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-gray-200 last:border-b-0">
      <div className={cn(
        'w-5 h-5 flex items-center justify-center',
        result.passed ? 'text-status-success' : 'text-status-error'
      )}>
        {result.passed ? <CheckCircle size={16} /> : <XCircle size={16} />}
      </div>
      <div className="flex-1">
        <span className="text-sm font-medium text-black">{result.gate_name}</span>
        <span className="text-xs text-gray-500 ml-2">
          ({typeof result.actual_value === 'boolean' ? (result.actual_value ? 'yes' : 'no') : result.actual_value} / {typeof result.threshold_value === 'boolean' ? (result.threshold_value ? 'yes' : 'no') : result.threshold_value})
        </span>
      </div>
      {!result.passed && result.improvement_suggestion && (
        <div className="text-xs text-status-warning max-w-[200px] truncate" title={result.improvement_suggestion}>
          {result.improvement_suggestion}
        </div>
      )}
    </div>
  );
}

/**
 * Quality Gate evaluation summary component.
 */
function GateEvaluationSummary({ evaluation }: { evaluation: QualityGateEvaluation }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const passRate = evaluation.gate_results.filter(g => g.passed).length / evaluation.gate_results.length;

  return (
    <div className="border-2 border-gray-200 mb-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={cn(
            'w-8 h-8 flex items-center justify-center border-2 border-black',
            evaluation.passed ? 'bg-status-success' : 'bg-status-warning'
          )}>
            {evaluation.passed ? <CheckCircle size={16} className="text-white" /> : <AlertTriangle size={16} className="text-white" />}
          </div>
          <div className="text-left">
            <div className="text-sm font-bold uppercase text-black">
              Quality Gates: {evaluation.passed ? 'Passed' : 'Failed'}
            </div>
            <div className="text-xs text-gray-500">
              {evaluation.gate_results.filter(g => g.passed).length}/{evaluation.gate_results.length} gates passed ({Math.round(passRate * 100)}%)
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-xl font-bold text-black">{Math.round(evaluation.gate_score)}</div>
            <div className="text-xs text-gray-500 uppercase">Score</div>
          </div>
          {isExpanded ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
        </div>
      </button>

      {isExpanded && (
        <div className="px-3 pb-3 border-t border-gray-200">
          <div className="pt-3 space-y-1">
            {evaluation.gate_results.map((result, idx) => (
              <GateResultRow key={idx} result={result} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Trade Idea view component.
 */
function TradeIdeaView({ idea }: { idea: TradeIdea }) {
  const direction = directionConfig[idea.direction];
  const horizon = horizonConfig[idea.time_horizon];
  const confidence = getConfidenceStyle(idea.confidence_level);
  const DirectionIcon = direction.icon;

  return (
    <div className="space-y-4">
      {/* Direction + Confidence Header */}
      <div className="flex items-stretch gap-4">
        {/* Direction */}
        <div className={cn(
          'flex-1 p-4 border-2 border-black',
          direction.bgColor
        )}>
          <div className="flex items-center gap-2 text-white mb-1">
            <DirectionIcon size={20} />
            <span className="text-lg font-bold uppercase">{direction.label}</span>
          </div>
          <div className="text-xs text-white/80 uppercase">
            {horizon.label} ({horizon.description})
          </div>
        </div>

        {/* Confidence */}
        <div className="flex-1 p-4 border-2 border-black bg-gray-50">
          <div className="text-xs text-gray-500 uppercase mb-1">Confidence</div>
          <div className="flex items-baseline gap-2">
            <span className={cn('text-2xl font-bold', confidence.color)}>
              {Math.round(idea.confidence_level)}%
            </span>
            <span className={cn('text-xs uppercase', confidence.color)}>
              {confidence.label}
            </span>
          </div>
        </div>
      </div>

      {/* Trade Parameters */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {/* Entry Zone */}
        <div className="p-3 border-2 border-gray-200 bg-gray-50">
          <div className="text-xs text-gray-500 uppercase mb-1 flex items-center gap-1">
            <Target size={12} />
            Entry Zone
          </div>
          <div className="text-sm font-bold text-black">{idea.entry_zone}</div>
        </div>

        {/* Target */}
        <div className="p-3 border-2 border-status-success/30 bg-status-success/5">
          <div className="text-xs text-status-success uppercase mb-1 flex items-center gap-1">
            <ArrowUpRight size={12} />
            Target
          </div>
          <div className="text-sm font-bold text-status-success">{idea.target}</div>
        </div>

        {/* Stop Loss */}
        <div className="p-3 border-2 border-status-error/30 bg-status-error/5">
          <div className="text-xs text-status-error uppercase mb-1 flex items-center gap-1">
            <Shield size={12} />
            Stop Loss
          </div>
          <div className="text-sm font-bold text-status-error">{idea.stop_loss}</div>
        </div>
      </div>

      {/* Invalidation */}
      <div className="p-3 border-2 border-status-warning/30 bg-status-warning/5">
        <div className="text-xs text-status-warning uppercase mb-1 flex items-center gap-1">
          <AlertTriangle size={12} />
          Invalidation
        </div>
        <div className="text-sm text-gray-700">{idea.invalidation}</div>
      </div>

      {/* Rationale */}
      <div className="p-3 border-2 border-gray-200">
        <div className="text-xs text-gray-500 uppercase mb-2 flex items-center gap-1">
          <HelpCircle size={12} />
          Rationale
        </div>
        <p className="text-sm text-gray-700 leading-relaxed">{idea.rationale}</p>
      </div>

      {/* Key Catalysts & Risk Factors */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Key Catalysts */}
        {idea.key_catalysts.length > 0 && (
          <div className="p-3 border-2 border-gray-200">
            <div className="text-xs text-gray-500 uppercase mb-2 flex items-center gap-1">
              <TrendingUp size={12} />
              Key Catalysts
            </div>
            <ul className="space-y-1">
              {idea.key_catalysts.map((catalyst, idx) => (
                <li key={idx} className="text-xs text-gray-700 flex items-start gap-2">
                  <span className="text-status-success mt-0.5">+</span>
                  <span>{catalyst}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Risk Factors */}
        {idea.risk_factors.length > 0 && (
          <div className="p-3 border-2 border-gray-200">
            <div className="text-xs text-gray-500 uppercase mb-2 flex items-center gap-1">
              <AlertTriangle size={12} />
              Risk Factors
            </div>
            <ul className="space-y-1">
              {idea.risk_factors.map((risk, idx) => (
                <li key={idx} className="text-xs text-gray-700 flex items-start gap-2">
                  <span className="text-status-error mt-0.5">-</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Research Plan view component.
 */
function ResearchPlanView({ plan }: { plan: ResearchPlan }) {
  const scoreStyle = getConfidenceStyle(plan.current_score);

  return (
    <div className="space-y-4">
      {/* Current Score Header */}
      <div className="p-4 border-2 border-status-warning bg-status-warning/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 flex items-center justify-center border-2 border-black bg-status-warning">
              <BookOpen size={20} className="text-white" />
            </div>
            <div>
              <div className="text-sm font-bold uppercase text-black">Research Required</div>
              <div className="text-xs text-gray-600">
                Quality gates not met - more evidence needed
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className={cn('text-2xl font-bold', scoreStyle.color)}>
              {Math.round(plan.current_score)}
            </div>
            <div className="text-xs text-gray-500 uppercase">Current Score</div>
          </div>
        </div>
      </div>

      {/* Gaps Identified */}
      {plan.gaps_identified.length > 0 && (
        <div className="p-3 border-2 border-status-error/30 bg-status-error/5">
          <div className="text-xs text-status-error uppercase mb-2 flex items-center gap-1">
            <XCircle size={12} />
            Gaps Identified
          </div>
          <ul className="space-y-2">
            {plan.gaps_identified.map((gap, idx) => (
              <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-status-error mt-0.5 flex-shrink-0">!</span>
                <span>{gap}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Questions to Verify */}
      {plan.questions_to_verify.length > 0 && (
        <div className="p-3 border-2 border-gray-200">
          <div className="text-xs text-gray-500 uppercase mb-2 flex items-center gap-1">
            <HelpCircle size={12} />
            Questions to Verify
          </div>
          <ul className="space-y-2">
            {plan.questions_to_verify.map((question, idx) => (
              <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-primary font-bold mt-0.5 flex-shrink-0">{idx + 1}.</span>
                <span>{question}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Evidence to Watch */}
      {plan.evidence_to_watch.length > 0 && (
        <div className="p-3 border-2 border-gray-200">
          <div className="text-xs text-gray-500 uppercase mb-2 flex items-center gap-1">
            <Eye size={12} />
            Evidence to Watch
          </div>
          <ul className="space-y-2">
            {plan.evidence_to_watch.map((evidence, idx) => (
              <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-blue-500 mt-1 flex-shrink-0">&#8226;</span>
                <span>{evidence}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Next Check Date */}
      {plan.next_check_date && (
        <div className="p-3 border-2 border-gray-200 bg-gray-50">
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-gray-500" />
            <div>
              <div className="text-xs text-gray-500 uppercase">Next Check</div>
              <div className="text-sm font-bold text-black">
                {new Date(plan.next_check_date).toLocaleDateString('en-US', {
                  weekday: 'short',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Loading skeleton for ActionPanel.
 */
function ActionPanelSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-16 bg-gray-200 border-2 border-gray-300" />
      <div className="flex gap-4">
        <div className="flex-1 h-24 bg-gray-200 border-2 border-gray-300" />
        <div className="flex-1 h-24 bg-gray-200 border-2 border-gray-300" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-16 bg-gray-200 border-2 border-gray-300" />
        ))}
      </div>
      <div className="h-20 bg-gray-200 border-2 border-gray-300" />
    </div>
  );
}

/**
 * Error state for ActionPanel.
 */
function ActionPanelError({ message }: { message: string }) {
  return (
    <div className="p-4 border-2 border-status-error/30 bg-status-error/5">
      <div className="flex items-center gap-3">
        <AlertTriangle size={20} className="text-status-error" />
        <div>
          <div className="text-sm font-bold text-status-error">Unable to Load Recommendation</div>
          <div className="text-xs text-gray-600">{message}</div>
        </div>
      </div>
    </div>
  );
}

/**
 * Main ActionPanel component.
 */
export function ActionPanel({ eventId, className }: ActionPanelProps) {
  const { data, isLoading, isError, error } = useEventRecommendation(eventId);

  if (isLoading) {
    return (
      <div className={cn('', className)}>
        <h3 className="text-sm font-bold uppercase tracking-wider text-black mb-4 flex items-center gap-2">
          <Loader2 size={16} className="animate-spin" />
          Loading Recommendation...
        </h3>
        <ActionPanelSkeleton />
      </div>
    );
  }

  if (isError) {
    return (
      <div className={className}>
        <h3 className="text-sm font-bold uppercase tracking-wider text-black mb-4">
          Action Panel
        </h3>
        <ActionPanelError message={error instanceof Error ? error.message : 'Unknown error occurred'} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className={className}>
        <h3 className="text-sm font-bold uppercase tracking-wider text-black mb-4">
          Action Panel
        </h3>
        <div className="p-4 border-2 border-gray-200 bg-gray-50 text-center">
          <div className="text-sm text-gray-500">No recommendation available</div>
        </div>
      </div>
    );
  }

  const isTradeIdea = data.type === 'trade_idea' && data.trade_idea;
  const title = isTradeIdea ? 'Trade Idea' : 'Research Plan';

  return (
    <div className={className}>
      <h3 className="text-sm font-bold uppercase tracking-wider text-black mb-4 flex items-center gap-2">
        {isTradeIdea ? (
          <Target size={16} className="text-status-success" />
        ) : (
          <BookOpen size={16} className="text-status-warning" />
        )}
        {title}
      </h3>

      {/* Quality Gate Summary */}
      {data.gate_evaluation && (
        <GateEvaluationSummary evaluation={data.gate_evaluation} />
      )}

      {/* Content based on type */}
      {isTradeIdea && data.trade_idea ? (
        <TradeIdeaView idea={data.trade_idea} />
      ) : data.research_plan ? (
        <ResearchPlanView plan={data.research_plan} />
      ) : (
        <div className="p-4 border-2 border-gray-200 bg-gray-50 text-center">
          <div className="text-sm text-gray-500">No recommendation data available</div>
        </div>
      )}
    </div>
  );
}
