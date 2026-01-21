"""
Event service for querying and managing events.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
# Add src to path to import tradz modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tradz.database import get_database

logger = logging.getLogger(__name__)


class EventService:
    """Service for retrieving and managing events from the database."""

    def get_events(
        self,
        status_filter: str = "active",
        sort_by: str = "attention_score",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get events with filtering, sorting, and pagination.

        Args:
            status_filter: Filter by status - "active" (new+ongoing), "resolved", "dismissed", "all"
            sort_by: Sort field - "attention_score", "last_update_at", "start_at"
            limit: Maximum number of events to return (1-100)
            offset: Number of events to skip

        Returns:
            Tuple of (list of event dicts, total count)
        """
        db = get_database()

        # Build status filter clause
        status_clause = self._build_status_clause(status_filter)

        # Build sort clause
        sort_clause = self._build_sort_clause(sort_by)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM events WHERE {status_clause}"
        count_result = db.conn.execute(count_query).fetchone()
        total_count: int = count_result[0] if count_result is not None else 0

        # Get events with pagination
        query = f"""
            SELECT e.*,
                   (SELECT COUNT(*) FROM event_observations eo WHERE eo.event_id = e.id) as obs_count
            FROM events e
            WHERE {status_clause}
            ORDER BY {sort_clause}
            LIMIT ? OFFSET ?
        """
        results = db.conn.execute(query, [limit, offset]).fetchall()

        events = []
        for row in results:
            event = self._row_to_event_dict(row)
            events.append(event)

        return events, total_count

    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single event by ID with full details including observations.

        Args:
            event_id: Event UUID string

        Returns:
            Event dict with observations or None if not found
        """
        db = get_database()

        # Get event
        query = """
            SELECT e.*,
                   (SELECT COUNT(*) FROM event_observations eo WHERE eo.event_id = e.id) as obs_count
            FROM events e
            WHERE e.id = ?
        """
        result = db.conn.execute(query, [event_id]).fetchone()

        if not result:
            return None

        event = self._row_to_event_dict(result)

        # Get observations linked to this event
        obs_query = """
            SELECT o.*
            FROM observations o
            JOIN event_observations eo ON o.id = eo.observation_id
            WHERE eo.event_id = ?
            ORDER BY o.observed_at DESC
            LIMIT 50
        """
        obs_results = db.conn.execute(obs_query, [event_id]).fetchall()

        observations = []
        for obs_row in obs_results:
            obs_dict = self._row_to_observation_dict(obs_row)
            observations.append(obs_dict)

        event["observations"] = observations

        # Get entity details if available
        if event.get("entity_id"):
            entity_query = """
                SELECT id, ticker, name FROM entities WHERE id = ?
            """
            entity_result = db.conn.execute(entity_query, [event["entity_id"]]).fetchone()
            if entity_result:
                event["entity"] = {
                    "entity_id": entity_result[0],
                    "ticker": entity_result[1],
                    "name": entity_result[2],
                }
            else:
                event["entity"] = {
                    "entity_id": event.get("entity_id"),
                    "ticker": event.get("ticker"),
                    "name": None,
                }
        else:
            event["entity"] = {
                "entity_id": None,
                "ticker": event.get("ticker"),
                "name": None,
            }

        return event

    def _build_status_clause(self, status_filter: str) -> str:
        """Build SQL WHERE clause for status filtering."""
        now = datetime.now(timezone.utc).isoformat()

        if status_filter == "active":
            # Active means: new, ongoing, or open; not snoozed
            return f"""
                (status IN ('new', 'ongoing', 'open')
                 AND (snoozed_until IS NULL OR snoozed_until <= '{now}'))
            """
        elif status_filter == "resolved":
            return "status = 'resolved'"
        elif status_filter == "dismissed":
            return "status = 'dismissed'"
        else:  # "all"
            return "1=1"

    def _build_sort_clause(self, sort_by: str) -> str:
        """Build SQL ORDER BY clause."""
        if sort_by == "last_update_at":
            return "last_update_at DESC"
        elif sort_by == "start_at":
            return "start_at DESC"
        else:  # "attention_score" (default)
            # Attention score formula: 0.3*anomaly + 0.3*catalyst + 0.25*flow + 0.15*confidence
            # Pinned events always sort to top
            return """
                pinned DESC,
                (anomaly_score * 0.3 + catalyst_score * 0.3 + flow_score * 0.25 + confidence_score * 0.15) DESC
            """

    def _row_to_event_dict(self, row) -> Dict[str, Any]:
        """Convert database row to event dictionary."""
        # Row structure matches the events table schema
        # id, primary_entity_id, primary_ticker, title, event_type, status, confidence,
        # start_at, last_update_at, resolved_at, parent_event_id, pinned, snoozed_until,
        # dismissed_reason, title_template, title_source, anomaly_score, catalyst_score,
        # flow_score, confidence_score, obs_count
        anomaly = row[16] if len(row) > 16 and row[16] is not None else 50.0
        catalyst = row[17] if len(row) > 17 and row[17] is not None else 50.0
        flow = row[18] if len(row) > 18 and row[18] is not None else 50.0
        confidence = row[19] if len(row) > 19 and row[19] is not None else 50.0

        # Calculate attention score
        attention_score = (
            anomaly * 0.3 +
            catalyst * 0.3 +
            flow * 0.25 +
            confidence * 0.15
        )

        obs_count = row[20] if len(row) > 20 else 0

        return {
            "event_id": row[0],
            "entity_id": row[1],
            "ticker": row[2],
            "title": row[3],
            "event_type": row[4],
            "status": row[5],
            "confidence": row[6],
            "start_at": row[7],
            "last_update_at": row[8],
            "resolved_at": row[9],
            "parent_event_id": row[10],
            "pinned": row[11] if row[11] is not None else False,
            "snoozed_until": row[12],
            "dismissed_reason": row[13],
            "title_template": row[14],
            "title_source": row[15] if row[15] else "template",
            "anomaly_score": anomaly,
            "catalyst_score": catalyst,
            "flow_score": flow,
            "confidence_score": confidence,
            "attention_score": attention_score,
            "observation_count": obs_count,
            "scores": {
                "anomaly_score": anomaly,
                "catalyst_score": catalyst,
                "flow_score": flow,
                "confidence_score": confidence,
            },
        }

    def _row_to_observation_dict(self, row) -> Dict[str, Any]:
        """Convert database row to observation dictionary."""
        # Row structure: id, source, entity_id, entity_ticker, effective_at, observed_at,
        # freshness_score, quality_score, summary, payload, source_url, title, raw_payload,
        # fact_entries, entity_mapping_confidence, payload_truncated
        fact_entries = []
        if len(row) > 13 and row[13]:
            try:
                raw_facts = json.loads(row[13]) if isinstance(row[13], str) else row[13]
                for fact in raw_facts:
                    fact_entries.append({
                        "fact_id": fact.get("fact_id", ""),
                        "fact_type": fact.get("fact_type", fact.get("category", "other")),
                        "label": fact.get("label", ""),
                        "value": fact.get("value"),
                        "unit": fact.get("unit"),
                        "source": fact.get("source", ""),
                        "timestamp": fact.get("timestamp"),
                    })
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "observation_id": row[0],
            "source": row[1],
            "entity_id": row[2],
            "entity_ticker": row[3],
            "timestamp": row[5],  # observed_at
            "summary": row[8] or "",
            "source_url": row[10] if len(row) > 10 else None,
            "title": row[11] if len(row) > 11 else None,
            "fact_entries": fact_entries,
        }


# Global service instance
event_service = EventService()
