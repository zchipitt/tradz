"""
Tests for Daily Brief API endpoints.

Covers:
- GET /api/briefs/{date} - Get brief by date
- GET /api/briefs/latest - Get most recent brief
- GET /api/briefs - List available briefs
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


class TestGetBriefByDate:
    """Tests for GET /api/briefs/{date}"""

    @pytest.fixture
    def mock_brief_service(self):
        """Mock BriefService instance."""
        service = MagicMock()
        service.get_brief_by_date = MagicMock()
        return service

    def test_get_brief_by_date_success(self, mock_brief_service):
        """Test getting existing brief by date."""
        # Mock brief data
        brief_date = "2024-01-15"
        mock_brief = {
            "id": str(uuid.uuid4()),
            "date": datetime(2024, 1, 15, tzinfo=timezone.utc),
            "executive_summary": "Today's top signal is AAPL...",
            "top_events": [
                {
                    "event_id": "evt-123",
                    "title": "AAPL Earnings Beat",
                    "ticker": "AAPL",
                    "event_type": "market_anomaly",
                    "attention_score": 85.5,
                    "anomaly_score": 80.0,
                    "catalyst_score": 90.0,
                    "flow_score": 70.0,
                    "confidence_score": 85.0,
                    "observation_count": 5,
                    "last_update_at": datetime.now(timezone.utc),
                }
            ],
            "trade_ideas": [],
            "research_ideas": [],
            "open_loops": [],
            "data_quality": None,
            "generation_method": "template",
            "created_at": datetime.now(timezone.utc),
            "run_id": None,
        }
        mock_brief_service.get_brief_by_date.return_value = mock_brief

        # Test endpoint
        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get(f"/api/briefs/{brief_date}")

        assert response.status_code == 200
        data = response.json()
        assert data["brief"]["id"] == mock_brief["id"]
        assert data["brief"]["date"] == "2024-01-15T00:00:00+00:00"
        assert data["brief"]["executive_summary"] == mock_brief["executive_summary"]
        assert len(data["brief"]["top_events"]) == 1
        assert data["brief"]["top_events"][0]["ticker"] == "AAPL"

    def test_get_brief_not_found(self, mock_brief_service):
        """Test 404 when brief not found."""
        mock_brief_service.get_brief_by_date.return_value = None

        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/briefs/2024-01-15")

        assert response.status_code == 404
        assert response.json()["error"] == "Brief not found for date"
        assert response.json()["date"] == "2024-01-15"

    def test_get_brief_invalid_date_format(self, mock_brief_service):
        """Test 400 for invalid date format."""
        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/invalid-date")

        assert response.status_code == 400
        assert response.json()["error"] == "Invalid date format"
        assert "YYYY-MM-DD" in response.json()["message"]

    def test_get_brief_date_wrong_format(self, mock_brief_service):
        """Test 400 for various wrong date formats."""
        invalid_dates = [
            "01-15-2024",  # MM-DD-YYYY
            "15-01-2024",  # DD-MM-YYYY
            "2024/01/15",  # Wrong separator
            "2024-1-15",   # Single digit month
            "2024-01-5",   # Single digit day
        ]

        for date in invalid_dates:
            with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
                with TestClient(app) as client:
                    response = client.get(f"/api/briefs/{date}")

            assert response.status_code == 400, f"Expected 400 for date {date}"


class TestGetLatestBrief:
    """Tests for GET /api/briefs/latest"""

    @pytest.fixture
    def mock_brief_service(self):
        """Mock BriefService instance."""
        service = MagicMock()
        service.get_latest_brief = MagicMock()
        return service

    def test_get_latest_brief_success(self, mock_brief_service):
        """Test getting the most recent brief."""
        mock_brief = {
            "id": str(uuid.uuid4()),
            "date": datetime(2024, 1, 20, tzinfo=timezone.utc),
            "executive_summary": "Latest brief summary...",
            "top_events": [],
            "trade_ideas": [],
            "research_ideas": [],
            "open_loops": [],
            "data_quality": None,
            "generation_method": "claude",
            "created_at": datetime.now(timezone.utc),
            "run_id": str(uuid.uuid4()),
        }
        mock_brief_service.get_latest_brief.return_value = mock_brief

        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/briefs/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["brief"]["id"] == mock_brief["id"]
        assert data["brief"]["generation_method"] == "claude"
        assert data["brief"]["date"] == "2024-01-20T00:00:00+00:00"

    def test_get_latest_brief_not_found(self, mock_brief_service):
        """Test 404 when no briefs exist."""
        mock_brief_service.get_latest_brief.return_value = None

        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/briefs/latest")

        assert response.status_code == 404
        assert "No briefs found" in response.json()["detail"]


class TestListBriefs:
    """Tests for GET /api/briefs """

    @pytest.fixture
    def mock_brief_service(self):
        """Mock BriefService instance."""
        service = MagicMock()
        service.list_briefs = MagicMock()
        return service

    def test_list_briefs_default_params(self, mock_brief_service):
        """Test listing briefs with default pagination."""
        mock_briefs = [
            {
                "id": str(uuid.uuid4()),
                "date": datetime(2024, 1, 20, tzinfo=timezone.utc),
                "generation_method": "claude",
                "created_at": datetime.now(timezone.utc),
                "event_count": 5,
                "trade_idea_count": 2,
                "top_entity": "AAPL",
                "report_path_md": "reports/2024-01-20.md",
                "report_path_json": "reports/2024-01-20.json",
                "run_id": str(uuid.uuid4()),
            },
            {
                "id": str(uuid.uuid4()),
                "date": datetime(2024, 1, 19, tzinfo=timezone.utc),
                "generation_method": "template",
                "created_at": datetime.now(timezone.utc),
                "event_count": 3,
                "trade_idea_count": 1,
                "top_entity": "TSLA",
                "report_path_md": "reports/2024-01-19.md",
                "report_path_json": "reports/2024-01-19.json",
                "run_id": None,
            },
        ]
        mock_brief_service.list_briefs.return_value = (mock_briefs, 25)

        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/briefs/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 25
        assert len(data["briefs"]) == 2
        assert data["briefs"][0]["date"] == "2024-01-20T00:00:00+00:00"
        assert data["briefs"][0]["event_count"] == 5
        assert data["briefs"][0]["top_entity"] == "AAPL"

    def test_list_briefs_with_pagination(self, mock_brief_service):
        """Test listing briefs with custom limit and offset."""
        mock_briefs = [
            {
                "id": str(uuid.uuid4()),
                "date": datetime(2024, 1, 15, tzinfo=timezone.utc),
                "generation_method": "template",
                "created_at": datetime.now(timezone.utc),
                "event_count": 4,
                "trade_idea_count": 2,
                "top_entity": "GOOGL",
                "report_path_md": None,
                "report_path_json": None,
                "run_id": None,
            }
        ]
        mock_brief_service.list_briefs.return_value = (mock_briefs, 100)

        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/briefs/?limit=1&offset=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["briefs"]) == 1
        # Verify pagination params were passed correctly
        mock_brief_service.list_briefs.assert_called_with(limit=1, offset=10)

    def test_list_briefs_limit_validation(self, mock_brief_service):
        """Test limit parameter validation."""
        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                # Test limit too small
                response = client.get("/api/briefs/?limit=0")
                assert response.status_code == 422  # FastAPI validation error

                # Test limit too large
                response = client.get("/api/briefs/?limit=101")
                assert response.status_code == 422

                # Test negative offset
                response = client.get("/api/briefs/?offset=-1")
                assert response.status_code == 422

    def test_list_briefs_empty_database(self, mock_brief_service):
        """Test listing briefs when database is empty."""
        mock_brief_service.list_briefs.return_value = ([], 0)

        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/briefs/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["briefs"] == []

    def test_list_briefs_limit_bounds(self, mock_brief_service):
        """Test that limits are clamped to valid range."""
        mock_briefs = []
        for i in range(10):
            mock_briefs.append({
                "id": str(uuid.uuid4()),
                "date": datetime(2024, 1, i + 1, tzinfo=timezone.utc),
                "generation_method": "template",
                "created_at": datetime.now(timezone.utc),
                "event_count": 3,
                "trade_idea_count": 1,
                "top_entity": "AAPL",
                "report_path_md": None,
                "report_path_json": None,
                "run_id": None,
            })

        mock_brief_service.list_briefs.return_value = (mock_briefs[:5], 10)

        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                # Default should return 50, but we only have 10
                response = client.get("/api/briefs/")

        assert response.status_code == 200
        # The service clamps the limit internally, so we should get our mocked result
        mock_brief_service.list_briefs.assert_called_with(limit=50, offset=0)


class TestBriefServiceErrorHandling:
    """Test error handling in brief service operations."""

    @pytest.fixture
    def mock_brief_service(self):
        """Mock BriefService that raises exceptions."""
        service = MagicMock()
        service.list_briefs = MagicMock(side_effect=Exception("Database connection failed"))
        return service

    def test_list_briefs_database_error(self, mock_brief_service):
        """Test 500 error when database fails."""
        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/briefs/")

        assert response.status_code == 500
        assert "Failed to list briefs" in response.json()["detail"]

    def test_get_brief_by_date_database_error(self, mock_brief_service):
        """Test error handling for get_by_date database failure."""
        mock_brief_service.get_brief_by_date = MagicMock(side_effect=Exception("Query failed"))

        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/briefs/2024-01-15")

        # Should return 500 for database errors (after validation passes)
        assert response.status_code == 500


class TestBriefDataStructure:
    """Test that brief data structure is properly formatted."""

    @pytest.fixture
    def mock_brief_service(self):
        """Mock BriefService with realistic data."""
        service = MagicMock()

        # Mock a complete brief with all sections
        mock_brief = {
            "id": str(uuid.uuid4()),
            "date": datetime(2024, 1, 15, tzinfo=timezone.utc),
            "executive_summary": "Today's top signal is AAPL with an attention score of 85...",
            "top_events": [
                {
                    "event_id": "evt-123",
                    "title": "AAPL Surges 8% on Strong Earnings",
                    "ticker": "AAPL",
                    "event_type": "catalyst_news",
                    "attention_score": 85.5,
                    "anomaly_score": 80.0,
                    "catalyst_score": 90.0,
                    "flow_score": 70.0,
                    "confidence_score": 85.0,
                    "observation_count": 5,
                    "last_update_at": datetime.now(timezone.utc),
                }
            ],
            "trade_ideas": [
                {
                    "event_id": "evt-123",
                    "ticker": "AAPL",
                    "direction": "long",
                    "entry_zone": "$180-185",
                    "target": "$200",
                    "stop_loss": "$175",
                    "confidence_level": 85.0,
                    "rationale": "Strong earnings momentum with positive flow signals",
                }
            ],
            "research_ideas": [
                {
                    "event_id": "evt-456",
                    "ticker": "TSLA",
                    "questions": ["Is the battery tech improvement sustainable?"],
                    "evidence_to_watch": ["Q4 delivery numbers", "Competitor responses"],
                    "current_score": 45.0,
                    "potential_score": 75.0,
                }
            ],
            "open_loops": [
                {
                    "loop_id": "loop-001",
                    "event_id": "evt-456",
                    "question": "Will TSLA maintain production targets?",
                    "created_at": datetime.now(timezone.utc),
                    "status": "open",
                }
            ],
            "data_quality": {
                "total_sources": 7,
                "healthy_count": 6,
                "degraded_count": 1,
                "error_count": 0,
                "sources": [
                    {
                        "name": "equities",
                        "display_name": "Equities",
                        "status": "ok",
                        "record_count_24h": 1500,
                        "freshness_indicator": "fresh",
                    }
                ],
                "overall_status": "ok",
                "quality_message": "All sources healthy",
            },
            "generation_method": "claude",
            "created_at": datetime.now(timezone.utc),
            "run_id": str(uuid.uuid4()),
        }

        service.get_brief_by_date.return_value = mock_brief
        service.get_latest_brief.return_value = mock_brief
        service.list_briefs.return_value = ([mock_brief], 1)

        return service

    def test_brief_response_structure(self, mock_brief_service):
        """Test that brief response has correct structure."""
        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/briefs/2024-01-15")

        assert response.status_code == 200
        data = response.json()["brief"]

        # Verify all expected fields are present
        assert "id" in data
        assert "date" in data
        assert "executive_summary" in data
        assert "top_events" in data
        assert "trade_ideas" in data
        assert "research_ideas" in data
        assert "open_loops" in data
        assert "data_quality" in data
        assert "generation_method" in data
        assert "created_at" in data
        assert "run_id" in data

        # Verify nested structures
        assert isinstance(data["top_events"], list)
        assert isinstance(data["trade_ideas"], list)
        assert isinstance(data["open_loops"], list)
        assert data["data_quality"]["total_sources"] == 7
        assert len(data["data_quality"]["sources"]) == 1

        # Verify generation method validation (should be claude or template)
        assert data["generation_method"] in ["claude", "template"]

    def test_brief_summary_structure(self, mock_brief_service):
        """Test that brief summary has correct structure."""
        with patch("api.routers.briefs.get_brief_service", return_value=mock_brief_service):
            with TestClient(app) as client:
                response = client.get("/api/briefs/")

        assert response.status_code == 200
        data = response.json()

        assert "briefs" in data
        assert "total_count" in data
        assert isinstance(data["briefs"], list)

        summary = data["briefs"][0]
        assert "id" in summary
        assert "date" in summary
        assert "generation_method" in summary
        assert "created_at" in summary
        assert "event_count" in summary
        assert "trade_idea_count" in summary
        assert "top_entity" in summary

        # Verify counts are correct
        assert summary["event_count"] == 1
        assert summary["trade_idea_count"] == 1
        assert summary["top_entity"] == "AAPL"
