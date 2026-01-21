"""
Event title generation with LLM and template fallback.

Generates human-readable titles for events using LLM when available,
with a reliable template fallback when LLM fails.
"""
import logging
from typing import Any, Dict, List, Optional

from ..models import Event, EventType, Observation, SourceType
from .llm_provider import (
    LLMProvider,
    LLMProviderError,
    get_default_provider,
)

logger = logging.getLogger(__name__)


# Title format: '[Entity] [Action Verb] [Key Detail]'
# Example: 'AAPL Surges 8% on Strong Earnings Beat'
TITLE_PROMPT_TEMPLATE = """Generate a concise, news-headline-style title for a trading event.

Event Context:
- Symbol: {symbol}
- Event Type: {event_type}
- Attention Score: {attention_score:.0f}/100
- Key Metrics:
{key_metrics}

Evidence Summary:
{evidence_summary}

Requirements:
1. Format: '[Symbol] [Action Verb] [Key Detail]'
2. Use active, impactful verbs (Surges, Plunges, Reveals, Files, Trades)
3. Include the most significant metric or catalyst
4. Maximum 80 characters
5. Do NOT use quotes or special formatting
6. Examples:
   - AAPL Surges 8% on Strong Earnings Beat
   - NVDA Files 10-K Showing Record Revenue
   - TSLA Draws Congressional Attention with $2M Trade

Generate only the title, nothing else:"""


