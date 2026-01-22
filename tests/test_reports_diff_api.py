"""
Tests for Reports Diff API endpoint.

Covers:
- GET /api/reports/diff - Compare two daily briefs
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


class TestReportsDiffEndpoint:
    """Tests for GET /api/reports/diff"""

    @pytest.fixture
    def mock_brief_service(self):
        """Mock BriefService instance."""
        service = MagicMock()
        service.compare_briefs = MagicMock()
        return service

    def test_diff_default_dates(self, mock_brief_service):
        """Test diff with default dates (today vs yesterday)."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

        mock_diff = {
            "date": today,
            "baseline": yesterday,
            "has_baseline": True,
            "new_events": [
                {
                    "event_id": "evt-new-001",
                    "title": "AAPL Surges 8%",
                    "ticker": "AAPL",
                    "event_type": "market_anomaly",
                    "attention_score": 85.0,
                }
            ],
            "resolved_events": [],
            "score_changes": [],
            "new_trade_ideas": [],
            "closed_loops": [],
            "total_new_events": 1,
            "total_resolved": 0,
            "total_score_changes": 0,
            "total_new_trade_ideas": 0,
            "total_closed_loops": 0,
        }
        mock_brief_service.compare_briefs.return_value = mock_diff

        with patch("api.routers.reports.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/reports/diff")

        assert response.status_code == 200
        data = response.json()
        assert data["date"] == today
        assert data["baseline"] == yesterday
        assert data["has_baseline"] is True
        assert data["total_new_events"] == 1
        assert len(data["new_events"]) == 1
        assert data["new_events"][0]["ticker"] == "AAPL"

    def test_diff_custom_dates(self, mock_brief_service):
        """Test diff with custom date and baseline parameters."""
        mock_diff = {
            "date": "2024-01-15",
            "baseline": "2024-01-10",
            "has_baseline": True,
            "new_events": [],
            "resolved_events": [
                {
                    "event_id": "evt-res-001",
                    "title": "MSFT Filing Event",
                    "ticker": "MSFT",
                    "resolution_type": "resolved",
                    "final_score": 72.5,
                }
            ],
            "score_changes": [
                {
                    "event_id": "evt-chg-001",
                    "title": "GOOGL Trend",
                    "ticker": "GOOGL",
                    "previous_score": 65.0,
                    "current_score": 78.0,
                    "delta": 13.0,
                    "direction": "up",
                }
            ],
            "new_trade_ideas": [],
            "closed_loops": [],
            "total_new_events": 0,
            "total_resolved": 1,
            "total_score_changes": 1,
            "total_new_trade_ideas": 0,
            "total_closed_loops": 0,
        }
        mock_brief_service.compare_briefs.return_value = mock_diff

        with patch("api.routers.reports.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/reports/diff?date=2024-01-15&baseline=2024-01-10")

        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2024-01-15"
        assert data["baseline"] == "2024-01-10"
        assert data["total_resolved"] == 1
        assert data["total_score_changes"] == 1
        assert data["resolved_events"][0]["ticker"] == "MSFT"
        assert data["score_changes"][0]["direction"] == "up"

    def test_diff_no_baseline(self, mock_brief_service):
        """Test diff when baseline brief doesn't exist."""
        mock_diff = {
            "date": "2024-01-15",
            "baseline": "2024-01-14",
            "has_baseline": False,
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
        mock_brief_service.compare_briefs.return_value = mock_diff

        with patch("api.routers.reports.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/reports/diff?date=2024-01-15")

        assert response.status_code == 200
        data = response.json()
        assert data["has_baseline"] is False
        assert data["total_new_events"] == 0
        assert data["total_resolved"] == 0

    def test_diff_invalid_date_format(self, mock_brief_service):
        """Test 400 error for invalid date format."""
        with patch("api.routers.reports.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/reports/diff?date=01-15-2024")

        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]

    def test_diff_invalid_baseline_format(self, mock_brief_service):
        """Test 400 error for invalid baseline format."""
        with patch("api.routers.reports.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/reports/diff?date=2024-01-15&baseline=invalid")

        assert response.status_code == 400
        assert "Invalid baseline date format" in response.json()["detail"]

    def test_diff_with_new_trade_ideas(self, mock_brief_service):
        """Test diff includes new trade ideas."""
        mock_diff = {
            "date": "2024-01-15",
            "baseline": "2024-01-14",
            "has_baseline": True,
            "new_events": [],
            "resolved_events": [],
            "score_changes": [],
            "new_trade_ideas": [
                {
                    "event_id": "evt-trade-001",
                    "ticker": "NVDA",
                    "direction": "long",
                    "entry_zone": "$500-510",
                    "target": "$550",
                }
            ],
            "closed_loops": [],
            "total_new_events": 0,
            "total_resolved": 0,
            "total_score_changes": 0,
            "total_new_trade_ideas": 1,
            "total_closed_loops": 0,
        }
        mock_brief_service.compare_briefs.return_value = mock_diff

        with patch("api.routers.reports.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/reports/diff?date=2024-01-15")

        assert response.status_code == 200
        data = response.json()
        assert data["total_new_trade_ideas"] == 1
        assert data["new_trade_ideas"][0]["ticker"] == "NVDA"
        assert data["new_trade_ideas"][0]["direction"] == "long"

    def test_diff_with_closed_loops(self, mock_brief_service):
        """Test diff includes closed loops."""
        mock_diff = {
            "date": "2024-01-15",
            "baseline": "2024-01-14",
            "has_baseline": True,
            "new_events": [],
            "resolved_events": [],
            "score_changes": [],
            "new_trade_ideas": [],
            "closed_loops": [
                {
                    "loop_id": "loop-001",
                    "question": "Will TSLA maintain production targets?",
                    "event_id": "evt-456",
                    "resolution": "closed",
                }
            ],
            "total_new_events": 0,
            "total_resolved": 0,
            "total_score_changes": 0,
            "total_new_trade_ideas": 0,
            "total_closed_loops": 1,
        }
        mock_brief_service.compare_briefs.return_value = mock_diff

        with patch("api.routers.reports.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/reports/diff?date=2024-01-15")

        assert response.status_code == 200
        data = response.json()
        assert data["total_closed_loops"] == 1
        assert data["closed_loops"][0]["loop_id"] == "loop-001"
        assert data["closed_loops"][0]["resolution"] == "closed"

    def test_diff_comprehensive_changes(self, mock_brief_service):
        """Test diff with all types of changes."""
        mock_diff = {
            "date": "2024-01-15",
            "baseline": "2024-01-14",
            "has_baseline": True,
            "new_events": [
                {
                    "event_id": "evt-new-001",
                    "title": "META Earnings Beat",
                    "ticker": "META",
                    "event_type": "catalyst_news",
                    "attention_score": 88.0,
                },
                {
                    "event_id": "evt-new-002",
                    "title": "AMZN Volume Spike",
                    "ticker": "AMZN",
                    "event_type": "market_anomaly",
                    "attention_score": 75.0,
                },
            ],
            "resolved_events": [
                {
                    "event_id": "evt-res-001",
                    "title": "AAPL Filing Complete",
                    "ticker": "AAPL",
                    "resolution_type": "resolved",
                    "final_score": 70.0,
                }
            ],
            "score_changes": [
                {
                    "event_id": "evt-chg-001",
                    "title": "MSFT Trend Shift",
                    "ticker": "MSFT",
                    "previous_score": 60.0,
                    "current_score": 80.0,
                    "delta": 20.0,
                    "direction": "up",
                },
                {
                    "event_id": "evt-chg-002",
                    "title": "TSLA Momentum Fading",
                    "ticker": "TSLA",
                    "previous_score": 75.0,
                    "current_score": 55.0,
                    "delta": -20.0,
                    "direction": "down",
                },
            ],
            "new_trade_ideas": [
                {
                    "event_id": "evt-new-001",
                    "ticker": "META",
                    "direction": "long",
                    "entry_zone": "$400-410",
                    "target": "$450",
                }
            ],
            "closed_loops": [
                {
                    "loop_id": "loop-001",
                    "question": "Will earnings beat expectations?",
                    "event_id": "evt-res-001",
                    "resolution": "resolved",
                }
            ],
            "total_new_events": 2,
            "total_resolved": 1,
            "total_score_changes": 2,
            "total_new_trade_ideas": 1,
            "total_closed_loops": 1,
        }
        mock_brief_service.compare_briefs.return_value = mock_diff

        with patch("api.routers.reports.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/reports/diff?date=2024-01-15&baseline=2024-01-14")

        assert response.status_code == 200
        data = response.json()

        # Verify counts
        assert data["total_new_events"] == 2
        assert data["total_resolved"] == 1
        assert data["total_score_changes"] == 2
        assert data["total_new_trade_ideas"] == 1
        assert data["total_closed_loops"] == 1

        # Verify new events
        assert len(data["new_events"]) == 2
        tickers = [e["ticker"] for e in data["new_events"]]
        assert "META" in tickers
        assert "AMZN" in tickers

        # Verify score changes include both directions
        directions = [c["direction"] for c in data["score_changes"]]
        assert "up" in directions
        assert "down" in directions

    def test_diff_service_error(self, mock_brief_service):
        """Test 500 error when service fails."""
        mock_brief_service.compare_briefs.side_effect = Exception("Database error")

        with patch("api.routers.reports.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/reports/diff?date=2024-01-15")

        assert response.status_code == 500
        assert "Failed to compare briefs" in response.json()["detail"]


