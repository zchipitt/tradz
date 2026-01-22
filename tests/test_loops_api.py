"""
Tests for Open Loops API endpoints (US-023).

Tests cover:
- GET /api/loops with status filtering
- GET /api/loops/{loop_id} for loop details
- POST /api/loops to create new loops
- PATCH /api/loops/{loop_id} to update status or add notes
- DELETE /api/loops/{loop_id} to remove loops
"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mock the database before importing app
with patch("src.tradz.database.get_database") as mock_get_db:
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_loop_service():
    """Create mock loop service."""
    with patch("api.routers.loops.loop_service") as mock:
        yield mock


def create_mock_loop_dict(
    loop_id: str | None = None,
    event_id: str | None = None,
    question: str = "Test question",
    status: str = "open",
    progress_notes_count: int = 0,
    progress_notes: list | None = None,
    event_summary: dict | None = None,
):
    """Helper to create mock loop dictionaries."""
    loop_id = loop_id or str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    return {
        "loop_id": loop_id,
        "event_id": event_id,
        "question": question,
        "created_at": now,
        "status": status,
        "progress_notes_count": progress_notes_count,
        "progress_notes": progress_notes or [],
        "resolved_at": None,
        "event_summary": event_summary,
    }


# ==================================================
# Test GET /api/loops
# ==================================================

class TestGetLoops:
    """Tests for GET /api/loops endpoint."""

    def test_get_loops_empty(self, client, mock_loop_service):
        """Test getting loops when none exist."""
        mock_loop_service.get_loops.return_value = ([], 0)

        response = client.get("/api/loops")
        assert response.status_code == 200

        data = response.json()
        assert data["total_count"] == 0
        assert data["loops"] == []

    def test_get_loops_returns_all(self, client, mock_loop_service):
        """Test getting all loops."""
        loops = [
            create_mock_loop_dict(question="Question 1", status="open"),
            create_mock_loop_dict(question="Question 2", status="in_progress"),
            create_mock_loop_dict(question="Question 3", status="resolved"),
        ]
        mock_loop_service.get_loops.return_value = (loops, 3)

        response = client.get("/api/loops")
        assert response.status_code == 200

        data = response.json()
        assert data["total_count"] == 3
        assert len(data["loops"]) == 3

    def test_get_loops_filter_by_status_open(self, client, mock_loop_service):
        """Test filtering loops by open status."""
        loops = [create_mock_loop_dict(question="Open question", status="open")]
        mock_loop_service.get_loops.return_value = (loops, 1)

        response = client.get("/api/loops?status=open")
        assert response.status_code == 200

        data = response.json()
        assert data["total_count"] == 1
        mock_loop_service.get_loops.assert_called_with(status_filter="open")

    def test_get_loops_filter_by_status_in_progress(self, client, mock_loop_service):
        """Test filtering loops by in_progress status."""
        loops = [create_mock_loop_dict(question="In progress", status="in_progress")]
        mock_loop_service.get_loops.return_value = (loops, 1)

        response = client.get("/api/loops?status=in_progress")
        assert response.status_code == 200

        mock_loop_service.get_loops.assert_called_with(status_filter="in_progress")

    def test_get_loops_filter_by_status_resolved(self, client, mock_loop_service):
        """Test filtering loops by resolved status."""
        loops = [create_mock_loop_dict(question="Resolved", status="resolved")]
        mock_loop_service.get_loops.return_value = (loops, 1)

        response = client.get("/api/loops?status=resolved")
        assert response.status_code == 200

        mock_loop_service.get_loops.assert_called_with(status_filter="resolved")

    def test_get_loops_with_event_summary(self, client, mock_loop_service):
        """Test loops include event summary when linked to event."""
        event_summary = {
            "event_id": str(uuid4()),
            "title": "Test Event",
            "attention_score": 85.0,
            "status": "new",
        }
        loops = [create_mock_loop_dict(
            question="Question about event",
            event_summary=event_summary,
        )]
        mock_loop_service.get_loops.return_value = (loops, 1)

        response = client.get("/api/loops")
        assert response.status_code == 200

        data = response.json()
        loop_data = data["loops"][0]
        assert loop_data["event_summary"] is not None
        assert loop_data["event_summary"]["title"] == "Test Event"

    def test_get_loops_response_structure(self, client, mock_loop_service):
        """Test loops response has correct structure."""
        loops = [create_mock_loop_dict(
            question="Test question",
            progress_notes_count=2,
        )]
        mock_loop_service.get_loops.return_value = (loops, 1)

        response = client.get("/api/loops")
        assert response.status_code == 200

        data = response.json()
        loop_data = data["loops"][0]

        assert "loop_id" in loop_data
        assert "question" in loop_data
        assert "created_at" in loop_data
        assert "status" in loop_data
        assert "progress_notes_count" in loop_data
        assert loop_data["progress_notes_count"] == 2


# ==================================================
# Test GET /api/loops/{loop_id}
# ==================================================

class TestGetLoopById:
    """Tests for GET /api/loops/{loop_id} endpoint."""

    def test_get_loop_by_id_success(self, client, mock_loop_service):
        """Test getting loop by ID."""
        loop_id = str(uuid4())
        loop = create_mock_loop_dict(
            loop_id=loop_id,
            question="Detailed question",
            status="in_progress",
            progress_notes=["First note", "Second note"],
        )
        mock_loop_service.get_loop_by_id.return_value = loop

        response = client.get(f"/api/loops/{loop_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["loop_id"] == loop_id
        assert data["question"] == "Detailed question"
        assert data["status"] == "in_progress"
        assert len(data["progress_notes"]) == 2

    def test_get_loop_by_id_not_found(self, client, mock_loop_service):
        """Test getting non-existent loop returns 404."""
        mock_loop_service.get_loop_by_id.return_value = None

        fake_id = str(uuid4())
        response = client.get(f"/api/loops/{fake_id}")
        assert response.status_code == 404

    def test_get_loop_by_id_with_event_summary(self, client, mock_loop_service):
        """Test loop detail includes event summary when linked."""
        loop_id = str(uuid4())
        event_summary = {
            "event_id": str(uuid4()),
            "title": "Test Event",
            "attention_score": 85.0,
            "status": "new",
        }
        loop = create_mock_loop_dict(
            loop_id=loop_id,
            question="Event-linked question",
            event_summary=event_summary,
        )
        mock_loop_service.get_loop_by_id.return_value = loop

        response = client.get(f"/api/loops/{loop_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["event_summary"] is not None
        assert data["event_summary"]["title"] == "Test Event"


# ==================================================
# Test POST /api/loops
# ==================================================

class TestCreateLoop:
    """Tests for POST /api/loops endpoint."""

    def test_create_loop_success(self, client, mock_loop_service):
        """Test creating a new loop."""
        loop_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        mock_loop_service.create_loop.return_value = {
            "loop_id": loop_id,
            "question": "What is the market impact?",
            "status": "open",
            "created_at": now,
        }

        response = client.post(
            "/api/loops",
            json={"question": "What is the market impact?"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["loop_id"] == loop_id
        assert data["question"] == "What is the market impact?"
        assert data["status"] == "open"

    def test_create_loop_with_event_id(self, client, mock_loop_service):
        """Test creating a loop linked to an event."""
        loop_id = str(uuid4())
        event_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        mock_loop_service.create_loop.return_value = {
            "loop_id": loop_id,
            "question": "What is the event impact?",
            "status": "open",
            "created_at": now,
        }

        response = client.post(
            "/api/loops",
            json={
                "question": "What is the event impact?",
                "event_id": event_id,
            }
        )
        assert response.status_code == 200
        mock_loop_service.create_loop.assert_called_once_with(
            question="What is the event impact?",
            event_id=event_id,
        )

    def test_create_loop_empty_question(self, client, mock_loop_service):
        """Test creating loop with empty question fails validation."""
        response = client.post("/api/loops", json={"question": ""})
        assert response.status_code == 422  # Pydantic validation error

    def test_create_loop_invalid_event_id(self, client, mock_loop_service):
        """Test creating loop with non-existent event returns error."""
        mock_loop_service.create_loop.side_effect = ValueError("Event not found")

        response = client.post(
            "/api/loops",
            json={
                "question": "Test question",
                "event_id": str(uuid4()),
            }
        )
        assert response.status_code == 400


# ==================================================
# Test PATCH /api/loops/{loop_id}
# ==================================================

class TestUpdateLoop:
    """Tests for PATCH /api/loops/{loop_id} endpoint."""

    def test_update_loop_status(self, client, mock_loop_service):
        """Test updating loop status."""
        loop_id = str(uuid4())
        mock_loop_service.update_loop.return_value = {
            "loop_id": loop_id,
            "status": "in_progress",
            "progress_notes_count": 0,
            "updated": True,
            "message": "Status updated to in_progress",
        }

        response = client.patch(
            f"/api/loops/{loop_id}",
            json={"status": "in_progress"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "in_progress"
        assert data["updated"] is True

    def test_update_loop_add_progress_note(self, client, mock_loop_service):
        """Test adding progress note to loop."""
        loop_id = str(uuid4())
        mock_loop_service.update_loop.return_value = {
            "loop_id": loop_id,
            "status": "open",
            "progress_notes_count": 1,
            "updated": True,
            "message": "Progress note added",
        }

        response = client.patch(
            f"/api/loops/{loop_id}",
            json={"progress_note": "Found new evidence"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["progress_notes_count"] == 1
        assert data["updated"] is True

    def test_update_loop_status_and_note(self, client, mock_loop_service):
        """Test updating both status and adding note."""
        loop_id = str(uuid4())
        mock_loop_service.update_loop.return_value = {
            "loop_id": loop_id,
            "status": "in_progress",
            "progress_notes_count": 1,
            "updated": True,
            "message": "Status updated to in_progress and Progress note added",
        }

        response = client.patch(
            f"/api/loops/{loop_id}",
            json={
                "status": "in_progress",
                "progress_note": "Starting research"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "in_progress"
        assert data["progress_notes_count"] == 1
        assert data["updated"] is True

    def test_update_loop_not_found(self, client, mock_loop_service):
        """Test updating non-existent loop returns 404."""
        mock_loop_service.update_loop.side_effect = ValueError("Loop not found")

        fake_id = str(uuid4())
        response = client.patch(
            f"/api/loops/{fake_id}",
            json={"status": "resolved"}
        )
        assert response.status_code == 404

    def test_update_loop_no_changes(self, client, mock_loop_service):
        """Test update with no changes."""
        loop_id = str(uuid4())
        mock_loop_service.update_loop.return_value = {
            "loop_id": loop_id,
            "status": "open",
            "progress_notes_count": 0,
            "updated": False,
            "message": "No updates made",
        }

        response = client.patch(f"/api/loops/{loop_id}", json={})
        assert response.status_code == 200

        data = response.json()
        assert data["updated"] is False
        assert data["message"] == "No updates made"


# ==================================================
# Test DELETE /api/loops/{loop_id}
# ==================================================

class TestDeleteLoop:
    """Tests for DELETE /api/loops/{loop_id} endpoint."""

    def test_delete_loop_success(self, client, mock_loop_service):
        """Test deleting a loop."""
        loop_id = str(uuid4())
        mock_loop_service.delete_loop.return_value = {
            "loop_id": loop_id,
            "deleted": True,
            "message": "Open loop deleted successfully",
        }

        response = client.delete(f"/api/loops/{loop_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["loop_id"] == loop_id
        assert data["deleted"] is True

    def test_delete_loop_not_found(self, client, mock_loop_service):
        """Test deleting non-existent loop returns 404."""
        mock_loop_service.delete_loop.side_effect = ValueError("Loop not found")

        fake_id = str(uuid4())
        response = client.delete(f"/api/loops/{fake_id}")
        assert response.status_code == 404


# ==================================================
# Service Layer Tests (Unit Tests)
# ==================================================

class TestLoopServiceUnit:
    """Unit tests for LoopService business logic."""

    def test_service_get_loops_with_status_filter(self):
        """Test service correctly filters by status."""
        from api.services.loop_service import LoopService
        from src.tradz.models import OpenLoopStatus

        with patch("api.services.loop_service.get_database") as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.get_open_loops.return_value = []

            service = LoopService()
            service.get_loops(status_filter="open")

            mock_db_instance.get_open_loops.assert_called_once_with(status=OpenLoopStatus.OPEN)

    def test_service_get_loops_all_status(self):
        """Test service returns all loops when status is 'all'."""
        from api.services.loop_service import LoopService

        with patch("api.services.loop_service.get_database") as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.get_open_loops.return_value = []

            service = LoopService()
            service.get_loops(status_filter="all")

            mock_db_instance.get_open_loops.assert_called_once_with(status=None)

    def test_service_create_loop_validates_event(self):
        """Test service validates event exists when event_id provided."""
        from api.services.loop_service import LoopService

        with patch("api.services.loop_service.get_database") as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.get_event_by_id.return_value = None  # Event not found

            service = LoopService()

            with pytest.raises(ValueError, match="not found"):
                service.create_loop(
                    question="Test question",
                    event_id=str(uuid4()),
                )

    def test_service_update_loop_validates_existence(self):
        """Test service validates loop exists before update."""
        from api.services.loop_service import LoopService

        with patch("api.services.loop_service.get_database") as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.get_open_loop_by_id.return_value = None

            service = LoopService()

            with pytest.raises(ValueError, match="not found"):
                service.update_loop(
                    loop_id=str(uuid4()),
                    status="resolved",
                )

    def test_service_delete_loop_validates_existence(self):
        """Test service validates loop exists before delete."""
        from api.services.loop_service import LoopService

        with patch("api.services.loop_service.get_database") as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.get_open_loop_by_id.return_value = None

            service = LoopService()

            with pytest.raises(ValueError, match="not found"):
                service.delete_loop(loop_id=str(uuid4()))
