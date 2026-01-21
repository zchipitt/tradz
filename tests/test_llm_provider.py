"""
Unit tests for LLM providers.

Tests cover:
- MockProvider functionality
- ClaudeCLIProvider availability check
- OpenRouterProvider availability check
- Error handling and retry logic
- Provider selection via get_default_provider
"""
import os
import pytest
from unittest.mock import MagicMock, patch

from src.tradz.events.llm_provider import (
    ClaudeCLIProvider,
    LLMAPIError,
    LLMProviderError,
    LLMTimeoutError,
    MockProvider,
    OpenRouterProvider,
    get_default_provider,
)


class TestMockProvider:
    """Tests for MockProvider."""

    def test_returns_configured_response(self):
        """MockProvider returns configured response."""
        provider = MockProvider(response="Test Title")
        result = provider.generate("any prompt")
        assert result == "Test Title"

    def test_tracks_call_count(self):
        """MockProvider tracks call count."""
        provider = MockProvider(response="Title")
        assert provider.call_count == 0

        provider.generate("prompt 1")
        assert provider.call_count == 1

        provider.generate("prompt 2")
        assert provider.call_count == 2

    def test_stores_last_prompt(self):
        """MockProvider stores last prompt."""
        provider = MockProvider(response="Title")
        provider.generate("my test prompt")
        assert provider.last_prompt == "my test prompt"

    def test_stores_all_prompts(self):
        """MockProvider stores all prompts."""
        provider = MockProvider(response="Title")
        provider.generate("prompt 1")
        provider.generate("prompt 2")
        provider.generate("prompt 3")
        assert provider.prompts == ["prompt 1", "prompt 2", "prompt 3"]

    def test_reset_clears_state(self):
        """MockProvider reset clears all tracking state."""
        provider = MockProvider(response="Title")
        provider.generate("prompt")
        provider.reset()

        assert provider.call_count == 0
        assert provider.last_prompt is None
        assert provider.prompts == []

    def test_should_fail_raises_error(self):
        """MockProvider with should_fail=True raises LLMAPIError."""
        provider = MockProvider(should_fail=True)
        with pytest.raises(LLMAPIError) as excinfo:
            provider.generate("prompt")
        assert "Mock failure" in str(excinfo.value)

    def test_fail_with_custom_exception(self):
        """MockProvider raises custom exception when configured."""
        custom_error = LLMTimeoutError("Custom timeout")
        provider = MockProvider(should_fail=True, fail_with=custom_error)

        with pytest.raises(LLMTimeoutError) as excinfo:
            provider.generate("prompt")
        assert "Custom timeout" in str(excinfo.value)

    def test_delay_within_timeout(self):
        """MockProvider with delay responds after delay."""
        provider = MockProvider(response="Title", delay=0.05, timeout=1.0)
        result = provider.generate("prompt")
        assert result == "Title"

    def test_delay_exceeding_timeout_raises(self):
        """MockProvider with delay > timeout raises timeout error."""
        provider = MockProvider(response="Title", delay=2.0, timeout=0.1)
        with pytest.raises(LLMTimeoutError):
            provider.generate("prompt")

    def test_generates_mock_response_without_configured(self):
        """MockProvider generates response based on prompt when none configured."""
        provider = MockProvider()
        result = provider.generate("symbol: TSLA")
        assert "TSLA" in result
        assert "Market Activity" in result

    def test_name_property(self):
        """MockProvider name is 'mock'."""
        provider = MockProvider()
        assert provider.name == "mock"

    def test_is_available_always_true(self):
        """MockProvider is always available."""
        provider = MockProvider()
        assert provider.is_available() is True


