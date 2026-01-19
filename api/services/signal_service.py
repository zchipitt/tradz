"""
Signal service wrapping existing SignalGenerator.
"""
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path to import tradz modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.services.cache_service import cache
from api.config import load_config


class SignalService:
    """Service for generating and retrieving trading signals."""

    CACHE_KEY = "signals_data"

    def __init__(self):
        self._config: Optional[Dict] = None
        self._signal_generator = None

    @property
    def config(self) -> Dict:
        if self._config is None:
            self._config = load_config()
        return self._config

    @property
    def signal_generator(self):
        if self._signal_generator is None:
            from tradz.signals import SignalGenerator
            self._signal_generator = SignalGenerator(self.config)
        return self._signal_generator

    def get_signals(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get trading signals, using cache if available.

        Args:
            force_refresh: Force refresh from data sources

        Returns:
            Dict with top_equities, top_crypto, all_signals, generated_at
        """
        # Check cache first
        if not force_refresh:
            cached = cache.get(self.CACHE_KEY)
            if cached:
                return cached

        # Fetch fresh data
        equity_data = self._fetch_equity_data()
        crypto_data = self._fetch_crypto_data()

        # Generate signals
        signals = self.signal_generator.generate_signals(equity_data, crypto_data)
        signals["generated_at"] = datetime.now().isoformat()

        # Cache the results
        cache.set(self.CACHE_KEY, signals)

        return signals

    def get_top_signals(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get only top signals.

        Args:
            force_refresh: Force refresh from data sources

        Returns:
            Dict with top_equities, top_crypto, generated_at
        """
        signals = self.get_signals(force_refresh)
        return {
            "top_equities": signals["top_equities"],
            "top_crypto": signals["top_crypto"],
            "generated_at": signals["generated_at"],
        }

    def get_signal_by_symbol(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any] | None:
        """
        Get signal for a specific symbol.

        Args:
            symbol: Asset symbol
            force_refresh: Force refresh from data sources

        Returns:
            Signal dict or None if not found
        """
        signals = self.get_signals(force_refresh)
        for signal in signals["all_signals"]:
            if signal["symbol"].upper() == symbol.upper():
                return signal
        return None

    def _fetch_equity_data(self) -> Dict:
        """Fetch equity OHLCV data."""
        from tradz.sources import EquitiesDataSource

        tickers = self.config.get("equities", {}).get("tickers", [])
        if not tickers:
            return {}

        source = EquitiesDataSource(
            max_retries=self.config.get("max_retries", 3),
            retry_delay=self.config.get("retry_delay", 2),
        )

        return source.get_latest_data(tickers, days=60)

    def _fetch_crypto_data(self) -> Dict:
        """Fetch crypto OHLCV data."""
        from tradz.sources import CryptoDataSource

        pairs = self.config.get("crypto", {}).get("pairs", [])
        if not pairs:
            return {}

        source = CryptoDataSource(
            exchange_id=self.config.get("crypto", {}).get("exchange", "binance"),
            max_retries=self.config.get("max_retries", 3),
            retry_delay=self.config.get("retry_delay", 2),
        )

        return source.get_latest_data(pairs, days=60)


# Global service instance
signal_service = SignalService()
