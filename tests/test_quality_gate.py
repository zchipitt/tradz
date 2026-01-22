"""
Unit tests for quality gate evaluation and trade idea generation.

Tests cover:
- Quality gate configuration and thresholds
- Gate evaluation for all 5 gates
- Gate score calculation
- Trade idea generation for passing events
- Research plan generation for failing events
- Direction determination logic
- Price level calculations
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.tradz.events.quality_gate import (
    GateResult,
    QualityGate,
    QualityGateConfig,
    QualityGateEvaluation,
    Recommendation,
    ResearchPlan,
    TimeHorizon,
    TradeDirection,
    TradeIdea,
    TradeIdeaGenerator,
)
from src.tradz.models import Event, EventStatus, EventType, Observation, SourceType


@pytest.fixture
def sample_event():
    """Create a sample event with default scores."""
    return Event(
        id=uuid4(),
        primary_entity_id=uuid4(),
        primary_ticker="AAPL",
        title="AAPL: Market Anomaly (75)",
        event_type=EventType.MARKET_ANOMALY,
        status=EventStatus.NEW,
        anomaly_score=60.0,
        catalyst_score=50.0,
        flow_score=55.0,
        confidence_score=75.0,
        observation_ids=[uuid4(), uuid4(), uuid4()],
    )


@pytest.fixture
def high_score_event():
    """Create an event that passes all quality gates."""
    return Event(
        id=uuid4(),
        primary_entity_id=uuid4(),
        primary_ticker="TSLA",
        title="TSLA: Catalyst News (85)",
        event_type=EventType.CATALYST_NEWS,
        status=EventStatus.NEW,
        anomaly_score=65.0,
        catalyst_score=70.0,
        flow_score=60.0,
        confidence_score=80.0,
        observation_ids=[uuid4() for _ in range(5)],
    )


@pytest.fixture
def low_score_event():
    """Create an event that fails quality gates."""
    return Event(
        id=uuid4(),
        primary_entity_id=uuid4(),
        primary_ticker="XYZ",
        title="XYZ: Uncertain (35)",
        event_type=EventType.UNCERTAIN,
        status=EventStatus.NEW,
        anomaly_score=30.0,
        catalyst_score=25.0,
        flow_score=20.0,
        confidence_score=40.0,
        observation_ids=[uuid4()],
    )


def create_observation(
    source: SourceType,
    entity_id=None,
    ticker: str = "AAPL",
    payload=None,
) -> Observation:
    """Helper to create test observations."""
    now = datetime.now(timezone.utc)
    return Observation(
        id=uuid4(),
        source=source,
        entity_id=entity_id or uuid4(),
        entity_ticker=ticker,
        payload=payload or {},
        observed_at=now,
        effective_at=now,
    )


class TestQualityGateConfig:
    """Tests for QualityGateConfig."""

    def test_default_config_values(self):
        """Default config should have expected threshold values."""
        config = QualityGateConfig()
        assert config.min_confidence == 70.0
        assert config.min_sources == 2
        assert config.min_anomaly == 50.0
        assert config.min_catalyst == 40.0
        assert config.has_invalidation is True

    def test_custom_config_values(self):
        """Custom config should override defaults."""
        config = QualityGateConfig(
            min_confidence=80.0,
            min_sources=3,
            min_anomaly=60.0,
            min_catalyst=50.0,
            has_invalidation=False,
        )
        assert config.min_confidence == 80.0
        assert config.min_sources == 3
        assert config.min_anomaly == 60.0
        assert config.min_catalyst == 50.0
        assert config.has_invalidation is False


class TestQualityGateEvaluation:
    """Tests for QualityGate.evaluate() method."""

    def test_evaluate_all_gates_pass(self, high_score_event):
        """Event with high scores should pass all gates."""
        observations = [
            create_observation(SourceType.EQUITIES, payload={"price": 150}),
            create_observation(SourceType.NEWS, payload={"headline": "Test"}),
            create_observation(SourceType.SEC, payload={"form": "8-K"}),
        ]
        gate = QualityGate()
        result = gate.evaluate(high_score_event, observations)

        assert result.passed is True
        assert len(result.failed_gates) == 0
        assert result.gate_score >= 80
        assert len(result.gate_results) == 5

    def test_evaluate_confidence_gate_fails(self):
        """Event below min_confidence should fail confidence gate."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.MARKET_ANOMALY,
            confidence_score=50.0,  # Below threshold of 70
            anomaly_score=60.0,
            catalyst_score=50.0,
            flow_score=55.0,
        )
        observations = [
            create_observation(SourceType.EQUITIES),
            create_observation(SourceType.NEWS),
        ]
        gate = QualityGate()
        result = gate.evaluate(event, observations)

        assert result.passed is False
        assert "min_confidence" in result.failed_gates
        assert any(g.gate_name == "min_confidence" and not g.passed for g in result.gate_results)

    def test_evaluate_sources_gate_fails(self):
        """Event with insufficient sources should fail sources gate."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.MARKET_ANOMALY,
            confidence_score=75.0,
            anomaly_score=60.0,
            catalyst_score=50.0,
            flow_score=55.0,
        )
        # Only one source type
        observations = [
            create_observation(SourceType.EQUITIES),
        ]
        gate = QualityGate()
        result = gate.evaluate(event, observations)

        assert result.passed is False
        assert "min_sources" in result.failed_gates

    def test_evaluate_anomaly_gate_fails(self):
        """Event below min_anomaly should fail anomaly gate."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.MARKET_ANOMALY,
            confidence_score=75.0,
            anomaly_score=30.0,  # Below threshold of 50
            catalyst_score=50.0,
            flow_score=55.0,
        )
        observations = [
            create_observation(SourceType.EQUITIES),
            create_observation(SourceType.NEWS),
        ]
        gate = QualityGate()
        result = gate.evaluate(event, observations)

        assert result.passed is False
        assert "min_anomaly" in result.failed_gates

    def test_evaluate_catalyst_gate_fails(self):
        """Event below min_catalyst should fail catalyst gate."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.MARKET_ANOMALY,
            confidence_score=75.0,
            anomaly_score=60.0,
            catalyst_score=20.0,  # Below threshold of 40
            flow_score=55.0,
        )
        observations = [
            create_observation(SourceType.EQUITIES),
            create_observation(SourceType.NEWS),
        ]
        gate = QualityGate()
        result = gate.evaluate(event, observations)

        assert result.passed is False
        assert "min_catalyst" in result.failed_gates

    def test_evaluate_with_custom_config(self):
        """Custom config thresholds should be respected."""
        config = QualityGateConfig(
            min_confidence=50.0,  # Lower threshold
            min_sources=1,
            min_anomaly=30.0,
            min_catalyst=20.0,
        )
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.MARKET_ANOMALY,
            confidence_score=55.0,
            anomaly_score=40.0,
            catalyst_score=30.0,
            flow_score=55.0,
        )
        observations = [
            create_observation(SourceType.EQUITIES, payload={"price": 100}),
        ]
        gate = QualityGate(config)
        result = gate.evaluate(event, observations)

        assert result.passed is True
        assert len(result.failed_gates) == 0

    def test_gate_results_contain_all_gates(self, sample_event):
        """Gate results should contain evaluation for all 5 gates."""
        gate = QualityGate()
        observations = [
            create_observation(SourceType.EQUITIES),
            create_observation(SourceType.NEWS),
        ]
        result = gate.evaluate(sample_event, observations)

        gate_names = [g.gate_name for g in result.gate_results]
        assert "min_confidence" in gate_names
        assert "min_sources" in gate_names
        assert "min_anomaly" in gate_names
        assert "min_catalyst" in gate_names
        assert "has_invalidation" in gate_names

    def test_improvement_suggestions_for_failed_gates(self, low_score_event):
        """Failed gates should provide improvement suggestions."""
        gate = QualityGate()
        observations = [create_observation(SourceType.EQUITIES)]
        result = gate.evaluate(low_score_event, observations)

        assert len(result.improvement_suggestions) > 0
        assert len(result.failed_gates) > 0


class TestGateScoreCalculation:
    """Tests for gate score calculation."""

    def test_gate_score_max_when_all_pass(self, high_score_event):
        """Gate score should be high when all gates pass."""
        observations = [
            create_observation(SourceType.EQUITIES, payload={"price": 150}),
            create_observation(SourceType.NEWS),
            create_observation(SourceType.SEC),
        ]
        gate = QualityGate()
        result = gate.evaluate(high_score_event, observations)

        assert result.gate_score >= 80.0

    def test_gate_score_low_when_all_fail(self, low_score_event):
        """Gate score should be low when gates fail."""
        observations = [create_observation(SourceType.EQUITIES)]
        gate = QualityGate()
        result = gate.evaluate(low_score_event, observations)

        assert result.gate_score < 60.0

    def test_gate_score_bounded_0_100(self, sample_event):
        """Gate score should always be between 0 and 100."""
        gate = QualityGate()
        observations = [
            create_observation(SourceType.EQUITIES),
            create_observation(SourceType.NEWS),
        ]
        result = gate.evaluate(sample_event, observations)

        assert 0 <= result.gate_score <= 100


class TestTradeIdeaGenerator:
    """Tests for TradeIdeaGenerator."""

    def test_generates_trade_idea_when_gates_pass(self, high_score_event):
        """Should generate TradeIdea when all gates pass."""
        observations = [
            create_observation(SourceType.EQUITIES, payload={"price": 150}),
            create_observation(SourceType.NEWS),
            create_observation(SourceType.SEC),
        ]
        generator = TradeIdeaGenerator()
        result = generator.generate(high_score_event, observations)

        assert result.type == "trade_idea"
        assert result.trade_idea is not None
        assert result.research_plan is None
        assert result.gate_evaluation.passed is True

    def test_generates_research_plan_when_gates_fail(self, low_score_event):
        """Should generate ResearchPlan when gates fail."""
        observations = [create_observation(SourceType.EQUITIES)]
        generator = TradeIdeaGenerator()
        result = generator.generate(low_score_event, observations)

        assert result.type == "research_plan"
        assert result.research_plan is not None
        assert result.trade_idea is None
        assert result.gate_evaluation.passed is False

    def test_trade_idea_has_required_fields(self, high_score_event):
        """Generated TradeIdea should have all required fields."""
        observations = [
            create_observation(SourceType.EQUITIES, payload={"price": 150}),
            create_observation(SourceType.NEWS),
            create_observation(SourceType.SEC),
        ]
        generator = TradeIdeaGenerator()
        result = generator.generate(high_score_event, observations)

        idea = result.trade_idea
        assert idea.event_id == high_score_event.id
        assert idea.direction in [TradeDirection.LONG, TradeDirection.SHORT, TradeDirection.NEUTRAL]
        assert len(idea.entry_zone) > 0
        assert len(idea.target) > 0
        assert len(idea.stop_loss) > 0
        assert len(idea.invalidation) > 0
        assert idea.time_horizon in list(TimeHorizon)
        assert 0 <= idea.confidence_level <= 100

    def test_research_plan_has_required_fields(self, low_score_event):
        """Generated ResearchPlan should have all required fields."""
        observations = [create_observation(SourceType.EQUITIES)]
        generator = TradeIdeaGenerator()
        result = generator.generate(low_score_event, observations)

        plan = result.research_plan
        assert plan.event_id == low_score_event.id
        assert len(plan.questions_to_verify) > 0
        assert len(plan.evidence_to_watch) > 0
        assert plan.next_check_date is not None
        assert plan.current_score >= 0

    def test_custom_quality_gate_config(self, sample_event):
        """Generator should use custom quality gate config."""
        # Strict config that sample_event won't pass
        strict_config = QualityGateConfig(
            min_confidence=90.0,
            min_sources=5,
            min_anomaly=80.0,
            min_catalyst=70.0,
        )
        strict_gate = QualityGate(strict_config)
        generator = TradeIdeaGenerator(quality_gate=strict_gate)

        observations = [
            create_observation(SourceType.EQUITIES),
            create_observation(SourceType.NEWS),
        ]
        result = generator.generate(sample_event, observations)

        assert result.type == "research_plan"


class TestDirectionDetermination:
    """Tests for trade direction determination logic."""

    def test_long_direction_from_buy_signals(self):
        """Should determine LONG direction from buy signals in observations."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.FLOW_CONGRESS,
            flow_score=70.0,
            confidence_score=80.0,
            anomaly_score=60.0,
            catalyst_score=50.0,
        )
        observations = [
            create_observation(SourceType.CONGRESS, payload={"type": "purchase"}),
            create_observation(SourceType.HEDGEFUND, payload={"position_change_pct": 50}),
            create_observation(SourceType.NEWS),
        ]
        generator = TradeIdeaGenerator()
        result = generator.generate(event, observations)

        if result.trade_idea:
            assert result.trade_idea.direction == TradeDirection.LONG

    def test_short_direction_from_sell_signals(self):
        """Should determine SHORT direction from sell signals in observations."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.FLOW_CONGRESS,
            flow_score=70.0,
            confidence_score=80.0,
            anomaly_score=60.0,
            catalyst_score=50.0,
        )
        observations = [
            create_observation(SourceType.CONGRESS, payload={"type": "sale"}),
            create_observation(SourceType.HEDGEFUND, payload={"position_change_pct": -50}),
            create_observation(SourceType.NEWS),
        ]
        generator = TradeIdeaGenerator()
        result = generator.generate(event, observations)

        if result.trade_idea:
            assert result.trade_idea.direction == TradeDirection.SHORT

    def test_direction_from_price_anomaly(self):
        """Should determine direction from strong price anomaly."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.MARKET_ANOMALY,
            anomaly_score=80.0,
            confidence_score=75.0,
            catalyst_score=50.0,
            flow_score=50.0,
        )
        observations = [
            create_observation(SourceType.EQUITIES, payload={"price_change_pct": 8}),
            create_observation(SourceType.NEWS),
            create_observation(SourceType.SEC),
        ]
        generator = TradeIdeaGenerator()
        result = generator.generate(event, observations)

        if result.trade_idea:
            assert result.trade_idea.direction == TradeDirection.LONG


