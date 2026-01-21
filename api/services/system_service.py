"""
System status service for monitoring data source health.
"""
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Add src to path to import tradz modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tradz.database import get_database

logger = logging.getLogger(__name__)

# Human-readable display names for data sources
SOURCE_DISPLAY_NAMES = {
    "equities": "Market Data (Equities)",
    "crypto": "Market Data (Crypto)",
    "congress": "Congress Trades",
    "hedgefund": "Hedge Fund (13F)",
    "polymarket": "Polymarket",
    "news": "News",
    "sec": "SEC Filings",
    "broker": "Broker Data",
    "x_sentiment": "X Sentiment",
}

# All known data sources in the system
ALL_SOURCES = [
    "equities",
    "crypto",
    "congress",
    "hedgefund",
    "polymarket",
    "news",
    "sec",
]


class SystemService:
    """Service for monitoring system health and data source status."""

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get health status for all data sources.

        Status determination logic:
        - ok: Last successful data fetch within the last hour
        - degraded: Last successful data fetch within the last 24 hours
        - error: No successful data fetch in the last 24 hours

        Returns:
            Dictionary with overall summary and per-source health status
        """
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        twenty_four_hours_ago = now - timedelta(hours=24)

        db = get_database()

        # Get observation counts by source for last 24h
        source_counts_24h = self._get_source_counts_since(db, twenty_four_hours_ago)

        # Get latest observation timestamps by source
        latest_timestamps = self._get_latest_timestamps_by_source(db)

        # Get errors from recent run_history
        recent_errors = self._get_recent_errors(db, twenty_four_hours_ago)

        sources = []
        healthy_count = 0
        degraded_count = 0
        error_count = 0

        for source_name in ALL_SOURCES:
            display_name = SOURCE_DISPLAY_NAMES.get(source_name, source_name.title())
            last_success_at = latest_timestamps.get(source_name)
            record_count_24h = source_counts_24h.get(source_name, 0)
            last_error = recent_errors.get(source_name)

            # Determine status
            status, freshness = self._determine_status(
                last_success_at, one_hour_ago, twenty_four_hours_ago
            )

            if status == "ok":
                healthy_count += 1
            elif status == "degraded":
                degraded_count += 1
            else:
                error_count += 1

            sources.append({
                "name": source_name,
                "display_name": display_name,
                "status": status,
                "last_success_at": last_success_at,
                "last_error": last_error,
                "record_count_24h": record_count_24h,
                "freshness_indicator": freshness,
            })

        overall = {
            "total_sources": len(ALL_SOURCES),
            "healthy_count": healthy_count,
            "degraded_count": degraded_count,
            "error_count": error_count,
        }

        return {
            "overall": overall,
            "sources": sources,
            "last_check_at": now,
        }

    def _get_source_counts_since(
        self, db: Any, since: datetime
    ) -> Dict[str, int]:
        """Get observation counts by source since a given timestamp."""
        try:
            results = db.conn.execute("""
                SELECT source, COUNT(*) as count
                FROM observations
                WHERE observed_at >= ?
                GROUP BY source
            """, [since]).fetchall()
            return {row[0]: row[1] for row in results}
        except Exception as e:
            logger.warning(f"Failed to get source counts: {e}")
            return {}

    def _get_latest_timestamps_by_source(self, db: Any) -> Dict[str, datetime]:
        """Get the most recent observation timestamp for each source."""
        try:
            results = db.conn.execute("""
                SELECT source, MAX(observed_at) as latest
                FROM observations
                GROUP BY source
            """).fetchall()
            return {row[0]: row[1] for row in results if row[1] is not None}
        except Exception as e:
            logger.warning(f"Failed to get latest timestamps: {e}")
            return {}

    def _get_recent_errors(
        self, db: Any, since: datetime
    ) -> Dict[str, Optional[str]]:
        """
        Get the most recent error for each source from run_history.

        This looks at the errors JSON array in run_history and extracts
        source-specific errors.
        """
        errors: Dict[str, Optional[str]] = {}
        try:
            # Get recent run_history entries with errors
            results = db.conn.execute("""
                SELECT errors
                FROM run_history
                WHERE started_at >= ?
                  AND errors IS NOT NULL
                  AND errors != '[]'
                ORDER BY started_at DESC
                LIMIT 10
            """, [since]).fetchall()

            for row in results:
                if row[0]:
                    import json
                    try:
                        error_list = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                        for error in error_list:
                            # Try to extract source from error message
                            error_str = str(error)
                            for source in ALL_SOURCES:
                                if source.lower() in error_str.lower():
                                    if source not in errors:
                                        errors[source] = error_str[:200]  # Truncate long errors
                    except (json.JSONDecodeError, TypeError):
                        pass
        except Exception as e:
            logger.warning(f"Failed to get recent errors: {e}")

        return errors

    def _determine_status(
        self,
        last_success_at: Optional[datetime],
        one_hour_ago: datetime,
        twenty_four_hours_ago: datetime,
    ) -> Tuple[str, str]:
        """
        Determine status and freshness indicator based on last success timestamp.

        Returns:
            Tuple of (status, freshness_indicator)
        """
        if last_success_at is None:
            return "error", "unknown"

        # Ensure both datetimes are timezone-aware for comparison
        if last_success_at.tzinfo is None:
            # Assume UTC if no timezone
            last_success_at = last_success_at.replace(tzinfo=timezone.utc)

        if last_success_at >= one_hour_ago:
            return "ok", "fresh"
        elif last_success_at >= twenty_four_hours_ago:
            return "degraded", "stale"
        else:
            return "error", "stale"


# Global service instance
system_service = SystemService()
