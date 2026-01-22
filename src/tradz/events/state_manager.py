"""Event state management for automatic transitions."""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from ..database import Database, get_database
from ..models import Event, EventStatus

logger = logging.getLogger(__name__)


class EventStateManager:
    """
    Manages automatic event state transitions based on activity rules.

    State machine:
    - new → ongoing (after 1 hour with observations)
    - ongoing → stale (no observations for 72 hours)
    - resolved/dismissed → ongoing (optional: high quality new evidence)
    """

    def __init__(self, db: Optional[Database] = None):
        """Initialize state manager with database connection."""
        self._db = db

    @property
    def db(self) -> Database:
        """Get database instance (lazy initialization)."""
        if self._db is None:
            self._db = get_database()
        return self._db

    def run_state_transitions(self) -> Dict[str, int]:
        """
        Run all state transitions in order.

        Returns:
            Dictionary with transition counts:
            - new_to_ongoing: Events that transitioned from new to ongoing
            - ongoing_to_stale: Events that transitioned from ongoing/new to stale
            - resolved_reactivated: Resolved events reactivated (optional)
            - dismissed_reactivated: Dismissed events reactivated (optional)
        """
        results: Dict[str, int] = {
            "new_to_ongoing": 0,
            "ongoing_to_stale": 0,
            "resolved_reactivated": 0,
            "dismissed_reactivated": 0,
        }

        # Transition 1: New → Ongoing (events older than 1 hour)
        new_to_ongoing = self.transition_new_to_ongoing()
        results["new_to_ongoing"] = new_to_ongoing

        # Transition 2: Ongoing/New → Stale (no activity for 72 hours)
        stale_results = self.transition_to_stale()
        results["ongoing_to_stale"] = stale_results["total_transitions"]

        # Transition 3: Check if resolved/dismissed events should be reactivated
        # (Optional, controlled by config)
        if self._should_reactivate_events():
            reactivation_results = self.check_reactivation_eligibility()
            results["resolved_reactivated"] = reactivation_results["resolved"]
            results["dismissed_reactivated"] = reactivation_results["dismissed"]

        logger.info(f"State transitions completed: {results}")
        return results

    def transition_new_to_ongoing(self) -> int:
        """
        Transition new events to ongoing if they have observations older than 1 hour.

        Returns:
            Number of events transitioned
        """
        # First, find events that need transition
        event_ids = self.db.conn.execute("""
            SELECT DISTINCT e.id FROM events e
            JOIN event_observations eo ON e.id = eo.event_id
            JOIN observations o ON eo.observation_id = o.id
            WHERE e.status = 'new'
            AND o.observed_at < CURRENT_TIMESTAMP - INTERVAL '1 hour'
        """).fetchall()

        count = len(event_ids)

        if count > 0:
            # Update all matching events
            ids_str = ", ".join([f"'{row[0]}'" for row in event_ids])
            self.db.conn.execute(f"""
                UPDATE events
                SET status = 'ongoing', last_update_at = CURRENT_TIMESTAMP
                WHERE id IN ({ids_str})
            """)
            logger.info(f"Transitioned {count} events from new to ongoing")

        return count

    def transition_to_stale(self) -> Dict[str, int]:
        """
        Transition events to stale if no observations in 72 hours.

        Returns:
            Dictionary with transition counts by source status
        """
        results: Dict[str, int] = {"total_transitions": 0}

        # Find events that should become stale
        event_ids = self.db.conn.execute("""
            SELECT e.id FROM events e
            WHERE e.status IN ('new', 'ongoing')
            AND NOT EXISTS (
                SELECT 1 FROM event_observations eo
                JOIN observations o ON eo.observation_id = o.id
                WHERE eo.event_id = e.id
                AND o.observed_at >= CURRENT_TIMESTAMP - INTERVAL '72 hours'
            )
        """).fetchall()

        count = len(event_ids)

        if count > 0:
            # Update all matching events
            ids_str = ", ".join([f"'{row[0]}'" for row in event_ids])
            self.db.conn.execute(f"""
                UPDATE events
                SET status = 'stale', last_update_at = CURRENT_TIMESTAMP
                WHERE id IN ({ids_str})
            """)
            logger.info(f"Transitioned {count} events to stale")

        results["total_transitions"] = count
        return results

    def check_reactivation_eligibility(self, quality_score: float = 0.8) -> Dict[str, int]:
        """
        Check if resolved or dismissed events should be reactivated.

        Default reactivation criteria:
        - New observations with quality_score >= 0.8
        - New observations after resolution/dismissal

        Args:
            quality_score: Minimum quality score for reactivation (0-1)

        Returns:
            Dictionary with reactivation counts by status
        """
        results: Dict[str, int] = {"resolved": 0, "dismissed": 0}

        # Find resolved events to reactivate
        resolved_ids = self.db.conn.execute("""
            SELECT DISTINCT e.id FROM events e
            JOIN event_observations eo ON e.id = eo.event_id
            JOIN observations o ON eo.observation_id = o.id
            WHERE e.status = 'resolved'
            AND o.observed_at > e.last_update_at
            AND o.quality_score >= ?
        """, [quality_score]).fetchall()

        if resolved_ids:
            ids_str = ", ".join([f"'{row[0]}'" for row in resolved_ids])
            self.db.conn.execute(f"""
                UPDATE events
                SET status = 'ongoing', last_update_at = CURRENT_TIMESTAMP
                WHERE id IN ({ids_str})
            """)
            results["resolved"] = len(resolved_ids)

        # Find dismissed events to reactivate
        dismissed_ids = self.db.conn.execute("""
            SELECT DISTINCT e.id FROM events e
            JOIN event_observations eo ON e.id = eo.event_id
            JOIN observations o ON eo.observation_id = o.id
            WHERE e.status = 'dismissed'
            AND o.observed_at > e.last_update_at
            AND o.quality_score >= ?
        """, [quality_score]).fetchall()

        if dismissed_ids:
            ids_str = ", ".join([f"'{row[0]}'" for row in dismissed_ids])
            self.db.conn.execute(f"""
                UPDATE events
                SET status = 'ongoing', last_update_at = CURRENT_TIMESTAMP
                WHERE id IN ({ids_str})
            """)
            results["dismissed"] = len(dismissed_ids)

        if results["resolved"] > 0 or results["dismissed"] > 0:
            logger.info(
                f"Reactivated {results['resolved']} resolved and "
                f"{results['dismissed']} dismissed events with new evidence"
            )

        return results

    def get_state_transition_candidates(self) -> Dict[EventStatus, List[Event]]:
        """
        Get events that are candidates for state transitions.

        Returns:
            Dictionary mapping target status to list of events
        """
        candidates: Dict[EventStatus, List[Event]] = {}

        # New events that should transition to ongoing
        new_results = self.db.conn.execute("""
            SELECT DISTINCT e.* FROM events e
            JOIN event_observations eo ON e.id = eo.event_id
            JOIN observations o ON eo.observation_id = o.id
            WHERE e.status = 'new'
            AND o.observed_at < CURRENT_TIMESTAMP - INTERVAL '1 hour'
        """).fetchall()
        candidates[EventStatus.ONGOING] = [
            self.db._row_to_event(r) for r in new_results
        ]

        # Events that should transition to stale
        stale_results = self.db.conn.execute("""
            SELECT DISTINCT e.* FROM events e
            WHERE e.status IN ('new', 'ongoing')
            AND NOT EXISTS (
                SELECT 1 FROM event_observations eo
                JOIN observations o ON eo.observation_id = o.id
                WHERE eo.event_id = e.id
                AND o.observed_at >= CURRENT_TIMESTAMP - INTERVAL '72 hours'
            )
        """).fetchall()
        candidates[EventStatus.STALE] = [
            self.db._row_to_event(r) for r in stale_results
        ]

        return candidates

    def _should_reactivate_events(self) -> bool:
        """
        Check if event reactivation is enabled (controlled by config).

        Returns:
            True if resolved/dismissed events should be reactivated
        """
        # TODO: Read from config or environment variable
        # For now, default to False for safety
        return False

    def record_state_transition_history(
        self,
        event_id: UUID,
        old_status: EventStatus,
        new_status: EventStatus,
        trigger_observation_id: Optional[UUID] = None,
    ) -> None:
        """
        Record state transition in event_type_history table.

        Args:
            event_id: ID of the event
            old_status: Previous status
            new_status: New status
            trigger_observation_id: ID of observation that triggered transition (optional)
        """
        from uuid import uuid4

        self.db.conn.execute("""
            INSERT INTO event_type_history (
                id, event_id, old_type, new_type, changed_at, trigger_observation_id
            )
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, [
            str(uuid4()),
            str(event_id),
            old_status.value,
            new_status.value,
            str(trigger_observation_id) if trigger_observation_id else None,
        ])

    def log_state_transitions(self, results: Dict[str, int]) -> None:
        """
        Log state transition results for monitoring.

        Args:
            results: Dictionary with transition counts
        """
        total_transitions = sum(results.values())
        if total_transitions > 0:
            logger.info(f"Event state manager: {total_transitions} total transitions")
            if "new_to_ongoing" in results:
                logger.info(f"  New→Ongoing: {results['new_to_ongoing']}")
            if "ongoing_to_stale" in results:
                logger.info(f"  Ongoing/New→Stale: {results['ongoing_to_stale']}")
            if "resolved_reactivated" in results:
                logger.info(f"  Resolved→Ongoing: {results['resolved_reactivated']}")
            if "dismissed_reactivated" in results:
                logger.info(f"  Dismissed→Ongoing: {results['dismissed_reactivated']}")


def run_state_transitions(db: Optional[Database] = None) -> Dict[str, int]:
    """
    Convenience function to run state transitions.

    Args:
        db: Database instance (optional)

    Returns:
        Transition results dictionary
    """
    manager = EventStateManager(db)
    return manager.run_state_transitions()


if __name__ == "__main__":
    # Run state transitions when called directly
    import sys
    logging.basicConfig(level=logging.INFO)

    db_instance = get_database()
    transition_results = run_state_transitions(db_instance)
    print(f"State transitions completed: {transition_results}")
    sys.exit(0 if sum(transition_results.values()) >= 0 else 1)