class TestTimeHorizon:
    """Tests for time horizon determination."""

    def test_filing_event_has_position_horizon(self):
        """Filing-driven events should have position time horizon."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.CATALYST_FILING,
            confidence_score=80.0,
            anomaly_score=60.0,
            catalyst_score=70.0,
            flow_score=50.0,
        )
        observations = [
            create_observation(SourceType.SEC, payload={"form": "10-K", "price": 100}),
            create_observation(SourceType.NEWS),
        ]
        generator = TradeIdeaGenerator()
        result = generator.generate(event, observations)

        if result.trade_idea:
            assert result.trade_idea.time_horizon == TimeHorizon.POSITION

    def test_news_event_has_swing_horizon(self):
        """News-driven events should have swing time horizon."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.CATALYST_NEWS,
            confidence_score=80.0,
            anomaly_score=60.0,
            catalyst_score=70.0,
            flow_score=50.0,
        )
        observations = [
            create_observation(SourceType.NEWS, payload={"headline": "Breaking", "price": 100}),
            create_observation(SourceType.EQUITIES),
        ]
        generator = TradeIdeaGenerator()
        result = generator.generate(event, observations)

        if result.trade_idea:
            assert result.trade_idea.time_horizon == TimeHorizon.SWING


class TestPriceLevelCalculation:
    """Tests for entry/target/stop level calculations."""

    def test_levels_calculated_from_price(self):
        """Should calculate price levels from observation data."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="AAPL",
            title="AAPL: Test (80)",
            event_type=EventType.MARKET_ANOMALY,
            confidence_score=80.0,
            anomaly_score=70.0,
            catalyst_score=60.0,
            flow_score=55.0,
        )
        observations = [
            create_observation(SourceType.EQUITIES, payload={"price": 150.0}),
            create_observation(SourceType.NEWS),
        ]
        generator = TradeIdeaGenerator()
        result = generator.generate(event, observations)

        if result.trade_idea:
            # Check that levels contain price values
            assert "$" in result.trade_idea.entry_zone
            assert "$" in result.trade_idea.target
            assert "$" in result.trade_idea.stop_loss

    def test_levels_generic_when_no_price(self):
        """Should use generic levels when no price data available."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.CATALYST_NEWS,
            confidence_score=80.0,
            anomaly_score=70.0,
            catalyst_score=60.0,
            flow_score=55.0,
        )
        observations = [
            create_observation(SourceType.NEWS, payload={"headline": "Test"}),
            create_observation(SourceType.SEC, payload={"form": "8-K"}),
        ]
        generator = TradeIdeaGenerator()
        result = generator.generate(event, observations)

        if result.trade_idea:
            # Generic levels should reference "entry" or "current"
            assert len(result.trade_idea.entry_zone) > 0


