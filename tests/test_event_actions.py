"""
Unit tests for Event Actions persistence (US-019).

Tests cover:
- EventAction model
- event_actions table operations
- Action logging in perform_action
- Snoozed events filtering
- Action history retrieval
"""
import sys
from pathlib import Path

# Add src to path for tradz imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4, UUID

from src.tradz.models import EventAction, EventActionType
from src.tradz.database import Database


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_actions.duckdb"
    db = Database(db_path)
    db.init_schema()
    yield db
    db.close()


@pytest.fixture
def sample_event_id():
    """Create a sample event ID for testing."""
    return str(uuid4())


@pytest.fixture
def setup_test_event(temp_db, sample_event_id):
    """Insert a test event into the database."""
    temp_db.conn.execute("""
        INSERT INTO events (id, primary_ticker, title, event_type, status, pinned)
        VALUES (?, 'AAPL', 'Test Event', 'market_anomaly', 'new', FALSE)
    """, [sample_event_id])
    return sample_event_id


class TestEventActionModel:
    """Tests for EventAction dataclass."""

    def test_event_action_creation_defaults(self):
        """Test creating EventAction with defaults."""
        action = EventAction()

        assert action.id is not None
        assert action.event_id is not None
        assert action.action_type == EventActionType.PIN
        assert action.performed_at is not None
        assert action.duration_hours is None
        assert action.reason is None
        assert action.previous_status is None
        assert action.new_status is None
        assert action.previous_pinned is None
        assert action.new_pinned is None
        assert action.snoozed_until is None
        assert action.user_id is None
        assert action.user_agent is None
        assert action.ip_address is None

    def test_event_action_creation_with_values(self):
        """Test creating EventAction with specific values."""
        event_id = uuid4()
        now = datetime.now(timezone.utc)
        snoozed_until = now + timedelta(hours=24)

        action = EventAction(
            event_id=event_id,
            action_type=EventActionType.SNOOZE,
            performed_at=now,
            duration_hours=24,
            previous_status="new",
            new_status=None,
            previous_pinned=False,
            new_pinned=None,
            snoozed_until=snoozed_until,
            user_id="user-123",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
        )

        assert action.event_id == event_id
        assert action.action_type == EventActionType.SNOOZE
        assert action.duration_hours == 24
        assert action.snoozed_until == snoozed_until
        assert action.user_id == "user-123"

    def test_event_action_to_dict(self):
        """Test EventAction.to_dict() method."""
        event_id = uuid4()
        action_id = uuid4()
        now = datetime.now(timezone.utc)

        action = EventAction(
            id=action_id,
            event_id=event_id,
            action_type=EventActionType.DISMISS,
            performed_at=now,
            reason="Not relevant",
            previous_status="new",
            new_status="dismissed",
        )

        result = action.to_dict()

        assert result["id"] == str(action_id)
        assert result["event_id"] == str(event_id)
        assert result["action_type"] == "dismiss"
        assert result["reason"] == "Not relevant"
        assert result["previous_status"] == "new"
        assert result["new_status"] == "dismissed"

    def test_event_action_types(self):
        """Test all EventActionType enum values."""
        assert EventActionType.PIN.value == "pin"
        assert EventActionType.UNPIN.value == "unpin"
        assert EventActionType.SNOOZE.value == "snooze"
        assert EventActionType.DISMISS.value == "dismiss"
        assert EventActionType.RESOLVE.value == "resolve"


