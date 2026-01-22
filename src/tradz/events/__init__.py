"""
Events module for aggregating observations into trackable events.

This module provides the EventBuilder class for creating and managing events
from observations, including classification, scoring, and hierarchy management.

Also provides:
- LLM-based title generation with template fallback
- Fact extraction from observations for structured reports
- Quality gate evaluation for trade ideas
- Daily brief generation with structured content

LLM Providers:
- LLMProvider: Abstract base class for LLM providers
- ClaudeCLIProvider: Uses Claude Code CLI
- OpenRouterProvider: Uses OpenRouter API
- MockProvider: For testing

Fact Extraction:
- extract_facts(): Extract FactTableEntry data from observations
- Source-specific extractors for Congress, SEC, News, Market, Polymarket

Quality Gates:
- QualityGate: Evaluates events against configurable thresholds
- TradeIdea: Actionable trade recommendations for events passing gates
- ResearchPlan: Research questions for events failing gates
- TradeIdeaGenerator: Generates appropriate recommendations based on gate results

Daily Brief:
- DailyBriefContent: Structured content for daily briefs
- DailyBriefGenerator: Generates daily briefs from events and system status
"""
from .builder import EventBuilder
from .fact_extractor import (
    batch_extract_facts,
    extract_congress_facts,
    extract_facts,
    extract_hedgefund_facts,
    extract_market_facts,
    extract_news_facts,
    extract_polymarket_facts,
    extract_sec_facts,
    update_observation_with_facts,
)
from .llm_provider import (
    ClaudeCLIProvider,
    LLMAPIError,
    LLMProvider,
    LLMProviderError,
    LLMTimeoutError,
    MockProvider,
    OpenRouterProvider,
    get_default_provider,
)
from .quality_gate import (
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
from .title_generator import TitleGenerator, generate_event_title
from .daily_brief_generator import (
    DailyBriefContent,
    DailyBriefGenerator,
    DataQualitySummary,
    EventSummary,
    OpenLoop,
    ResearchIdeaSummary,
    SourceHealthSummary,
    TradeIdeaSummary,
)
from .narrative_generator import (
    GenerationResult,
    NarrativeGenerator,
    NarrativeMetrics,
    generate_brief_with_llm,
)

__all__ = [
    "EventBuilder",
    # LLM providers
    "LLMProvider",
    "ClaudeCLIProvider",
    "OpenRouterProvider",
    "MockProvider",
    "get_default_provider",
    # Exceptions
    "LLMProviderError",
    "LLMTimeoutError",
    "LLMAPIError",
    # Title generation
    "TitleGenerator",
    "generate_event_title",
    # Fact extraction
    "extract_facts",
    "extract_congress_facts",
    "extract_sec_facts",
    "extract_news_facts",
    "extract_market_facts",
    "extract_polymarket_facts",
    "extract_hedgefund_facts",
    "update_observation_with_facts",
    "batch_extract_facts",
    # Quality gates
    "QualityGate",
    "QualityGateConfig",
    "QualityGateEvaluation",
    "GateResult",
    "TradeIdea",
    "ResearchPlan",
    "Recommendation",
    "TradeIdeaGenerator",
    "TradeDirection",
    "TimeHorizon",
    # Daily brief generation
    "DailyBriefContent",
    "DailyBriefGenerator",
    "DataQualitySummary",
    "EventSummary",
    "OpenLoop",
    "ResearchIdeaSummary",
    "SourceHealthSummary",
    "TradeIdeaSummary",
    # Narrative generation
    "NarrativeGenerator",
    "NarrativeMetrics",
    "GenerationResult",
    "generate_brief_with_llm",
]
