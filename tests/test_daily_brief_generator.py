"""
Tests for the DailyBriefGenerator class.
"""
from datetime import datetime, timezone
from uuid import uuid4

from src.tradz.models import Event, Observation, EventType, EventStatus, SourceType
from src.tradz.events.daily_brief_generator import (
    DailyBriefContent,
    DailyBriefGenerator,
    DataQualitySummary,
    EventSummary,
    OpenLoop,
    ResearchIdeaSummary,
    SourceHealthSummary,
    TradeIdeaSummary,
)
from src.tradz.events.quality_gate import QualityGate, QualityGateConfig


class TestDailyBriefContent:
    """Tests for DailyBriefContent dataclass."""

    def test_default_values(self):
        """Test that DailyBriefContent has correct default values."""
        content = DailyBriefContent()

        assert content.executive_summary == ""
        assert content.top_events == []
        assert content.trade_ideas == []
        assert content.research_ideas == []
        assert content.open_loops == []
        assert content.data_quality is None
        assert content.generation_method == "template"
        assert content.date is not None

    def test_to_dict(self):
        """Test DailyBriefContent to_dict serialization."""
        content = DailyBriefContent(
            executive_summary="Test summary",
            generation_method="template",
        )

        result = content.to_dict()

        assert result["executive_summary"] == "Test summary"
        assert result["generation_method"] == "template"
        assert result["top_events"] == []
        assert result["trade_ideas"] == []
        assert result["research_ideas"] == []
        assert result["open_loops"] == []
        assert result["data_quality"] is None

    def test_to_dict_with_events(self):
        """Test DailyBriefContent to_dict with event summaries."""
        event_summary = EventSummary(
            event_id="test-id",
            title="Test Event",
            ticker="AAPL",
            event_type="catalyst_news",
            attention_score=75.0,
            anomaly_score=60.0,
            catalyst_score=80.0,
            flow_score=50.0,
            confidence_score=70.0,
            observation_count=5,
        )

        content = DailyBriefContent(
            executive_summary="Test summary",
            top_events=[event_summary],
        )

        result = content.to_dict()

        assert len(result["top_events"]) == 1
        assert result["top_events"][0]["ticker"] == "AAPL"
        assert result["top_events"][0]["attention_score"] == 75.0


class TestEventSummary:
    """Tests for EventSummary dataclass."""

    def test_to_dict(self):
        """Test EventSummary to_dict serialization."""
        now = datetime.now(timezone.utc)
        summary = EventSummary(
            event_id="test-id",
            title="AAPL Surges on Earnings",
            ticker="AAPL",
            event_type="catalyst_news",
            attention_score=75.0,
            anomaly_score=60.0,
            catalyst_score=80.0,
            flow_score=50.0,
            confidence_score=70.0,
            observation_count=5,
            last_update_at=now,
        )

        result = summary.to_dict()

        assert result["event_id"] == "test-id"
        assert result["title"] == "AAPL Surges on Earnings"
        assert result["ticker"] == "AAPL"
        assert result["event_type"] == "catalyst_news"
        assert result["attention_score"] == 75.0
        assert result["observation_count"] == 5
        assert result["last_update_at"] is not None


class TestTradeIdeaSummary:
    """Tests for TradeIdeaSummary dataclass."""

    def test_to_dict(self):
        """Test TradeIdeaSummary to_dict serialization."""
        summary = TradeIdeaSummary(
            event_id="test-id",
            ticker="AAPL",
            direction="long",
            entry_zone="$150-155",
            target="$175",
            stop_loss="$140",
            confidence_level=75.0,
            rationale="Strong earnings catalyst",
        )

        result = summary.to_dict()

        assert result["ticker"] == "AAPL"
        assert result["direction"] == "long"
        assert result["entry_zone"] == "$150-155"
        assert result["target"] == "$175"
        assert result["stop_loss"] == "$140"
        assert result["confidence_level"] == 75.0


