"""
Event service for querying and managing events.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
# Add src to path to import tradz modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tradz.database import get_database
from tradz.models import Event, Observation, EventType as ModelEventType, EventStatus as ModelEventStatus
from tradz.events.quality_gate import TradeIdeaGenerator

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

    def perform_action(
        self,
        event_id: str,
        action: str,
        duration_hours: int = 24,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform an action on an event.

        Args:
            event_id: Event UUID string
            action: Action type - "pin", "unpin", "snooze", "dismiss", "resolve"
            duration_hours: Duration for snooze in hours (default 24)
            reason: Optional reason for dismiss action

        Returns:
            Dict with action result including success, message, and updated fields

        Raises:
            ValueError: If event not found or action invalid
        """
        db = get_database()

        # Verify event exists
        check_query = "SELECT id, status, pinned FROM events WHERE id = ?"
        result = db.conn.execute(check_query, [event_id]).fetchone()

        if not result:
            raise ValueError(f"Event {event_id} not found")

        current_status = result[1]
        current_pinned = result[2] if result[2] is not None else False

        now = datetime.now(timezone.utc)
        response: Dict[str, Any] = {
            "event_id": event_id,
            "action": action,
            "success": True,
            "message": "",
            "new_status": None,
            "pinned": None,
            "snoozed_until": None,
        }

        if action == "pin":
            if current_pinned:
                response["message"] = "Event is already pinned"
            else:
                db.conn.execute(
                    "UPDATE events SET pinned = TRUE WHERE id = ?",
                    [event_id],
                )
                response["message"] = "Event pinned successfully"
                response["pinned"] = True

        elif action == "unpin":
            if not current_pinned:
                response["message"] = "Event is not pinned"
            else:
                db.conn.execute(
                    "UPDATE events SET pinned = FALSE WHERE id = ?",
                    [event_id],
                )
                response["message"] = "Event unpinned successfully"
                response["pinned"] = False

        elif action == "snooze":
            from datetime import timedelta
            snoozed_until = now + timedelta(hours=duration_hours)
            db.conn.execute(
                "UPDATE events SET snoozed_until = ? WHERE id = ?",
                [snoozed_until.isoformat(), event_id],
            )
            response["message"] = f"Event snoozed for {duration_hours} hours"
            response["snoozed_until"] = snoozed_until.isoformat()

        elif action == "dismiss":
            if current_status == "dismissed":
                response["message"] = "Event is already dismissed"
            else:
                db.conn.execute(
                    "UPDATE events SET status = 'dismissed', dismissed_reason = ? WHERE id = ?",
                    [reason, event_id],
                )
                response["message"] = "Event dismissed"
                response["new_status"] = "dismissed"

        elif action == "resolve":
            if current_status == "resolved":
                response["message"] = "Event is already resolved"
            else:
                db.conn.execute(
                    "UPDATE events SET status = 'resolved', resolved_at = ? WHERE id = ?",
                    [now.isoformat(), event_id],
                )
                response["message"] = "Event marked as resolved"
                response["new_status"] = "resolved"

        else:
            raise ValueError(f"Invalid action: {action}")

        return response

    def get_event_timeline(
        self,
        event_id: str,
        source_filter: str = "all",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get chronological observations for an event with filtering and pagination.

        Args:
            event_id: Event UUID string
            source_filter: Filter by source - "all", "market", "news", "sec", "congress", "13f", "polymarket"
            limit: Maximum number of observations to return (1-100)
            offset: Number of observations to skip

        Returns:
            Tuple of (list of observation dicts, total count)

        Raises:
            ValueError: If event not found
        """
        db = get_database()

        # Verify event exists
        check_query = "SELECT id FROM events WHERE id = ?"
        result = db.conn.execute(check_query, [event_id]).fetchone()
        if not result:
            raise ValueError(f"Event {event_id} not found")

        # Build source filter clause
        source_clause = self._build_source_filter_clause(source_filter)

        # Get total count
        count_query = f"""
            SELECT COUNT(*)
            FROM observations o
            JOIN event_observations eo ON o.id = eo.observation_id
            WHERE eo.event_id = ? AND {source_clause}
        """
        count_result = db.conn.execute(count_query, [event_id]).fetchone()
        total_count: int = count_result[0] if count_result is not None else 0

        # Get observations with pagination, sorted by timestamp desc
        query = f"""
            SELECT o.*
            FROM observations o
            JOIN event_observations eo ON o.id = eo.observation_id
            WHERE eo.event_id = ? AND {source_clause}
            ORDER BY o.observed_at DESC
            LIMIT ? OFFSET ?
        """
        results = db.conn.execute(query, [event_id, limit, offset]).fetchall()

        observations = []
        for row in results:
            obs_dict = self._row_to_timeline_observation_dict(row)
            observations.append(obs_dict)

        return observations, total_count

    def _build_source_filter_clause(self, source_filter: str) -> str:
        """Build SQL WHERE clause for source filtering."""
        if source_filter == "all":
            return "1=1"
        elif source_filter == "market":
            # Market includes equities and crypto
            return "LOWER(o.source) IN ('equities', 'crypto')"
        elif source_filter == "news":
            return "LOWER(o.source) = 'news'"
        elif source_filter == "sec":
            return "LOWER(o.source) = 'sec'"
        elif source_filter == "congress":
            return "LOWER(o.source) = 'congress'"
        elif source_filter == "13f":
            # 13f is alias for hedgefund
            return "LOWER(o.source) IN ('hedgefund', '13f')"
        elif source_filter == "polymarket":
            return "LOWER(o.source) = 'polymarket'"
        else:
            # Default to all if unknown filter
            return "1=1"

    def _row_to_timeline_observation_dict(self, row) -> Dict[str, Any]:
        """Convert database row to timeline observation dictionary."""
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

        # Determine observation_type from payload or source
        source = row[1] or ""
        observation_type = ""
        if len(row) > 9 and row[9]:
            try:
                payload = json.loads(row[9]) if isinstance(row[9], str) else row[9]
                observation_type = payload.get("observation_type", payload.get("type", ""))
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "observation_id": row[0],
            "source": source,
            "observation_type": observation_type,
            "timestamp": row[5],  # observed_at
            "title": row[11] if len(row) > 11 else None,
            "summary": row[8] or "",
            "fact_entries": fact_entries,
            "source_url": row[10] if len(row) > 10 else None,
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

    def get_event_recommendation(
        self,
        event_id: str,
    ) -> Dict[str, Any]:
        """
        Generate a recommendation (TradeIdea or ResearchPlan) for an event.

        Args:
            event_id: Event UUID string

        Returns:
            Dict with recommendation type, trade_idea/research_plan, and gate_evaluation

        Raises:
            ValueError: If event not found
        """
        # Get event data
        event_dict = self.get_event_by_id(event_id)
        if event_dict is None:
            raise ValueError(f"Event {event_id} not found")

        # Convert to Event model for TradeIdeaGenerator
        try:
            event_type = ModelEventType(event_dict["event_type"])
        except ValueError:
            event_type = ModelEventType.UNCERTAIN

        try:
            event_status = ModelEventStatus(event_dict["status"])
        except ValueError:
            event_status = ModelEventStatus.NEW

        # Parse entity_id - may not be a valid UUID in the database
        entity_id = None
        if event_dict.get("entity_id"):
            try:
                entity_id = UUID(event_dict["entity_id"])
            except (ValueError, AttributeError):
                # Entity ID is not a UUID format, skip it
                pass

        event = Event(
            id=UUID(event_dict["event_id"]),
            primary_entity_id=entity_id,
            primary_ticker=event_dict.get("ticker"),
            title=event_dict["title"],
            event_type=event_type,
            status=event_status,
            confidence=event_dict.get("confidence", 0.5),
            observation_ids=[],  # Not needed for scoring
            anomaly_score=event_dict.get("anomaly_score", 50.0),
            catalyst_score=event_dict.get("catalyst_score", 50.0),
            flow_score=event_dict.get("flow_score", 50.0),
            confidence_score=event_dict.get("confidence_score", 50.0),
        )

        # Convert observations to Observation models
        observations: List[Observation] = []
        for obs_dict in event_dict.get("observations", []):
            try:
                obs = Observation(
                    id=UUID(obs_dict["observation_id"]),
                    source=obs_dict["source"],
                    entity_id=UUID(obs_dict["entity_id"]) if obs_dict.get("entity_id") else None,
                    entity_ticker=obs_dict.get("entity_ticker"),
                    summary=obs_dict.get("summary", ""),
                    title=obs_dict.get("title"),
                    source_url=obs_dict.get("source_url"),
                )
                observations.append(obs)
            except (ValueError, KeyError):
                # Skip invalid observations
                continue

        # Generate recommendation
        generator = TradeIdeaGenerator()
        recommendation = generator.generate(event, observations)

        return recommendation.to_dict()


# Global service instance
event_service = EventService()
