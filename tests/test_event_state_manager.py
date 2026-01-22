"""Tests for event state manager and automatic state transitions."""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from src.tradz.database import Database
from src.tradz.events import EventStateManager, run_state_transitions
from src.tradz.models import Event, EventStatus, EventType, Observation, SourceType


@pytest.fixture
def db():
    """Create a test database with schema initialized."""
    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.duckdb"
        database = Database(db_path)
        database.init_schema()
        yield database
        database.close()


@pytest.fixture
def mock_db():
    """Create a mock database for testing state transitions."""
    mock = MagicMock()
    mock.conn = MagicMock()
    return mock


def insert_test_event(
    db: Database,
    status: EventStatus = EventStatus.NEW,
    ticker: str = "AAPL",
    title: str = "Test Event",
) -> UUID:
    """Insert a test event and return its ID."""
    event_id = uuid.uuid4()
    event = Event(
        id=event_id,
        primary_ticker=ticker,
        title=title,
        event_type=EventType.CATALYST,
        status=status,
    )
    db.insert_event(event)
    return event_id


def insert_test_observation(
    db: Database,
    observed_at: Optional[datetime] = None,
    entity_ticker: str = "AAPL",
    quality_score: float = 1.0,
    freshness_score: float = 1.0,
) -> UUID:
    """Insert a test observation and return its ID."""
    obs_id = uuid.uuid4()
    obs = Observation(
        id=obs_id,
        source=SourceType.EQUITIES,
        entity_ticker=entity_ticker,
        observed_at=observed_at or datetime.now(),
        quality_score=quality_score,
        freshness_score=freshness_score,
        summary="Test observation",
    )
    db.insert_observation(obs)
    return obs_id


