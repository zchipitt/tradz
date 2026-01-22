"""
Daily Brief Service for database operations.

Handles queries to daily_briefs table including:
- Retrieving brief by date
- Retrieving latest brief
- Listing all available briefs
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add src to path to import tradz modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tradz.database import get_database

logger = logging.getLogger(__name__)


class BriefService:
    """Service for daily brief database operations."""

    def __init__(self):
        """Initialize with database connection."""
        self.db = get_database()

    def get_brief_by_date(self, date_str: str) -> Optional[Dict[str, Any]]:
        """
        Get daily brief for a specific date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Dictionary with brief data if found, None otherwise

        Raises:
            ValueError: If date format is invalid
        """
        try:
            # Parse date string to ensure valid format
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

        query = """
        SELECT *
        FROM daily_briefs
        WHERE DATE(date) = ?
        ORDER BY created_at DESC
        LIMIT 1
        """

        try:
            result = self.db.conn.execute(query, [date_obj]).fetchone()
            if not result:
                return None

            return self._row_to_brief_dict(result)

        except Exception as e:
            logger.error(f"Error retrieving brief for date {date_str}: {e}")
            raise

    def get_latest_brief(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent daily brief.

        Returns:
            Dictionary with brief data if found, None otherwise
        """
        query = """
        SELECT *
        FROM daily_briefs
        ORDER BY date DESC, created_at DESC
        LIMIT 1
        """

        try:
            result = self.db.conn.execute(query).fetchone()
            if not result:
                return None

            return self._row_to_brief_dict(result)

        except Exception as e:
            logger.error(f"Error retrieving latest brief: {e}")
            raise

    def list_briefs(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List available daily briefs with pagination.

        Args:
            limit: Maximum number of briefs to return (default 50, max 100)
            offset: Number of briefs to skip for pagination

        Returns:
            Tuple of (briefs list, total_count)
        """
        # Validate limit
        limit = max(1, min(limit, 100))  # Ensure between 1 and 100

        # Get total count first
        count_query = "SELECT COUNT(*) as count FROM daily_briefs"
        try:
            total_count = self.db.conn.execute(count_query).fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting briefs: {e}")
            raise

        # Get paginated results
        query = """
        SELECT *
        FROM daily_briefs
        ORDER BY date DESC, created_at DESC
        LIMIT ? OFFSET ?
        """

        try:
            results = self.db.conn.execute(query, [limit, offset]).fetchall()
            briefs = [self._row_to_brief_summary_dict(row) for row in results]

            return briefs, total_count

        except Exception as e:
            logger.error(f"Error listing briefs: {e}")
            raise

    def _row_to_brief_dict(self, row: Any) -> Dict[str, Any]:
        """
        Convert database row to brief dictionary with full detail.

        Args:
            row: Database row from daily_briefs table

        Returns:
            Dictionary with brief data properly structured
        """
        # Parse JSON summary
        import json
        summary_json = {}
        if row["summary_json"]:
            try:
                summary_json = json.loads(row["summary_json"]) if isinstance(row["summary_json"], str) else row["summary_json"]
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse summary_json for brief {row['id']}")
                summary_json = {}

        # Convert datetime fields
        date = row["date"]
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace("Z", "+00:00"))

        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        return {
            "id": str(row["id"]),
            "date": date,
            "executive_summary": summary_json.get("executive_summary", ""),
            "top_events": summary_json.get("top_events", []),
            "trade_ideas": summary_json.get("trade_ideas", []),
            "research_ideas": summary_json.get("research_ideas", []),
            "open_loops": summary_json.get("open_loops", []),
            "data_quality": summary_json.get("data_quality"),
            "generation_method": row["generation_method"],
            "created_at": created_at,
            "run_id": row.get("run_id"),
        }

    def _row_to_brief_summary_dict(self, row: Any) -> Dict[str, Any]:
        """
        Convert database row to brief summary dictionary.

        Args:
            row: Database row from daily_briefs table

        Returns:
            Dictionary with brief summary data
        """
        # Parse JSON summary for counts
        import json
        summary_json = {}
        if row["summary_json"]:
            try:
                summary_json = json.loads(row["summary_json"]) if isinstance(row["summary_json"], str) else row["summary_json"]
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse summary_json for brief {row['id']}")
                summary_json = {}

        # Get counts
        event_count = len(summary_json.get("top_events", []))
        trade_idea_count = len(summary_json.get("trade_ideas", []))

        # Get top entity (first event's ticker if available)
        top_entity = None
        top_events = summary_json.get("top_events", [])
        if top_events:
            top_entity = top_events[0].get("ticker")

        # Convert datetime fields
        date = row["date"]
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace("Z", "+00:00"))

        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        return {
            "id": str(row["id"]),
            "date": date,
            "generation_method": row["generation_method"],
            "created_at": created_at,
            "event_count": event_count,
            "trade_idea_count": trade_idea_count,
            "top_entity": top_entity,
            "report_path_md": row.get("report_path_md"),
            "report_path_json": row.get("report_path_json"),
            "run_id": row.get("run_id"),
        }

    def brief_exists_for_date(self, date_str: str) -> bool:
        """
        Check if a brief exists for the given date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            True if brief exists, False otherwise
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return False

        query = """
        SELECT COUNT(*) as count
        FROM daily_briefs
        WHERE DATE(date) = ?
        """

        try:
            result = self.db.conn.execute(query, [date_obj]).fetchone()
            return result[0] > 0
        except Exception as e:
            logger.error(f"Error checking brief existence: {e}")
            return False


# Singleton instance
_brief_service: Optional[BriefService] = None


def get_brief_service() -> BriefService:
    """Get singleton instance of BriefService."""
    global _brief_service
    if _brief_service is None:
        _brief_service = BriefService()
    return _brief_service
