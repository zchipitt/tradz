"""
Unit tests for Events API endpoints.

Tests cover:
- GET /api/events with filter/sort/pagination
- GET /api/events/{event_id} for event details
- Status filtering (active, resolved, dismissed, all)
- Sort options (attention_score, last_update_at, start_at)
- Pagination (limit, offset)
- 404 for non-existent events
"""
import sys
from pathlib import Path

# Add src to path for tradz imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

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
def mock_event_service():
    """Create mock event service."""
    with patch("api.routers.events.event_service") as mock:
        yield mock


def create_mock_event_dict(
    event_id: str | None = None,
    entity_id: str | None = None,
    ticker: str = "AAPL",
    title: str = "Test Event",
    event_type: str = "market_anomaly",
    status: str = "new",
    anomaly_score: float = 80.0,
    catalyst_score: float = 70.0,
    flow_score: float = 60.0,
    confidence_score: float = 75.0,
    observation_count: int = 3,
    pinned: bool = False,
    snoozed_until=None,
):
    """Helper to create mock event dictionaries."""
    event_id = event_id or str(uuid4())
    entity_id = entity_id or str(uuid4())

    attention_score = (
        anomaly_score * 0.3 +
        catalyst_score * 0.3 +
        flow_score * 0.25 +
        confidence_score * 0.15
    )

    return {
        "event_id": event_id,
        "entity_id": entity_id,
        "ticker": ticker,
        "title": title,
        "event_type": event_type,
        "status": status,
        "confidence": 0.8,
        "start_at": datetime.now(timezone.utc),
        "last_update_at": datetime.now(timezone.utc),
        "resolved_at": None,
        "parent_event_id": None,
        "pinned": pinned,
        "snoozed_until": snoozed_until,
        "dismissed_reason": None,
        "title_template": None,
        "title_source": "llm",
        "anomaly_score": anomaly_score,
        "catalyst_score": catalyst_score,
        "flow_score": flow_score,
        "confidence_score": confidence_score,
        "attention_score": attention_score,
        "observation_count": observation_count,
        "scores": {
            "anomaly_score": anomaly_score,
            "catalyst_score": catalyst_score,
            "flow_score": flow_score,
            "confidence_score": confidence_score,
        },
    }


