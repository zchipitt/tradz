"""
Unit tests for Open Loops data model (US-022).

Tests cover:
- OpenLoop model (dataclass, to_dict, from_dict)
- OpenLoopStatus enum
- open_loops table operations (CRUD)
- Auto-creation from Research Plan questions
- Status transitions and progress notes
"""
import sys
from pathlib import Path

# Add src to path for tradz imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from src.tradz.models import OpenLoop, OpenLoopStatus
from src.tradz.database import Database


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_open_loops.duckdb"
    db = Database(db_path)
    db.init_schema()
    yield db
    db.close()


@pytest.fixture
def sample_event_id():
    """Create a sample event ID for testing."""
    return uuid4()


@pytest.fixture
def setup_test_event(temp_db, sample_event_id):
    """Insert a test event into the database."""
    temp_db.conn.execute("""
        INSERT INTO events (id, primary_ticker, title, event_type, status, pinned)
        VALUES (?, 'AAPL', 'Test Event', 'market_anomaly', 'new', FALSE)
    """, [str(sample_event_id)])
    return sample_event_id


class TestOpenLoopStatusEnum:
    """Tests for OpenLoopStatus enum."""

    def test_all_status_values_exist(self):
        """Test all expected status values are defined."""
        assert OpenLoopStatus.OPEN.value == "open"
        assert OpenLoopStatus.IN_PROGRESS.value == "in_progress"
        assert OpenLoopStatus.RESOLVED.value == "resolved"
        assert OpenLoopStatus.STALE.value == "stale"

    def test_status_values_count(self):
        """Test the correct number of status values."""
        assert len(OpenLoopStatus) == 4

    def test_status_is_string_enum(self):
        """Test status values are strings."""
        for status in OpenLoopStatus:
            assert isinstance(status.value, str)


class TestOpenLoopModel:
    """Tests for OpenLoop dataclass."""

    def test_open_loop_creation_defaults(self):
        """Test creating OpenLoop with defaults."""
        loop = OpenLoop()

        assert loop.id is not None
        assert loop.event_id is None
        assert loop.question == ""
        assert loop.created_at is not None
        assert loop.status == OpenLoopStatus.OPEN
        assert loop.progress_notes == []
        assert loop.resolved_at is None

    def test_open_loop_creation_with_values(self):
        """Test creating OpenLoop with specific values."""
        event_id = uuid4()
        now = datetime.now(timezone.utc)

        loop = OpenLoop(
            event_id=event_id,
            question="What caused the price spike?",
            created_at=now,
            status=OpenLoopStatus.IN_PROGRESS,
            progress_notes=["Initial investigation started", "Found possible cause"],
            resolved_at=None,
        )

        assert loop.event_id == event_id
        assert loop.question == "What caused the price spike?"
        assert loop.status == OpenLoopStatus.IN_PROGRESS
        assert len(loop.progress_notes) == 2

    def test_open_loop_to_dict(self):
        """Test OpenLoop serialization to dict."""
        event_id = uuid4()
        loop_id = uuid4()
        now = datetime.now(timezone.utc)

        loop = OpenLoop(
            id=loop_id,
            event_id=event_id,
            question="Is this a buyout rumor?",
            created_at=now,
            status=OpenLoopStatus.OPEN,
            progress_notes=["Monitoring news"],
        )

        result = loop.to_dict()

        assert result["id"] == str(loop_id)
        assert result["event_id"] == str(event_id)
        assert result["question"] == "Is this a buyout rumor?"
        assert result["status"] == "open"
        assert result["progress_notes"] == ["Monitoring news"]
        assert result["resolved_at"] is None

    def test_open_loop_to_dict_with_resolved(self):
        """Test OpenLoop serialization with resolved_at."""
        now = datetime.now(timezone.utc)
        resolved = now + timedelta(days=1)

        loop = OpenLoop(
            question="Market anomaly cause?",
            created_at=now,
            status=OpenLoopStatus.RESOLVED,
            resolved_at=resolved,
        )

        result = loop.to_dict()

        assert result["status"] == "resolved"
        assert result["resolved_at"] is not None

    def test_open_loop_from_dict(self):
        """Test creating OpenLoop from dictionary."""
        loop_id = str(uuid4())
        event_id = str(uuid4())
        now = datetime.now(timezone.utc)

        data = {
            "id": loop_id,
            "event_id": event_id,
            "question": "Is this institutional accumulation?",
            "created_at": now.isoformat(),
            "status": "in_progress",
            "progress_notes": ["Checked 13F filings"],
            "resolved_at": None,
        }

        loop = OpenLoop.from_dict(data)

        assert str(loop.id) == loop_id
        assert str(loop.event_id) == event_id
        assert loop.question == "Is this institutional accumulation?"
        assert loop.status == OpenLoopStatus.IN_PROGRESS
        assert loop.progress_notes == ["Checked 13F filings"]

    def test_open_loop_from_dict_minimal(self):
        """Test creating OpenLoop from minimal dictionary."""
        data = {
            "question": "Simple question",
        }

        loop = OpenLoop.from_dict(data)

        assert loop.id is not None
        assert loop.event_id is None
        assert loop.question == "Simple question"
        assert loop.status == OpenLoopStatus.OPEN

    def test_open_loop_from_dict_invalid_status(self):
        """Test from_dict handles invalid status gracefully."""
        data = {
            "question": "Test question",
            "status": "invalid_status",
        }

        loop = OpenLoop.from_dict(data)

        # Should default to OPEN for invalid status
        assert loop.status == OpenLoopStatus.OPEN


