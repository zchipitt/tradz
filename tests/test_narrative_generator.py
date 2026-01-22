"""
Tests for the NarrativeGenerator class.
"""
from datetime import datetime, timezone
from uuid import uuid4

from src.tradz.models import FactTableEntry, FactType
from src.tradz.events.narrative_generator import (
    GenerationResult,
    NarrativeGenerator,
    NarrativeMetrics,
    generate_brief_with_llm,
)
from src.tradz.events.daily_brief_generator import (
    DailyBriefContent,
    EventSummary,
    DataQualitySummary,
)
from src.tradz.events.llm_provider import (
    MockProvider,
    LLMAPIError,
    LLMTimeoutError,
)


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_creation(self):
        """Test GenerationResult creation."""
        result = GenerationResult(
            content="Test content",
            source="llm",
            generation_time_ms=150.5,
        )

        assert result.content == "Test content"
        assert result.source == "llm"
        assert result.generation_time_ms == 150.5
        assert result.success is True
        assert result.error_message is None

    def test_creation_with_error(self):
        """Test GenerationResult with error."""
        result = GenerationResult(
            content="Fallback content",
            source="template",
            generation_time_ms=10.0,
            success=False,
            error_message="LLM timeout",
        )

        assert result.success is False
        assert result.error_message == "LLM timeout"


class TestNarrativeMetrics:
    """Tests for NarrativeMetrics dataclass."""

    def test_default_values(self):
        """Test NarrativeMetrics default values."""
        metrics = NarrativeMetrics()

        assert metrics.total_generations == 0
        assert metrics.llm_successes == 0
        assert metrics.template_fallbacks == 0
        assert metrics.total_time_ms == 0.0
        assert metrics.llm_errors == []

    def test_llm_success_rate_zero_generations(self):
        """Test success rate with no generations."""
        metrics = NarrativeMetrics()
        assert metrics.llm_success_rate == 0.0

    def test_llm_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = NarrativeMetrics(
            total_generations=10,
            llm_successes=7,
            template_fallbacks=3,
        )
        assert metrics.llm_success_rate == 70.0

    def test_average_time_calculation(self):
        """Test average time calculation."""
        metrics = NarrativeMetrics(
            total_generations=4,
            total_time_ms=400.0,
        )
        assert metrics.average_time_ms == 100.0

    def test_to_dict(self):
        """Test NarrativeMetrics to_dict."""
        metrics = NarrativeMetrics(
            total_generations=10,
            llm_successes=8,
            template_fallbacks=2,
            total_time_ms=1000.0,
            llm_errors=["Error 1", "Error 2"],
        )

        result = metrics.to_dict()

        assert result["total_generations"] == 10
        assert result["llm_successes"] == 8
        assert result["template_fallbacks"] == 2
        assert result["llm_success_rate"] == 80.0
        assert result["average_time_ms"] == 100.0
        assert result["total_time_ms"] == 1000.0
        assert len(result["llm_errors"]) == 2


