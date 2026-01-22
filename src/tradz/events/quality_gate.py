"""
Quality gate evaluation and trade idea generation for events.

Provides:
- QualityGate: Evaluates events against configurable thresholds
- TradeIdea: Actionable trade recommendations for events passing gates
- ResearchPlan: Research questions for events failing gates
- TradeIdeaGenerator: Generates appropriate recommendations based on gate results
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)

from ..models import Event, Observation, FactTableEntry

logger = logging.getLogger(__name__)


class TradeDirection(str, Enum):
    """Direction of a trade idea."""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class TimeHorizon(str, Enum):
    """Time horizon for a trade idea."""
    INTRADAY = "intraday"
    SWING = "swing"  # 1-5 days
    POSITION = "position"  # 1-4 weeks
    INVESTMENT = "investment"  # >1 month


@dataclass
class QualityGateConfig:
    """Configuration for quality gate thresholds."""
    min_confidence: float = 70.0  # Minimum confidence score (0-100)
    min_sources: int = 2  # Minimum number of unique sources
    min_anomaly: float = 50.0  # Minimum anomaly score (0-100)
    min_catalyst: float = 40.0  # Minimum catalyst score (0-100)
    has_invalidation: bool = True  # Require invalidation condition


@dataclass
class GateResult:
    """Result of a single quality gate evaluation."""
    gate_name: str
    passed: bool
    actual_value: Any
    threshold_value: Any
    improvement_suggestion: Optional[str] = None


@dataclass
class QualityGateEvaluation:
    """
    Result of quality gate evaluation for an event.

    Determines whether the event qualifies for a TradeIdea or ResearchPlan.
    """
    passed: bool  # True if all gates pass
    gate_score: float  # Overall score 0-100
    failed_gates: List[str]  # Names of failed gates
    improvement_suggestions: List[str]  # Suggestions for improving scores
    gate_results: List[GateResult] = field(default_factory=list)

    @property
    def passed_gate_count(self) -> int:
        """Count of gates that passed."""
        return sum(1 for g in self.gate_results if g.passed)

    @property
    def total_gate_count(self) -> int:
        """Total number of gates evaluated."""
        return len(self.gate_results)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "gate_score": self.gate_score,
            "failed_gates": self.failed_gates,
            "improvement_suggestions": self.improvement_suggestions,
            "gate_results": [
                {
                    "gate_name": g.gate_name,
                    "passed": g.passed,
                    "actual_value": g.actual_value,
                    "threshold_value": g.threshold_value,
                    "improvement_suggestion": g.improvement_suggestion,
                }
                for g in self.gate_results
            ],
        }


@dataclass
class TradeIdea:
    """
    Actionable trade recommendation for events passing quality gates.

    Includes entry/exit levels, invalidation conditions, and time horizon.
    """
    id: UUID = field(default_factory=uuid4)
    event_id: Optional[UUID] = None

    # Core trade parameters
    direction: TradeDirection = TradeDirection.LONG
    entry_zone: str = ""  # Price range for entry, e.g., "$150-155"
    target: str = ""  # Target price/range, e.g., "$175"
    stop_loss: str = ""  # Stop loss level, e.g., "$140"
    invalidation: str = ""  # Condition that invalidates the thesis
    time_horizon: TimeHorizon = TimeHorizon.SWING

    # Supporting info
    confidence_level: float = 0.0  # 0-100
    rationale: str = ""  # Brief explanation
    key_catalysts: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "event_id": str(self.event_id) if self.event_id else None,
            "direction": self.direction.value,
            "entry_zone": self.entry_zone,
            "target": self.target,
            "stop_loss": self.stop_loss,
            "invalidation": self.invalidation,
            "time_horizon": self.time_horizon.value,
            "confidence_level": self.confidence_level,
            "rationale": self.rationale,
            "key_catalysts": self.key_catalysts,
            "risk_factors": self.risk_factors,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ResearchPlan:
    """
    Research plan for events that fail quality gates.

    Contains questions to verify, evidence to watch, and next check date.
    """
    id: UUID = field(default_factory=uuid4)
    event_id: Optional[UUID] = None

    # Research items
    questions_to_verify: List[str] = field(default_factory=list)
    evidence_to_watch: List[str] = field(default_factory=list)
    next_check_date: Optional[datetime] = None

    # Context
    current_score: float = 0.0  # Current gate score
    gaps_identified: List[str] = field(default_factory=list)  # What's missing

    # Metadata
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "event_id": str(self.event_id) if self.event_id else None,
            "questions_to_verify": self.questions_to_verify,
            "evidence_to_watch": self.evidence_to_watch,
            "next_check_date": self.next_check_date.isoformat() if self.next_check_date else None,
            "current_score": self.current_score,
            "gaps_identified": self.gaps_identified,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Recommendation:
    """
    Unified recommendation result containing either TradeIdea or ResearchPlan.
    """
    type: str  # "trade_idea" or "research_plan"
    trade_idea: Optional[TradeIdea] = None
    research_plan: Optional[ResearchPlan] = None
    gate_evaluation: Optional[QualityGateEvaluation] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "trade_idea": self.trade_idea.to_dict() if self.trade_idea else None,
            "research_plan": self.research_plan.to_dict() if self.research_plan else None,
            "gate_evaluation": self.gate_evaluation.to_dict() if self.gate_evaluation else None,
        }


class QualityGate:
    """
    Evaluates events against configurable quality gate thresholds.

    Gates:
    - min_confidence (70): Minimum confidence score
    - min_sources (2): Minimum number of unique data sources
    - min_anomaly (50): Minimum anomaly score
    - min_catalyst (40): Minimum catalyst score
    - has_invalidation (True): Whether invalidation condition can be defined
    """

    def __init__(self, config: Optional[QualityGateConfig] = None):
        """
        Initialize QualityGate with configuration.

        Args:
            config: Gate configuration. Uses defaults if not provided.
        """
        self.config = config or QualityGateConfig()

    def evaluate(
        self,
        event: Event,
        observations: Optional[List[Observation]] = None,
    ) -> QualityGateEvaluation:
        """
        Evaluate an event against all quality gates.

        Args:
            event: Event to evaluate.
            observations: Optional list of observations for source counting.
                         Uses event.observation_ids count if not provided.

        Returns:
            QualityGateEvaluation with pass/fail status and details.
        """
        gate_results: List[GateResult] = []
        failed_gates: List[str] = []
        improvement_suggestions: List[str] = []

        # Gate 1: Minimum confidence score
        confidence_passed = event.confidence_score >= self.config.min_confidence
        gate_results.append(GateResult(
            gate_name="min_confidence",
            passed=confidence_passed,
            actual_value=event.confidence_score,
            threshold_value=self.config.min_confidence,
            improvement_suggestion=(
                f"Confidence score {event.confidence_score:.0f} is below {self.config.min_confidence:.0f}. "
                "Add more corroborating evidence from diverse sources."
            ) if not confidence_passed else None,
        ))
        if not confidence_passed:
            failed_gates.append("min_confidence")
            improvement_suggestions.append(
                f"Increase confidence by adding more verified data sources (current: {event.confidence_score:.0f}, need: {self.config.min_confidence:.0f})"
            )

        # Gate 2: Minimum number of sources
        source_count = self._count_unique_sources(event, observations)
        sources_passed = source_count >= self.config.min_sources
        gate_results.append(GateResult(
            gate_name="min_sources",
            passed=sources_passed,
            actual_value=source_count,
            threshold_value=self.config.min_sources,
            improvement_suggestion=(
                f"Only {source_count} data source(s). Need at least {self.config.min_sources} for validation."
            ) if not sources_passed else None,
        ))
        if not sources_passed:
            failed_gates.append("min_sources")
            improvement_suggestions.append(
                f"Add data from {self.config.min_sources - source_count} more independent source(s)"
            )

        # Gate 3: Minimum anomaly score
        anomaly_passed = event.anomaly_score >= self.config.min_anomaly
        gate_results.append(GateResult(
            gate_name="min_anomaly",
            passed=anomaly_passed,
            actual_value=event.anomaly_score,
            threshold_value=self.config.min_anomaly,
            improvement_suggestion=(
                f"Anomaly score {event.anomaly_score:.0f} is below {self.config.min_anomaly:.0f}. "
                "Look for more significant price/volume deviations."
            ) if not anomaly_passed else None,
        ))
        if not anomaly_passed:
            failed_gates.append("min_anomaly")
            improvement_suggestions.append(
                f"Monitor for larger price/volume deviations (current anomaly: {event.anomaly_score:.0f})"
            )

        # Gate 4: Minimum catalyst score
        catalyst_passed = event.catalyst_score >= self.config.min_catalyst
        gate_results.append(GateResult(
            gate_name="min_catalyst",
            passed=catalyst_passed,
            actual_value=event.catalyst_score,
            threshold_value=self.config.min_catalyst,
            improvement_suggestion=(
                f"Catalyst score {event.catalyst_score:.0f} is below {self.config.min_catalyst:.0f}. "
                "Wait for news, SEC filings, or prediction market signals."
            ) if not catalyst_passed else None,
        ))
        if not catalyst_passed:
            failed_gates.append("min_catalyst")
            improvement_suggestions.append(
                f"Wait for catalyst news or filings (current catalyst: {event.catalyst_score:.0f})"
            )

        # Gate 5: Invalidation condition requirement
        # This is evaluated during trade idea generation, not here
        # We assume invalidation is possible if other conditions are met
        has_invalidation = self._can_define_invalidation(event, observations)
        invalidation_passed = (not self.config.has_invalidation) or has_invalidation
        gate_results.append(GateResult(
            gate_name="has_invalidation",
            passed=invalidation_passed,
            actual_value=has_invalidation,
            threshold_value=self.config.has_invalidation,
            improvement_suggestion=(
                "Cannot define clear invalidation condition. Need price levels or specific events to watch."
            ) if not invalidation_passed else None,
        ))
        if not invalidation_passed:
            failed_gates.append("has_invalidation")
            improvement_suggestions.append(
                "Identify specific price levels or events that would invalidate the thesis"
            )

        # Calculate overall gate score (0-100)
        # Weight: confidence (30%), sources (20%), anomaly (20%), catalyst (20%), invalidation (10%)
        gate_score = self._calculate_gate_score(
            event, source_count, has_invalidation
        )

        # All gates must pass for overall pass
        all_passed = len(failed_gates) == 0

        return QualityGateEvaluation(
            passed=all_passed,
            gate_score=gate_score,
            failed_gates=failed_gates,
            improvement_suggestions=improvement_suggestions,
            gate_results=gate_results,
        )

    def _count_unique_sources(
        self,
        event: Event,
        observations: Optional[List[Observation]],
    ) -> int:
        """
        Count unique data sources for an event.

        Args:
            event: Event to count sources for.
            observations: List of observations if available.

        Returns:
            Number of unique source types.
        """
        if observations:
            return len(set(obs.source for obs in observations))

        # Estimate from event properties if observations not provided
        # Confidence score above 60 typically means 2+ sources
        # Above 75 typically means 3+ sources
        if event.confidence_score >= 75:
            return 3
        elif event.confidence_score >= 60:
            return 2
        elif len(event.observation_ids) > 0:
            return 1
        return 0

    def _can_define_invalidation(
        self,
        event: Event,
        observations: Optional[List[Observation]],
    ) -> bool:
        """
        Check if an invalidation condition can be defined for this event.

        Invalidation requires:
        - Price data (for stop-loss levels)
        - Or specific catalyst events that can be monitored

        Args:
            event: Event to check.
            observations: List of observations if available.

        Returns:
            True if invalidation can be defined.
        """
        # If we have anomaly score > 30, we likely have price data
        if event.anomaly_score > 30:
            return True

        # If we have catalyst score > 30, we have events to monitor
        if event.catalyst_score > 30:
            return True

        # Check observations for price/event data
        if observations:
            for obs in observations:
                payload = obs.payload or {}
                if "price" in payload or "close" in payload:
                    return True
                if "form" in payload or "headline" in payload:
                    return True

        return False

    def _calculate_gate_score(
        self,
        event: Event,
        source_count: int,
        has_invalidation: bool,
    ) -> float:
        """
        Calculate overall gate score (0-100).

        Weights:
        - Confidence: 30%
        - Sources: 20%
        - Anomaly: 20%
        - Catalyst: 20%
        - Invalidation: 10%

        Args:
            event: Event being evaluated.
            source_count: Number of unique sources.
            has_invalidation: Whether invalidation can be defined.

        Returns:
            Gate score 0-100.
        """
        # Normalize each component to 0-1
        confidence_norm = min(event.confidence_score / self.config.min_confidence, 1.0)
        sources_norm = min(source_count / self.config.min_sources, 1.0)
        anomaly_norm = min(event.anomaly_score / self.config.min_anomaly, 1.0)
        catalyst_norm = min(event.catalyst_score / self.config.min_catalyst, 1.0)
        invalidation_norm = 1.0 if has_invalidation or not self.config.has_invalidation else 0.0

        # Weighted average
        score = (
            confidence_norm * 0.30 +
            sources_norm * 0.20 +
            anomaly_norm * 0.20 +
            catalyst_norm * 0.20 +
            invalidation_norm * 0.10
        ) * 100

        return min(max(score, 0), 100)


class TradeIdeaGenerator:
    """
    Generates TradeIdea or ResearchPlan based on quality gate evaluation.

    If all gates pass, generates a TradeIdea with entry/exit levels.
    If gates fail, generates a ResearchPlan with questions to verify.
    """

    def __init__(self, quality_gate: Optional[QualityGate] = None):
        """
        Initialize TradeIdeaGenerator.

        Args:
            quality_gate: QualityGate instance. Creates default if not provided.
        """
        self.quality_gate = quality_gate or QualityGate()

    def generate(
        self,
        event: Event,
        observations: Optional[List[Observation]] = None,
        facts: Optional[List[FactTableEntry]] = None,
    ) -> Recommendation:
        """
        Generate recommendation for an event.

        Evaluates quality gates and generates either:
        - TradeIdea if all gates pass
        - ResearchPlan if any gates fail

        Args:
            event: Event to generate recommendation for.
            observations: Optional observations for the event.
            facts: Optional extracted facts for price/detail info.

        Returns:
            Recommendation containing either TradeIdea or ResearchPlan.
        """
        # Evaluate quality gates
        evaluation = self.quality_gate.evaluate(event, observations)

        if evaluation.passed:
            trade_idea = self._generate_trade_idea(event, observations, facts, evaluation)
            return Recommendation(
                type="trade_idea",
                trade_idea=trade_idea,
                gate_evaluation=evaluation,
            )
        else:
            research_plan = self._generate_research_plan(event, observations, evaluation)
            return Recommendation(
                type="research_plan",
                research_plan=research_plan,
                gate_evaluation=evaluation,
            )

    def _generate_trade_idea(
        self,
        event: Event,
        observations: Optional[List[Observation]],
        facts: Optional[List[FactTableEntry]],
        evaluation: QualityGateEvaluation,
    ) -> TradeIdea:
        """
        Generate a TradeIdea for an event that passed quality gates.

        Args:
            event: Event to generate trade idea for.
            observations: Observations for price data.
            facts: Extracted facts for additional details.
            evaluation: Gate evaluation results.

        Returns:
            TradeIdea with entry/exit parameters.
        """
        # Determine direction from event type and scores
        direction = self._determine_direction(event, observations)

        # Extract price levels from observations/facts
        price_info = self._extract_price_info(observations, facts)
        current_price = price_info.get("current_price")

        # Calculate entry zone, target, and stop loss
        entry_zone, target, stop_loss = self._calculate_levels(
            current_price, direction, event
        )

        # Determine time horizon from event type
        time_horizon = self._determine_time_horizon(event)

        # Generate invalidation condition
        invalidation = self._generate_invalidation(event, observations, direction, stop_loss)

        # Extract catalysts and risks
        key_catalysts = self._extract_catalysts(event, observations)
        risk_factors = self._extract_risks(event, observations)

        # Build rationale
        rationale = self._build_rationale(event, direction, key_catalysts)

        return TradeIdea(
            event_id=event.id,
            direction=direction,
            entry_zone=entry_zone,
            target=target,
            stop_loss=stop_loss,
            invalidation=invalidation,
            time_horizon=time_horizon,
            confidence_level=evaluation.gate_score,
            rationale=rationale,
            key_catalysts=key_catalysts,
            risk_factors=risk_factors,
        )

    def _generate_research_plan(
        self,
        event: Event,
        _observations: Optional[List[Observation]],
        evaluation: QualityGateEvaluation,
    ) -> ResearchPlan:
        """
        Generate a ResearchPlan for an event that failed quality gates.

        Args:
            event: Event to generate research plan for.
            observations: Observations for context.
            evaluation: Gate evaluation results.

        Returns:
            ResearchPlan with questions and evidence to watch.
        """
        questions_to_verify: List[str] = []
        evidence_to_watch: List[str] = []
        gaps_identified: List[str] = []

        # Generate questions based on failed gates
        for gate_result in evaluation.gate_results:
            if not gate_result.passed:
                gaps_identified.append(f"{gate_result.gate_name}: {gate_result.improvement_suggestion}")

                if gate_result.gate_name == "min_confidence":
                    questions_to_verify.append("Is there additional corroborating evidence from independent sources?")
                    evidence_to_watch.append("SEC filings, institutional holdings, or news confirmations")

                elif gate_result.gate_name == "min_sources":
                    questions_to_verify.append("Can we find data from additional independent sources?")
                    evidence_to_watch.append("Congress trades, 13F filings, or Polymarket sentiment")

                elif gate_result.gate_name == "min_anomaly":
                    questions_to_verify.append("Is the price/volume behavior truly anomalous?")
                    evidence_to_watch.append("Unusual volume spikes, gap moves, or volatility expansion")

                elif gate_result.gate_name == "min_catalyst":
                    questions_to_verify.append("What catalyst could drive the expected move?")
                    evidence_to_watch.append("Upcoming earnings, FDA decisions, or regulatory announcements")

                elif gate_result.gate_name == "has_invalidation":
                    questions_to_verify.append("What price level or event would invalidate this thesis?")
                    evidence_to_watch.append("Key support/resistance levels or news developments")

        # Add event-specific questions
        ticker = event.primary_ticker or "the asset"
        questions_to_verify.append(f"What is the base case scenario for {ticker}?")
        questions_to_verify.append(f"What are the key risks to monitor for {ticker}?")

        # Set next check date (default to 24 hours)
        next_check_date = _utcnow() + timedelta(hours=24)

        return ResearchPlan(
            event_id=event.id,
            questions_to_verify=questions_to_verify,
            evidence_to_watch=evidence_to_watch,
            next_check_date=next_check_date,
            current_score=evaluation.gate_score,
            gaps_identified=gaps_identified,
        )

    def _determine_direction(
        self,
        event: Event,
        observations: Optional[List[Observation]],
    ) -> TradeDirection:
        """
        Determine trade direction from event data.

        Args:
            event: Event to analyze.
            observations: Observations for additional context.

        Returns:
            TradeDirection (LONG, SHORT, or NEUTRAL).
        """
        # Check flow score - high flow often indicates direction
        if event.flow_score > 65:
            # Check if flow is positive (buys) or negative (sells)
            if observations:
                buy_signals = 0
                sell_signals = 0
                for obs in observations:
                    payload = obs.payload or {}
                    tx_type = str(payload.get("type", "")).lower()
                    position_change = payload.get("position_change_pct", 0)

                    if "purchase" in tx_type or "buy" in tx_type or position_change > 0:
                        buy_signals += 1
                    elif "sale" in tx_type or "sell" in tx_type or position_change < 0:
                        sell_signals += 1

                if buy_signals > sell_signals:
                    return TradeDirection.LONG
                elif sell_signals > buy_signals:
                    return TradeDirection.SHORT

        # Check anomaly - strong positive price moves suggest long
        if event.anomaly_score > 60:
            if observations:
                for obs in observations:
                    payload = obs.payload or {}
                    price_change = payload.get("price_change_pct", payload.get("day_return", 0))
                    if price_change > 3:
                        return TradeDirection.LONG
                    elif price_change < -3:
                        return TradeDirection.SHORT

        # Default to long for catalyst events (unless clearly negative)
        if event.catalyst_score > 50:
            return TradeDirection.LONG

        return TradeDirection.NEUTRAL

    def _extract_price_info(
        self,
        observations: Optional[List[Observation]],
        facts: Optional[List[FactTableEntry]],
    ) -> Dict[str, Any]:
        """
        Extract price information from observations and facts.

        Args:
            observations: Observations with price data.
            facts: Extracted facts with price data.

        Returns:
            Dictionary with price info (current_price, high, low, etc.).
        """
        price_info: Dict[str, Any] = {}

        # Check observations for price data
        if observations:
            for obs in observations:
                payload = obs.payload or {}
                if "price" in payload:
                    price_info["current_price"] = payload["price"]
                elif "close" in payload:
                    price_info["current_price"] = payload["close"]

                if "high" in payload:
                    price_info["high"] = payload["high"]
                if "low" in payload:
                    price_info["low"] = payload["low"]
                if "52w_high" in payload:
                    price_info["52w_high"] = payload["52w_high"]
                if "52w_low" in payload:
                    price_info["52w_low"] = payload["52w_low"]

        # Check facts for price data
        if facts:
            for fact in facts:
                if fact.fact_type == "price" and fact.value is not None:
                    price_info["current_price"] = fact.value
                elif fact.fact_type == "price_change" and fact.value is not None:
                    price_info["price_change_pct"] = fact.value

        return price_info

    def _calculate_levels(
        self,
        current_price: Optional[float],
        direction: TradeDirection,
        event: Event,
    ) -> tuple:
        """
        Calculate entry zone, target, and stop loss levels.

        Args:
            current_price: Current asset price if available.
            direction: Trade direction.
            event: Event for context.

        Returns:
            Tuple of (entry_zone, target, stop_loss) as strings.
        """
        if current_price is None:
            # No price data - use generic levels
            if direction == TradeDirection.LONG:
                return ("Current level", "+5-10% from entry", "-3-5% from entry")
            elif direction == TradeDirection.SHORT:
                return ("Current level", "-5-10% from entry", "+3-5% from entry")
            else:
                return ("Near current level", "Range-bound", "Outside range")

        # Calculate levels based on confidence and direction
        confidence_factor = event.confidence_score / 100.0

        if direction == TradeDirection.LONG:
            # Entry zone: current price -2% to current price
            entry_low = current_price * 0.98
            entry_high = current_price
            entry_zone = f"${entry_low:.2f}-${entry_high:.2f}"

            # Target: 5-15% upside based on confidence
            target_pct = 0.05 + (confidence_factor * 0.10)
            target_price = current_price * (1 + target_pct)
            target = f"${target_price:.2f}"

            # Stop loss: 3-7% downside
            stop_pct = 0.03 + ((1 - confidence_factor) * 0.04)
            stop_price = current_price * (1 - stop_pct)
            stop_loss = f"${stop_price:.2f}"

        elif direction == TradeDirection.SHORT:
            # Entry zone: current price to current price +2%
            entry_low = current_price
            entry_high = current_price * 1.02
            entry_zone = f"${entry_low:.2f}-${entry_high:.2f}"

            # Target: 5-15% downside
            target_pct = 0.05 + (confidence_factor * 0.10)
            target_price = current_price * (1 - target_pct)
            target = f"${target_price:.2f}"

            # Stop loss: 3-7% upside
            stop_pct = 0.03 + ((1 - confidence_factor) * 0.04)
            stop_price = current_price * (1 + stop_pct)
            stop_loss = f"${stop_price:.2f}"

        else:
            # Neutral - range trade
            entry_zone = f"${current_price:.2f}"
            target = f"${current_price * 1.03:.2f}-${current_price * 0.97:.2f}"
            stop_loss = "Break of range"

        return (entry_zone, target, stop_loss)

    def _determine_time_horizon(self, event: Event) -> TimeHorizon:
        """
        Determine appropriate time horizon based on event type.

        Args:
            event: Event to analyze.

        Returns:
            TimeHorizon enum value.
        """
        from ..models import EventType

        # Filing-driven events often have longer horizons
        if event.event_type in [EventType.CATALYST_FILING, EventType.FLOW_13F]:
            return TimeHorizon.POSITION

        # News-driven events are typically shorter
        if event.event_type in [EventType.CATALYST_NEWS, EventType.MARKET_ANOMALY]:
            return TimeHorizon.SWING

        # Congress trades often have medium-term implications
        if event.event_type == EventType.FLOW_CONGRESS:
            return TimeHorizon.SWING

        # Prediction shifts depend on event timing
        if event.event_type == EventType.PREDICTION_SHIFT:
            return TimeHorizon.SWING

        # Default to swing trade
        return TimeHorizon.SWING

    def _generate_invalidation(
        self,
        event: Event,
        _observations: Optional[List[Observation]],
        direction: TradeDirection,
        stop_loss: str,
    ) -> str:
        """
        Generate invalidation condition description.

        Args:
            event: Event for context.
            observations: Observations for additional context.
            direction: Trade direction.
            stop_loss: Stop loss level.

        Returns:
            Invalidation condition string.
        """
        conditions: List[str] = []

        # Price-based invalidation
        if stop_loss and stop_loss != "Break of range":
            if direction == TradeDirection.LONG:
                conditions.append(f"Price closes below {stop_loss}")
            elif direction == TradeDirection.SHORT:
                conditions.append(f"Price closes above {stop_loss}")

        # Event-based invalidation
        from ..models import EventType

        if event.event_type == EventType.CATALYST_NEWS:
            conditions.append("Material negative news contradicting thesis")
        elif event.event_type == EventType.CATALYST_FILING:
            conditions.append("Subsequent filing with contradictory information")
        elif event.event_type == EventType.FLOW_CONGRESS:
            conditions.append("Same member reverses position")
        elif event.event_type == EventType.FLOW_13F:
            conditions.append("Major fund significantly reduces position")

        # Default invalidation
        if not conditions:
            conditions.append(f"Price moves against position by >7%")

        return " OR ".join(conditions)

    def _extract_catalysts(
        self,
        event: Event,
        observations: Optional[List[Observation]],
    ) -> List[str]:
        """
        Extract key catalysts from event and observations.

        Args:
            event: Event for context.
            observations: Observations for details.

        Returns:
            List of catalyst descriptions.
        """
        catalysts: List[str] = []

        # Add event-type based catalysts
        from ..models import EventType

        if event.event_type == EventType.CATALYST_NEWS:
            catalysts.append("News-driven momentum")
        elif event.event_type == EventType.CATALYST_FILING:
            catalysts.append("SEC filing disclosure")
        elif event.event_type == EventType.FLOW_CONGRESS:
            catalysts.append("Congressional trading activity")
        elif event.event_type == EventType.FLOW_13F:
            catalysts.append("Institutional position change")
        elif event.event_type == EventType.MARKET_ANOMALY:
            catalysts.append("Unusual price/volume activity")
        elif event.event_type == EventType.PREDICTION_SHIFT:
            catalysts.append("Prediction market sentiment shift")

        # Extract from observations
        if observations:
            for obs in observations:
                title = obs.title
                if title and len(title) < 100:
                    catalysts.append(title)

        # Limit to top 5
        return catalysts[:5]

    def _extract_risks(
        self,
        event: Event,
        _observations: Optional[List[Observation]],
    ) -> List[str]:
        """
        Extract risk factors from event and observations.

        Args:
            event: Event for context.
            observations: Observations for details.

        Returns:
            List of risk descriptions.
        """
        risks: List[str] = []

        # Standard risks
        risks.append("Overall market conditions could override thesis")

        # Confidence-based risks
        if event.confidence_score < 70:
            risks.append("Moderate confidence - position size appropriately")

        # Source diversity risk
        if event.confidence_score < 60:
            risks.append("Limited source corroboration")

        # Timing risks
        risks.append("Execution timing may impact entry levels")

        return risks[:5]

    def _build_rationale(
        self,
        event: Event,
        direction: TradeDirection,
        catalysts: List[str],
    ) -> str:
        """
        Build trade rationale description.

        Args:
            event: Event for context.
            direction: Trade direction.
            catalysts: List of catalysts.

        Returns:
            Rationale string.
        """
        ticker = event.primary_ticker or "Asset"
        direction_word = "bullish" if direction == TradeDirection.LONG else (
            "bearish" if direction == TradeDirection.SHORT else "neutral"
        )

        catalyst_summary = catalysts[0] if catalysts else "multiple signals"

        rationale = (
            f"{ticker} shows {direction_word} setup based on {catalyst_summary.lower()}. "
            f"Attention score of {event.attention_score:.0f} with confidence at {event.confidence_score:.0f}%."
        )

        return rationale