class TestOpenLoopsDatabase:
    """Tests for open_loops table operations."""

    def test_insert_open_loop(self, temp_db, setup_test_event, sample_event_id):  # noqa: ARG002
        """Test inserting an open loop."""
        loop = OpenLoop(
            event_id=sample_event_id,
            question="Why did the stock gap up?",
            status=OpenLoopStatus.OPEN,
            progress_notes=["Initial observation"],
        )

        loop_id = temp_db.insert_open_loop(loop)

        assert loop_id == str(loop.id)

    def test_insert_open_loop_without_event(self, temp_db):
        """Test inserting an open loop without event link."""
        loop = OpenLoop(
            question="General market question",
            status=OpenLoopStatus.OPEN,
        )

        loop_id = temp_db.insert_open_loop(loop)

        assert loop_id == str(loop.id)

    def test_insert_open_loop_upsert(self, temp_db, setup_test_event, sample_event_id):
        """Test that inserting same ID updates the record."""
        loop_id = uuid4()
        loop1 = OpenLoop(
            id=loop_id,
            event_id=sample_event_id,
            question="Original question",
            status=OpenLoopStatus.OPEN,
        )
        temp_db.insert_open_loop(loop1)

        # Update with same ID
        loop2 = OpenLoop(
            id=loop_id,
            event_id=sample_event_id,
            question="Updated question",
            status=OpenLoopStatus.IN_PROGRESS,
            progress_notes=["Made progress"],
        )
        temp_db.insert_open_loop(loop2)

        # Verify update
        result = temp_db.get_open_loop_by_id(loop_id)
        assert result.question == "Updated question"
        assert result.status == OpenLoopStatus.IN_PROGRESS

    def test_get_open_loop_by_id(self, temp_db, setup_test_event, sample_event_id):
        """Test retrieving an open loop by ID."""
        loop = OpenLoop(
            event_id=sample_event_id,
            question="Test retrieval",
            status=OpenLoopStatus.OPEN,
        )
        temp_db.insert_open_loop(loop)

        result = temp_db.get_open_loop_by_id(loop.id)

        assert result is not None
        assert result.id == loop.id
        assert result.question == "Test retrieval"

    def test_get_open_loop_by_id_not_found(self, temp_db):
        """Test retrieving non-existent open loop returns None."""
        result = temp_db.get_open_loop_by_id(uuid4())
        assert result is None

    def test_get_open_loops_all(self, temp_db, setup_test_event, sample_event_id):
        """Test retrieving all open loops."""
        for i in range(3):
            loop = OpenLoop(
                event_id=sample_event_id,
                question=f"Question {i}",
                status=OpenLoopStatus.OPEN,
            )
            temp_db.insert_open_loop(loop)

        results = temp_db.get_open_loops()

        assert len(results) == 3

    def test_get_open_loops_by_status(self, temp_db, setup_test_event, sample_event_id):
        """Test filtering open loops by status."""
        statuses = [OpenLoopStatus.OPEN, OpenLoopStatus.IN_PROGRESS, OpenLoopStatus.RESOLVED]
        for i, status in enumerate(statuses):
            loop = OpenLoop(
                event_id=sample_event_id,
                question=f"Question {i}",
                status=status,
            )
            temp_db.insert_open_loop(loop)

        open_results = temp_db.get_open_loops(status=OpenLoopStatus.OPEN)
        in_progress_results = temp_db.get_open_loops(status=OpenLoopStatus.IN_PROGRESS)

        assert len(open_results) == 1
        assert len(in_progress_results) == 1

    def test_get_open_loops_by_event(self, temp_db, setup_test_event, sample_event_id):
        """Test retrieving open loops by event ID."""
        # Create loops for our event
        for i in range(2):
            loop = OpenLoop(
                event_id=sample_event_id,
                question=f"Event question {i}",
            )
            temp_db.insert_open_loop(loop)

        # Create loop without event
        loop_no_event = OpenLoop(question="No event question")
        temp_db.insert_open_loop(loop_no_event)

        results = temp_db.get_open_loops_by_event(sample_event_id)

        assert len(results) == 2
        for r in results:
            assert r.event_id == sample_event_id

    def test_get_open_loops_pagination(self, temp_db, setup_test_event, sample_event_id):
        """Test pagination of open loops."""
        for i in range(10):
            loop = OpenLoop(
                event_id=sample_event_id,
                question=f"Question {i}",
            )
            temp_db.insert_open_loop(loop)

        # Get first page
        page1 = temp_db.get_open_loops(limit=5, offset=0)
        page2 = temp_db.get_open_loops(limit=5, offset=5)

        assert len(page1) == 5
        assert len(page2) == 5
        # Ensure no overlap
        page1_ids = {l.id for l in page1}
        page2_ids = {l.id for l in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_update_open_loop_status(self, temp_db, setup_test_event, sample_event_id):
        """Test updating open loop status."""
        loop = OpenLoop(
            event_id=sample_event_id,
            question="Status update test",
            status=OpenLoopStatus.OPEN,
        )
        temp_db.insert_open_loop(loop)

        # Update to in_progress
        temp_db.update_open_loop_status(loop.id, OpenLoopStatus.IN_PROGRESS)

        result = temp_db.get_open_loop_by_id(loop.id)
        assert result.status == OpenLoopStatus.IN_PROGRESS

    def test_update_open_loop_status_resolved(self, temp_db, setup_test_event, sample_event_id):
        """Test updating to resolved status sets resolved_at."""
        loop = OpenLoop(
            event_id=sample_event_id,
            question="Resolution test",
            status=OpenLoopStatus.IN_PROGRESS,
        )
        temp_db.insert_open_loop(loop)

        # Resolve
        temp_db.update_open_loop_status(loop.id, OpenLoopStatus.RESOLVED)

        result = temp_db.get_open_loop_by_id(loop.id)
        assert result.status == OpenLoopStatus.RESOLVED
        assert result.resolved_at is not None

    def test_add_progress_note(self, temp_db, setup_test_event, sample_event_id):
        """Test adding progress notes to an open loop."""
        loop = OpenLoop(
            event_id=sample_event_id,
            question="Progress test",
            progress_notes=["Initial note"],
        )
        temp_db.insert_open_loop(loop)

        # Add note
        success = temp_db.add_progress_note(loop.id, "Second note")

        assert success is True
        result = temp_db.get_open_loop_by_id(loop.id)
        assert len(result.progress_notes) == 2
        assert result.progress_notes[1] == "Second note"

    def test_add_progress_note_not_found(self, temp_db):
        """Test adding note to non-existent loop returns False."""
        success = temp_db.add_progress_note(uuid4(), "Note")
        assert success is False

    def test_delete_open_loop(self, temp_db, setup_test_event, sample_event_id):
        """Test deleting an open loop."""
        loop = OpenLoop(
            event_id=sample_event_id,
            question="Delete test",
        )
        temp_db.insert_open_loop(loop)

        # Delete
        success = temp_db.delete_open_loop(loop.id)

        assert success is True
        result = temp_db.get_open_loop_by_id(loop.id)
        assert result is None

    def test_get_stale_open_loops(self, temp_db, setup_test_event, sample_event_id):
        """Test retrieving stale open loops."""
        # Create an old loop (manually set old timestamp)
        old_loop = OpenLoop(
            event_id=sample_event_id,
            question="Old question",
            status=OpenLoopStatus.OPEN,
        )
        temp_db.insert_open_loop(old_loop)

        # Update created_at to 10 days ago via raw SQL
        ten_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
        temp_db.conn.execute("""
            UPDATE open_loops SET created_at = ? WHERE id = ?
        """, [ten_days_ago, str(old_loop.id)])

        # Create a recent loop
        recent_loop = OpenLoop(
            event_id=sample_event_id,
            question="Recent question",
            status=OpenLoopStatus.OPEN,
        )
        temp_db.insert_open_loop(recent_loop)

        # Get stale loops (older than 7 days)
        stale = temp_db.get_stale_open_loops(stale_days=7)

        assert len(stale) == 1
        assert stale[0].id == old_loop.id

    def test_count_open_loops(self, temp_db, setup_test_event, sample_event_id):
        """Test counting open loops."""
        statuses = [OpenLoopStatus.OPEN, OpenLoopStatus.OPEN, OpenLoopStatus.IN_PROGRESS]
        for i, status in enumerate(statuses):
            loop = OpenLoop(
                event_id=sample_event_id,
                question=f"Question {i}",
                status=status,
            )
            temp_db.insert_open_loop(loop)

        total = temp_db.count_open_loops()
        open_count = temp_db.count_open_loops(status=OpenLoopStatus.OPEN)
        in_progress_count = temp_db.count_open_loops(status=OpenLoopStatus.IN_PROGRESS)

        assert total == 3
        assert open_count == 2
        assert in_progress_count == 1


class TestOpenLoopIntegration:
    """Integration tests for open loops with events."""

    def test_open_loop_links_to_event(self, temp_db, setup_test_event, sample_event_id):
        """Test that open loop properly links to event via foreign key."""
        loop = OpenLoop(
            event_id=sample_event_id,
            question="Linked question",
        )
        temp_db.insert_open_loop(loop)

        # Verify we can query by event
        results = temp_db.get_open_loops_by_event(sample_event_id)
        assert len(results) == 1
        assert results[0].event_id == sample_event_id

    def test_multiple_loops_per_event(self, temp_db, setup_test_event, sample_event_id):
        """Test multiple open loops can be linked to same event."""
        for i in range(5):
            loop = OpenLoop(
                event_id=sample_event_id,
                question=f"Question {i} about the event",
            )
            temp_db.insert_open_loop(loop)

        results = temp_db.get_open_loops_by_event(sample_event_id)
        assert len(results) == 5

    def test_open_loop_lifecycle(self, temp_db, setup_test_event, sample_event_id):
        """Test complete open loop lifecycle: create -> progress -> resolve."""
        # Create
        loop = OpenLoop(
            event_id=sample_event_id,
            question="What is causing this pattern?",
            status=OpenLoopStatus.OPEN,
        )
        temp_db.insert_open_loop(loop)

        # Start investigation
        temp_db.update_open_loop_status(loop.id, OpenLoopStatus.IN_PROGRESS)
        temp_db.add_progress_note(loop.id, "Started investigating SEC filings")

        # More progress
        temp_db.add_progress_note(loop.id, "Found relevant 8-K filing")

        # Resolve
        temp_db.update_open_loop_status(loop.id, OpenLoopStatus.RESOLVED)

        # Verify final state
        result = temp_db.get_open_loop_by_id(loop.id)
        assert result.status == OpenLoopStatus.RESOLVED
        assert result.resolved_at is not None
        assert len(result.progress_notes) == 2