class TestEventStateManagerWithMocks:
    """Test event state manager functionality using mocks."""

    def test_transition_new_to_ongoing(self, mock_db):
        """Test new events transition to ongoing after 1 hour."""
        # Setup mock to return one event ID
        mock_db.conn.execute.return_value.fetchall.return_value = [
            ("event-id-1",),
        ]

        manager = EventStateManager(mock_db)
        count = manager.transition_new_to_ongoing()

        assert count == 1
        # Verify execute was called for both SELECT and UPDATE
        assert mock_db.conn.execute.call_count == 2

    def test_no_transition_new_without_old_observations(self, mock_db):
        """Test new events without old observations stay new."""
        # Setup mock to return no events
        mock_db.conn.execute.return_value.fetchall.return_value = []

        manager = EventStateManager(mock_db)
        count = manager.transition_new_to_ongoing()

        assert count == 0
        # Only SELECT was called, no UPDATE
        assert mock_db.conn.execute.call_count == 1

    def test_transition_to_stale(self, mock_db):
        """Test events transition to stale after 72 hours of inactivity."""
        # Setup mock to return one event
        mock_db.conn.execute.return_value.fetchall.return_value = [
            ("event-id-1",),
        ]

        manager = EventStateManager(mock_db)
        results = manager.transition_to_stale()

        assert results["total_transitions"] == 1
        # Verify execute was called for both SELECT and UPDATE
        assert mock_db.conn.execute.call_count == 2

    def test_no_transition_to_stale_with_recent_observations(self, mock_db):
        """Test events with recent observations don't become stale."""
        # Setup mock to return no events
        mock_db.conn.execute.return_value.fetchall.return_value = []

        manager = EventStateManager(mock_db)
        results = manager.transition_to_stale()

        assert results["total_transitions"] == 0
        # Only SELECT was called
        assert mock_db.conn.execute.call_count == 1

    def test_check_reactivation_eligibility_resolved(self, mock_db):
        """Test resolved events reactivate with new high-quality evidence."""
        # First call returns resolved events, second returns dismissed events (empty)
        mock_db.conn.execute.return_value.fetchall.side_effect = [
            [("resolved-event-1",)],  # Resolved events
            [],  # Dismissed events
        ]

        manager = EventStateManager(mock_db)
        results = manager.check_reactivation_eligibility()

        assert results["resolved"] == 1
        assert results["dismissed"] == 0

    def test_check_reactivation_eligibility_dismissed(self, mock_db):
        """Test dismissed events reactivate with new high-quality evidence."""
        # First call returns resolved events (empty), second returns dismissed events
        mock_db.conn.execute.return_value.fetchall.side_effect = [
            [],  # Resolved events
            [("dismissed-event-1",)],  # Dismissed events
        ]

        manager = EventStateManager(mock_db)
        results = manager.check_reactivation_eligibility()

        assert results["resolved"] == 0
        assert results["dismissed"] == 1

    def test_no_reactivation_without_high_quality(self, mock_db):
        """Test events don't reactivate without high-quality evidence."""
        # Setup mock to return no events
        mock_db.conn.execute.return_value.fetchall.return_value = []

        manager = EventStateManager(mock_db)
        results = manager.check_reactivation_eligibility()

        assert results["resolved"] == 0
        assert results["dismissed"] == 0

    def test_run_all_state_transitions(self, mock_db):
        """Test complete state transition workflow."""
        # Setup mock for all three transition methods
        # new_to_ongoing: 1 event
        # transition_to_stale: 1 event
        mock_db.conn.execute.return_value.fetchall.side_effect = [
            [("event-1",)],  # new_to_ongoing SELECT
            [("event-2",)],  # transition_to_stale SELECT
        ]

        manager = EventStateManager(mock_db)
        results = manager.run_state_transitions()

        assert results["new_to_ongoing"] == 1
        assert results["ongoing_to_stale"] == 1
        assert results["resolved_reactivated"] == 0
        assert results["dismissed_reactivated"] == 0

    def test_should_reactivate_events_default(self, mock_db):
        """Test reactivation check returns False by default."""
        manager = EventStateManager(mock_db)
        assert not manager._should_reactivate_events()

    def test_record_state_transition_history(self, mock_db):
        """Test state transition history is recorded."""
        event_id = uuid.uuid4()
        old_status = EventStatus.NEW
        new_status = EventStatus.ONGOING

        manager = EventStateManager(mock_db)
        manager.record_state_transition_history(event_id, old_status, new_status)

        # Verify INSERT was called
        mock_db.conn.execute.assert_called_once()
        call_args = mock_db.conn.execute.call_args
        assert "INSERT INTO event_type_history" in call_args[0][0]

    def test_record_state_transition_history_with_observation(self, mock_db):
        """Test state transition history with trigger observation."""
        event_id = uuid.uuid4()
        observation_id = uuid.uuid4()
        old_status = EventStatus.ONGOING
        new_status = EventStatus.STALE

        manager = EventStateManager(mock_db)
        manager.record_state_transition_history(
            event_id, old_status, new_status, observation_id
        )

        # Verify INSERT was called with observation ID
        mock_db.conn.execute.assert_called_once()
        call_args = mock_db.conn.execute.call_args
        # The observation_id should be in the args list (second positional argument)
        assert str(observation_id) in str(call_args[0][1])

    def test_log_state_transitions(self, mock_db):
        """Test state transition logging."""
        results = {
            "new_to_ongoing": 5,
            "ongoing_to_stale": 3,
            "resolved_reactivated": 1,
            "dismissed_reactivated": 0,
        }

        manager = EventStateManager(mock_db)
        # Should not raise any errors
        manager.log_state_transitions(results)

    def test_log_state_transitions_zero_count(self, mock_db):
        """Test state transition logging with zero transitions."""
        results = {
            "new_to_ongoing": 0,
            "ongoing_to_stale": 0,
            "resolved_reactivated": 0,
            "dismissed_reactivated": 0,
        }

        manager = EventStateManager(mock_db)
        # Should not raise any errors
        manager.log_state_transitions(results)