class TestNarrativeGeneratorWithMock:
    """Tests for NarrativeGenerator using MockProvider."""

    def _create_event_summary(
        self,
        event_id: str = "",
        ticker: str = "AAPL",
        attention_score: float = 75.0,
    ) -> EventSummary:
        """Create a test EventSummary."""
        actual_event_id = event_id if event_id else str(uuid4())
        return EventSummary(
            event_id=actual_event_id,
            title=f"{ticker} Test Event",
            ticker=ticker,
            event_type="catalyst_news",
            attention_score=attention_score,
            anomaly_score=60.0,
            catalyst_score=70.0,
            flow_score=50.0,
            confidence_score=65.0,
            observation_count=5,
        )

    def _create_data_quality(self) -> DataQualitySummary:
        """Create test DataQualitySummary."""
        return DataQualitySummary(
            total_sources=7,
            healthy_count=6,
            degraded_count=1,
            error_count=0,
            overall_status="degraded",
            quality_message="1 source has stale data",
        )

    def _create_facts(self, _ticker: str = "AAPL") -> list:
        """Create test FactTableEntry list."""
        now = datetime.now(timezone.utc)
        obs_id = uuid4()

        return [
            FactTableEntry(
                fact_id=f"{str(obs_id)[:8]}_price",
                fact_type=FactType.PRICE.value,
                label="Price",
                value=175.50,
                unit="$",
                source="Yahoo Finance",
                timestamp=now,
                observation_id=obs_id,
            ),
            FactTableEntry(
                fact_id=f"{str(obs_id)[:8]}_change",
                fact_type=FactType.PRICE_CHANGE.value,
                label="Price Change",
                value=5.2,
                unit="%",
                source="Yahoo Finance",
                timestamp=now,
                observation_id=obs_id,
            ),
            FactTableEntry(
                fact_id=f"{str(obs_id)[:8]}_vol",
                fact_type=FactType.VOLUME_VS_AVG.value,
                label="Volume vs Avg",
                value=2.5,
                unit="x",
                source="Yahoo Finance",
                timestamp=now,
                observation_id=obs_id,
            ),
        ]

    def test_generate_with_llm_success(self):
        """Test narrative generation with successful LLM response."""
        mock_response = (
            "AAPL surged 5.2% on strong volume, leading today's signals. "
            "MSFT and GOOGL also showed notable activity. "
            "High conviction signals suggest reviewing trade ideas."
        )
        mock_provider = MockProvider(response=mock_response)
        generator = NarrativeGenerator(provider=mock_provider, use_llm=True)

        top_events = [self._create_event_summary("evt-1", "AAPL", 80)]
        data_quality = self._create_data_quality()
        facts_by_event = {"evt-1": self._create_facts("AAPL")}

        result = generator.generate_executive_summary(
            top_events, data_quality, facts_by_event
        )

        assert result.source == "llm"
        assert "AAPL" in result.content
        assert result.generation_time_ms > 0
        assert mock_provider.call_count == 1

    def test_generate_with_llm_empty_response_falls_back(self):
        """Test that empty LLM response triggers template fallback."""
        mock_provider = MockProvider(response="")  # Empty response
        generator = NarrativeGenerator(provider=mock_provider, use_llm=True)

        top_events = [self._create_event_summary("evt-1", "AAPL", 80)]
        facts_by_event = {"evt-1": self._create_facts("AAPL")}

        result = generator.generate_executive_summary(
            top_events, None, facts_by_event
        )

        assert result.source == "template"
        assert "AAPL" in result.content

    def test_generate_with_llm_short_response_falls_back(self):
        """Test that too-short LLM response triggers template fallback."""
        mock_provider = MockProvider(response="Too short")  # < 50 chars
        generator = NarrativeGenerator(provider=mock_provider, use_llm=True)

        top_events = [self._create_event_summary("evt-1", "AAPL", 80)]
        facts_by_event = {"evt-1": self._create_facts("AAPL")}

        result = generator.generate_executive_summary(
            top_events, None, facts_by_event
        )

        assert result.source == "template"

    def test_generate_with_llm_timeout_falls_back(self):
        """Test that LLM timeout triggers template fallback."""
        mock_provider = MockProvider(
            should_fail=True,
            fail_with=LLMTimeoutError("Timeout"),
        )
        generator = NarrativeGenerator(provider=mock_provider, use_llm=True)

        top_events = [self._create_event_summary("evt-1", "AAPL", 80)]
        facts_by_event = {"evt-1": self._create_facts("AAPL")}

        result = generator.generate_executive_summary(
            top_events, None, facts_by_event
        )

        assert result.source == "template"
        assert generator.metrics.llm_errors  # Error was recorded

    def test_generate_with_llm_api_error_falls_back(self):
        """Test that LLM API error triggers template fallback."""
        mock_provider = MockProvider(
            should_fail=True,
            fail_with=LLMAPIError("API Error"),
        )
        generator = NarrativeGenerator(provider=mock_provider, use_llm=True)

        top_events = [self._create_event_summary("evt-1", "AAPL", 80)]
        facts_by_event = {"evt-1": self._create_facts("AAPL")}

        result = generator.generate_executive_summary(
            top_events, None, facts_by_event
        )

        assert result.source == "template"
        assert "API Error" in generator.metrics.llm_errors[0]

    def test_generate_with_use_llm_false_uses_template(self):
        """Test that use_llm=False always uses template."""
        mock_provider = MockProvider(response="LLM response")
        generator = NarrativeGenerator(provider=mock_provider, use_llm=False)

        top_events = [self._create_event_summary("evt-1", "AAPL", 80)]
        facts_by_event = {"evt-1": self._create_facts("AAPL")}

        result = generator.generate_executive_summary(
            top_events, None, facts_by_event
        )

        assert result.source == "template"
        assert mock_provider.call_count == 0  # LLM never called

    def test_template_summary_no_events(self):
        """Test template summary with no events."""
        generator = NarrativeGenerator(use_llm=False)

        result = generator.generate_executive_summary([], None, {})

        assert result.source == "template"
        assert "No significant events" in result.content

    def test_template_summary_with_events(self):
        """Test template summary with events."""
        generator = NarrativeGenerator(use_llm=False)

        top_events = [
            self._create_event_summary("evt-1", "AAPL", 80),
            self._create_event_summary("evt-2", "MSFT", 70),
        ]

        result = generator.generate_executive_summary(top_events, None, {})

        assert result.source == "template"
        assert "AAPL" in result.content
        assert "MSFT" in result.content

    def test_template_summary_high_attention(self):
        """Test template summary recommends action for high attention."""
        generator = NarrativeGenerator(use_llm=False)

        top_events = [
            self._create_event_summary("evt-1", "AAPL", 85),  # High attention
        ]

        result = generator.generate_executive_summary(top_events, None, {})

        assert "High conviction" in result.content or "reviewing" in result.content.lower()

    def test_template_summary_low_attention(self):
        """Test template summary recommends monitoring for low attention."""
        generator = NarrativeGenerator(use_llm=False)

        # Create event with low attention score
        event = self._create_event_summary("evt-1", "AAPL", 35)

        result = generator.generate_executive_summary([event], None, {})

        assert "Low-conviction" in result.content or "monitoring" in result.content.lower()

    def test_template_summary_with_facts(self):
        """Test template summary uses facts when available."""
        generator = NarrativeGenerator(use_llm=False)

        event = self._create_event_summary("evt-1", "AAPL", 75)
        facts_by_event = {"evt-1": self._create_facts("AAPL")}

        result = generator.generate_executive_summary([event], None, facts_by_event)

        # Should include some fact detail
        assert "AAPL" in result.content

    def test_generate_brief_narrative_updates_content(self):
        """Test that generate_brief_narrative updates content correctly."""
        mock_response = (
            "AAPL shows strong momentum with 5.2% gain. "
            "Volume exceeds average by 2.5x. "
            "Consider reviewing trade opportunities."
        )
        mock_provider = MockProvider(response=mock_response)
        generator = NarrativeGenerator(provider=mock_provider, use_llm=True)

        content = DailyBriefContent(
            executive_summary="",  # Empty, will be generated
            top_events=[self._create_event_summary("evt-1", "AAPL", 80)],
            data_quality=self._create_data_quality(),
        )
        facts_by_event = {"evt-1": self._create_facts("AAPL")}

        result = generator.generate_brief_narrative(content, facts_by_event)

        assert result.executive_summary != ""
        assert result.generation_method == "claude"  # LLM succeeded

    def test_generate_brief_narrative_template_fallback(self):
        """Test that generate_brief_narrative falls back to template."""
        mock_provider = MockProvider(
            should_fail=True,
            fail_with=LLMAPIError("Error"),
        )
        generator = NarrativeGenerator(provider=mock_provider, use_llm=True)

        content = DailyBriefContent(
            executive_summary="",
            top_events=[self._create_event_summary("evt-1", "AAPL", 80)],
        )

        result = generator.generate_brief_narrative(content, {})

        assert result.executive_summary != ""
        assert result.generation_method == "template"

    def test_metrics_tracking(self):
        """Test that metrics are tracked correctly."""
        mock_provider = MockProvider(response="Valid response with enough characters to pass validation.")
        generator = NarrativeGenerator(provider=mock_provider, use_llm=True)

        top_events = [self._create_event_summary("evt-1", "AAPL", 80)]

        # First generation - success
        generator.generate_executive_summary(top_events, None, {})

        assert generator.metrics.total_generations == 1
        assert generator.metrics.llm_successes == 1
        assert generator.metrics.template_fallbacks == 0

        # Second generation with failure
        mock_provider.should_fail = True
        mock_provider.fail_with = LLMAPIError("Error")
        generator.generate_executive_summary(top_events, None, {})

        assert generator.metrics.total_generations == 2
        assert generator.metrics.llm_successes == 1
        assert generator.metrics.template_fallbacks == 1

    def test_get_metrics(self):
        """Test get_metrics returns correct data."""
        generator = NarrativeGenerator(use_llm=False)
        top_events = [self._create_event_summary("evt-1", "AAPL", 80)]

        generator.generate_executive_summary(top_events, None, {})
        generator.generate_executive_summary(top_events, None, {})

        metrics = generator.get_metrics()

        assert metrics["total_generations"] == 2
        assert metrics["template_fallbacks"] == 2
        assert metrics["llm_success_rate"] == 0.0

    def test_reset_metrics(self):
        """Test reset_metrics clears all metrics."""
        generator = NarrativeGenerator(use_llm=False)
        top_events = [self._create_event_summary("evt-1", "AAPL", 80)]

        generator.generate_executive_summary(top_events, None, {})
        generator.reset_metrics()

        assert generator.metrics.total_generations == 0
        assert generator.metrics.llm_successes == 0
        assert generator.metrics.template_fallbacks == 0

    def test_clean_narrative_removes_prefixes(self):
        """Test that narrative cleaning removes common prefixes."""
        generator = NarrativeGenerator(use_llm=False)

        # Test various prefix patterns
        test_cases = [
            ("Summary: The market shows...", "The market shows..."),
            ("Executive Summary: Strong performance...", "Strong performance..."),
            ("Here is the summary: Test content...", "Test content..."),
            ("**Summary:** Bold text...", "Bold text..."),
        ]

        for input_text, expected_start in test_cases:
            cleaned = generator._clean_narrative(input_text)
            assert cleaned.startswith(expected_start.split("...")[0]), f"Failed for: {input_text}"

    def test_clean_narrative_removes_quotes(self):
        """Test that narrative cleaning removes quotes."""
        generator = NarrativeGenerator(use_llm=False)

        assert generator._clean_narrative('"Quoted text"') == "Quoted text"
        assert generator._clean_narrative("'Single quoted'") == "Single quoted"

    def test_clean_narrative_truncates_long_text(self):
        """Test that narrative cleaning truncates very long text."""
        generator = NarrativeGenerator(use_llm=False)

        long_text = "A" * 600  # Very long
        cleaned = generator._clean_narrative(long_text)

        assert len(cleaned) <= 500


