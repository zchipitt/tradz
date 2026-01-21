"""
LLM Provider abstraction for event title generation.

Provides multiple LLM backends:
- ClaudeCLIProvider: Uses Claude Code CLI
- OpenRouterProvider: Uses OpenRouter API
- MockProvider: For testing
"""
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


# Default configuration
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_DELAY = 1.0


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMTimeoutError(LLMProviderError):
    """Raised when LLM request times out."""
    pass


class LLMAPIError(LLMProviderError):
    """Raised when LLM API returns an error."""
    pass


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement the generate() method to produce text
    completions from a prompt.
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        """
        Initialize LLM provider.

        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            retry_delay: Delay between retries in seconds.
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate text completion from prompt.

        Args:
            prompt: The input prompt.

        Returns:
            Generated text response.

        Raises:
            LLMTimeoutError: If request times out.
            LLMAPIError: If API returns an error.
            LLMProviderError: For other errors.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass

    def is_available(self) -> bool:
        """
        Check if the provider is available.

        Returns:
            True if provider can be used.
        """
        return True


class ClaudeCLIProvider(LLMProvider):
    """
    LLM provider using Claude Code CLI.

    Invokes the 'claude' command line tool for completions.
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        skip_permissions: bool = True,
    ):
        """
        Initialize Claude CLI provider.

        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
            retry_delay: Delay between retries.
            skip_permissions: Whether to skip Claude permission prompts.
        """
        super().__init__(timeout, max_retries, retry_delay)
        self.skip_permissions = skip_permissions
        self._available: Optional[bool] = None

    @property
    def name(self) -> str:
        return "claude_cli"

    def is_available(self) -> bool:
        """Check if Claude CLI is installed and available."""
        if self._available is not None:
            return self._available

        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            self._available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._available = False

        return self._available

    def generate(self, prompt: str) -> str:
        """
        Generate text using Claude CLI.

        Args:
            prompt: The input prompt.

        Returns:
            Generated text response.
        """
        if not self.is_available():
            raise LLMProviderError("Claude CLI not available")

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                return self._invoke_claude(prompt)
            except subprocess.TimeoutExpired as e:
                last_error = LLMTimeoutError(f"Claude CLI timed out after {self.timeout}s")
                logger.warning(f"Attempt {attempt + 1} timed out")
            except subprocess.CalledProcessError as e:
                last_error = LLMAPIError(f"Claude CLI error: {e.stderr}")
                logger.warning(f"Attempt {attempt + 1} failed: {e.stderr}")
            except Exception as e:
                last_error = LLMProviderError(str(e))
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

            if attempt < self.max_retries:
                import time
                time.sleep(self.retry_delay)

        raise last_error or LLMProviderError("Unknown error")

    def _invoke_claude(self, prompt: str) -> str:
        """Invoke Claude CLI with the given prompt."""
        cmd = [
            "claude",
            "-p", prompt,
            "--output-format", "text",
        ]

        if self.skip_permissions:
            cmd.append("--dangerously-skip-permissions")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            env={**os.environ},
        )

        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                cmd,
                result.stdout,
                result.stderr,
            )

        return result.stdout.strip()


