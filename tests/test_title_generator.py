"""
Unit tests for TitleGenerator.

Tests cover:
- LLM title generation success
- LLM failure with template fallback
- Template title generation for all event types
- Title cleaning and formatting
- Configuration options
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.tradz.events.llm_provider import (
    LLMAPIError,
    LLMTimeoutError,
    MockProvider,
)
from src.tradz.events.title_generator import (
    TitleGenerator,
    generate_event_title,
)
from src.tradz.models import Event, EventStatus, EventType, Observation, SourceType


@pytest.fixture
def sample_entity_id():
    """Create a sample entity UUID."""
    return uuid4()


@pytest.fixture
def sample_event(sample_entity_id):
    """Create a sample event."""
    return Event(
        id=uuid4(),
        primary_entity_id=sample_entity_id,
        primary_ticker="AAPL",
        title="",
        event_type=EventType.MARKET_ANOMALY,
        status=EventStatus.NEW,
        anomaly_score=75.0,
        catalyst_score=60.0,
        flow_score=55.0,
        confidence_score=70.0,
        start_at=datetime.now(timezone.utc),
        last_update_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_observations(sample_entity_id):
    """Create sample observations."""
    return [
        Observation(
            id=uuid4(),
            source=SourceType.EQUITIES,
            entity_id=sample_entity_id,
            entity_ticker="AAPL",
            summary="AAPL price up 5.2% on heavy volume",
            payload={"price_change_pct": 5.2, "volume_ratio": 2.5},
            observed_at=datetime.now(timezone.utc),
        ),
        Observation(
            id=uuid4(),
            source=SourceType.NEWS,
            entity_id=sample_entity_id,
            entity_ticker="AAPL",
            summary="Apple announces new product line",
            payload={"headline": "Apple Unveils New Products"},
            observed_at=datetime.now(timezone.utc),
        ),
    ]


class TestTitleGeneratorLLM:
    """Tests for LLM-based title generation."""

    def test_generates_llm_title_success(self, sample_event, sample_observations):
        """TitleGenerator generates title using LLM on success."""
        mock_provider = MockProvider(response="AAPL Surges 5% on Product Announcement")
        generator = TitleGenerator(provider=mock_provider)

        title, source = generator.generate_title(sample_event, sample_observations)

        assert title == "AAPL Surges 5% on Product Announcement"
        assert source == "llm"
        assert mock_provider.call_count == 1

    def test_includes_event_context_in_prompt(self, sample_event, sample_observations):
        """TitleGenerator includes event context in LLM prompt."""
        mock_provider = MockProvider(response="Test Title")
        generator = TitleGenerator(provider=mock_provider)

        generator.generate_title(sample_event, sample_observations)

        prompt = mock_provider.last_prompt
        assert "AAPL" in prompt
        assert "Market Anomaly" in prompt
        assert "Anomaly" in prompt

    def test_falls_back_on_llm_api_error(self, sample_event, sample_observations):
        """TitleGenerator falls back to template on LLM API error."""
        mock_provider = MockProvider(should_fail=True, fail_with=LLMAPIError("API error"))
        generator = TitleGenerator(provider=mock_provider)

        title, source = generator.generate_title(sample_event, sample_observations)

        assert source == "template"
        assert "AAPL" in title

    def test_falls_back_on_llm_timeout(self, sample_event, sample_observations):
        """TitleGenerator falls back to template on LLM timeout."""
        mock_provider = MockProvider(should_fail=True, fail_with=LLMTimeoutError("Timeout"))
        generator = TitleGenerator(provider=mock_provider)

        title, source = generator.generate_title(sample_event, sample_observations)

        assert source == "template"
        assert "AAPL" in title

    def test_falls_back_on_empty_llm_response(self, sample_event, sample_observations):
        """TitleGenerator falls back to template on empty LLM response."""
        mock_provider = MockProvider(response="")
        generator = TitleGenerator(provider=mock_provider)

        title, source = generator.generate_title(sample_event, sample_observations)

        assert source == "template"
        assert "AAPL" in title

    def test_falls_back_on_too_short_llm_response(self, sample_event, sample_observations):
        """TitleGenerator falls back to template on too short LLM response."""
        mock_provider = MockProvider(response="Short")
        generator = TitleGenerator(provider=mock_provider)

        title, source = generator.generate_title(sample_event, sample_observations)

        assert source == "template"

    def test_use_llm_false_skips_llm(self, sample_event, sample_observations):
        """TitleGenerator with use_llm=False skips LLM entirely."""
        mock_provider = MockProvider(response="LLM Title")
        generator = TitleGenerator(provider=mock_provider, use_llm=False)

        title, source = generator.generate_title(sample_event, sample_observations)

        assert source == "template"
        assert mock_provider.call_count == 0


class TestTitleGeneratorCleanup:
    """Tests for LLM response cleanup."""

    def test_removes_title_prefix(self, sample_event, sample_observations):
        """TitleGenerator removes 'Title:' prefix from LLM response."""
        mock_provider = MockProvider(response="Title: AAPL Surges 5%")
        generator = TitleGenerator(provider=mock_provider)

        title, source = generator.generate_title(sample_event, sample_observations)

        assert title == "AAPL Surges 5%"
        assert source == "llm"

    def test_removes_quotes(self, sample_event, sample_observations):
        """TitleGenerator removes quotes from LLM response."""
        mock_provider = MockProvider(response='"AAPL Surges 5%"')
        generator = TitleGenerator(provider=mock_provider)

        title, source = generator.generate_title(sample_event, sample_observations)

        assert title == "AAPL Surges 5%"

    def test_takes_first_line_only(self, sample_event, sample_observations):
        """TitleGenerator takes first line only from multi-line response."""
        mock_provider = MockProvider(response="AAPL Surges 5%\nThis is additional text")
        generator = TitleGenerator(provider=mock_provider)

        title, source = generator.generate_title(sample_event, sample_observations)

        assert title == "AAPL Surges 5%"
        assert "\n" not in title

    def test_truncates_long_title(self, sample_event, sample_observations):
        """TitleGenerator truncates titles over 100 chars."""
        long_title = "A" * 150
        mock_provider = MockProvider(response=long_title)
        generator = TitleGenerator(provider=mock_provider)

        title, source = generator.generate_title(sample_event, sample_observations)

        assert len(title) <= 100
        assert title.endswith("...")


class TestTitleGeneratorTemplate:
    """Tests for template-based title generation."""

    def test_market_anomaly_with_price_change(self, sample_entity_id):
        """Template generates market anomaly title with price change."""
        event = Event(
            primary_entity_id=sample_entity_id,
            primary_ticker="TSLA",
            event_type=EventType.MARKET_ANOMALY,
            anomaly_score=80.0,
        )
        obs = [
            Observation(
                source=SourceType.EQUITIES,
                entity_id=sample_entity_id,
                entity_ticker="TSLA",
                payload={"price_change_pct": -7.5},
            )
        ]
        generator = TitleGenerator(use_llm=False)

        title, source = generator.generate_title(event, obs)

        assert source == "template"
        assert "TSLA" in title
        assert "Drops" in title
        assert "7.5%" in title

    def test_catalyst_news_multiple_articles(self, sample_entity_id):
        """Template generates catalyst news title with article count."""
        event = Event(
            primary_entity_id=sample_entity_id,
            primary_ticker="NVDA",
            event_type=EventType.CATALYST_NEWS,
            catalyst_score=70.0,
        )
        obs = [
            Observation(source=SourceType.NEWS, entity_id=sample_entity_id),
            Observation(source=SourceType.NEWS, entity_id=sample_entity_id),
            Observation(source=SourceType.NEWS, entity_id=sample_entity_id),
        ]
        generator = TitleGenerator(use_llm=False)

        title, source = generator.generate_title(event, obs)

        assert "NVDA" in title
        assert "3 News Items" in title or "News Spotlight" in title

    def test_catalyst_filing_with_form_type(self, sample_entity_id):
        """Template generates catalyst filing title with form type."""
        event = Event(
            primary_entity_id=sample_entity_id,
            primary_ticker="META",
            event_type=EventType.CATALYST_FILING,
            catalyst_score=65.0,
        )
        obs = [
            Observation(
                source=SourceType.SEC,
                entity_id=sample_entity_id,
                payload={"form": "10-K"},
            )
        ]
        generator = TitleGenerator(use_llm=False)

        title, source = generator.generate_title(event, obs)

        assert "META" in title
        assert "10-K" in title
        assert "SEC" in title

    def test_flow_congress_with_trade_info(self, sample_entity_id):
        """Template generates flow congress title with trade info."""
        event = Event(
            primary_entity_id=sample_entity_id,
            primary_ticker="GOOGL",
            event_type=EventType.FLOW_CONGRESS,
            flow_score=75.0,
        )
        obs = [
            Observation(
                source=SourceType.CONGRESS,
                entity_id=sample_entity_id,
                payload={"member": "Nancy Pelosi", "type": "purchase"},
            )
        ]
        generator = TitleGenerator(use_llm=False)

        title, source = generator.generate_title(event, obs)

        assert "GOOGL" in title
        assert "Pelosi" in title
        assert "Purchase" in title

    def test_flow_13f_title(self, sample_entity_id):
        """Template generates flow 13F title."""
        event = Event(
            primary_entity_id=sample_entity_id,
            primary_ticker="AMZN",
            event_type=EventType.FLOW_13F,
            flow_score=60.0,
        )
        generator = TitleGenerator(use_llm=False)

        title, source = generator.generate_title(event, [])

        assert "AMZN" in title
        assert "Institutional" in title

    def test_prediction_shift_with_probability(self, sample_entity_id):
        """Template generates prediction shift title with probability change."""
        event = Event(
            primary_entity_id=sample_entity_id,
            primary_ticker="BTC",
            event_type=EventType.PREDICTION_SHIFT,
            catalyst_score=70.0,
        )
        obs = [
            Observation(
                source=SourceType.POLYMARKET,
                entity_id=sample_entity_id,
                payload={"probability_change": 15},
            )
        ]
        generator = TitleGenerator(use_llm=False)

        title, source = generator.generate_title(event, obs)

        assert "BTC" in title
        assert "Prediction" in title
        assert "15%" in title

    def test_mixed_event_with_source_count(self, sample_entity_id):
        """Template generates mixed event title with source count."""
        event = Event(
            primary_entity_id=sample_entity_id,
            primary_ticker="MSFT",
            event_type=EventType.MIXED,
            anomaly_score=65.0,
        )
        obs = [
            Observation(source=SourceType.EQUITIES, entity_id=sample_entity_id),
            Observation(source=SourceType.NEWS, entity_id=sample_entity_id),
            Observation(source=SourceType.SEC, entity_id=sample_entity_id),
        ]
        generator = TitleGenerator(use_llm=False)

        title, source = generator.generate_title(event, obs)

        assert "MSFT" in title
        assert "Multi-Signal" in title
        assert "3 Sources" in title

    def test_uncertain_event_default_format(self, sample_entity_id):
        """Template generates uncertain event with default format."""
        event = Event(
            primary_entity_id=sample_entity_id,
            primary_ticker="XYZ",
            event_type=EventType.UNCERTAIN,
            anomaly_score=50.0,
        )
        generator = TitleGenerator(use_llm=False)

        title, source = generator.generate_title(event, [])

        assert "XYZ" in title
        assert "Uncertain" in title

    def test_handles_missing_ticker(self):
        """Template handles missing ticker gracefully."""
        event = Event(
            primary_ticker=None,
            event_type=EventType.MARKET_ANOMALY,
        )
        generator = TitleGenerator(use_llm=False)

        title, source = generator.generate_title(event, [])

        assert "Unknown" in title


class TestTitleGeneratorConfiguration:
    """Tests for TitleGenerator configuration."""

    def test_lazy_provider_initialization(self):
        """TitleGenerator lazily initializes provider."""
        generator = TitleGenerator(use_llm=False)
        assert generator._provider is None
        assert generator._provider_initialized is False

    def test_provider_initialized_on_access(self):
        """TitleGenerator initializes provider on first access."""
        mock_provider = MockProvider()
        generator = TitleGenerator(provider=mock_provider)

        # Accessing provider should work
        assert generator.provider is mock_provider

    def test_passes_config_to_provider_selection(self):
        """TitleGenerator passes config to provider selection."""
        config = {"llm": {"provider": "mock", "timeout": 30}}
        generator = TitleGenerator(config=config)

        # Should not raise, should get mock provider
        provider = generator.provider
        assert provider is not None


class TestGenerateEventTitleFunction:
    """Tests for convenience function."""

    def test_generate_event_title_function(self, sample_event, sample_observations):
        """generate_event_title function works correctly."""
        title, source = generate_event_title(
            sample_event,
            sample_observations,
            use_llm=False,
        )

        assert len(title) > 0
        assert source == "template"

    def test_generate_event_title_with_config(self, sample_event):
        """generate_event_title accepts config."""
        config = {"llm": {"provider": "mock"}}
        title, source = generate_event_title(
            sample_event,
            config=config,
        )

        assert len(title) > 0

    def test_generate_event_title_without_observations(self, sample_event):
        """generate_event_title works without observations."""
        title, source = generate_event_title(sample_event, use_llm=False)

        assert len(title) > 0
        assert "AAPL" in title