class TestGenerateBriefWithLlm:
    """Tests for the convenience function."""

    def test_generate_brief_with_llm_function(self):
        """Test the convenience function."""
        content = DailyBriefContent(
            executive_summary="",
            top_events=[
                EventSummary(
                    event_id="test",
                    title="Test Event",
                    ticker="AAPL",
                    event_type="catalyst_news",
                    attention_score=75.0,
                    anomaly_score=60.0,
                    catalyst_score=70.0,
                    flow_score=50.0,
                    confidence_score=65.0,
                    observation_count=5,
                )
            ],
        )

        result = generate_brief_with_llm(content, use_llm=False)

        assert result.executive_summary != ""
        assert result.generation_method == "template"


class TestFactFormatting:
    """Tests for fact value formatting."""

    def test_format_percentage(self):
        """Test percentage formatting."""
        generator = NarrativeGenerator(use_llm=False)

        fact = FactTableEntry(
            fact_id="test",
            fact_type=FactType.PRICE_CHANGE.value,
            label="Change",
            value=5.23,
            unit="%",
            source="Test",
            timestamp=datetime.now(timezone.utc),
            observation_id=uuid4(),
        )

        formatted = generator._format_fact_value(fact)
        assert formatted == "+5.2%"

    def test_format_negative_percentage(self):
        """Test negative percentage formatting."""
        generator = NarrativeGenerator(use_llm=False)

        fact = FactTableEntry(
            fact_id="test",
            fact_type=FactType.PRICE_CHANGE.value,
            label="Change",
            value=-3.5,
            unit="%",
            source="Test",
            timestamp=datetime.now(timezone.utc),
            observation_id=uuid4(),
        )

        formatted = generator._format_fact_value(fact)
        assert formatted == "-3.5%"

    def test_format_large_dollar_amount(self):
        """Test large dollar amount formatting."""
        generator = NarrativeGenerator(use_llm=False)

        fact = FactTableEntry(
            fact_id="test",
            fact_type=FactType.PRICE.value,
            label="Value",
            value=1500000,
            unit="$",
            source="Test",
            timestamp=datetime.now(timezone.utc),
            observation_id=uuid4(),
        )

        formatted = generator._format_fact_value(fact)
        assert formatted == "$1.5M"

    def test_format_medium_dollar_amount(self):
        """Test medium dollar amount formatting."""
        generator = NarrativeGenerator(use_llm=False)

        fact = FactTableEntry(
            fact_id="test",
            fact_type=FactType.PRICE.value,
            label="Value",
            value=50000,
            unit="$",
            source="Test",
            timestamp=datetime.now(timezone.utc),
            observation_id=uuid4(),
        )

        formatted = generator._format_fact_value(fact)
        assert formatted == "$50.0K"

    def test_format_multiplier(self):
        """Test multiplier formatting."""
        generator = NarrativeGenerator(use_llm=False)

        fact = FactTableEntry(
            fact_id="test",
            fact_type=FactType.VOLUME_VS_AVG.value,
            label="Volume vs Avg",
            value=2.5,
            unit="x",
            source="Test",
            timestamp=datetime.now(timezone.utc),
            observation_id=uuid4(),
        )

        formatted = generator._format_fact_value(fact)
        assert formatted == "2.5x"

    def test_format_string_value(self):
        """Test string value formatting."""
        generator = NarrativeGenerator(use_llm=False)

        fact = FactTableEntry(
            fact_id="test",
            fact_type=FactType.TRADE_TYPE.value,
            label="Trade Type",
            value="Purchase",
            source="Test",
            timestamp=datetime.now(timezone.utc),
            observation_id=uuid4(),
        )

        formatted = generator._format_fact_value(fact)
        assert formatted == "Purchase"


