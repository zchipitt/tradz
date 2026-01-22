"""
Daily brief narrative generation with LLM and template fallback.

Generates human-readable narratives for daily briefs using LLM when available,
with a reliable template fallback when LLM fails.

Key features:
- LLM generates executive_summary from FactTable data (no fabrication)
- LLM generates natural language descriptions for each section
- Template fallback generates bullet-point format when LLM fails
- Template uses only FactTableEntry data for content
- Fallback triggered on: LLM timeout, API error, empty response
- Generation time logged for monitoring
"""
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..models import FactTableEntry
from .daily_brief_generator import (
    DailyBriefContent,
    EventSummary,
    DataQualitySummary,
)
from .llm_provider import (
    LLMProvider,
    LLMProviderError,
    get_default_provider,
)

logger = logging.getLogger(__name__)


# LLM Prompt for executive summary
EXECUTIVE_SUMMARY_PROMPT = """Generate a concise executive summary for a daily trading brief.

## Facts (verified data only - do not fabricate):
{facts_summary}

## Top Events by Attention Score:
{top_events_summary}

## Data Quality:
{data_quality_summary}

## Requirements:
1. Write exactly 3 sentences
2. First sentence: Highlight the most significant event and its key metric
3. Second sentence: Mention 1-2 other notable events briefly
4. Third sentence: Provide an actionable recommendation based on signal strength
5. Use ONLY the facts provided above - do not invent any data
6. Be specific with numbers and percentages from the facts
7. Avoid vague language like "significant activity" without backing data

## Output:
Write the executive summary (3 sentences only, no other text):"""


# LLM Prompt for event descriptions
EVENT_DESCRIPTION_PROMPT = """Generate a brief description for this trading event.

## Event Details:
- Ticker: {ticker}
- Event Type: {event_type}
- Attention Score: {attention_score:.0f}/100

## Scores:
- Anomaly: {anomaly_score:.0f} (market deviation)
- Catalyst: {catalyst_score:.0f} (news/filings)
- Flow: {flow_score:.0f} (trading activity)
- Confidence: {confidence_score:.0f} (data quality)

## Evidence Facts:
{facts}

## Requirements:
1. Write 1-2 sentences max
2. Focus on the most actionable insight
3. Include specific numbers from the facts
4. Do not fabricate any data

## Output:
Write the description (1-2 sentences only):"""


# LLM Prompt for trade idea descriptions
TRADE_IDEA_PROMPT = """Generate a brief rationale for this trade idea.

## Trade Setup:
- Ticker: {ticker}
- Direction: {direction}
- Entry Zone: {entry_zone}
- Target: {target}
- Stop Loss: {stop_loss}
- Confidence: {confidence:.0f}%

## Supporting Facts:
{facts}

## Requirements:
1. Write 1-2 sentences explaining WHY this setup makes sense
2. Reference specific facts that support the trade
3. Mention the key invalidation risk
4. Do not fabricate any data

## Output:
Write the rationale (1-2 sentences only):"""


@dataclass
class GenerationResult:
    """Result of a narrative generation attempt."""

    content: str
    source: str  # "llm" or "template"
    generation_time_ms: float
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class NarrativeMetrics:
    """Metrics for narrative generation performance."""

    total_generations: int = 0
    llm_successes: int = 0
    template_fallbacks: int = 0
    total_time_ms: float = 0.0
    llm_errors: List[str] = field(default_factory=list)

    @property
    def llm_success_rate(self) -> float:
        """Calculate LLM success rate."""
        if self.total_generations == 0:
            return 0.0
        return self.llm_successes / self.total_generations * 100

    @property
    def average_time_ms(self) -> float:
        """Calculate average generation time."""
        if self.total_generations == 0:
            return 0.0
        return self.total_time_ms / self.total_generations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_generations": self.total_generations,
            "llm_successes": self.llm_successes,
            "template_fallbacks": self.template_fallbacks,
            "llm_success_rate": self.llm_success_rate,
            "average_time_ms": self.average_time_ms,
            "total_time_ms": self.total_time_ms,
            "llm_errors": self.llm_errors[-10:],  # Last 10 errors
        }


