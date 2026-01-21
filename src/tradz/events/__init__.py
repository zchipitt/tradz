"""
Events module for aggregating observations into trackable events.

This module provides the EventBuilder class for creating and managing events
from observations, including classification, scoring, and hierarchy management.

Also provides LLM-based title generation with template fallback:
- LLMProvider: Abstract base class for LLM providers
- ClaudeCLIProvider: Uses Claude Code CLI
- OpenRouterProvider: Uses OpenRouter API
- MockProvider: For testing
- TitleGenerator: Event title generation with fallback
"""
from .builder import EventBuilder
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
]