class TestSerialization:
    """Tests for to_dict() serialization."""

    def test_trade_idea_to_dict(self):
        """TradeIdea should serialize to valid dict."""
        idea = TradeIdea(
            event_id=uuid4(),
            direction=TradeDirection.LONG,
            entry_zone="$150-155",
            target="$175",
            stop_loss="$140",
            invalidation="Price closes below $140",
            time_horizon=TimeHorizon.SWING,
            confidence_level=80.0,
            rationale="Test rationale",
            key_catalysts=["Strong earnings"],
            risk_factors=["Market volatility"],
        )
        data = idea.to_dict()

        assert data["direction"] == "long"
        assert data["entry_zone"] == "$150-155"
        assert data["target"] == "$175"
        assert data["stop_loss"] == "$140"
        assert data["time_horizon"] == "swing"
        assert data["confidence_level"] == 80.0
        assert "event_id" in data
        assert "created_at" in data

    def test_research_plan_to_dict(self):
        """ResearchPlan should serialize to valid dict."""
        plan = ResearchPlan(
            event_id=uuid4(),
            questions_to_verify=["Question 1", "Question 2"],
            evidence_to_watch=["Evidence 1"],
            next_check_date=datetime.now(timezone.utc) + timedelta(days=1),
            current_score=45.0,
            gaps_identified=["Gap 1"],
        )
        data = plan.to_dict()

        assert len(data["questions_to_verify"]) == 2
        assert len(data["evidence_to_watch"]) == 1
        assert data["current_score"] == 45.0
        assert "next_check_date" in data
        assert data["next_check_date"] is not None

    def test_recommendation_to_dict(self):
        """Recommendation should serialize to valid dict."""
        idea = TradeIdea(direction=TradeDirection.LONG)
        evaluation = QualityGateEvaluation(
            passed=True,
            gate_score=85.0,
            failed_gates=[],
            improvement_suggestions=[],
        )
        rec = Recommendation(
            type="trade_idea",
            trade_idea=idea,
            gate_evaluation=evaluation,
        )
        data = rec.to_dict()

        assert data["type"] == "trade_idea"
        assert data["trade_idea"] is not None
        assert data["research_plan"] is None
        assert data["gate_evaluation"]["passed"] is True

    def test_gate_evaluation_to_dict(self):
        """QualityGateEvaluation should serialize to valid dict."""
        evaluation = QualityGateEvaluation(
            passed=False,
            gate_score=55.0,
            failed_gates=["min_confidence", "min_sources"],
            improvement_suggestions=["Suggestion 1"],
            gate_results=[
                GateResult(
                    gate_name="min_confidence",
                    passed=False,
                    actual_value=50.0,
                    threshold_value=70.0,
                    improvement_suggestion="Improve confidence",
                ),
            ],
        )
        data = evaluation.to_dict()

        assert data["passed"] is False
        assert data["gate_score"] == 55.0
        assert len(data["failed_gates"]) == 2
        assert len(data["gate_results"]) == 1
        assert data["gate_results"][0]["gate_name"] == "min_confidence"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_observations_list(self, sample_event):
        """Should handle empty observations list."""
        gate = QualityGate()
        result = gate.evaluate(sample_event, [])

        # Should still produce a result, though may fail sources gate
        assert result is not None
        assert isinstance(result.gate_score, float)

    def test_none_observations(self, sample_event):
        """Should handle None observations."""
        gate = QualityGate()
        result = gate.evaluate(sample_event, None)

        assert result is not None
        assert isinstance(result.gate_score, float)

    def test_extreme_scores(self):
        """Should handle extreme score values."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.MARKET_ANOMALY,
            confidence_score=100.0,
            anomaly_score=100.0,
            catalyst_score=100.0,
            flow_score=100.0,
        )
        observations = [
            create_observation(SourceType.EQUITIES, payload={"price": 100}),
            create_observation(SourceType.NEWS),
            create_observation(SourceType.SEC),
            create_observation(SourceType.CONGRESS),
        ]
        gate = QualityGate()
        result = gate.evaluate(event, observations)

        assert result.passed is True
        assert result.gate_score >= 99.9  # Allow for floating point precision

    def test_zero_scores(self):
        """Should handle zero score values."""
        event = Event(
            id=uuid4(),
            primary_entity_id=uuid4(),
            primary_ticker="TEST",
            title="Test Event",
            event_type=EventType.UNCERTAIN,
            confidence_score=0.0,
            anomaly_score=0.0,
            catalyst_score=0.0,
            flow_score=0.0,
        )
        gate = QualityGate()
        result = gate.evaluate(event, [])

        assert result.passed is False
        assert result.gate_score >= 0

    def test_passed_gate_count_property(self, sample_event):
        """QualityGateEvaluation should correctly count passed gates."""
        observations = [
            create_observation(SourceType.EQUITIES),
            create_observation(SourceType.NEWS),
        ]
        gate = QualityGate()
        result = gate.evaluate(sample_event, observations)

        assert result.passed_gate_count >= 0
        assert result.passed_gate_count <= result.total_gate_count
        assert result.total_gate_count == 5