class TestClaudeCLIProvider:
    """Tests for ClaudeCLIProvider."""

    def test_name_property(self):
        """ClaudeCLIProvider name is 'claude_cli'."""
        provider = ClaudeCLIProvider()
        assert provider.name == "claude_cli"

    @patch("subprocess.run")
    def test_is_available_when_cli_exists(self, mock_run):
        """ClaudeCLIProvider is available when claude CLI exists."""
        mock_run.return_value = MagicMock(returncode=0)
        provider = ClaudeCLIProvider()
        # Reset cached availability
        provider._available = None

        assert provider.is_available() is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_not_available_when_cli_missing(self, mock_run):
        """ClaudeCLIProvider is not available when claude CLI is missing."""
        mock_run.side_effect = FileNotFoundError()
        provider = ClaudeCLIProvider()
        provider._available = None

        assert provider.is_available() is False

    @patch("subprocess.run")
    def test_not_available_on_timeout(self, mock_run):
        """ClaudeCLIProvider is not available on version check timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)
        provider = ClaudeCLIProvider()
        provider._available = None

        assert provider.is_available() is False

    @patch("subprocess.run")
    def test_generate_calls_cli(self, mock_run):
        """ClaudeCLIProvider.generate calls claude CLI."""
        # Mock availability check
        mock_run.return_value = MagicMock(returncode=0, stdout="Generated Title")
        provider = ClaudeCLIProvider()
        provider._available = True

        result = provider.generate("test prompt")
        assert result == "Generated Title"

    @patch("subprocess.run")
    def test_generate_raises_on_cli_error(self, mock_run):
        """ClaudeCLIProvider raises LLMAPIError on CLI error."""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", "", "Error")
        provider = ClaudeCLIProvider(max_retries=0)
        provider._available = True

        with pytest.raises(LLMAPIError):
            provider.generate("prompt")

    @patch("subprocess.run")
    def test_generate_raises_on_timeout(self, mock_run):
        """ClaudeCLIProvider raises LLMTimeoutError on timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)
        provider = ClaudeCLIProvider(max_retries=0)
        provider._available = True

        with pytest.raises(LLMTimeoutError):
            provider.generate("prompt")

    @patch("subprocess.run")
    def test_retries_on_failure(self, mock_run):
        """ClaudeCLIProvider retries on failure."""
        import subprocess
        mock_run.side_effect = [
            subprocess.TimeoutExpired("cmd", 10),
            MagicMock(returncode=0, stdout="Success"),
        ]
        provider = ClaudeCLIProvider(max_retries=1, retry_delay=0.01)
        provider._available = True

        result = provider.generate("prompt")
        assert result == "Success"
        assert mock_run.call_count == 2

    def test_raises_when_not_available(self):
        """ClaudeCLIProvider raises error when not available."""
        provider = ClaudeCLIProvider()
        provider._available = False

        with pytest.raises(LLMProviderError) as excinfo:
            provider.generate("prompt")
        assert "not available" in str(excinfo.value)


