"""
Unit tests for EventBuilder class.

Tests cover:
- Observation grouping by entity_id
- Time window logic (72h default)
- Event type classification rules
- 4D score calculation
- Attention score with coverage bonus
- Primary/Secondary event hierarchy
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from src.tradz.events.builder import EventBuilder, DEFAULT_TIME_WINDOW_HOURS
from src.tradz.models import Event, EventStatus, EventType, Observation, SourceType


@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = MagicMock()
    db.get_open_events.return_value = []
    db.insert_event.return_value = "event-id"
    db.link_observation_to_event.return_value = None
    db.insert_event_type_history.return_value = "history-id"
    return db


@pytest.fixture
def event_builder(mock_db):
    """Create EventBuilder with mock database."""
    return EventBuilder(db=mock_db)


@pytest.fixture
def sample_entity_id():
    """Create a sample entity UUID."""
    return uuid4()


def create_observation(
    source: SourceType,
    entity_id,
    ticker: str = "AAPL",
    payload=None,
    observed_at=None,
    effective_at=None,
    quality_score: float = 1.0,
    freshness_score: float = 1.0,
) -> Observation:
    """Helper to create test observations."""
    now = datetime.now(timezone.utc)
    return Observation(
        id=uuid4(),
        source=source,
        entity_id=entity_id,
        entity_ticker=ticker,
        payload=payload or {},
        observed_at=observed_at or now,
        effective_at=effective_at or now,
        quality_score=quality_score,
        freshness_score=freshness_score,
    )


class TestEventBuilderGrouping:
    """Tests for observation grouping logic."""

    def test_groups_observations_by_entity_id(self, event_builder, sample_entity_id):
        """Observations with same entity_id should be grouped together."""
        entity2_id = uuid4()

        observations = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
            create_observation(SourceType.NEWS, sample_entity_id),
            create_observation(SourceType.EQUITIES, entity2_id),
        ]

        grouped = event_builder._group_observations_by_entity(observations)

        assert len(grouped[sample_entity_id]) == 2
        assert len(grouped[entity2_id]) == 1

    def test_skips_observations_without_entity_id(self, event_builder):
        """Observations without entity_id should be skipped in event building."""
        observations = [
            create_observation(SourceType.EQUITIES, None),  # type: ignore
        ]

        events = event_builder.build_events(observations)

        assert len(events) == 0

    def test_empty_observations_returns_empty_events(self, event_builder):
        """Empty observation list returns empty event list."""
        events = event_builder.build_events([])
        assert events == []


class TestTimeWindowLogic:
    """Tests for time window grouping logic."""

    def test_default_time_window_is_72_hours(self, event_builder):
        """Default time window should be 72 hours."""
        assert event_builder.time_window_hours == DEFAULT_TIME_WINDOW_HOURS
        assert event_builder.time_window_hours == 72

    def test_custom_time_window(self, mock_db):
        """Custom time window should be respected."""
        builder = EventBuilder(db=mock_db, time_window_hours=24)
        assert builder.time_window_hours == 24

    def test_observations_within_window_grouped(self, event_builder, sample_entity_id):
        """Observations within time window should be in same event."""
        now = datetime.now(timezone.utc)

        observations = [
            create_observation(
                SourceType.EQUITIES,
                sample_entity_id,
                observed_at=now,
                effective_at=now,
            ),
            create_observation(
                SourceType.NEWS,
                sample_entity_id,
                observed_at=now + timedelta(hours=24),
                effective_at=now + timedelta(hours=24),
            ),
        ]

        events = event_builder.build_events(observations)

        # Should create single event with both observations
        assert len(events) == 1
        assert len(events[0].observation_ids) == 2


class TestEventTypeClassification:
    """Tests for event type classification rules."""

    def test_market_anomaly_classification(self, event_builder, sample_entity_id):
        """Events with only market data and anomaly indicators -> MARKET_ANOMALY."""
        observations = [
            create_observation(
                SourceType.EQUITIES,
                sample_entity_id,
                payload={"price_change_pct": 5.0, "is_anomaly": True},
            ),
        ]

        event_type = event_builder._classify_event_type(observations)

        assert event_type == EventType.MARKET_ANOMALY

    def test_catalyst_news_classification(self, event_builder, sample_entity_id):
        """Events dominated by NEWS source -> CATALYST_NEWS."""
        observations = [
            create_observation(SourceType.NEWS, sample_entity_id),
            create_observation(SourceType.NEWS, sample_entity_id),
            create_observation(SourceType.EQUITIES, sample_entity_id),
        ]

        event_type = event_builder._classify_event_type(observations)

        assert event_type == EventType.CATALYST_NEWS

    def test_catalyst_filing_classification(self, event_builder, sample_entity_id):
        """Events dominated by SEC source -> CATALYST_FILING."""
        observations = [
            create_observation(SourceType.SEC, sample_entity_id),
            create_observation(SourceType.SEC, sample_entity_id),
        ]

        event_type = event_builder._classify_event_type(observations)

        assert event_type == EventType.CATALYST_FILING

    def test_flow_congress_classification(self, event_builder, sample_entity_id):
        """Events dominated by CONGRESS source -> FLOW_CONGRESS."""
        observations = [
            create_observation(SourceType.CONGRESS, sample_entity_id),
            create_observation(SourceType.CONGRESS, sample_entity_id),
        ]

        event_type = event_builder._classify_event_type(observations)

        assert event_type == EventType.FLOW_CONGRESS

    def test_flow_13f_classification(self, event_builder, sample_entity_id):
        """Events dominated by HEDGEFUND source -> FLOW_13F."""
        observations = [
            create_observation(SourceType.HEDGEFUND, sample_entity_id),
            create_observation(SourceType.HEDGEFUND, sample_entity_id),
        ]

        event_type = event_builder._classify_event_type(observations)

        assert event_type == EventType.FLOW_13F

    def test_prediction_shift_classification(self, event_builder, sample_entity_id):
        """Events dominated by POLYMARKET source -> PREDICTION_SHIFT."""
        observations = [
            create_observation(SourceType.POLYMARKET, sample_entity_id),
            create_observation(SourceType.POLYMARKET, sample_entity_id),
        ]

        event_type = event_builder._classify_event_type(observations)

        assert event_type == EventType.PREDICTION_SHIFT

    def test_mixed_classification(self, event_builder, sample_entity_id):
        """Events with multiple dominant sources -> MIXED."""
        observations = [
            create_observation(SourceType.NEWS, sample_entity_id),
            create_observation(SourceType.NEWS, sample_entity_id),
            create_observation(SourceType.SEC, sample_entity_id),
            create_observation(SourceType.SEC, sample_entity_id),
        ]

        event_type = event_builder._classify_event_type(observations)

        assert event_type == EventType.MIXED

    def test_uncertain_classification(self, event_builder):
        """Events that cannot be classified -> UNCERTAIN."""
        # Empty list
        assert event_builder._classify_event_type([]) == EventType.UNCERTAIN

    def test_source_to_event_type_mapping(self, event_builder):
        """Test all source to event type mappings."""
        assert event_builder._source_to_event_type(SourceType.EQUITIES) == EventType.MARKET_ANOMALY
        assert event_builder._source_to_event_type(SourceType.CRYPTO) == EventType.MARKET_ANOMALY
        assert event_builder._source_to_event_type(SourceType.NEWS) == EventType.CATALYST_NEWS
        assert event_builder._source_to_event_type(SourceType.SEC) == EventType.CATALYST_FILING
        assert event_builder._source_to_event_type(SourceType.CONGRESS) == EventType.FLOW_CONGRESS
        assert event_builder._source_to_event_type(SourceType.HEDGEFUND) == EventType.FLOW_13F
        assert event_builder._source_to_event_type(SourceType.POLYMARKET) == EventType.PREDICTION_SHIFT


class TestAttentionScoreCalculation:
    """Tests for attention score calculation with coverage bonus."""

    def test_attention_score_formula(self, event_builder, sample_entity_id):
        """Test attention score = 0.3*anomaly + 0.3*catalyst + 0.25*flow + 0.15*confidence + bonus."""
        observations = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
        ]

        # Use known scores
        anomaly, catalyst, flow, confidence = 80, 70, 60, 50

        attention = event_builder._calculate_attention_score(
            anomaly, catalyst, flow, confidence, observations
        )

        # Base: 0.3*80 + 0.3*70 + 0.25*60 + 0.15*50 = 24 + 21 + 15 + 7.5 = 67.5
        # Bonus: 1 source * 5 = 5
        # Total: 72.5
        assert attention == 72.5

    def test_coverage_bonus_multiple_sources(self, event_builder, sample_entity_id):
        """Coverage bonus increases with unique sources."""
        # Single source
        obs_single = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
        ]
        score_single = event_builder._calculate_attention_score(50, 50, 50, 50, obs_single)

        # Multiple sources
        obs_multi = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
            create_observation(SourceType.NEWS, sample_entity_id),
            create_observation(SourceType.SEC, sample_entity_id),
        ]
        score_multi = event_builder._calculate_attention_score(50, 50, 50, 50, obs_multi)

        # Multi should have higher score due to coverage bonus
        assert score_multi > score_single
        # Difference should be 2 more sources * 5 = 10
        assert score_multi - score_single == 10

    def test_coverage_bonus_max_cap(self, event_builder, sample_entity_id):
        """Coverage bonus should be capped at MAX_COVERAGE_BONUS (20)."""
        # Create observations from many sources
        observations = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
            create_observation(SourceType.NEWS, sample_entity_id),
            create_observation(SourceType.SEC, sample_entity_id),
            create_observation(SourceType.CONGRESS, sample_entity_id),
            create_observation(SourceType.HEDGEFUND, sample_entity_id),
            create_observation(SourceType.POLYMARKET, sample_entity_id),
        ]

        # 6 sources * 5 = 30, but should cap at 20
        attention = event_builder._calculate_attention_score(50, 50, 50, 50, observations)

        # Base: 50 * (0.3 + 0.3 + 0.25 + 0.15) = 50
        # Bonus: min(30, 20) = 20
        # Total: 70
        assert attention == 70

    def test_attention_score_capped_at_100(self, event_builder, sample_entity_id):
        """Attention score should never exceed 100."""
        observations = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
            create_observation(SourceType.NEWS, sample_entity_id),
            create_observation(SourceType.SEC, sample_entity_id),
            create_observation(SourceType.CONGRESS, sample_entity_id),
        ]

        # Use max scores
        attention = event_builder._calculate_attention_score(100, 100, 100, 100, observations)

        assert attention == 100  # Capped at 100


class Test4DScoreCalculation:
    """Tests for individual 4D score calculations."""

    def test_anomaly_score_baseline(self, event_builder):
        """Anomaly score should start at baseline 50."""
        observations: list = []
        score = event_builder._calculate_anomaly_score(observations)
        assert score == 50.0

    def test_anomaly_score_increases_with_price_change(self, event_builder, sample_entity_id):
        """Higher price changes should increase anomaly score."""
        obs_low = [
            create_observation(
                SourceType.EQUITIES,
                sample_entity_id,
                payload={"price_change_pct": 1.5},
            ),
        ]
        obs_high = [
            create_observation(
                SourceType.EQUITIES,
                sample_entity_id,
                payload={"price_change_pct": 8.0},
            ),
        ]

        score_low = event_builder._calculate_anomaly_score(obs_low)
        score_high = event_builder._calculate_anomaly_score(obs_high)

        assert score_high > score_low

    def test_catalyst_score_sec_8k_boost(self, event_builder, sample_entity_id):
        """SEC 8-K filings should get higher catalyst boost."""
        obs_10k = [
            create_observation(
                SourceType.SEC,
                sample_entity_id,
                payload={"form": "10-K"},
            ),
        ]
        obs_8k = [
            create_observation(
                SourceType.SEC,
                sample_entity_id,
                payload={"form": "8-K"},
            ),
        ]

        score_10k = event_builder._calculate_catalyst_score(obs_10k)
        score_8k = event_builder._calculate_catalyst_score(obs_8k)

        # 8-K should have higher impact (1.5x)
        assert score_8k > score_10k

    def test_flow_score_purchase_vs_sale(self, event_builder, sample_entity_id):
        """Congress purchases should increase flow score more than sales decrease it."""
        obs_purchase = [
            create_observation(
                SourceType.CONGRESS,
                sample_entity_id,
                payload={"type": "purchase"},
            ),
        ]
        obs_sale = [
            create_observation(
                SourceType.CONGRESS,
                sample_entity_id,
                payload={"type": "sale"},
            ),
        ]

        score_purchase = event_builder._calculate_flow_score(obs_purchase)
        score_sale = event_builder._calculate_flow_score(obs_sale)

        # Purchases add more than sales subtract
        assert score_purchase > 50  # Above baseline
        assert score_sale < 50  # Below baseline
        assert (score_purchase - 50) > abs(50 - score_sale)  # Purchase impact > sale impact

    def test_confidence_score_source_diversity(self, event_builder, sample_entity_id):
        """More diverse sources should increase confidence score."""
        obs_single = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
        ]
        obs_diverse = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
            create_observation(SourceType.NEWS, sample_entity_id),
            create_observation(SourceType.SEC, sample_entity_id),
        ]

        score_single = event_builder._calculate_confidence_score(obs_single)
        score_diverse = event_builder._calculate_confidence_score(obs_diverse)

        assert score_diverse > score_single


class TestPrimarySecondaryHierarchy:
    """Tests for Primary/Secondary event hierarchy support."""

    def test_create_secondary_event(self, event_builder, sample_entity_id):
        """Secondary event should be linked to primary via parent_event_id."""
        primary_event = Event(
            id=uuid4(),
            primary_entity_id=sample_entity_id,
            primary_ticker="AAPL",
            title="Primary Event",
            event_type=EventType.CATALYST_NEWS,
            status=EventStatus.NEW,
        )

        secondary_observations = [
            create_observation(SourceType.SEC, sample_entity_id),
        ]

        secondary = event_builder.create_secondary_event(primary_event, secondary_observations)

        assert secondary.parent_event_id == primary_event.id
        assert secondary.primary_entity_id == sample_entity_id

    def test_secondary_event_requires_primary_entity(self, event_builder):
        """Creating secondary event without primary entity should raise error."""
        primary_event = Event(
            id=uuid4(),
            primary_entity_id=None,  # No entity
            title="Primary Event",
        )

        with pytest.raises(ValueError):
            event_builder.create_secondary_event(primary_event, [])


class TestEventCreation:
    """Tests for event creation."""

    def test_event_created_with_new_status(self, event_builder, sample_entity_id):
        """New events should have NEW status."""
        observations = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
        ]

        events = event_builder.build_events(observations)

        assert len(events) == 1
        assert events[0].status == EventStatus.NEW

    def test_event_has_template_title(self, event_builder, sample_entity_id):
        """Events should have template-generated title."""
        observations = [
            create_observation(SourceType.NEWS, sample_entity_id, ticker="MSFT"),
            create_observation(SourceType.NEWS, sample_entity_id, ticker="MSFT"),
        ]

        events = event_builder.build_events(observations)

        assert "MSFT" in events[0].title
        assert events[0].title_source == "template"

    def test_event_observation_ids_populated(self, event_builder, sample_entity_id):
        """Event should have observation_ids populated."""
        observations = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
            create_observation(SourceType.NEWS, sample_entity_id),
        ]

        events = event_builder.build_events(observations)

        assert len(events[0].observation_ids) == 2

    def test_event_timestamps_set_correctly(self, event_builder, sample_entity_id):
        """Event timestamps should be derived from observations."""
        now = datetime.now(timezone.utc)
        earlier = now - timedelta(hours=2)

        observations = [
            create_observation(
                SourceType.EQUITIES,
                sample_entity_id,
                observed_at=earlier,
                effective_at=earlier,
            ),
            create_observation(
                SourceType.NEWS,
                sample_entity_id,
                observed_at=now,
                effective_at=now,
            ),
        ]

        events = event_builder.build_events(observations)

        assert events[0].start_at == earlier
        assert events[0].last_update_at == now


class TestEventPersistence:
    """Tests for event persistence."""

    def test_persist_events(self, event_builder, mock_db, sample_entity_id):
        """Events should be persisted to database."""
        observations = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
        ]

        events = event_builder.build_events(observations)
        count = event_builder.persist_events(events)

        assert count == 1
        mock_db.insert_event.assert_called_once()
        mock_db.link_observation_to_event.assert_called()

    def test_persist_links_observations(self, event_builder, mock_db, sample_entity_id):
        """Persisting events should link all observations."""
        observations = [
            create_observation(SourceType.EQUITIES, sample_entity_id),
            create_observation(SourceType.NEWS, sample_entity_id),
        ]

        events = event_builder.build_events(observations)
        event_builder.persist_events(events)

        # Should have linked 2 observations
        assert mock_db.link_observation_to_event.call_count == 2


class TestTitleGeneration:
    """Tests for template title generation."""

    def test_template_title_format(self, event_builder):
        """Template title should follow format: '{symbol}: {event_type} ({score})'."""
        title = event_builder._generate_template_title(
            ticker="AAPL",
            event_type=EventType.MARKET_ANOMALY,
            attention_score=75.5,
        )

        assert title == "AAPL: Market Anomaly (76)"

    def test_template_title_unknown_ticker(self, event_builder):
        """Template title should handle None ticker."""
        title = event_builder._generate_template_title(
            ticker=None,
            event_type=EventType.CATALYST_NEWS,
            attention_score=60.0,
        )

        assert title == "Unknown: Catalyst News (60)"