class TestDatabaseEventActions:
    """Tests for Database event_actions operations."""

    def test_insert_event_action(self, temp_db, setup_test_event):
        """Test inserting an event action."""
        event_id = setup_test_event
        action = EventAction(
            event_id=UUID(event_id),
            action_type=EventActionType.PIN,
            performed_at=datetime.now(timezone.utc),
            previous_pinned=False,
            new_pinned=True,
        )

        action_id = temp_db.insert_event_action(action)

        assert action_id == str(action.id)

        # Verify it was inserted
        result = temp_db.conn.execute(
            "SELECT id, event_id, action_type FROM event_actions WHERE id = ?",
            [action_id]
        ).fetchone()

        assert result is not None
        assert result[1] == event_id
        assert result[2] == "pin"

    def test_get_event_action_history(self, temp_db, setup_test_event):
        """Test retrieving action history for an event."""
        event_id = setup_test_event

        # Insert multiple actions
        for i, action_type in enumerate([
            EventActionType.PIN,
            EventActionType.SNOOZE,
            EventActionType.UNPIN,
        ]):
            action = EventAction(
                event_id=UUID(event_id),
                action_type=action_type,
                performed_at=datetime.now(timezone.utc) + timedelta(seconds=i),
            )
            temp_db.insert_event_action(action)

        # Get history
        history = temp_db.get_event_action_history(UUID(event_id))

        assert len(history) == 3
        # Should be sorted by performed_at DESC (most recent first)
        assert history[0].action_type == EventActionType.UNPIN
        assert history[1].action_type == EventActionType.SNOOZE
        assert history[2].action_type == EventActionType.PIN

    def test_get_event_action_history_limit(self, temp_db, setup_test_event):
        """Test action history respects limit parameter."""
        event_id = setup_test_event

        # Insert 5 actions
        for i in range(5):
            action = EventAction(
                event_id=UUID(event_id),
                action_type=EventActionType.PIN,
                performed_at=datetime.now(timezone.utc) + timedelta(seconds=i),
            )
            temp_db.insert_event_action(action)

        # Get history with limit
        history = temp_db.get_event_action_history(UUID(event_id), limit=3)

        assert len(history) == 3

    def test_get_recent_event_actions(self, temp_db, setup_test_event):
        """Test retrieving recent actions across all events."""
        event_id = setup_test_event

        # Insert recent action
        recent_action = EventAction(
            event_id=UUID(event_id),
            action_type=EventActionType.PIN,
            performed_at=datetime.now(timezone.utc),
        )
        temp_db.insert_event_action(recent_action)

        # Get recent actions (within last 24 hours)
        recent = temp_db.get_recent_event_actions(hours=24)

        assert len(recent) >= 1
        assert any(a.id == recent_action.id for a in recent)

    def test_insert_event_action_with_all_fields(self, temp_db, setup_test_event):
        """Test inserting action with all fields populated."""
        event_id = setup_test_event
        now = datetime.now(timezone.utc)
        snoozed = now + timedelta(hours=48)

        action = EventAction(
            event_id=UUID(event_id),
            action_type=EventActionType.SNOOZE,
            performed_at=now,
            duration_hours=48,
            reason=None,
            previous_status="new",
            new_status=None,
            previous_pinned=True,
            new_pinned=None,
            snoozed_until=snoozed,
            user_id="test-user",
            user_agent="Test Agent",
            ip_address="10.0.0.1",
        )

        temp_db.insert_event_action(action)

        # Retrieve and verify
        history = temp_db.get_event_action_history(UUID(event_id))
        retrieved = history[0]

        assert retrieved.duration_hours == 48
        assert retrieved.previous_status == "new"
        assert retrieved.previous_pinned is True
        assert retrieved.user_id == "test-user"
        assert retrieved.user_agent == "Test Agent"
        assert retrieved.ip_address == "10.0.0.1"

    def test_row_to_event_action_conversion(self, temp_db, setup_test_event):
        """Test that _row_to_event_action correctly converts database rows."""
        event_id = setup_test_event

        action = EventAction(
            event_id=UUID(event_id),
            action_type=EventActionType.RESOLVE,
            performed_at=datetime.now(timezone.utc),
            previous_status="ongoing",
            new_status="resolved",
            reason="Trade completed",
        )
        temp_db.insert_event_action(action)

        # Retrieve and verify conversion
        history = temp_db.get_event_action_history(UUID(event_id))

        assert len(history) == 1
        retrieved = history[0]

        assert isinstance(retrieved, EventAction)
        assert isinstance(retrieved.id, UUID)
        assert isinstance(retrieved.event_id, UUID)
        assert isinstance(retrieved.action_type, EventActionType)
        assert retrieved.action_type == EventActionType.RESOLVE
        assert retrieved.previous_status == "ongoing"
        assert retrieved.new_status == "resolved"


