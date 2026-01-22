"""
Daily Brief Service for database operations.

Handles queries to daily_briefs table including:
- Retrieving brief by date
- Retrieving latest brief
- Listing all available briefs
- Comparing briefs between dates
"""
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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

    def compare_briefs(
        self,
        date_str: str,
        baseline_str: Optional[str] = None,
        score_change_threshold: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Compare two briefs and return the differences.

        Args:
            date_str: Comparison date in YYYY-MM-DD format
            baseline_str: Baseline date in YYYY-MM-DD format (default: yesterday)
            score_change_threshold: Minimum score change to report (default 5.0)

        Returns:
            Dictionary with diff data including new_events, resolved_events,
            score_changes, new_trade_ideas, closed_loops

        Raises:
            ValueError: If date format is invalid
        """
        # Parse and validate dates
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

        if baseline_str is None:
            # Default to yesterday
            baseline_obj = date_obj - timedelta(days=1)
            baseline_str = baseline_obj.strftime("%Y-%m-%d")
        else:
            try:
                baseline_obj = datetime.strptime(baseline_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Baseline date must be in YYYY-MM-DD format")

        # Get both briefs
        current_brief = self.get_brief_by_date(date_str)
        baseline_brief = self.get_brief_by_date(baseline_str)

        has_baseline = baseline_brief is not None

        # Initialize result
        result: Dict[str, Any] = {
            "date": date_str,
            "baseline": baseline_str,
            "has_baseline": has_baseline,
            "new_events": [],
            "resolved_events": [],
            "score_changes": [],
            "new_trade_ideas": [],
            "closed_loops": [],
            "total_new_events": 0,
            "total_resolved": 0,
            "total_score_changes": 0,
            "total_new_trade_ideas": 0,
            "total_closed_loops": 0,
        }

        # If no current brief, return empty result
        if current_brief is None:
            return result

        # Extract events from both briefs
        current_events = current_brief.get("top_events", [])
        baseline_events = baseline_brief.get("top_events", []) if baseline_brief else []

        # Build event ID sets
        current_event_ids: Set[str] = {
            e.get("event_id", "") for e in current_events if e.get("event_id")
        }
        baseline_event_ids: Set[str] = {
            e.get("event_id", "") for e in baseline_events if e.get("event_id")
        }

        # Build event ID to event mapping
        current_events_map: Dict[str, Dict[str, Any]] = {
            e.get("event_id", ""): e for e in current_events if e.get("event_id")
        }
        baseline_events_map: Dict[str, Dict[str, Any]] = {
            e.get("event_id", ""): e for e in baseline_events if e.get("event_id")
        }

        # Find new events (in current but not in baseline)
        new_event_ids = current_event_ids - baseline_event_ids
        for event_id in new_event_ids:
            event = current_events_map.get(event_id, {})
            if event:
                result["new_events"].append({
                    "event_id": event_id,
                    "title": event.get("title", ""),
                    "ticker": event.get("ticker"),
                    "event_type": event.get("event_type", "unknown"),
                    "attention_score": event.get("attention_score", 0),
                })

        # Find resolved events (in baseline but not in current)
        resolved_event_ids = baseline_event_ids - current_event_ids
        for event_id in resolved_event_ids:
            event = baseline_events_map.get(event_id, {})
            if event:
                result["resolved_events"].append({
                    "event_id": event_id,
                    "title": event.get("title", ""),
                    "ticker": event.get("ticker"),
                    "resolution_type": "resolved",  # Default, actual resolution from DB would be better
                    "final_score": event.get("attention_score", 0),
                })

        # Find score changes (events in both)
        common_event_ids = current_event_ids & baseline_event_ids
        for event_id in common_event_ids:
            current_event = current_events_map.get(event_id, {})
            baseline_event = baseline_events_map.get(event_id, {})

            current_score = current_event.get("attention_score", 0)
            previous_score = baseline_event.get("attention_score", 0)
            delta = current_score - previous_score

            # Only include if delta exceeds threshold
            if abs(delta) >= score_change_threshold:
                direction = "up" if delta > 0 else "down" if delta < 0 else "unchanged"
                result["score_changes"].append({
                    "event_id": event_id,
                    "title": current_event.get("title", ""),
                    "ticker": current_event.get("ticker"),
                    "previous_score": previous_score,
                    "current_score": current_score,
                    "delta": round(delta, 2),
                    "direction": direction,
                })

        # Compare trade ideas
        current_trade_ideas = current_brief.get("trade_ideas", [])
        baseline_trade_ideas = baseline_brief.get("trade_ideas", []) if baseline_brief else []

        baseline_trade_event_ids: Set[str] = {
            t.get("event_id", "") for t in baseline_trade_ideas if t.get("event_id")
        }

        for trade in current_trade_ideas:
            trade_event_id = trade.get("event_id", "")
            if trade_event_id and trade_event_id not in baseline_trade_event_ids:
                result["new_trade_ideas"].append({
                    "event_id": trade_event_id,
                    "ticker": trade.get("ticker"),
                    "direction": trade.get("direction", "unknown"),
                    "entry_zone": trade.get("entry_zone", ""),
                    "target": trade.get("target", ""),
                })

        # Compare open loops
        current_loops = current_brief.get("open_loops", [])
        baseline_loops = baseline_brief.get("open_loops", []) if baseline_brief else []

        current_loop_ids: Set[str] = {
            lo.get("loop_id", "") for lo in current_loops if lo.get("loop_id")
        }
        baseline_loops_map: Dict[str, Dict[str, Any]] = {
            lo.get("loop_id", ""): lo for lo in baseline_loops if lo.get("loop_id")
        }

        # Find closed loops (in baseline but not in current, or status changed to resolved)
        for loop_id, loop in baseline_loops_map.items():
            if loop_id not in current_loop_ids:
                result["closed_loops"].append({
                    "loop_id": loop_id,
                    "question": loop.get("question", ""),
                    "event_id": loop.get("event_id"),
                    "resolution": "closed",
                })
            else:
                # Check if status changed to resolved
                for current_loop in current_loops:
                    if current_loop.get("loop_id") == loop_id:
                        if (loop.get("status") != "resolved" and
                            current_loop.get("status") == "resolved"):
                            result["closed_loops"].append({
                                "loop_id": loop_id,
                                "question": loop.get("question", ""),
                                "event_id": loop.get("event_id"),
                                "resolution": "resolved",
                            })
                        break

        # Update totals
        result["total_new_events"] = len(result["new_events"])
        result["total_resolved"] = len(result["resolved_events"])
        result["total_score_changes"] = len(result["score_changes"])
        result["total_new_trade_ideas"] = len(result["new_trade_ideas"])
        result["total_closed_loops"] = len(result["closed_loops"])

        return result


# Singleton instance
_brief_service: Optional[BriefService] = None


def get_brief_service() -> BriefService:
    """Get singleton instance of BriefService."""
    global _brief_service
    if _brief_service is None:
        _brief_service = BriefService()
    return _brief_service