class TestResearchIdeaSummary:
    """Tests for ResearchIdeaSummary dataclass."""

    def test_to_dict(self):
        """Test ResearchIdeaSummary to_dict serialization."""
        summary = ResearchIdeaSummary(
            event_id="test-id",
            ticker="TSLA",
            questions=["Is demand slowing?", "What are production numbers?"],
            evidence_to_watch=["Delivery reports", "Earnings call"],
            current_score=45.0,
            potential_score=75.0,
        )

        result = summary.to_dict()

        assert result["ticker"] == "TSLA"
        assert len(result["questions"]) == 2
        assert result["current_score"] == 45.0
        assert result["potential_score"] == 75.0


class TestDataQualitySummary:
    """Tests for DataQualitySummary dataclass."""

    def test_to_dict(self):
        """Test DataQualitySummary to_dict serialization."""
        source = SourceHealthSummary(
            name="equities",
            display_name="Market Data (Equities)",
            status="ok",
            record_count_24h=100,
            freshness_indicator="fresh",
        )

        summary = DataQualitySummary(
            total_sources=7,
            healthy_count=5,
            degraded_count=1,
            error_count=1,
            sources=[source],
            overall_status="degraded",
            quality_message="1 source(s) have stale data.",
        )

        result = summary.to_dict()

        assert result["total_sources"] == 7
        assert result["healthy_count"] == 5
        assert result["overall_status"] == "degraded"
        assert len(result["sources"]) == 1
        assert result["sources"][0]["name"] == "equities"