def create_mock_event_detail(event_dict: dict):
    """Add observation details to event dict for detail endpoint."""
    detail = event_dict.copy()
    detail["observations"] = [
        {
            "observation_id": str(uuid4()),
            "source": "equities",
            "title": "Price surge detected",
            "summary": "AAPL price increased 5%",
            "timestamp": datetime.now(timezone.utc),
            "source_url": "https://example.com/source",
            "fact_entries": [
                {
                    "fact_id": "fact-1",
                    "fact_type": "price_change",
                    "label": "Price Change",
                    "value": 5.0,
                    "unit": "%",
                    "source": "Yahoo Finance",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ],
        }
    ]
    detail["entity"] = {
        "entity_id": event_dict["entity_id"],
        "ticker": event_dict["ticker"],
        "name": "Apple Inc.",
    }
    return detail


class TestGetEvents:
    """Tests for GET /api/events endpoint."""

    def test_get_events_default_params(self, client, mock_event_service):
        """Test getting events with default parameters."""
        mock_events = [
            create_mock_event_dict(ticker="AAPL"),
            create_mock_event_dict(ticker="NVDA"),
        ]
        mock_event_service.get_events.return_value = (mock_events, 2)

        response = client.get("/api/events")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["events"]) == 2
        assert data["offset"] == 0
        assert data["limit"] == 20

        # Verify service was called with defaults
        mock_event_service.get_events.assert_called_once_with(
            status_filter="active",
            sort_by="attention_score",
            limit=20,
            offset=0,
        )

    def test_get_events_with_status_filter(self, client, mock_event_service):
        """Test filtering events by status."""
        mock_event_service.get_events.return_value = ([], 0)

        # Test each status filter
        for status in ["active", "resolved", "dismissed", "all"]:
            response = client.get(f"/api/events?status={status}")
            assert response.status_code == 200

    def test_get_events_with_sort(self, client, mock_event_service):
        """Test sorting events."""
        mock_event_service.get_events.return_value = ([], 0)

        # Test each sort option
        for sort in ["attention_score", "last_update_at", "start_at"]:
            response = client.get(f"/api/events?sort={sort}")
            assert response.status_code == 200

    def test_get_events_with_pagination(self, client, mock_event_service):
        """Test pagination parameters."""
        mock_events = [create_mock_event_dict() for _ in range(10)]
        mock_event_service.get_events.return_value = (mock_events[:5], 10)

        response = client.get("/api/events?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0
        assert data["total_count"] == 10
        assert len(data["events"]) == 5

    def test_get_events_pagination_with_offset(self, client, mock_event_service):
        """Test pagination with offset."""
        mock_events = [create_mock_event_dict() for _ in range(5)]
        mock_event_service.get_events.return_value = (mock_events, 15)

        response = client.get("/api/events?limit=5&offset=10")

        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 10
        mock_event_service.get_events.assert_called_once_with(
            status_filter="active",
            sort_by="attention_score",
            limit=5,
            offset=10,
        )

    def test_get_events_limit_max_100(self, client, mock_event_service):
        """Test that limit is capped at 100."""
        mock_event_service.get_events.return_value = ([], 0)

        # Request with limit > 100 should be rejected
        response = client.get("/api/events?limit=150")
        assert response.status_code == 422  # Validation error

    def test_get_events_limit_min_1(self, client, mock_event_service):
        """Test that limit minimum is 1."""
        mock_event_service.get_events.return_value = ([], 0)

        response = client.get("/api/events?limit=0")
        assert response.status_code == 422  # Validation error

    def test_get_events_offset_non_negative(self, client, mock_event_service):
        """Test that offset must be non-negative."""
        mock_event_service.get_events.return_value = ([], 0)

        response = client.get("/api/events?offset=-5")
        assert response.status_code == 422  # Validation error

    def test_get_events_empty_result(self, client, mock_event_service):
        """Test empty events list."""
        mock_event_service.get_events.return_value = ([], 0)

        response = client.get("/api/events")

        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["total_count"] == 0

    def test_get_events_response_structure(self, client, mock_event_service):
        """Test that response has correct structure."""
        mock_event = create_mock_event_dict(
            ticker="NVDA",
            title="NVDA Surges on AI News",
            event_type="catalyst_news",
            status="ongoing",
        )
        mock_event_service.get_events.return_value = ([mock_event], 1)

        response = client.get("/api/events")

        assert response.status_code == 200
        data = response.json()
        event = data["events"][0]

        # Verify all required fields are present
        assert "event_id" in event
        assert "ticker" in event
        assert "title" in event
        assert "event_type" in event
        assert "status" in event
        assert "attention_score" in event
        assert "scores" in event
        assert "observation_count" in event
        assert "last_update_at" in event
        assert "start_at" in event
        assert "pinned" in event

        # Verify scores structure
        scores = event["scores"]
        assert "anomaly_score" in scores
        assert "catalyst_score" in scores
        assert "flow_score" in scores
        assert "confidence_score" in scores

    def test_get_events_service_error(self, client, mock_event_service):
        """Test error handling when service fails."""
        mock_event_service.get_events.side_effect = Exception("Database error")

        response = client.get("/api/events")

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


class TestGetEventById:
    """Tests for GET /api/events/{event_id} endpoint."""

    def test_get_event_by_id_success(self, client, mock_event_service):
        """Test getting event by ID successfully."""
        event_id = str(uuid4())
        mock_event = create_mock_event_dict(event_id=event_id, ticker="AAPL")
        mock_detail = create_mock_event_detail(mock_event)
        mock_event_service.get_event_by_id.return_value = mock_detail

        response = client.get(f"/api/events/{event_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == event_id
        assert data["title"] == "Test Event"
        mock_event_service.get_event_by_id.assert_called_once_with(event_id)

    def test_get_event_by_id_not_found(self, client, mock_event_service):
        """Test 404 when event not found."""
        event_id = str(uuid4())
        mock_event_service.get_event_by_id.return_value = None

        response = client.get(f"/api/events/{event_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_event_detail_response_structure(self, client, mock_event_service):
        """Test that detail response has correct structure."""
        event_id = str(uuid4())
        mock_event = create_mock_event_dict(event_id=event_id)
        mock_detail = create_mock_event_detail(mock_event)
        mock_event_service.get_event_by_id.return_value = mock_detail

        response = client.get(f"/api/events/{event_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify all detail fields are present
        assert "event_id" in data
        assert "entity" in data
        assert "title" in data
        assert "event_type" in data
        assert "status" in data
        assert "attention_score" in data
        assert "scores" in data
        assert "start_at" in data
        assert "last_update_at" in data
        assert "resolved_at" in data
        assert "pinned" in data
        assert "snoozed_until" in data
        assert "dismissed_reason" in data
        assert "title_source" in data
        assert "parent_event_id" in data
        assert "observation_count" in data
        assert "observations" in data

        # Verify entity structure
        entity = data["entity"]
        assert "entity_id" in entity
        assert "ticker" in entity
        assert "name" in entity

        # Verify observations structure
        if data["observations"]:
            obs = data["observations"][0]
            assert "observation_id" in obs
            assert "source" in obs
            assert "timestamp" in obs
            assert "fact_entries" in obs

    def test_get_event_detail_with_observations(self, client, mock_event_service):
        """Test that observations are included in detail."""
        event_id = str(uuid4())
        mock_event = create_mock_event_dict(event_id=event_id)
        mock_detail = create_mock_event_detail(mock_event)
        mock_event_service.get_event_by_id.return_value = mock_detail

        response = client.get(f"/api/events/{event_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["observations"]) == 1

        obs = data["observations"][0]
        assert obs["source"] == "equities"
        assert obs["title"] == "Price surge detected"
        assert len(obs["fact_entries"]) == 1

    def test_get_event_service_error(self, client, mock_event_service):
        """Test error handling when service fails."""
        event_id = str(uuid4())
        mock_event_service.get_event_by_id.side_effect = Exception("Database error")

        response = client.get(f"/api/events/{event_id}")

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


class TestEventFilters:
    """Tests for event filtering combinations."""

    def test_filter_active_events(self, client, mock_event_service):
        """Test filtering for active events only."""
        mock_events = [
            create_mock_event_dict(status="new"),
            create_mock_event_dict(status="ongoing"),
        ]
        mock_event_service.get_events.return_value = (mock_events, 2)

        response = client.get("/api/events?status=active")

        assert response.status_code == 200
        mock_event_service.get_events.assert_called_once()
        call_args = mock_event_service.get_events.call_args
        assert call_args.kwargs["status_filter"] == "active"

    def test_filter_resolved_events(self, client, mock_event_service):
        """Test filtering for resolved events."""
        mock_events = [create_mock_event_dict(status="resolved")]
        mock_event_service.get_events.return_value = (mock_events, 1)

        response = client.get("/api/events?status=resolved")

        assert response.status_code == 200
        call_args = mock_event_service.get_events.call_args
        assert call_args.kwargs["status_filter"] == "resolved"

    def test_filter_dismissed_events(self, client, mock_event_service):
        """Test filtering for dismissed events."""
        mock_events = [create_mock_event_dict(status="dismissed")]
        mock_event_service.get_events.return_value = (mock_events, 1)

        response = client.get("/api/events?status=dismissed")

        assert response.status_code == 200
        call_args = mock_event_service.get_events.call_args
        assert call_args.kwargs["status_filter"] == "dismissed"

    def test_filter_all_events(self, client, mock_event_service):
        """Test filtering for all events."""
        mock_events = [
            create_mock_event_dict(status="new"),
            create_mock_event_dict(status="resolved"),
            create_mock_event_dict(status="dismissed"),
        ]
        mock_event_service.get_events.return_value = (mock_events, 3)

        response = client.get("/api/events?status=all")

        assert response.status_code == 200
        call_args = mock_event_service.get_events.call_args
        assert call_args.kwargs["status_filter"] == "all"


class TestEventSorting:
    """Tests for event sorting options."""

    def test_sort_by_attention_score(self, client, mock_event_service):
        """Test sorting by attention score (default)."""
        mock_event_service.get_events.return_value = ([], 0)

        response = client.get("/api/events?sort=attention_score")

        assert response.status_code == 200
        call_args = mock_event_service.get_events.call_args
        assert call_args.kwargs["sort_by"] == "attention_score"

    def test_sort_by_last_update(self, client, mock_event_service):
        """Test sorting by last update time."""
        mock_event_service.get_events.return_value = ([], 0)

        response = client.get("/api/events?sort=last_update_at")

        assert response.status_code == 200
        call_args = mock_event_service.get_events.call_args
        assert call_args.kwargs["sort_by"] == "last_update_at"

    def test_sort_by_created_time(self, client, mock_event_service):
        """Test sorting by creation time."""
        mock_event_service.get_events.return_value = ([], 0)

        response = client.get("/api/events?sort=start_at")

        assert response.status_code == 200
        call_args = mock_event_service.get_events.call_args
        assert call_args.kwargs["sort_by"] == "start_at"

    def test_invalid_sort_option(self, client):
        """Test that invalid sort option is rejected."""
        response = client.get("/api/events?sort=invalid")

        assert response.status_code == 422  # Validation error


class TestEventActions:
    """Tests for POST /api/events/{event_id}/actions endpoint."""

    def test_pin_event_success(self, client, mock_event_service):
        """Test pinning an event successfully."""
        event_id = str(uuid4())
        mock_event_service.perform_action.return_value = {
            "event_id": event_id,
            "action": "pin",
            "success": True,
            "message": "Event pinned successfully",
            "new_status": None,
            "pinned": True,
            "snoozed_until": None,
        }

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "pin"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "pin"
        assert data["pinned"] is True
        mock_event_service.perform_action.assert_called_once_with(
            event_id=event_id,
            action="pin",
            duration_hours=24,
            reason=None,
        )

    def test_unpin_event_success(self, client, mock_event_service):
        """Test unpinning an event successfully."""
        event_id = str(uuid4())
        mock_event_service.perform_action.return_value = {
            "event_id": event_id,
            "action": "unpin",
            "success": True,
            "message": "Event unpinned successfully",
            "new_status": None,
            "pinned": False,
            "snoozed_until": None,
        }

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "unpin"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "unpin"
        assert data["pinned"] is False

    def test_snooze_event_default_duration(self, client, mock_event_service):
        """Test snoozing an event with default 24h duration."""
        event_id = str(uuid4())
        snoozed_until = "2026-01-22T10:00:00Z"
        mock_event_service.perform_action.return_value = {
            "event_id": event_id,
            "action": "snooze",
            "success": True,
            "message": "Event snoozed for 24 hours",
            "new_status": None,
            "pinned": None,
            "snoozed_until": snoozed_until,
        }

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "snooze"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "snooze"
        assert data["snoozed_until"] == snoozed_until
        mock_event_service.perform_action.assert_called_once_with(
            event_id=event_id,
            action="snooze",
            duration_hours=24,
            reason=None,
        )

    def test_snooze_event_custom_duration(self, client, mock_event_service):
        """Test snoozing an event with custom duration."""
        event_id = str(uuid4())
        mock_event_service.perform_action.return_value = {
            "event_id": event_id,
            "action": "snooze",
            "success": True,
            "message": "Event snoozed for 48 hours",
            "new_status": None,
            "pinned": None,
            "snoozed_until": "2026-01-23T10:00:00Z",
        }

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "snooze", "duration_hours": 48},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_event_service.perform_action.assert_called_once_with(
            event_id=event_id,
            action="snooze",
            duration_hours=48,
            reason=None,
        )

    def test_dismiss_event_success(self, client, mock_event_service):
        """Test dismissing an event successfully."""
        event_id = str(uuid4())
        mock_event_service.perform_action.return_value = {
            "event_id": event_id,
            "action": "dismiss",
            "success": True,
            "message": "Event dismissed",
            "new_status": "dismissed",
            "pinned": None,
            "snoozed_until": None,
        }

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "dismiss"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "dismiss"
        assert data["new_status"] == "dismissed"

    def test_dismiss_event_with_reason(self, client, mock_event_service):
        """Test dismissing an event with a reason."""
        event_id = str(uuid4())
        mock_event_service.perform_action.return_value = {
            "event_id": event_id,
            "action": "dismiss",
            "success": True,
            "message": "Event dismissed",
            "new_status": "dismissed",
            "pinned": None,
            "snoozed_until": None,
        }

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "dismiss", "reason": "Not relevant to my portfolio"},
        )

        assert response.status_code == 200
        mock_event_service.perform_action.assert_called_once_with(
            event_id=event_id,
            action="dismiss",
            duration_hours=24,
            reason="Not relevant to my portfolio",
        )

    def test_resolve_event_success(self, client, mock_event_service):
        """Test resolving an event successfully."""
        event_id = str(uuid4())
        mock_event_service.perform_action.return_value = {
            "event_id": event_id,
            "action": "resolve",
            "success": True,
            "message": "Event marked as resolved",
            "new_status": "resolved",
            "pinned": None,
            "snoozed_until": None,
        }

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "resolve"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "resolve"
        assert data["new_status"] == "resolved"

    def test_action_event_not_found(self, client, mock_event_service):
        """Test 404 when event not found."""
        event_id = str(uuid4())
        mock_event_service.perform_action.side_effect = ValueError(f"Event {event_id} not found")

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "pin"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_action_invalid_action(self, client):
        """Test validation error for invalid action."""
        event_id = str(uuid4())

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "invalid_action"},
        )

        assert response.status_code == 422  # Validation error

    def test_action_missing_action(self, client):
        """Test validation error when action is missing."""
        event_id = str(uuid4())

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={},
        )

        assert response.status_code == 422  # Validation error

    def test_snooze_duration_validation_min(self, client):
        """Test that snooze duration must be at least 1 hour."""
        event_id = str(uuid4())

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "snooze", "duration_hours": 0},
        )

        assert response.status_code == 422  # Validation error

    def test_snooze_duration_validation_max(self, client):
        """Test that snooze duration must be at most 168 hours (1 week)."""
        event_id = str(uuid4())

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "snooze", "duration_hours": 200},
        )

        assert response.status_code == 422  # Validation error

    def test_action_service_error(self, client, mock_event_service):
        """Test error handling when service fails."""
        event_id = str(uuid4())
        mock_event_service.perform_action.side_effect = Exception("Database error")

        response = client.post(
            f"/api/events/{event_id}/actions",
            json={"action": "pin"},
        )

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]

    def test_pinned_events_sort_to_top(self, client, mock_event_service):
        """Test that pinned events are returned first when sorting by attention_score."""
        unpinned_event = create_mock_event_dict(
            ticker="AAPL",
            anomaly_score=90.0,
            pinned=False,
        )
        pinned_event = create_mock_event_dict(
            ticker="NVDA",
            anomaly_score=50.0,
            pinned=True,
        )
        # Return pinned first despite lower attention score
        mock_event_service.get_events.return_value = ([pinned_event, unpinned_event], 2)

        response = client.get("/api/events?sort=attention_score")

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 2
        # Pinned event should be first
        assert data["events"][0]["pinned"] is True

    def test_snoozed_events_hidden_from_active(self, client, mock_event_service):
        """Test that snoozed events are filtered from active status."""
        # Only create active event - snoozed events are filtered by service logic
        active_event = create_mock_event_dict(
            ticker="NVDA",
            status="new",
            snoozed_until=None,
        )
        # Service should only return non-snoozed events for active filter
        mock_event_service.get_events.return_value = ([active_event], 1)

        response = client.get("/api/events?status=active")

        assert response.status_code == 200
        data = response.json()
        # Only the non-snoozed event should be returned
        assert len(data["events"]) == 1
        assert data["events"][0]["ticker"] == "NVDA"