class TestPerformActionLogging:
    """Tests for action logging in EventService.perform_action."""

    @pytest.fixture
    def mock_event_service(self):
        """Create mock event service with database."""
        with patch("api.services.event_service.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            from api.services.event_service import EventService
            service = EventService()
            yield service, mock_db

    def test_pin_action_logs_to_database(self, mock_event_service):
        """Test that pin action is logged to event_actions table."""
        service, mock_db = mock_event_service
        event_id = str(uuid4())

        # Mock event exists with pinned=False
        mock_db.conn.execute.return_value.fetchone.return_value = (event_id, "new", False)

        result = service.perform_action(
            event_id=event_id,
            action="pin",
        )

        assert result["success"] is True
        assert result["pinned"] is True

        # Verify insert_event_action was called
        assert mock_db.insert_event_action.called

    def test_snooze_action_logs_with_duration(self, mock_event_service):
        """Test that snooze action logs duration_hours."""
        service, mock_db = mock_event_service
        event_id = str(uuid4())

        mock_db.conn.execute.return_value.fetchone.return_value = (event_id, "new", False)

        result = service.perform_action(
            event_id=event_id,
            action="snooze",
            duration_hours=48,
        )

        assert result["success"] is True
        assert result["snoozed_until"] is not None

        # Verify insert_event_action was called with action containing duration
        assert mock_db.insert_event_action.called
        call_args = mock_db.insert_event_action.call_args[0][0]
        assert call_args.action_type == EventActionType.SNOOZE
        assert call_args.duration_hours == 48

    def test_dismiss_action_logs_reason(self, mock_event_service):
        """Test that dismiss action logs the reason."""
        service, mock_db = mock_event_service
        event_id = str(uuid4())

        mock_db.conn.execute.return_value.fetchone.return_value = (event_id, "new", False)

        result = service.perform_action(
            event_id=event_id,
            action="dismiss",
            reason="Not relevant to my strategy",
        )

        assert result["success"] is True
        assert result["new_status"] == "dismissed"

        # Verify insert_event_action was called with reason
        assert mock_db.insert_event_action.called
        call_args = mock_db.insert_event_action.call_args[0][0]
        assert call_args.action_type == EventActionType.DISMISS
        assert call_args.reason == "Not relevant to my strategy"

    def test_resolve_action_logs_status_change(self, mock_event_service):
        """Test that resolve action logs status transition."""
        service, mock_db = mock_event_service
        event_id = str(uuid4())

        mock_db.conn.execute.return_value.fetchone.return_value = (event_id, "ongoing", True)

        result = service.perform_action(
            event_id=event_id,
            action="resolve",
        )

        assert result["success"] is True
        assert result["new_status"] == "resolved"

        # Verify status transition was logged
        assert mock_db.insert_event_action.called
        call_args = mock_db.insert_event_action.call_args[0][0]
        assert call_args.previous_status == "ongoing"
        assert call_args.new_status == "resolved"

    def test_action_logs_user_context(self, mock_event_service):
        """Test that user context is logged with actions."""
        service, mock_db = mock_event_service
        event_id = str(uuid4())

        mock_db.conn.execute.return_value.fetchone.return_value = (event_id, "new", False)

        result = service.perform_action(
            event_id=event_id,
            action="pin",
            user_id="user-456",
            user_agent="Mozilla/5.0 Chrome",
            ip_address="192.168.1.100",
        )

        assert result["success"] is True

        # Verify user context was logged
        assert mock_db.insert_event_action.called
        call_args = mock_db.insert_event_action.call_args[0][0]
        assert call_args.user_id == "user-456"
        assert call_args.user_agent == "Mozilla/5.0 Chrome"
        assert call_args.ip_address == "192.168.1.100"

    def test_action_logging_failure_does_not_fail_action(self, mock_event_service):
        """Test that action completes even if logging fails."""
        service, mock_db = mock_event_service
        event_id = str(uuid4())

        mock_db.conn.execute.return_value.fetchone.return_value = (event_id, "new", False)
        mock_db.insert_event_action.side_effect = Exception("Database error")

        # Action should still succeed
        result = service.perform_action(
            event_id=event_id,
            action="pin",
        )

        assert result["success"] is True
        assert result["pinned"] is True


class TestSnoozedEventsFiltering:
    """Tests for filtering snoozed events in queries."""

    @pytest.fixture
    def mock_event_service(self):
        """Create mock event service."""
        with patch("api.services.event_service.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            from api.services.event_service import EventService
            service = EventService()
            yield service, mock_db

    def test_active_filter_excludes_snoozed_events(self, mock_event_service):
        """Test that active status filter excludes snoozed events."""
        service, _ = mock_event_service

        # Build the status clause
        clause = service._build_status_clause("active")

        # Clause should include snoozed_until check
        assert "snoozed_until" in clause
        assert "snoozed_until IS NULL OR snoozed_until <=" in clause

    def test_all_filter_includes_snoozed_events(self, mock_event_service):
        """Test that 'all' status filter includes snoozed events."""
        service, _ = mock_event_service

        clause = service._build_status_clause("all")

        # Should return all events without snoozed filtering
        assert clause == "1=1"

    def test_resolved_filter_ignores_snooze(self, mock_event_service):
        """Test that resolved filter doesn't check snooze status."""
        service, _ = mock_event_service

        clause = service._build_status_clause("resolved")

        # Should only filter by status, not snooze
        assert clause == "status = 'resolved'"
        assert "snoozed_until" not in clause


class TestActionPersistenceIntegration:
    """Integration tests for action persistence."""

    def test_full_action_workflow(self, temp_db):
        """Test complete workflow: create event, perform actions, verify history."""
        # Create event
        event_id = str(uuid4())
        temp_db.conn.execute("""
            INSERT INTO events (id, primary_ticker, title, event_type, status, pinned)
            VALUES (?, 'TSLA', 'Tesla Event', 'catalyst_news', 'new', FALSE)
        """, [event_id])

        # Perform sequence of actions
        actions = [
            EventAction(
                event_id=UUID(event_id),
                action_type=EventActionType.PIN,
                performed_at=datetime.now(timezone.utc),
                previous_pinned=False,
                new_pinned=True,
            ),
            EventAction(
                event_id=UUID(event_id),
                action_type=EventActionType.SNOOZE,
                performed_at=datetime.now(timezone.utc) + timedelta(seconds=1),
                duration_hours=24,
                snoozed_until=datetime.now(timezone.utc) + timedelta(hours=24),
            ),
            EventAction(
                event_id=UUID(event_id),
                action_type=EventActionType.DISMISS,
                performed_at=datetime.now(timezone.utc) + timedelta(seconds=2),
                previous_status="new",
                new_status="dismissed",
                reason="False signal",
            ),
        ]

        for action in actions:
            temp_db.insert_event_action(action)

        # Verify history
        history = temp_db.get_event_action_history(UUID(event_id))

        assert len(history) == 3

        # Most recent first
        assert history[0].action_type == EventActionType.DISMISS
        assert history[0].reason == "False signal"

        assert history[1].action_type == EventActionType.SNOOZE
        assert history[1].duration_hours == 24

        assert history[2].action_type == EventActionType.PIN
        assert history[2].new_pinned is True