class NarrativeGenerator:
    """
    Generates narrative content for daily briefs using LLM with template fallback.

    Provides reliable narrative generation by:
    1. Attempting LLM-based generation for natural language narratives
    2. Falling back to template generation when LLM fails
    3. Using only FactTableEntry data to prevent fabrication
    4. Tracking generation metrics for monitoring
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        config: Optional[Dict[str, Any]] = None,
        use_llm: bool = True,
    ):
        """
        Initialize narrative generator.

        Args:
            provider: LLM provider to use. Auto-detected if not provided.
            config: Configuration dict.
            use_llm: Whether to attempt LLM generation. If False, always uses template.
        """
        self.config = config or {}
        self.use_llm = use_llm
        self._provider: Optional[LLMProvider] = provider
        self._provider_initialized = provider is not None
        self.metrics = NarrativeMetrics()

    @property
    def provider(self) -> Optional[LLMProvider]:
        """Lazily initialize LLM provider."""
        if not self._provider_initialized:
            self._provider_initialized = True
            if self.use_llm:
                try:
                    self._provider = get_default_provider(self.config)
                    logger.info(f"Using LLM provider for narratives: {self._provider.name}")
                except LLMProviderError as e:
                    logger.warning(f"No LLM provider available for narratives: {e}")
                    self._provider = None
        return self._provider

    def generate_brief_narrative(
        self,
        content: DailyBriefContent,
        facts_by_event: Optional[Dict[str, List[FactTableEntry]]] = None,
    ) -> DailyBriefContent:
        """
        Enhance DailyBriefContent with LLM-generated narratives.

        Generates:
        - Executive summary from facts
        - Enhanced event descriptions
        - Enhanced trade idea rationales

        Falls back to template format on LLM failure.

        Args:
            content: DailyBriefContent with basic data populated.
            facts_by_event: Optional dict mapping event_id to facts.

        Returns:
            Enhanced DailyBriefContent with LLM or template narratives.
        """
        facts_by_event = facts_by_event or {}

        # Generate executive summary
        summary_result = self.generate_executive_summary(
            content.top_events,
            content.data_quality,
            facts_by_event,
        )
        content.executive_summary = summary_result.content

        # Set generation method based on summary result
        content.generation_method = "claude" if summary_result.source == "llm" else "template"

        logger.info(
            f"Generated daily brief narrative: method={content.generation_method}, "
            f"time={summary_result.generation_time_ms:.0f}ms"
        )

        return content

    def generate_executive_summary(
        self,
        top_events: List[EventSummary],
        data_quality: Optional[DataQualitySummary],
        facts_by_event: Dict[str, List[FactTableEntry]],
    ) -> GenerationResult:
        """
        Generate executive summary for the daily brief.

        Args:
            top_events: Top events by attention score.
            data_quality: Data quality summary.
            facts_by_event: Facts mapped by event ID.

        Returns:
            GenerationResult with summary content.
        """
        start_time = time.time()

        # Try LLM first if available and enabled
        if self.use_llm and self.provider is not None:
            try:
                summary = self._generate_llm_executive_summary(
                    top_events, data_quality, facts_by_event
                )
                if summary and len(summary.strip()) >= 50:
                    generation_time = (time.time() - start_time) * 1000
                    self._record_success("llm", generation_time)
                    logger.info(f"Generated LLM executive summary in {generation_time:.0f}ms")
                    return GenerationResult(
                        content=summary.strip(),
                        source="llm",
                        generation_time_ms=generation_time,
                    )
                logger.warning("LLM returned too short executive summary, using template")
            except LLMProviderError as e:
                self._record_error(str(e))
                logger.warning(f"LLM executive summary generation failed: {e}")
            except Exception as e:
                self._record_error(str(e))
                logger.error(f"Unexpected error in LLM summary generation: {e}")

        # Fall back to template
        summary = self._generate_template_executive_summary(
            top_events, data_quality, facts_by_event
        )
        generation_time = (time.time() - start_time) * 1000
        self._record_success("template", generation_time)
        logger.info(f"Generated template executive summary in {generation_time:.0f}ms")

        return GenerationResult(
            content=summary,
            source="template",
            generation_time_ms=generation_time,
        )

    def _generate_llm_executive_summary(
        self,
        top_events: List[EventSummary],
        data_quality: Optional[DataQualitySummary],
        facts_by_event: Dict[str, List[FactTableEntry]],
    ) -> str:
        """Generate executive summary using LLM."""
        if self.provider is None:
            raise LLMProviderError("No LLM provider available")

        # Build prompt
        prompt = self._build_executive_summary_prompt(
            top_events, data_quality, facts_by_event
        )

        # Generate summary
        response = self.provider.generate(prompt)

        # Clean up response
        return self._clean_narrative(response)

    def _build_executive_summary_prompt(
        self,
        top_events: List[EventSummary],
        data_quality: Optional[DataQualitySummary],
        facts_by_event: Dict[str, List[FactTableEntry]],
    ) -> str:
        """Build the prompt for executive summary generation."""
        # Collect all facts for top events
        facts_lines = []
        for event in top_events[:3]:
            event_facts = facts_by_event.get(event.event_id, [])
            for fact in event_facts[:5]:  # Limit facts per event
                value_str = self._format_fact_value(fact)
                facts_lines.append(f"- {event.ticker or 'Unknown'}: {fact.label} = {value_str}")

        facts_summary = "\n".join(facts_lines) if facts_lines else "No detailed facts available."

        # Build top events summary
        events_lines = []
        for event in top_events[:5]:
            events_lines.append(
                f"- {event.ticker or 'Unknown'}: {event.event_type} "
                f"(attention={event.attention_score:.0f})"
            )
        top_events_summary = "\n".join(events_lines) if events_lines else "No events to report."

        # Build data quality summary
        if data_quality:
            data_quality_summary = (
                f"Sources: {data_quality.healthy_count}/{data_quality.total_sources} healthy. "
                f"Status: {data_quality.overall_status}."
            )
        else:
            data_quality_summary = "Data quality: Unknown"

        return EXECUTIVE_SUMMARY_PROMPT.format(
            facts_summary=facts_summary,
            top_events_summary=top_events_summary,
            data_quality_summary=data_quality_summary,
        )

    def _generate_template_executive_summary(
        self,
        top_events: List[EventSummary],
        _data_quality: Optional[DataQualitySummary],
        facts_by_event: Dict[str, List[FactTableEntry]],
    ) -> str:
        """
        Generate executive summary using template format.

        Uses bullet-point format with only FactTableEntry data.
        """
        if not top_events:
            return (
                "No significant events to report today. "
                "Market conditions appear normal. "
                "Continue monitoring key positions."
            )

        lines = []

        # First sentence: top event with key fact
        top = top_events[0]
        ticker = top.ticker or "Unknown asset"

        # Find most interesting fact for top event
        top_facts = facts_by_event.get(top.event_id, [])
        fact_detail = self._get_key_fact_detail(top_facts)

        if fact_detail:
            lines.append(f"Today's top signal is {ticker} ({fact_detail}).")
        else:
            lines.append(
                f"Today's top signal is {ticker} with an attention score of {top.attention_score:.0f}/100."
            )

        # Second sentence: other notable events
        if len(top_events) >= 2:
            others = [e.ticker or "Unknown" for e in top_events[1:3] if e.ticker]
            if others:
                others_str = " and ".join(others)
                lines.append(f"Additional notable activity detected in {others_str}.")
        else:
            lines.append("No other significant events detected today.")

        # Third sentence: action recommendation
        if top.attention_score >= 70:
            lines.append("High conviction signals suggest reviewing actionable trade ideas.")
        elif top.attention_score >= 50:
            lines.append("Moderate signals warrant further investigation before taking positions.")
        else:
            lines.append("Low-conviction signals today; focus on monitoring open positions.")

        return " ".join(lines)

    def _get_key_fact_detail(self, facts: List[FactTableEntry]) -> Optional[str]:
        """Extract a key fact detail for the summary."""
        # Priority order for interesting facts
        priority_types = [
            "price_change",
            "volume_vs_avg",
            "trade_type",
            "filing_type",
            "probability_change",
        ]

        for fact_type in priority_types:
            for fact in facts:
                if fact.fact_type == fact_type:
                    value_str = self._format_fact_value(fact)
                    return f"{fact.label}: {value_str}"

        # Fallback to first fact with a numeric value
        for fact in facts:
            if isinstance(fact.value, (int, float)):
                value_str = self._format_fact_value(fact)
                return f"{fact.label}: {value_str}"

        return None

    def _format_fact_value(self, fact: FactTableEntry) -> str:
        """Format a fact value with its unit."""
        value = fact.value
        unit = fact.unit or ""

        if isinstance(value, float):
            if unit == "%":
                return f"{value:+.1f}%"
            elif unit == "$":
                if value >= 1_000_000:
                    return f"${value/1_000_000:.1f}M"
                elif value >= 1_000:
                    return f"${value/1_000:.1f}K"
                return f"${value:.2f}"
            elif unit == "x":
                return f"{value:.1f}x"
            return f"{value:.2f}{unit}"
        elif isinstance(value, int):
            if unit == "$":
                if value >= 1_000_000:
                    return f"${value/1_000_000:.1f}M"
                elif value >= 1_000:
                    return f"${value/1_000:.1f}K"
                return f"${value}"
            return f"{value:,}{unit}"

        return str(value)

    def _clean_narrative(self, response: str) -> str:
        """
        Clean up LLM response to extract narrative.

        Removes quotes, extra whitespace, and any preamble text.
        """
        text = response.strip()

        # Remove common LLM preamble patterns
        prefixes_to_remove = [
            "Summary:",
            "Executive Summary:",
            "Here is the summary:",
            "Here's the summary:",
            "Here is the executive summary:",
            "**Summary:**",
            "**Executive Summary:**",
        ]
        for prefix in prefixes_to_remove:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()

        # Remove quotes
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]

        # Remove markdown bold markers
        text = text.replace("**", "")

        # Truncate if too long (executive summary should be ~3 sentences)
        if len(text) > 500:
            # Try to cut at sentence boundary
            sentences = text.split(".")
            result = []
            length = 0
            for sentence in sentences[:4]:  # Max 4 sentences
                if length + len(sentence) < 480:
                    result.append(sentence)
                    length += len(sentence) + 1
            text = ".".join(result)
            if not text.endswith("."):
                text += "."

        return text

    def _record_success(self, source: str, generation_time: float):
        """Record a successful generation."""
        self.metrics.total_generations += 1
        self.metrics.total_time_ms += generation_time
        if source == "llm":
            self.metrics.llm_successes += 1
        else:
            self.metrics.template_fallbacks += 1

    def _record_error(self, error_message: str):
        """Record an LLM error."""
        self.metrics.llm_errors.append(error_message)
        # Keep only last 100 errors
        if len(self.metrics.llm_errors) > 100:
            self.metrics.llm_errors = self.metrics.llm_errors[-100:]

    def get_metrics(self) -> Dict[str, Any]:
        """Get generation metrics for monitoring."""
        return self.metrics.to_dict()

    def reset_metrics(self):
        """Reset generation metrics."""
        self.metrics = NarrativeMetrics()


def generate_brief_with_llm(
    content: DailyBriefContent,
    facts_by_event: Optional[Dict[str, List[FactTableEntry]]] = None,
    config: Optional[Dict[str, Any]] = None,
    use_llm: bool = True,
) -> DailyBriefContent:
    """
    Convenience function to enhance a daily brief with LLM narratives.

    Args:
        content: DailyBriefContent with basic data.
        facts_by_event: Optional dict mapping event_id to facts.
        config: Optional configuration dict.
        use_llm: Whether to attempt LLM generation.

    Returns:
        Enhanced DailyBriefContent.
    """
    generator = NarrativeGenerator(config=config, use_llm=use_llm)
    return generator.generate_brief_narrative(content, facts_by_event)