class TestOpenRouterProvider:
    """Tests for OpenRouterProvider."""

    def test_name_property(self):
        """OpenRouterProvider name is 'openrouter'."""
        provider = OpenRouterProvider()
        assert provider.name == "openrouter"

    def test_is_available_with_api_key(self):
        """OpenRouterProvider is available when API key is set."""
        provider = OpenRouterProvider(api_key="test-key")
        assert provider.is_available() is True

    def test_not_available_without_api_key(self):
        """OpenRouterProvider is not available without API key."""
        # Clear env var if set
        original = os.environ.pop("OPENROUTER_API_KEY", None)
        try:
            provider = OpenRouterProvider(api_key=None)
            assert provider.is_available() is False
        finally:
            if original:
                os.environ["OPENROUTER_API_KEY"] = original

    def test_uses_env_var_for_api_key(self):
        """OpenRouterProvider uses OPENROUTER_API_KEY env var."""
        original = os.environ.get("OPENROUTER_API_KEY")
        try:
            os.environ["OPENROUTER_API_KEY"] = "env-key"
            provider = OpenRouterProvider()
            assert provider.api_key == "env-key"
            assert provider.is_available() is True
        finally:
            if original:
                os.environ["OPENROUTER_API_KEY"] = original
            else:
                os.environ.pop("OPENROUTER_API_KEY", None)

    def test_default_model(self):
        """OpenRouterProvider uses default model."""
        provider = OpenRouterProvider(api_key="key")
        assert provider.model == "anthropic/claude-3-haiku"

    def test_custom_model(self):
        """OpenRouterProvider accepts custom model."""
        provider = OpenRouterProvider(api_key="key", model="openai/gpt-4")
        assert provider.model == "openai/gpt-4"

    @patch("httpx.Client")
    def test_generate_calls_api(self, mock_client_class):
        """OpenRouterProvider.generate calls API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated Title"}}]
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        provider = OpenRouterProvider(api_key="test-key")
        result = provider.generate("test prompt")

        assert result == "Generated Title"

    def test_raises_when_not_available(self):
        """OpenRouterProvider raises error when not available."""
        original = os.environ.pop("OPENROUTER_API_KEY", None)
        try:
            provider = OpenRouterProvider(api_key=None)
            with pytest.raises(LLMProviderError) as excinfo:
                provider.generate("prompt")
            assert "not configured" in str(excinfo.value)
        finally:
            if original:
                os.environ["OPENROUTER_API_KEY"] = original


class TestGetDefaultProvider:
    """Tests for get_default_provider function."""

    def test_returns_mock_when_configured(self):
        """get_default_provider returns MockProvider when configured."""
        config = {"llm": {"provider": "mock"}}
        provider = get_default_provider(config)
        assert isinstance(provider, MockProvider)

    def test_raises_for_unavailable_claude_cli(self):
        """get_default_provider raises for unavailable Claude CLI."""
        config = {"llm": {"provider": "claude_cli"}}
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            with pytest.raises(LLMProviderError) as excinfo:
                get_default_provider(config)
            assert "not available" in str(excinfo.value)

    def test_raises_for_unavailable_openrouter(self):
        """get_default_provider raises for unavailable OpenRouter."""
        original = os.environ.pop("OPENROUTER_API_KEY", None)
        try:
            config = {"llm": {"provider": "openrouter"}}
            with pytest.raises(LLMProviderError) as excinfo:
                get_default_provider(config)
            assert "not configured" in str(excinfo.value)
        finally:
            if original:
                os.environ["OPENROUTER_API_KEY"] = original

    def test_auto_selects_openrouter_when_available(self):
        """get_default_provider auto-selects OpenRouter when API key available."""
        original = os.environ.get("OPENROUTER_API_KEY")
        try:
            os.environ["OPENROUTER_API_KEY"] = "test-key"
            provider = get_default_provider({})
            assert isinstance(provider, OpenRouterProvider)
        finally:
            if original:
                os.environ["OPENROUTER_API_KEY"] = original
            else:
                os.environ.pop("OPENROUTER_API_KEY", None)

    @patch("subprocess.run")
    def test_auto_selects_claude_cli_when_available(self, mock_run):
        """get_default_provider auto-selects Claude CLI when available."""
        # Clear OpenRouter key
        original = os.environ.pop("OPENROUTER_API_KEY", None)
        try:
            mock_run.return_value = MagicMock(returncode=0)
            provider = get_default_provider({})
            assert isinstance(provider, ClaudeCLIProvider)
        finally:
            if original:
                os.environ["OPENROUTER_API_KEY"] = original

    @patch("subprocess.run")
    def test_raises_when_no_provider_available(self, mock_run):
        """get_default_provider raises when no provider available."""
        original = os.environ.pop("OPENROUTER_API_KEY", None)
        try:
            mock_run.side_effect = FileNotFoundError()
            with pytest.raises(LLMProviderError) as excinfo:
                get_default_provider({})
            assert "No LLM provider available" in str(excinfo.value)
        finally:
            if original:
                os.environ["OPENROUTER_API_KEY"] = original

    def test_passes_timeout_to_provider(self):
        """get_default_provider passes timeout config to provider."""
        config = {"llm": {"provider": "mock", "timeout": 30}}
        provider = get_default_provider(config)
        assert provider.timeout == 30

    def test_passes_max_retries_to_provider(self):
        """get_default_provider passes max_retries config to provider."""
        config = {"llm": {"provider": "mock", "max_retries": 5}}
        provider = get_default_provider(config)
        assert provider.max_retries == 5
