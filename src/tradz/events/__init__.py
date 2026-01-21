"""
Events module for aggregating observations into trackable events.

This module provides the EventBuilder class for creating and managing events
from observations, including classification, scoring, and hierarchy management.

Also provides:
- LLM-based title generation with template fallback
- Fact extraction from observations for structured reports

LLM Providers:
- LLMProvider: Abstract base class for LLM providers
- ClaudeCLIProvider: Uses Claude Code CLI
- OpenRouterProvider: Uses OpenRouter API
- MockProvider: For testing

Fact Extraction:
- extract_facts(): Extract FactTableEntry data from observations
- Source-specific extractors for Congress, SEC, News, Market, Polymarket
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
from .title_generator import TitleGenerator, generate_event_title

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
]