class TitleGenerator:
    """
    Generates event titles using LLM with template fallback.

    Provides reliable title generation for events by:
    1. Attempting LLM-based generation for natural language titles
    2. Falling back to template generation when LLM fails
    3. Storing title source metadata for tracking
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        config: Optional[Dict[str, Any]] = None,
        use_llm: bool = True,
    ):
        """
        Initialize title generator.

        Args:
            provider: LLM provider to use. Auto-detected if not provided.
            config: Configuration dict.
            use_llm: Whether to attempt LLM generation. If False, always uses template.
        """
        self.config = config or {}
        self.use_llm = use_llm
        self._provider: Optional[LLMProvider] = provider
        self._provider_initialized = provider is not None

    @property
    def provider(self) -> Optional[LLMProvider]:
        """Lazily initialize LLM provider."""
        if not self._provider_initialized:
            self._provider_initialized = True
            if self.use_llm:
                try:
                    self._provider = get_default_provider(self.config)
                    logger.info(f"Using LLM provider: {self._provider.name}")
                except LLMProviderError as e:
                    logger.warning(f"No LLM provider available: {e}")
                    self._provider = None
        return self._provider

    def generate_title(
        self,
        event: Event,
        observations: Optional[List[Observation]] = None,
    ) -> tuple[str, str]:
        """
        Generate a title for an event.

        Attempts LLM generation first, falls back to template on failure.

        Args:
            event: The event to generate a title for.
            observations: Optional list of observations for context.

        Returns:
            Tuple of (title, source) where source is 'llm' or 'template'.
        """
        observations = observations or []

        # Try LLM first if available and enabled
        if self.use_llm and self.provider is not None:
            try:
                title = self._generate_llm_title(event, observations)
                if title and len(title.strip()) >= 10:
                    logger.info(f"Generated LLM title for {event.primary_ticker}: {title}")
                    return title.strip(), "llm"
                logger.warning("LLM returned empty or too short title, using template")
            except LLMProviderError as e:
                logger.warning(f"LLM title generation failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in LLM title generation: {e}")

        # Fall back to template
        title = self._generate_template_title(event, observations)
        logger.info(f"Generated template title for {event.primary_ticker}: {title}")
        return title, "template"

    def _generate_llm_title(
        self,
        event: Event,
        observations: List[Observation],
    ) -> str:
        """
        Generate title using LLM.

        Args:
            event: The event to generate a title for.
            observations: Observations for context.

        Returns:
            Generated title string.
        """
        if self.provider is None:
            raise LLMProviderError("No LLM provider available")

        # Build prompt
        prompt = self._build_title_prompt(event, observations)

        # Generate title
        response = self.provider.generate(prompt)

        # Clean up response
        title = self._clean_title(response)

        return title

    def _build_title_prompt(
        self,
        event: Event,
        observations: List[Observation],
    ) -> str:
        """
        Build the prompt for LLM title generation.

        Args:
            event: The event.
            observations: Related observations.

        Returns:
            Formatted prompt string.
        """
        symbol = event.primary_ticker or "Unknown"
        event_type = event.event_type.value.replace("_", " ").title()
        attention_score = event.attention_score

        # Extract key metrics from event scores
        key_metrics = self._format_key_metrics(event)

        # Summarize evidence from observations
        evidence_summary = self._format_evidence_summary(observations)

        return TITLE_PROMPT_TEMPLATE.format(
            symbol=symbol,
            event_type=event_type,
            attention_score=attention_score,
            key_metrics=key_metrics,
            evidence_summary=evidence_summary,
        )

    def _format_key_metrics(self, event: Event) -> str:
        """Format event scores as key metrics for the prompt."""
        metrics = []

        # Include notable scores
        if event.anomaly_score > 60:
            metrics.append(f"  - Anomaly: {event.anomaly_score:.0f}/100 (significant market deviation)")
        if event.catalyst_score > 60:
            metrics.append(f"  - Catalyst: {event.catalyst_score:.0f}/100 (notable news/filings)")
        if event.flow_score > 60:
            metrics.append(f"  - Flow: {event.flow_score:.0f}/100 (unusual trading activity)")
        if event.confidence_score > 70:
            metrics.append(f"  - Confidence: {event.confidence_score:.0f}/100 (high data quality)")

        if not metrics:
            metrics.append(f"  - Anomaly: {event.anomaly_score:.0f}, Catalyst: {event.catalyst_score:.0f}")
            metrics.append(f"  - Flow: {event.flow_score:.0f}, Confidence: {event.confidence_score:.0f}")

        return "\n".join(metrics)

    def _format_evidence_summary(self, observations: List[Observation]) -> str:
        """Format observations as evidence summary for the prompt."""
        if not observations:
            return "  - No detailed evidence available"

        summary_parts = []
        source_counts: Dict[SourceType, int] = {}

        for obs in observations:
            source_counts[obs.source] = source_counts.get(obs.source, 0) + 1

            # Include up to 3 observation summaries
            if len(summary_parts) < 3 and obs.summary:
                summary_parts.append(f"  - [{obs.source.value}] {obs.summary[:100]}")

        # Add source breakdown
        sources = ", ".join(f"{s.value}: {c}" for s, c in sorted(source_counts.items(), key=lambda x: -x[1]))
        summary_parts.insert(0, f"  - Sources: {sources}")

        return "\n".join(summary_parts[:4])

    def _clean_title(self, response: str) -> str:
        """
        Clean up LLM response to extract title.

        Removes quotes, extra whitespace, and any preamble text.

        Args:
            response: Raw LLM response.

        Returns:
            Cleaned title string.
        """
        title = response.strip()

        # Remove common LLM preamble patterns
        prefixes_to_remove = [
            "Title:",
            "Here is the title:",
            "Here's a title:",
            "Generated title:",
        ]
        for prefix in prefixes_to_remove:
            if title.lower().startswith(prefix.lower()):
                title = title[len(prefix):].strip()

        # Remove quotes
        if (title.startswith('"') and title.endswith('"')) or \
           (title.startswith("'") and title.endswith("'")):
            title = title[1:-1]

        # Take only first line if multiple lines
        if "\n" in title:
            title = title.split("\n")[0].strip()

        # Truncate if too long
        if len(title) > 100:
            title = title[:97] + "..."

        return title

    def _generate_template_title(
        self,
        event: Event,
        observations: List[Observation],
    ) -> str:
        """
        Generate title using template format.

        Format: '{symbol}: {event_type} ({attention_score})'

        Enhanced format based on event type and available data.

        Args:
            event: The event.
            observations: Related observations.

        Returns:
            Template-generated title string.
        """
        symbol = event.primary_ticker or "Unknown"
        attention = event.attention_score

        # Generate type-specific title
        title = self._get_type_specific_title(event, observations)

        if title:
            return title

        # Default format
        type_display = event.event_type.value.replace("_", " ").title()
        return f"{symbol}: {type_display} ({attention:.0f})"

    def _get_type_specific_title(
        self,
        event: Event,
        observations: List[Observation],
    ) -> Optional[str]:
        """
        Generate type-specific template title with more detail.

        Args:
            event: The event.
            observations: Related observations.

        Returns:
            Type-specific title or None to use default.
        """
        symbol = event.primary_ticker or "Unknown"

        if event.event_type == EventType.MARKET_ANOMALY:
            # Try to find price change from observations
            price_change = self._extract_price_change(observations)
            if price_change is not None:
                direction = "Surges" if price_change > 0 else "Drops"
                return f"{symbol} {direction} {abs(price_change):.1f}% in Unusual Move"

        elif event.event_type == EventType.CATALYST_NEWS:
            news_count = sum(1 for o in observations if o.source == SourceType.NEWS)
            if news_count > 1:
                return f"{symbol} Attracts Attention with {news_count} News Items"
            return f"{symbol} in News Spotlight"

        elif event.event_type == EventType.CATALYST_FILING:
            form_type = self._extract_filing_type(observations)
            if form_type:
                return f"{symbol} Files {form_type} with SEC"
            return f"{symbol} SEC Filing Activity Detected"

        elif event.event_type == EventType.FLOW_CONGRESS:
            trade_info = self._extract_congress_trade(observations)
            if trade_info:
                return f"{symbol} Congressional Trade: {trade_info}"
            return f"{symbol} Draws Congressional Trading Interest"

        elif event.event_type == EventType.FLOW_13F:
            return f"{symbol} Shows Institutional Position Changes"

        elif event.event_type == EventType.PREDICTION_SHIFT:
            prob_change = self._extract_probability_change(observations)
            if prob_change is not None:
                direction = "up" if prob_change > 0 else "down"
                return f"{symbol} Prediction Market Shifts {abs(prob_change):.0f}% {direction}"
            return f"{symbol} Prediction Market Activity"

        elif event.event_type == EventType.MIXED:
            source_count = len(set(o.source for o in observations))
            return f"{symbol} Multi-Signal Event ({source_count} Sources)"

        return None

    def _extract_price_change(self, observations: List[Observation]) -> Optional[float]:
        """Extract price change from market observations."""
        for obs in observations:
            if obs.source in {SourceType.EQUITIES, SourceType.CRYPTO}:
                payload = obs.payload or {}
                for key in ["price_change_pct", "day_return", "change_pct"]:
                    if key in payload:
                        return payload[key]
        return None

    def _extract_filing_type(self, observations: List[Observation]) -> Optional[str]:
        """Extract SEC filing type from observations."""
        for obs in observations:
            if obs.source == SourceType.SEC:
                payload = obs.payload or {}
                form = payload.get("form") or payload.get("form_type")
                if form:
                    return form
        return None

    def _extract_congress_trade(self, observations: List[Observation]) -> Optional[str]:
        """Extract Congress trade info from observations."""
        for obs in observations:
            if obs.source == SourceType.CONGRESS:
                payload = obs.payload or {}
                member = payload.get("member") or payload.get("politician")
                tx_type = payload.get("type") or payload.get("transaction_type")
                if member and tx_type:
                    # Shorten to last name
                    last_name = member.split()[-1] if member else "Member"
                    return f"{last_name} {tx_type.title()}"
        return None

    def _extract_probability_change(self, observations: List[Observation]) -> Optional[float]:
        """Extract probability change from Polymarket observations."""
        for obs in observations:
            if obs.source == SourceType.POLYMARKET:
                payload = obs.payload or {}
                change = payload.get("probability_change") or payload.get("price_change")
                if change is not None:
                    return change
        return None


def generate_event_title(
    event: Event,
    observations: Optional[List[Observation]] = None,
    config: Optional[Dict[str, Any]] = None,
    use_llm: bool = True,
) -> tuple[str, str]:
    """
    Convenience function to generate an event title.

    Args:
        event: The event to generate a title for.
        observations: Optional list of observations.
        config: Optional configuration dict.
        use_llm: Whether to attempt LLM generation.

    Returns:
        Tuple of (title, source) where source is 'llm' or 'template'.
    """
    generator = TitleGenerator(config=config, use_llm=use_llm)
    return generator.generate_title(event, observations)