class TestBriefServiceCompareBriefs:
    """Unit tests for BriefService.compare_briefs method."""

    @pytest.fixture
    def brief_service(self):
        """Create a BriefService with mocked database."""
        from api.services.brief_service import BriefService

        service = BriefService.__new__(BriefService)
        service.db = MagicMock()
        return service

    def test_compare_no_current_brief(self, brief_service):
        """Test compare when current brief doesn't exist."""
        with patch.object(brief_service, 'get_brief_by_date', return_value=None):
            result = brief_service.compare_briefs("2024-01-15", "2024-01-14")

        assert result["date"] == "2024-01-15"
        assert result["baseline"] == "2024-01-14"
        assert result["total_new_events"] == 0
        assert result["total_resolved"] == 0

    def test_compare_default_baseline(self, brief_service):
        """Test that baseline defaults to yesterday."""
        mock_current = {
            "top_events": [],
            "trade_ideas": [],
            "open_loops": [],
        }

        with patch.object(brief_service, 'get_brief_by_date', side_effect=[mock_current, None]):
            result = brief_service.compare_briefs("2024-01-15")

        assert result["date"] == "2024-01-15"
        assert result["baseline"] == "2024-01-14"  # Yesterday
        assert result["has_baseline"] is False

    def test_compare_finds_new_events(self, brief_service):
        """Test detection of new events."""
        mock_current = {
            "top_events": [
                {"event_id": "evt-001", "title": "Event A", "ticker": "AAPL", "event_type": "anomaly", "attention_score": 80},
                {"event_id": "evt-002", "title": "Event B", "ticker": "MSFT", "event_type": "news", "attention_score": 70},
            ],
            "trade_ideas": [],
            "open_loops": [],
        }
        mock_baseline = {
            "top_events": [
                {"event_id": "evt-001", "title": "Event A", "ticker": "AAPL", "event_type": "anomaly", "attention_score": 75},
            ],
            "trade_ideas": [],
            "open_loops": [],
        }

        with patch.object(brief_service, 'get_brief_by_date', side_effect=[mock_current, mock_baseline]):
            result = brief_service.compare_briefs("2024-01-15", "2024-01-14")

        assert result["total_new_events"] == 1
        assert len(result["new_events"]) == 1
        assert result["new_events"][0]["event_id"] == "evt-002"
        assert result["new_events"][0]["ticker"] == "MSFT"

    def test_compare_finds_resolved_events(self, brief_service):
        """Test detection of resolved events."""
        mock_current = {
            "top_events": [
                {"event_id": "evt-002", "title": "Event B", "ticker": "MSFT", "event_type": "news", "attention_score": 70},
            ],
            "trade_ideas": [],
            "open_loops": [],
        }
        mock_baseline = {
            "top_events": [
                {"event_id": "evt-001", "title": "Event A", "ticker": "AAPL", "event_type": "anomaly", "attention_score": 80},
                {"event_id": "evt-002", "title": "Event B", "ticker": "MSFT", "event_type": "news", "attention_score": 65},
            ],
            "trade_ideas": [],
            "open_loops": [],
        }

        with patch.object(brief_service, 'get_brief_by_date', side_effect=[mock_current, mock_baseline]):
            result = brief_service.compare_briefs("2024-01-15", "2024-01-14")

        assert result["total_resolved"] == 1
        assert len(result["resolved_events"]) == 1
        assert result["resolved_events"][0]["event_id"] == "evt-001"
        assert result["resolved_events"][0]["ticker"] == "AAPL"

    def test_compare_finds_score_changes(self, brief_service):
        """Test detection of score changes exceeding threshold."""
        mock_current = {
            "top_events": [
                {"event_id": "evt-001", "title": "Event A", "ticker": "AAPL", "event_type": "anomaly", "attention_score": 90},
                {"event_id": "evt-002", "title": "Event B", "ticker": "MSFT", "event_type": "news", "attention_score": 72},
            ],
            "trade_ideas": [],
            "open_loops": [],
        }
        mock_baseline = {
            "top_events": [
                {"event_id": "evt-001", "title": "Event A", "ticker": "AAPL", "event_type": "anomaly", "attention_score": 75},
                {"event_id": "evt-002", "title": "Event B", "ticker": "MSFT", "event_type": "news", "attention_score": 70},
            ],
            "trade_ideas": [],
            "open_loops": [],
        }

        with patch.object(brief_service, 'get_brief_by_date', side_effect=[mock_current, mock_baseline]):
            result = brief_service.compare_briefs("2024-01-15", "2024-01-14", score_change_threshold=5.0)

        # Only evt-001 should appear (delta=15), evt-002 delta=2 < threshold
        assert result["total_score_changes"] == 1
        assert len(result["score_changes"]) == 1
        assert result["score_changes"][0]["event_id"] == "evt-001"
        assert result["score_changes"][0]["delta"] == 15.0
        assert result["score_changes"][0]["direction"] == "up"

    def test_compare_finds_new_trade_ideas(self, brief_service):
        """Test detection of new trade ideas."""
        mock_current = {
            "top_events": [],
            "trade_ideas": [
                {"event_id": "evt-001", "ticker": "AAPL", "direction": "long", "entry_zone": "$180", "target": "$200"},
                {"event_id": "evt-002", "ticker": "MSFT", "direction": "short", "entry_zone": "$350", "target": "$320"},
            ],
            "open_loops": [],
        }
        mock_baseline = {
            "top_events": [],
            "trade_ideas": [
                {"event_id": "evt-001", "ticker": "AAPL", "direction": "long", "entry_zone": "$175", "target": "$195"},
            ],
            "open_loops": [],
        }

        with patch.object(brief_service, 'get_brief_by_date', side_effect=[mock_current, mock_baseline]):
            result = brief_service.compare_briefs("2024-01-15", "2024-01-14")

        assert result["total_new_trade_ideas"] == 1
        assert len(result["new_trade_ideas"]) == 1
        assert result["new_trade_ideas"][0]["event_id"] == "evt-002"
        assert result["new_trade_ideas"][0]["ticker"] == "MSFT"

    def test_compare_finds_closed_loops(self, brief_service):
        """Test detection of closed loops."""
        mock_current = {
            "top_events": [],
            "trade_ideas": [],
            "open_loops": [
                {"loop_id": "loop-002", "question": "Q2?", "status": "open"},
            ],
        }
        mock_baseline = {
            "top_events": [],
            "trade_ideas": [],
            "open_loops": [
                {"loop_id": "loop-001", "question": "Q1?", "event_id": "evt-001", "status": "open"},
                {"loop_id": "loop-002", "question": "Q2?", "status": "open"},
            ],
        }

        with patch.object(brief_service, 'get_brief_by_date', side_effect=[mock_current, mock_baseline]):
            result = brief_service.compare_briefs("2024-01-15", "2024-01-14")

        assert result["total_closed_loops"] == 1
        assert len(result["closed_loops"]) == 1
        assert result["closed_loops"][0]["loop_id"] == "loop-001"
        assert result["closed_loops"][0]["question"] == "Q1?"

    def test_compare_invalid_date_format(self, brief_service):
        """Test ValueError for invalid date format."""
        with pytest.raises(ValueError) as exc_info:
            brief_service.compare_briefs("01-15-2024")

        assert "YYYY-MM-DD" in str(exc_info.value)

    def test_compare_invalid_baseline_format(self, brief_service):
        """Test ValueError for invalid baseline format."""
        with pytest.raises(ValueError) as exc_info:
            brief_service.compare_briefs("2024-01-15", "invalid")

        assert "YYYY-MM-DD" in str(exc_info.value)

    def test_compare_score_change_directions(self, brief_service):
        """Test correct direction assignment for score changes."""
        mock_current = {
            "top_events": [
                {"event_id": "evt-up", "title": "Up", "ticker": "UP", "event_type": "a", "attention_score": 80},
                {"event_id": "evt-down", "title": "Down", "ticker": "DN", "event_type": "a", "attention_score": 40},
                {"event_id": "evt-same", "title": "Same", "ticker": "SM", "event_type": "a", "attention_score": 50},
            ],
            "trade_ideas": [],
            "open_loops": [],
        }
        mock_baseline = {
            "top_events": [
                {"event_id": "evt-up", "title": "Up", "ticker": "UP", "event_type": "a", "attention_score": 60},
                {"event_id": "evt-down", "title": "Down", "ticker": "DN", "event_type": "a", "attention_score": 60},
                {"event_id": "evt-same", "title": "Same", "ticker": "SM", "event_type": "a", "attention_score": 50},
            ],
            "trade_ideas": [],
            "open_loops": [],
        }

        with patch.object(brief_service, 'get_brief_by_date', side_effect=[mock_current, mock_baseline]):
            result = brief_service.compare_briefs("2024-01-15", "2024-01-14", score_change_threshold=5.0)

        # evt-same should not appear (delta=0)
        # evt-up and evt-down should appear
        assert result["total_score_changes"] == 2

        changes_by_id = {c["event_id"]: c for c in result["score_changes"]}
        assert changes_by_id["evt-up"]["direction"] == "up"
        assert changes_by_id["evt-up"]["delta"] == 20.0
        assert changes_by_id["evt-down"]["direction"] == "down"
        assert changes_by_id["evt-down"]["delta"] == -20.0