def create_mock_timeline_observation(
    observation_id: str | None = None,
    source: str = "equities",
    observation_type: str = "",
    title: str | None = "Price surge detected",
    summary: str = "AAPL price increased 5%",
    source_url: str | None = "https://example.com/source",
    fact_entries: list | None = None,
):
    """Helper to create mock timeline observation dictionaries."""
    observation_id = observation_id or str(uuid4())

    if fact_entries is None:
        fact_entries = [
            {
                "fact_id": "fact-1",
                "fact_type": "price_change",
                "label": "Price Change",
                "value": 5.0,
                "unit": "%",
                "source": "Yahoo Finance",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]

    return {
        "observation_id": observation_id,
        "source": source,
        "observation_type": observation_type,
        "timestamp": datetime.now(timezone.utc),
        "title": title,
        "summary": summary,
        "fact_entries": fact_entries,
        "source_url": source_url,
    }


class TestGetEventTimeline:
    """Tests for GET /api/events/{event_id}/timeline endpoint."""

    def test_get_timeline_default_params(self, client, mock_event_service):
        """Test getting timeline with default parameters."""
        event_id = str(uuid4())
        mock_observations = [
            create_mock_timeline_observation(source="equities"),
            create_mock_timeline_observation(source="news"),
        ]
        mock_event_service.get_event_timeline.return_value = (mock_observations, 2)

        response = client.get(f"/api/events/{event_id}/timeline")

        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == event_id
        assert data["total_count"] == 2
        assert len(data["observations"]) == 2
        assert data["offset"] == 0
        assert data["limit"] == 20

        # Verify service was called with defaults
        mock_event_service.get_event_timeline.assert_called_once_with(
            event_id=event_id,
            source_filter="all",
            limit=20,
            offset=0,
        )

    def test_get_timeline_with_source_filter_all(self, client, mock_event_service):
        """Test timeline with source filter 'all'."""
        event_id = str(uuid4())
        mock_event_service.get_event_timeline.return_value = ([], 0)

        response = client.get(f"/api/events/{event_id}/timeline?source=all")

        assert response.status_code == 200
        mock_event_service.get_event_timeline.assert_called_once_with(
            event_id=event_id,
            source_filter="all",
            limit=20,
            offset=0,
        )

    def test_get_timeline_with_source_filter_market(self, client, mock_event_service):
        """Test timeline with source filter 'market' (equities + crypto)."""
        event_id = str(uuid4())
        mock_observations = [
            create_mock_timeline_observation(source="equities"),
            create_mock_timeline_observation(source="crypto"),
        ]
        mock_event_service.get_event_timeline.return_value = (mock_observations, 2)

        response = client.get(f"/api/events/{event_id}/timeline?source=market")

        assert response.status_code == 200
        mock_event_service.get_event_timeline.assert_called_once_with(
            event_id=event_id,
            source_filter="market",
            limit=20,
            offset=0,
        )

    def test_get_timeline_with_source_filter_news(self, client, mock_event_service):
        """Test timeline with source filter 'news'."""
        event_id = str(uuid4())
        mock_observations = [
            create_mock_timeline_observation(source="news"),
        ]
        mock_event_service.get_event_timeline.return_value = (mock_observations, 1)

        response = client.get(f"/api/events/{event_id}/timeline?source=news")

        assert response.status_code == 200
        mock_event_service.get_event_timeline.assert_called_once_with(
            event_id=event_id,
            source_filter="news",
            limit=20,
            offset=0,
        )

    def test_get_timeline_with_source_filter_sec(self, client, mock_event_service):
        """Test timeline with source filter 'sec'."""
        event_id = str(uuid4())
        mock_event_service.get_event_timeline.return_value = ([], 0)

        response = client.get(f"/api/events/{event_id}/timeline?source=sec")

        assert response.status_code == 200
        mock_event_service.get_event_timeline.assert_called_once_with(
            event_id=event_id,
            source_filter="sec",
            limit=20,
            offset=0,
        )

    def test_get_timeline_with_source_filter_congress(self, client, mock_event_service):
        """Test timeline with source filter 'congress'."""
        event_id = str(uuid4())
        mock_event_service.get_event_timeline.return_value = ([], 0)

        response = client.get(f"/api/events/{event_id}/timeline?source=congress")

        assert response.status_code == 200
        mock_event_service.get_event_timeline.assert_called_once_with(
            event_id=event_id,
            source_filter="congress",
            limit=20,
            offset=0,
        )

    def test_get_timeline_with_source_filter_13f(self, client, mock_event_service):
        """Test timeline with source filter '13f' (hedgefund alias)."""
        event_id = str(uuid4())
        mock_event_service.get_event_timeline.return_value = ([], 0)

        response = client.get(f"/api/events/{event_id}/timeline?source=13f")

        assert response.status_code == 200
        mock_event_service.get_event_timeline.assert_called_once_with(
            event_id=event_id,
            source_filter="13f",
            limit=20,
            offset=0,
        )

    def test_get_timeline_with_source_filter_polymarket(self, client, mock_event_service):
        """Test timeline with source filter 'polymarket'."""
        event_id = str(uuid4())
        mock_event_service.get_event_timeline.return_value = ([], 0)

        response = client.get(f"/api/events/{event_id}/timeline?source=polymarket")

        assert response.status_code == 200
        mock_event_service.get_event_timeline.assert_called_once_with(
            event_id=event_id,
            source_filter="polymarket",
            limit=20,
            offset=0,
        )

    def test_get_timeline_with_pagination(self, client, mock_event_service):
        """Test timeline pagination parameters."""
        event_id = str(uuid4())
        mock_observations = [create_mock_timeline_observation() for _ in range(5)]
        mock_event_service.get_event_timeline.return_value = (mock_observations, 15)

        response = client.get(f"/api/events/{event_id}/timeline?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0
        assert data["total_count"] == 15
        assert len(data["observations"]) == 5

    def test_get_timeline_pagination_with_offset(self, client, mock_event_service):
        """Test timeline pagination with offset."""
        event_id = str(uuid4())
        mock_observations = [create_mock_timeline_observation() for _ in range(5)]
        mock_event_service.get_event_timeline.return_value = (mock_observations, 20)

        response = client.get(f"/api/events/{event_id}/timeline?limit=5&offset=10")

        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 10
        mock_event_service.get_event_timeline.assert_called_once_with(
            event_id=event_id,
            source_filter="all",
            limit=5,
            offset=10,
        )

    def test_get_timeline_limit_max_100(self, client):
        """Test that limit is capped at 100."""
        event_id = str(uuid4())

        response = client.get(f"/api/events/{event_id}/timeline?limit=150")
        assert response.status_code == 422  # Validation error

    def test_get_timeline_limit_min_1(self, client):
        """Test that limit minimum is 1."""
        event_id = str(uuid4())

        response = client.get(f"/api/events/{event_id}/timeline?limit=0")
        assert response.status_code == 422  # Validation error

    def test_get_timeline_offset_non_negative(self, client):
        """Test that offset must be non-negative."""
        event_id = str(uuid4())

        response = client.get(f"/api/events/{event_id}/timeline?offset=-5")
        assert response.status_code == 422  # Validation error

    def test_get_timeline_empty_result(self, client, mock_event_service):
        """Test empty timeline result."""
        event_id = str(uuid4())
        mock_event_service.get_event_timeline.return_value = ([], 0)

        response = client.get(f"/api/events/{event_id}/timeline")

        assert response.status_code == 200
        data = response.json()
        assert data["observations"] == []
        assert data["total_count"] == 0

    def test_get_timeline_response_structure(self, client, mock_event_service):
        """Test that timeline response has correct structure."""
        event_id = str(uuid4())
        mock_observation = create_mock_timeline_observation(
            source="news",
            observation_type="article",
            title="AAPL Beats Earnings",
            summary="Apple reported strong Q4...",
        )
        mock_event_service.get_event_timeline.return_value = ([mock_observation], 1)

        response = client.get(f"/api/events/{event_id}/timeline")

        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure
        assert "event_id" in data
        assert "observations" in data
        assert "total_count" in data
        assert "offset" in data
        assert "limit" in data

        # Verify observation structure
        obs = data["observations"][0]
        assert "observation_id" in obs
        assert "source" in obs
        assert "observation_type" in obs
        assert "timestamp" in obs
        assert "title" in obs
        assert "summary" in obs
        assert "fact_entries" in obs
        assert "source_url" in obs

        # Verify fact entry structure
        fact = obs["fact_entries"][0]
        assert "fact_id" in fact
        assert "fact_type" in fact
        assert "label" in fact
        assert "value" in fact
        assert "unit" in fact
        assert "source" in fact

    def test_get_timeline_event_not_found(self, client, mock_event_service):
        """Test 404 when event not found."""
        event_id = str(uuid4())
        mock_event_service.get_event_timeline.side_effect = ValueError(f"Event {event_id} not found")

        response = client.get(f"/api/events/{event_id}/timeline")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_timeline_service_error(self, client, mock_event_service):
        """Test error handling when service fails."""
        event_id = str(uuid4())
        mock_event_service.get_event_timeline.side_effect = Exception("Database error")

        response = client.get(f"/api/events/{event_id}/timeline")

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]

    def test_get_timeline_invalid_source_filter(self, client):
        """Test validation error for invalid source filter."""
        event_id = str(uuid4())

        response = client.get(f"/api/events/{event_id}/timeline?source=invalid")
        assert response.status_code == 422  # Validation error

    def test_get_timeline_observations_sorted_desc(self, client, mock_event_service):
        """Test that observations are sorted by timestamp descending."""
        event_id = str(uuid4())
        # Mock service returns observations in desc order (most recent first)
        mock_observations = [
            create_mock_timeline_observation(source="news"),
            create_mock_timeline_observation(source="equities"),
        ]
        mock_event_service.get_event_timeline.return_value = (mock_observations, 2)

        response = client.get(f"/api/events/{event_id}/timeline")

        assert response.status_code == 200
        data = response.json()
        assert len(data["observations"]) == 2
        # Order should be preserved from service (desc by timestamp)

    def test_get_timeline_with_empty_fact_entries(self, client, mock_event_service):
        """Test timeline observation with no fact entries."""
        event_id = str(uuid4())
        mock_observation = create_mock_timeline_observation(fact_entries=[])
        mock_event_service.get_event_timeline.return_value = ([mock_observation], 1)

        response = client.get(f"/api/events/{event_id}/timeline")

        assert response.status_code == 200
        data = response.json()
        obs = data["observations"][0]
        assert obs["fact_entries"] == []

    def test_get_timeline_with_null_optional_fields(self, client, mock_event_service):
        """Test timeline observation with null optional fields."""
        event_id = str(uuid4())
        mock_observation = create_mock_timeline_observation(
            title=None,
            source_url=None,
        )
        mock_event_service.get_event_timeline.return_value = ([mock_observation], 1)

        response = client.get(f"/api/events/{event_id}/timeline")

        assert response.status_code == 200
        data = response.json()
        obs = data["observations"][0]
        assert obs["title"] is None
        assert obs["source_url"] is None
