"""
Daily brief data model and generation pipeline.

Provides:
- DailyBriefContent: Structured content for daily briefs
- DailyBriefGenerator: Generates daily briefs from events and system status
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ..models import Event, Observation, DailyBrief
from .quality_gate import (
    QualityGate,
    TradeIdeaGenerator,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass
class EventSummary:
    """Summary of an event for the daily brief."""
    event_id: str
    title: str
    ticker: Optional[str]
    event_type: str
    attention_score: float
    anomaly_score: float
    catalyst_score: float
    flow_score: float
    confidence_score: float
    observation_count: int
    last_update_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "ticker": self.ticker,
            "event_type": self.event_type,
            "attention_score": self.attention_score,
            "anomaly_score": self.anomaly_score,
            "catalyst_score": self.catalyst_score,
            "flow_score": self.flow_score,
            "confidence_score": self.confidence_score,
            "observation_count": self.observation_count,
            "last_update_at": self.last_update_at.isoformat() if self.last_update_at else None,
        }


@dataclass
class TradeIdeaSummary:
    """Summary of a trade idea for the daily brief."""
    event_id: str
    ticker: Optional[str]
    direction: str
    entry_zone: str
    target: str
    stop_loss: str
    confidence_level: float
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "ticker": self.ticker,
            "direction": self.direction,
            "entry_zone": self.entry_zone,
            "target": self.target,
            "stop_loss": self.stop_loss,
            "confidence_level": self.confidence_level,
            "rationale": self.rationale,
        }


@dataclass
class ResearchIdeaSummary:
    """Summary of a research plan for the daily brief."""
    event_id: str
    ticker: Optional[str]
    questions: List[str]
    evidence_to_watch: List[str]
    current_score: float
    potential_score: float  # Estimated score if gates were to pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "ticker": self.ticker,
            "questions": self.questions,
            "evidence_to_watch": self.evidence_to_watch,
            "current_score": self.current_score,
            "potential_score": self.potential_score,
        }


@dataclass
class OpenLoop:
    """An open question or unresolved issue to track."""
    loop_id: str
    event_id: Optional[str]
    question: str
    created_at: datetime
    status: str  # "open", "in_progress", "resolved"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "event_id": self.event_id,
            "question": self.question,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
        }


@dataclass
class SourceHealthSummary:
    """Summary of a data source health status."""
    name: str
    display_name: str
    status: str  # "ok", "degraded", "error"
    record_count_24h: int
    freshness_indicator: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "status": self.status,
            "record_count_24h": self.record_count_24h,
            "freshness_indicator": self.freshness_indicator,
        }


@dataclass
class DataQualitySummary:
    """Summary of overall data quality for the brief."""
    total_sources: int
    healthy_count: int
    degraded_count: int
    error_count: int
    sources: List[SourceHealthSummary] = field(default_factory=list)
    overall_status: str = "ok"  # "ok", "degraded", "error"
    quality_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_sources": self.total_sources,
            "healthy_count": self.healthy_count,
            "degraded_count": self.degraded_count,
            "error_count": self.error_count,
            "sources": [s.to_dict() for s in self.sources],
            "overall_status": self.overall_status,
            "quality_message": self.quality_message,
        }


@dataclass
class DailyBriefContent:
    """
    Structured content for a daily brief.

    Contains:
    - executive_summary: 3 sentences summarizing top 3 events
    - top_events: Top 5 events by attention_score
    - trade_ideas: Events that passed quality gates
    - research_ideas: Events that failed gates but have high potential
    - open_loops: Unresolved questions from research plans
    - data_quality: Summary of source health
    """
    date: datetime = field(default_factory=_utcnow)
    executive_summary: str = ""
    top_events: List[EventSummary] = field(default_factory=list)
    trade_ideas: List[TradeIdeaSummary] = field(default_factory=list)
    research_ideas: List[ResearchIdeaSummary] = field(default_factory=list)
    open_loops: List[OpenLoop] = field(default_factory=list)
    data_quality: Optional[DataQualitySummary] = None
    generation_method: str = "template"  # "claude" or "template"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat() if isinstance(self.date, datetime) else str(self.date),
            "executive_summary": self.executive_summary,
            "top_events": [e.to_dict() for e in self.top_events],
            "trade_ideas": [t.to_dict() for t in self.trade_ideas],
            "research_ideas": [r.to_dict() for r in self.research_ideas],
            "open_loops": [o.to_dict() for o in self.open_loops],
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "generation_method": self.generation_method,
        }


class DailyBriefGenerator:
    """
    Generates daily briefs from events and system status.

    The generator:
    1. Retrieves top events by attention_score
    2. Evaluates quality gates for each event
    3. Separates into trade ideas (passed) and research ideas (failed but high potential)
    4. Generates executive summary from top 3 events
    5. Collects data quality summary
    """

    # Threshold for high potential research ideas (failed gates but promising)
    HIGH_POTENTIAL_THRESHOLD = 50.0

    def __init__(
        self,
        quality_gate: Optional[QualityGate] = None,
        trade_idea_generator: Optional[TradeIdeaGenerator] = None,
    ):
        """
        Initialize DailyBriefGenerator.

        Args:
            quality_gate: QualityGate instance for evaluating events.
            trade_idea_generator: TradeIdeaGenerator instance.
        """
        self.quality_gate = quality_gate or QualityGate()
        self.trade_idea_generator = trade_idea_generator or TradeIdeaGenerator(self.quality_gate)

    def generate(
        self,
        events: List[Event],
        observations_by_event: Optional[Dict[UUID, List[Observation]]] = None,
        system_status: Optional[Dict[str, Any]] = None,
    ) -> DailyBriefContent:
        """
        Generate a daily brief from events and system status.

        Args:
            events: List of active events to include in the brief.
            observations_by_event: Optional dict mapping event_id to observations.
            system_status: Optional system status dict from SystemService.

        Returns:
            DailyBriefContent with all sections populated.
        """
        observations_by_event = observations_by_event or {}
        logger.info(f"Generating daily brief for {len(events)} events")

        # Sort events by attention_score descending
        sorted_events = sorted(
            events,
            key=lambda e: e.attention_score,
            reverse=True,
        )

        # Get top 5 events for the brief
        top_events = self._extract_top_events(sorted_events[:5])

        # Evaluate quality gates and separate into trade ideas and research ideas
        trade_ideas, research_ideas, open_loops = self._evaluate_events(
            sorted_events,
            observations_by_event,
        )

        # Generate executive summary from top 3 events
        executive_summary = self._generate_executive_summary(sorted_events[:3])

        # Process data quality if provided
        data_quality = self._process_data_quality(system_status)

        return DailyBriefContent(
            date=_utcnow(),
            executive_summary=executive_summary,
            top_events=top_events,
            trade_ideas=trade_ideas,
            research_ideas=research_ideas,
            open_loops=open_loops,
            data_quality=data_quality,
            generation_method="template",  # US-013b will add LLM support
        )

    def _extract_top_events(self, events: List[Event]) -> List[EventSummary]:
        """
        Extract EventSummary objects from top events.

        Args:
            events: Top events to summarize.

        Returns:
            List of EventSummary objects.
        """
        summaries = []
        for event in events:
            summaries.append(EventSummary(
                event_id=str(event.id),
                title=event.title,
                ticker=event.primary_ticker,
                event_type=event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
                attention_score=event.attention_score,
                anomaly_score=event.anomaly_score,
                catalyst_score=event.catalyst_score,
                flow_score=event.flow_score,
                confidence_score=event.confidence_score,
                observation_count=len(event.observation_ids),
                last_update_at=event.last_update_at,
            ))
        return summaries

    def _evaluate_events(
        self,
        events: List[Event],
        observations_by_event: Dict[UUID, List[Observation]],
    ) -> tuple:
        """
        Evaluate quality gates for each event and categorize.

        Args:
            events: All events to evaluate.
            observations_by_event: Observations mapped by event ID.

        Returns:
            Tuple of (trade_ideas, research_ideas, open_loops).
        """
        trade_ideas: List[TradeIdeaSummary] = []
        research_ideas: List[ResearchIdeaSummary] = []
        open_loops: List[OpenLoop] = []

        for event in events:
            observations = observations_by_event.get(event.id, [])
            recommendation = self.trade_idea_generator.generate(event, observations)

            if recommendation.type == "trade_idea" and recommendation.trade_idea:
                # Event passed quality gates - add to trade ideas
                idea = recommendation.trade_idea
                trade_ideas.append(TradeIdeaSummary(
                    event_id=str(event.id),
                    ticker=event.primary_ticker,
                    direction=idea.direction.value if hasattr(idea.direction, 'value') else str(idea.direction),
                    entry_zone=idea.entry_zone,
                    target=idea.target,
                    stop_loss=idea.stop_loss,
                    confidence_level=idea.confidence_level,
                    rationale=idea.rationale,
                ))

            elif recommendation.type == "research_plan" and recommendation.research_plan:
                plan = recommendation.research_plan
                gate_eval = recommendation.gate_evaluation

                # Calculate potential score - what would the score be if gates passed?
                # We estimate this as the current attention score + improvement potential
                potential_score = self._estimate_potential_score(event, gate_eval)

                # Only include if the event has high potential (above threshold)
                if potential_score >= self.HIGH_POTENTIAL_THRESHOLD:
                    research_ideas.append(ResearchIdeaSummary(
                        event_id=str(event.id),
                        ticker=event.primary_ticker,
                        questions=plan.questions_to_verify[:3],  # Limit to top 3 questions
                        evidence_to_watch=plan.evidence_to_watch[:3],
                        current_score=plan.current_score,
                        potential_score=potential_score,
                    ))

                # Add research plan questions as open loops
                for q_idx, question in enumerate(plan.questions_to_verify[:2]):  # Top 2 questions
                    open_loops.append(OpenLoop(
                        loop_id=f"{event.id}-q{q_idx}",
                        event_id=str(event.id),
                        question=question,
                        created_at=_utcnow(),
                        status="open",
                    ))

        return trade_ideas, research_ideas, open_loops

    def _estimate_potential_score(
        self,
        event: Event,
        gate_eval: Optional[Any],
    ) -> float:
        """
        Estimate the potential score if quality gates were to pass.

        Uses the event's attention score as a base and adds improvement
        potential based on how close the gates are to passing.

        Args:
            event: Event to estimate potential for.
            gate_eval: Gate evaluation result.

        Returns:
            Estimated potential score (0-100).
        """
        base_score = event.attention_score

        if gate_eval is None:
            return base_score

        # Add improvement potential based on gate score
        # If gate_score is 80, we're close to passing - high potential
        # If gate_score is 20, far from passing - lower potential
        gate_score = getattr(gate_eval, 'gate_score', 50)
        improvement_factor = gate_score / 100.0 * 20  # Up to +20 points

        potential = base_score + improvement_factor
        return min(potential, 100.0)

    def _generate_executive_summary(self, top_events: List[Event]) -> str:
        """
        Generate executive summary from top 3 events.

        Limited to 3 sentences, mentioning the top 3 events.

        Args:
            top_events: Top 3 events by attention_score.

        Returns:
            Executive summary string.
        """
        if not top_events:
            return "No significant events to report today. Market conditions appear normal. Continue monitoring key positions."

        # Build summary from event data (template approach)
        # US-013b will add LLM-based generation

        sentences = []

        # First sentence: highlight the top event
        top = top_events[0]
        ticker = top.primary_ticker or "Unknown asset"
        attention = top.attention_score
        event_type = top.event_type.value if hasattr(top.event_type, 'value') else str(top.event_type)

        sentences.append(
            f"Today's top signal is {ticker} with an attention score of {attention:.0f}, "
            f"flagged as {event_type.replace('_', ' ')}."
        )

        # Second sentence: mention other notable events
        if len(top_events) >= 2:
            others = [e.primary_ticker or "Unknown" for e in top_events[1:3]]
            others_str = " and ".join(others)
            sentences.append(f"Additional notable activity detected in {others_str}.")
        else:
            sentences.append("No other significant events detected today.")

        # Third sentence: action recommendation based on top event scores
        if attention >= 70:
            sentences.append("High conviction signals suggest reviewing actionable trade ideas.")
        elif attention >= 50:
            sentences.append("Moderate signals warrant further investigation before taking positions.")
        else:
            sentences.append("Low-conviction signals today; focus on monitoring open positions.")

        return " ".join(sentences)

    def _process_data_quality(
        self,
        system_status: Optional[Dict[str, Any]],
    ) -> Optional[DataQualitySummary]:
        """
        Process system status into DataQualitySummary.

        Args:
            system_status: System status dict from SystemService.

        Returns:
            DataQualitySummary or None if no status provided.
        """
        if not system_status:
            return None

        overall = system_status.get("overall", {})
        sources_data = system_status.get("sources", [])

        # Convert sources to SourceHealthSummary objects
        sources = []
        for source in sources_data:
            sources.append(SourceHealthSummary(
                name=source.get("name", ""),
                display_name=source.get("display_name", source.get("name", "")),
                status=source.get("status", "error"),
                record_count_24h=source.get("record_count_24h", 0),
                freshness_indicator=source.get("freshness_indicator", "unknown"),
            ))

        # Determine overall status and message
        total = overall.get("total_sources", 0)
        healthy = overall.get("healthy_count", 0)
        degraded = overall.get("degraded_count", 0)
        error = overall.get("error_count", 0)

        if error > 0:
            overall_status = "error"
            quality_message = f"{error} source(s) are experiencing errors. Data may be incomplete."
        elif degraded > 0:
            overall_status = "degraded"
            quality_message = f"{degraded} source(s) have stale data. Some signals may be outdated."
        else:
            overall_status = "ok"
            quality_message = f"All {total} data sources are healthy and up to date."

        return DataQualitySummary(
            total_sources=total,
            healthy_count=healthy,
            degraded_count=degraded,
            error_count=error,
            sources=sources,
            overall_status=overall_status,
            quality_message=quality_message,
        )

    def to_daily_brief(
        self,
        content: DailyBriefContent,
        run_id: Optional[str] = None,
    ) -> DailyBrief:
        """
        Convert DailyBriefContent to a DailyBrief model for database storage.

        Args:
            content: The generated brief content.
            run_id: Optional run_id to link to run_history.

        Returns:
            DailyBrief model instance.
        """
        return DailyBrief(
            id=uuid4(),
            date=content.date,
            summary_json=content.to_dict(),
            generation_method=content.generation_method,
            created_at=_utcnow(),
            run_id=run_id,
        )