class TestEventStateManagerWithRealDB:
    """Test event state manager with real database (no FK-violating updates)."""

    def test_new_event_starts_in_new_status(self, db):
        """Test that events start in 'new' status on creation."""
        event = Event(
            primary_ticker="AAPL",
            title="Test Event",
            event_type=EventType.CATALYST,
        )
        # Default status should be NEW
        assert event.status == EventStatus.NEW

        # Insert and verify
        db.insert_event(event)
        result = db.conn.execute(
            "SELECT status FROM events WHERE id = ?",
            [str(event.id)]
        ).fetchone()
        assert result[0] == 'new'

    def test_event_without_observations_goes_stale(self, db):
        """Test event with no observations eventually becomes stale."""
        # Create an event without linking any observations
        event_id = insert_test_event(db, status=EventStatus.ONGOING)

        # Run transitions - event with no observations should go stale
        manager = EventStateManager(db)
        results = manager.transition_to_stale()

        assert results["total_transitions"] == 1

        # Verify stale
        db_result = db.conn.execute(
            "SELECT status FROM events WHERE id = ?",
            [str(event_id)]
        ).fetchone()
        assert db_result[0] == 'stale'

    def test_get_state_transition_candidates_ongoing(self, db):
        """Test getting candidates for ongoing transition."""
        # Create new event
        event_id = insert_test_event(db, status=EventStatus.NEW)

        # Add old observation (but don't link - to avoid FK issues)
        # Instead, check that candidate detection works without linked observations
        manager = EventStateManager(db)
        candidates = manager.get_state_transition_candidates()

        # Event should NOT be candidate for ongoing (no linked observations)
        ongoing_candidates = candidates.get(EventStatus.ONGOING, [])
        assert len(ongoing_candidates) == 0

    def test_get_state_transition_candidates_stale(self, db):
        """Test getting candidates for stale transition."""
        # Create ongoing event (no linked observations)
        insert_test_event(db, status=EventStatus.ONGOING)

        # Get candidates
        manager = EventStateManager(db)
        candidates = manager.get_state_transition_candidates()

        # Event should be candidate for stale (no recent observations)
        stale_candidates = candidates.get(EventStatus.STALE, [])
        assert len(stale_candidates) == 1

    def test_no_reactivation_user_action_events(self, db):
        """Test resolved/dismissed events don't reactivate if disabled."""
        # Create resolved event
        insert_test_event(db, status=EventStatus.RESOLVED)

        # By default, reactivation is disabled
        manager = EventStateManager(db)
        assert not manager._should_reactivate_events()

    def test_resolved_dismissed_no_auto_transition_to_stale(self, db):
        """Test user action events don't transition to stale."""
        # Create resolved and dismissed events (no observations)
        resolved_id = insert_test_event(db, status=EventStatus.RESOLVED)
        dismissed_id = insert_test_event(db, status=EventStatus.DISMISSED)

        # Run all state transitions
        manager = EventStateManager(db)
        results = manager.run_state_transitions()

        # User action events should not auto-transition
        assert results["ongoing_to_stale"] == 0

        # Verify statuses unchanged
        for event_id, expected_status in [
            (resolved_id, 'resolved'),
            (dismissed_id, 'dismissed')
        ]:
            db_result = db.conn.execute(
                "SELECT status FROM events WHERE id = ?",
                [str(event_id)]
            ).fetchone()
            assert db_result[0] == expected_status

    def test_record_state_transition_history_real_db(self, db):
        """Test state transition history is recorded in real database."""
        # First create the event (FK constraint requires it to exist)
        event_id = insert_test_event(db, status=EventStatus.NEW)
        old_status = EventStatus.NEW
        new_status = EventStatus.ONGOING

        manager = EventStateManager(db)
        manager.record_state_transition_history(event_id, old_status, new_status)

        # Verify history entry
        result = db.conn.execute(
            """SELECT old_type, new_type FROM event_type_history
               WHERE event_id = ?""",
            [str(event_id)]
        ).fetchone()

        assert result[0] == old_status.value
        assert result[1] == new_status.value


class TestConvenienceFunction:
    """Test the run_state_transitions convenience function."""

    def test_convenience_function_with_mock(self):
        """Test run_state_transitions convenience function."""
        mock_db = MagicMock()
        mock_db.conn.execute.return_value.fetchall.side_effect = [
            [("event-1",)],  # new_to_ongoing
            [],  # stale
        ]

        results = run_state_transitions(mock_db)

        assert results["new_to_ongoing"] == 1

    def test_convenience_function_no_db(self):
        """Test run_state_transitions creates its own database."""
        with patch("src.tradz.events.state_manager.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_db.conn.execute.return_value.fetchall.return_value = []
            mock_get_db.return_value = mock_db

            results = run_state_transitions()

            mock_get_db.assert_called_once()
            assert "new_to_ongoing" in results