class OpenRouterProvider(LLMProvider):
    """
    LLM provider using OpenRouter API.

    Supports multiple models via OpenRouter's unified API.
    """

    DEFAULT_MODEL = "anthropic/claude-3-haiku"
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        """
        Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key. Uses OPENROUTER_API_KEY env var if not provided.
            model: Model to use. Defaults to claude-3-haiku.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
            retry_delay: Delay between retries.
        """
        super().__init__(timeout, max_retries, retry_delay)
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or self.DEFAULT_MODEL

    @property
    def name(self) -> str:
        return "openrouter"

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def generate(self, prompt: str) -> str:
        """
        Generate text using OpenRouter API.

        Args:
            prompt: The input prompt.

        Returns:
            Generated text response.
        """
        if not self.is_available():
            raise LLMProviderError("OpenRouter API key not configured")

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                return self._call_api(prompt)
            except httpx.TimeoutException:
                last_error = LLMTimeoutError(f"OpenRouter API timed out after {self.timeout}s")
                logger.warning(f"Attempt {attempt + 1} timed out")
            except httpx.HTTPStatusError as e:
                last_error = LLMAPIError(f"OpenRouter API error: {e.response.status_code}")
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
            except Exception as e:
                last_error = LLMProviderError(str(e))
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

            if attempt < self.max_retries:
                import time
                time.sleep(self.retry_delay)

        raise last_error or LLMProviderError("Unknown error")

    def _call_api(self, prompt: str) -> str:
        """Make API call to OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/tradz",
            "X-Title": "Tradz Trading Intelligence",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,  # Titles are short
            "temperature": 0.7,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.API_URL, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()

            raise LLMAPIError("Empty response from OpenRouter")


class MockProvider(LLMProvider):
    """
    Mock LLM provider for testing.

    Returns configurable responses or generates predictable output.
    """

    def __init__(
        self,
        response: Optional[str] = None,
        should_fail: bool = False,
        fail_with: Optional[Exception] = None,
        delay: float = 0.0,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        """
        Initialize mock provider.

        Args:
            response: Fixed response to return. If None, generates based on prompt.
            should_fail: Whether to simulate failure.
            fail_with: Exception to raise on failure. Defaults to LLMAPIError.
            delay: Simulated delay before response.
            timeout: Request timeout (used for delay check).
            max_retries: Maximum retry attempts.
            retry_delay: Delay between retries.
        """
        super().__init__(timeout, max_retries, retry_delay)
        self.response = response
        self.should_fail = should_fail
        self.fail_with = fail_with
        self.delay = delay
        self.call_count = 0
        self.last_prompt: Optional[str] = None
        self.prompts: List[str] = []

    @property
    def name(self) -> str:
        return "mock"

    def generate(self, prompt: str) -> str:
        """
        Generate mock response.

        Args:
            prompt: The input prompt.

        Returns:
            Mock response text.
        """
        self.call_count += 1
        self.last_prompt = prompt
        self.prompts.append(prompt)

        if self.delay > 0:
            import time
            if self.delay > self.timeout:
                time.sleep(self.timeout)
                raise LLMTimeoutError(f"Mock timeout after {self.timeout}s")
            time.sleep(self.delay)

        if self.should_fail:
            if self.fail_with:
                raise self.fail_with
            raise LLMAPIError("Mock failure")

        if self.response is not None:
            return self.response

        # Generate predictable response based on prompt
        return self._generate_mock_response(prompt)

    def _generate_mock_response(self, prompt: str) -> str:
        """Generate a mock response based on prompt content."""
        # Extract symbol from prompt if present
        import re
        symbol_match = re.search(r"symbol[:\s]+([A-Z]{1,5})", prompt, re.IGNORECASE)
        symbol = symbol_match.group(1) if symbol_match else "AAPL"

        # Generate timestamp-based variation
        timestamp = datetime.now(timezone.utc).strftime("%H%M")

        return f"{symbol} Shows Significant Market Activity (+{timestamp[-2:]}% Move)"

    def reset(self):
        """Reset mock state."""
        self.call_count = 0
        self.last_prompt = None
        self.prompts = []


def get_default_provider(config: Optional[Dict[str, Any]] = None) -> LLMProvider:
    """
    Get the default LLM provider based on configuration and availability.

    Priority:
    1. Configured provider if specified
    2. OpenRouter if API key available
    3. Claude CLI if available
    4. Raises error if none available

    Args:
        config: Optional configuration dict with 'llm' section.

    Returns:
        Configured LLMProvider instance.

    Raises:
        LLMProviderError: If no provider is available.
    """
    config = config or {}
    llm_config = config.get("llm", {})

    provider_name = llm_config.get("provider")
    timeout = llm_config.get("timeout", DEFAULT_TIMEOUT_SECONDS)
    max_retries = llm_config.get("max_retries", DEFAULT_MAX_RETRIES)

    # If specific provider requested
    if provider_name == "claude_cli":
        provider = ClaudeCLIProvider(timeout=timeout, max_retries=max_retries)
        if provider.is_available():
            return provider
        raise LLMProviderError("Claude CLI requested but not available")

    if provider_name == "openrouter":
        provider = OpenRouterProvider(
            api_key=llm_config.get("api_key"),
            model=llm_config.get("model"),
            timeout=timeout,
            max_retries=max_retries,
        )
        if provider.is_available():
            return provider
        raise LLMProviderError("OpenRouter requested but API key not configured")

    if provider_name == "mock":
        return MockProvider(timeout=timeout, max_retries=max_retries)

    # Auto-detect available provider
    # Try OpenRouter first (faster, more reliable)
    openrouter = OpenRouterProvider(timeout=timeout, max_retries=max_retries)
    if openrouter.is_available():
        logger.info("Using OpenRouter provider")
        return openrouter

    # Fall back to Claude CLI
    claude = ClaudeCLIProvider(timeout=timeout, max_retries=max_retries)
    if claude.is_available():
        logger.info("Using Claude CLI provider")
        return claude

    raise LLMProviderError(
        "No LLM provider available. Set OPENROUTER_API_KEY or install Claude CLI."
    )
