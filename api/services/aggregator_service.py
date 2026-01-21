"""
Aggregator service wrapping existing DataAggregator.
"""
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path to import tradz modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.services.cache_service import cache
from api.config import load_config


class AggregatorService:
    """Service for aggregating data from multiple sources."""

    def __init__(self):
        self._config: Optional[Dict] = None
        self._aggregator = None

    @property
    def config(self) -> Dict:
        if self._config is None:
            self._config = load_config()
        return self._config

    @property
    def aggregator(self):
        if self._aggregator is None:
            from tradz.aggregator import DataAggregator
            self._aggregator = DataAggregator(self.config)
        return self._aggregator

    def _get_cached_or_fetch(self, cache_key: str, fetch_method: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get data from cache or fetch fresh.

        Args:
            cache_key: Key for caching
            fetch_method: Name of private method to call for fetching
            force_refresh: Force refresh from data source

        Returns:
            Data dict
        """
        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                return cached

        # Fetch fresh data using the aggregator's private method
        method = getattr(self.aggregator, fetch_method, None)
        if method:
            data = method()
            data["fetched_at"] = datetime.now().isoformat()
            cache.set(cache_key, data)
            return data

        return {"error": f"Method {fetch_method} not found"}

    def get_equities(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get equities data."""
        return self._get_cached_or_fetch("equities_data", "_fetch_equities", force_refresh)

    def get_crypto(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get crypto data."""
        return self._get_cached_or_fetch("crypto_data", "_fetch_crypto", force_refresh)

    def get_congress(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get congress trading data."""
        if not self.config.get("congress", {}).get("enabled", True):
            return {"error": "Congress data source is disabled"}
        return self._get_cached_or_fetch("congress_data", "_fetch_congress", force_refresh)

    def get_hedgefunds(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get hedge fund 13F data."""
        if not self.config.get("hedgefunds", {}).get("enabled", True):
            return {"error": "Hedge fund data source is disabled"}

        data = self._get_cached_or_fetch("hedgefunds_data", "_fetch_hedgefunds", force_refresh)

        # Transform data to match frontend expected format
        # Backend returns 'latest_filings', frontend expects 'filings'
        latest_filings = data.get("latest_filings", [])

        # Extract unique fund names for notable_funds
        notable_funds = list(set(
            f.get("fund_name", "") for f in latest_filings if f.get("fund_name")
        ))

        result = {
            "filings": latest_filings,
            "filings_found": data.get("filings_found", len(latest_filings)),
            "notable_funds": notable_funds,
            "tracked_funds": data.get("tracked_funds", 0),
            "fetched_at": data.get("fetched_at"),
        }

        # Only include error if it exists
        if data.get("error"):
            result["error"] = data["error"]

        return result

    def get_polymarket(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get Polymarket prediction data."""
        if not self.config.get("polymarket", {}).get("enabled", True):
            return {"error": "Polymarket data source is disabled"}
        return self._get_cached_or_fetch("polymarket_data", "_fetch_polymarket", force_refresh)

    def get_news(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get news data."""
        if not self.config.get("news", {}).get("enabled", True):
            return {"error": "News data source is disabled"}
        return self._get_cached_or_fetch("news_data", "_fetch_news", force_refresh)

    def get_sec_filings(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get SEC filings data."""
        if not self.config.get("sec_filings", {}).get("enabled", True):
            return {"error": "SEC filings data source is disabled"}
        return self._get_cached_or_fetch("sec_filings_data", "_fetch_sec_filings", force_refresh)

    def get_all_sources(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get all source data."""
        return {
            "equities": self.get_equities(force_refresh),
            "crypto": self.get_crypto(force_refresh),
            "congress": self.get_congress(force_refresh),
            "hedgefunds": self.get_hedgefunds(force_refresh),
            "polymarket": self.get_polymarket(force_refresh),
            "news": self.get_news(force_refresh),
            "sec_filings": self.get_sec_filings(force_refresh),
            "fetched_at": datetime.now().isoformat(),
        }

    def load_historical_data(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Load previously saved data for a specific date.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            Data dict or None
        """
        return self.aggregator.load_data(date)


# Global service instance
aggregator_service = AggregatorService()
