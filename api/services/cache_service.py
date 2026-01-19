"""
Simple in-memory cache service.
"""
from datetime import datetime, timedelta
from typing import Any, Optional, Dict


class CacheService:
    """In-memory cache with TTL support."""

    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache service.

        Args:
            ttl_seconds: Time-to-live in seconds (default 5 minutes)
        """
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                return data
            # Expired, remove from cache
            del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (value, datetime.now())

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()

    def delete(self, key: str) -> bool:
        """
        Delete a specific key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False


# Global cache instance
cache = CacheService()