class TestLLMPromptBuilding:
    """Tests for LLM prompt building."""

    def test_build_executive_summary_prompt_includes_facts(self):
        """Test that prompt includes fact data."""
        generator = NarrativeGenerator(use_llm=False)

        event = EventSummary(
            event_id="evt-1",
            title="AAPL Test Event",
            ticker="AAPL",
            event_type="catalyst_news",
            attention_score=75.0,
            anomaly_score=60.0,
            catalyst_score=70.0,
            flow_score=50.0,
            confidence_score=65.0,
            observation_count=5,
        )

        facts = [
            FactTableEntry(
                fact_id="test",
                fact_type=FactType.PRICE_CHANGE.value,
                label="Price Change",
                value=5.2,
                unit="%",
                source="Test",
                timestamp=datetime.now(timezone.utc),
                observation_id=uuid4(),
            ),
        ]

        data_quality = DataQualitySummary(
            total_sources=7,
            healthy_count=6,
            degraded_count=1,
            error_count=0,
            overall_status="degraded",
        )

        prompt = generator._build_executive_summary_prompt(
            [event], data_quality, {"evt-1": facts}
        )

        assert "AAPL" in prompt
        assert "Price Change" in prompt
        assert "Sources: 6/7 healthy" in prompt

    def test_build_executive_summary_prompt_no_facts(self):
        """Test prompt building when no facts available."""
        generator = NarrativeGenerator(use_llm=False)

        event = EventSummary(
            event_id="evt-1",
            title="AAPL Test Event",
            ticker="AAPL",
            event_type="catalyst_news",
            attention_score=75.0,
            anomaly_score=60.0,
            catalyst_score=70.0,
            flow_score=50.0,
            confidence_score=65.0,
            observation_count=5,
        )

        prompt = generator._build_executive_summary_prompt([event], None, {})

        assert "AAPL" in prompt
        assert "No detailed facts available" in prompt