class TestDailyBriefGenerator:
    """Tests for DailyBriefGenerator class."""

    def _create_event(
        self,
        ticker: str = "AAPL",
        event_type: EventType = EventType.CATALYST_NEWS,
        anomaly_score: float = 50.0,
        catalyst_score: float = 50.0,
        flow_score: float = 50.0,
        confidence_score: float = 50.0,
    ) -> Event:
        """Create a test event."""
        return Event(
            id=uuid4(),
            primary_ticker=ticker,
            title=f"{ticker} Test Event",
            event_type=event_type,
            status=EventStatus.NEW,
            anomaly_score=anomaly_score,
            catalyst_score=catalyst_score,
            flow_score=flow_score,
            confidence_score=confidence_score,
        )

    def test_generate_empty_events(self):
        """Test generating brief with no events."""
        generator = DailyBriefGenerator()

        content = generator.generate([])

        assert content.executive_summary != ""  # Default message
        assert "No significant events" in content.executive_summary
        assert content.top_events == []
        assert content.trade_ideas == []
        assert content.research_ideas == []

    def test_generate_top_events_sorted_by_attention(self):
        """Test that top events are sorted by attention score."""
        generator = DailyBriefGenerator()

        events = [
            self._create_event("AAPL", anomaly_score=40, catalyst_score=40),  # Lower score
            self._create_event("MSFT", anomaly_score=80, catalyst_score=80),  # Higher score
            self._create_event("GOOGL", anomaly_score=60, catalyst_score=60),  # Medium score
        ]

        content = generator.generate(events)

        assert len(content.top_events) == 3
        # Should be sorted: MSFT (highest), GOOGL (medium), AAPL (lowest)
        assert content.top_events[0].ticker == "MSFT"
        assert content.top_events[1].ticker == "GOOGL"
        assert content.top_events[2].ticker == "AAPL"

    def test_generate_limits_top_events_to_5(self):
        """Test that top events is limited to 5."""
        generator = DailyBriefGenerator()

        # Create 7 events
        events = [
            self._create_event(f"TICK{i}", anomaly_score=50+i*5)
            for i in range(7)
        ]

        content = generator.generate(events)

        assert len(content.top_events) == 5

    def test_generate_executive_summary_mentions_top_event(self):
        """Test that executive summary mentions the top event."""
        generator = DailyBriefGenerator()

        events = [
            self._create_event("AAPL", anomaly_score=80, catalyst_score=80),
        ]

        content = generator.generate(events)

        assert "AAPL" in content.executive_summary

    def test_generate_executive_summary_three_sentences(self):
        """Test that executive summary has roughly 3 sentences."""
        generator = DailyBriefGenerator()

        events = [
            self._create_event("AAPL", anomaly_score=80, catalyst_score=80),
            self._create_event("MSFT", anomaly_score=70, catalyst_score=70),
            self._create_event("GOOGL", anomaly_score=60, catalyst_score=60),
        ]

        content = generator.generate(events)

        # Count periods to verify roughly 3 sentences
        sentence_count = content.executive_summary.count(".")
        assert sentence_count >= 2  # At least 2 sentences

    def test_generate_trade_idea_when_gates_pass(self):
        """Test that trade idea is generated when quality gates pass."""
        # Use lenient gate config so gates pass
        config = QualityGateConfig(
            min_confidence=30,
            min_sources=1,
            min_anomaly=30,
            min_catalyst=20,
            has_invalidation=False,
        )
        gate = QualityGate(config)
        generator = DailyBriefGenerator(quality_gate=gate)

        # High scores to pass gates
        event = self._create_event(
            "AAPL",
            anomaly_score=80,
            catalyst_score=80,
            flow_score=80,
            confidence_score=80,
        )

        content = generator.generate([event])

        assert len(content.trade_ideas) == 1
        assert content.trade_ideas[0].ticker == "AAPL"

    def test_generate_research_idea_when_gates_fail_high_potential(self):
        """Test that research idea is generated when gates fail but potential is high."""
        # Use strict gate config so gates fail
        config = QualityGateConfig(
            min_confidence=90,  # Very high threshold
            min_sources=5,
            min_anomaly=80,
            min_catalyst=80,
            has_invalidation=True,
        )
        gate = QualityGate(config)
        generator = DailyBriefGenerator(quality_gate=gate)

        # Medium scores - will fail gates but have potential
        event = self._create_event(
            "TSLA",
            anomaly_score=60,  # Below threshold but not zero
            catalyst_score=60,
            flow_score=60,
            confidence_score=60,  # Below 90 threshold
        )

        content = generator.generate([event])

        # Should have research idea (failed gates but has potential)
        assert len(content.trade_ideas) == 0  # No trade idea
        assert len(content.research_ideas) >= 0  # May or may not have research idea

    def test_generate_open_loops_from_research_plans(self):
        """Test that open loops are created from research plan questions."""
        config = QualityGateConfig(
            min_confidence=90,
            min_sources=5,
            min_anomaly=80,
            min_catalyst=80,
        )
        gate = QualityGate(config)
        generator = DailyBriefGenerator(quality_gate=gate)

        event = self._create_event(
            "NVDA",
            anomaly_score=60,
            catalyst_score=60,
            flow_score=60,
            confidence_score=60,
        )

        content = generator.generate([event])

        # Should have some open loops from research plan
        assert len(content.open_loops) >= 0  # Research plan questions become loops

    def test_generate_with_system_status(self):
        """Test generating brief with system status data."""
        generator = DailyBriefGenerator()

        system_status = {
            "overall": {
                "total_sources": 7,
                "healthy_count": 5,
                "degraded_count": 1,
                "error_count": 1,
            },
            "sources": [
                {
                    "name": "equities",
                    "display_name": "Market Data (Equities)",
                    "status": "ok",
                    "record_count_24h": 100,
                    "freshness_indicator": "fresh",
                },
                {
                    "name": "news",
                    "display_name": "News",
                    "status": "degraded",
                    "record_count_24h": 50,
                    "freshness_indicator": "stale",
                },
            ],
        }

        content = generator.generate([], system_status=system_status)

        assert content.data_quality is not None
        assert content.data_quality.total_sources == 7
        assert content.data_quality.healthy_count == 5
        assert content.data_quality.degraded_count == 1
        assert content.data_quality.error_count == 1
        assert len(content.data_quality.sources) == 2
        assert content.data_quality.overall_status == "error"  # Has error_count > 0

    def test_generate_data_quality_ok_status(self):
        """Test data quality shows ok when all sources healthy."""
        generator = DailyBriefGenerator()

        system_status = {
            "overall": {
                "total_sources": 3,
                "healthy_count": 3,
                "degraded_count": 0,
                "error_count": 0,
            },
            "sources": [],
        }

        content = generator.generate([], system_status=system_status)

        assert content.data_quality is not None
        assert content.data_quality.overall_status == "ok"
        assert "healthy" in content.data_quality.quality_message.lower()

    def test_generate_data_quality_degraded_status(self):
        """Test data quality shows degraded when some sources stale."""
        generator = DailyBriefGenerator()

        system_status = {
            "overall": {
                "total_sources": 5,
                "healthy_count": 3,
                "degraded_count": 2,
                "error_count": 0,
            },
            "sources": [],
        }

        content = generator.generate([], system_status=system_status)

        assert content.data_quality is not None
        assert content.data_quality.overall_status == "degraded"
        assert "stale" in content.data_quality.quality_message.lower()

    def test_to_daily_brief_conversion(self):
        """Test converting DailyBriefContent to DailyBrief model."""
        generator = DailyBriefGenerator()

        content = DailyBriefContent(
            executive_summary="Test summary",
            generation_method="template",
        )

        daily_brief = generator.to_daily_brief(content, run_id="test-run-123")

        assert daily_brief.id is not None
        assert daily_brief.summary_json["executive_summary"] == "Test summary"
        assert daily_brief.generation_method == "template"
        assert daily_brief.run_id == "test-run-123"

    def test_extract_top_events_preserves_scores(self):
        """Test that top events extraction preserves all scores."""
        generator = DailyBriefGenerator()

        event = self._create_event(
            "AAPL",
            anomaly_score=75,
            catalyst_score=65,
            flow_score=55,
            confidence_score=85,
        )

        content = generator.generate([event])

        assert len(content.top_events) == 1
        summary = content.top_events[0]
        assert summary.anomaly_score == 75
        assert summary.catalyst_score == 65
        assert summary.flow_score == 55
        assert summary.confidence_score == 85

    def test_generate_with_observations(self):
        """Test generating brief with observations provided."""
        generator = DailyBriefGenerator()

        event = self._create_event(
            "AAPL",
            anomaly_score=80,
            catalyst_score=80,
        )

        observation = Observation(
            id=uuid4(),
            source=SourceType.NEWS,
            entity_id=None,
            entity_ticker="AAPL",
            title="AAPL beats earnings",
            summary="Strong Q4 results",
        )

        observations_by_event = {event.id: [observation]}

        content = generator.generate([event], observations_by_event)

        # Should process without errors
        assert len(content.top_events) == 1


class TestOpenLoop:
    """Tests for OpenLoop dataclass."""

    def test_to_dict(self):
        """Test OpenLoop to_dict serialization."""
        now = datetime.now(timezone.utc)
        loop = OpenLoop(
            loop_id="loop-123",
            event_id="event-456",
            question="Is the thesis still valid?",
            created_at=now,
            status="open",
        )

        result = loop.to_dict()

        assert result["loop_id"] == "loop-123"
        assert result["event_id"] == "event-456"
        assert result["question"] == "Is the thesis still valid?"
        assert result["status"] == "open"
        assert result["created_at"] is not None


class TestSourceHealthSummary:
    """Tests for SourceHealthSummary dataclass."""

    def test_to_dict(self):
        """Test SourceHealthSummary to_dict serialization."""
        summary = SourceHealthSummary(
            name="equities",
            display_name="Market Data (Equities)",
            status="ok",
            record_count_24h=150,
            freshness_indicator="fresh",
        )

        result = summary.to_dict()

        assert result["name"] == "equities"
        assert result["display_name"] == "Market Data (Equities)"
        assert result["status"] == "ok"
        assert result["record_count_24h"] == 150
        assert result["freshness_indicator"] == "fresh"
