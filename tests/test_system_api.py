"""
Unit tests for System Status API endpoint.

Tests cover:
- GET /api/system/status returns health status for all data sources
- Status determination logic (ok/degraded/error)
- Source-specific health information
- Overall health summary
- Data freshness indicators
"""
import sys
from pathlib import Path

# Add src to path for tradz imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

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
def mock_system_service():
    """Create mock system service."""
    with patch("api.routers.system.system_service") as mock:
        yield mock


def create_mock_status_response(
    equities_status: str = "ok",
    crypto_status: str = "ok",
    congress_status: str = "ok",
    hedgefund_status: str = "degraded",
    polymarket_status: str = "ok",
    news_status: str = "ok",
    sec_status: str = "error",
):
    """Helper to create mock system status response."""
    now = datetime.now(timezone.utc)
    twelve_hours_ago = now - timedelta(hours=12)
    two_days_ago = now - timedelta(days=2)

    def get_timestamp(status):
        if status == "ok":
            return now - timedelta(minutes=30)
        elif status == "degraded":
            return twelve_hours_ago
        else:
            return two_days_ago

    def get_freshness(status):
        if status == "ok":
            return "fresh"
        elif status == "degraded":
            return "stale"
        else:
            return "stale"

    sources = [
        {
            "name": "equities",
            "display_name": "Market Data (Equities)",
            "status": equities_status,
            "last_success_at": get_timestamp(equities_status),
            "last_error": None if equities_status == "ok" else "Timeout error",
            "record_count_24h": 100 if equities_status != "error" else 0,
            "freshness_indicator": get_freshness(equities_status),
        },
        {
            "name": "crypto",
            "display_name": "Market Data (Crypto)",
            "status": crypto_status,
            "last_success_at": get_timestamp(crypto_status),
            "last_error": None if crypto_status == "ok" else "API error",
            "record_count_24h": 80 if crypto_status != "error" else 0,
            "freshness_indicator": get_freshness(crypto_status),
        },
        {
            "name": "congress",
            "display_name": "Congress Trades",
            "status": congress_status,
            "last_success_at": get_timestamp(congress_status),
            "last_error": None,
            "record_count_24h": 15,
            "freshness_indicator": get_freshness(congress_status),
        },
        {
            "name": "hedgefund",
            "display_name": "Hedge Fund (13F)",
            "status": hedgefund_status,
            "last_success_at": get_timestamp(hedgefund_status),
            "last_error": "Rate limit exceeded" if hedgefund_status != "ok" else None,
            "record_count_24h": 5 if hedgefund_status != "error" else 0,
            "freshness_indicator": get_freshness(hedgefund_status),
        },
        {
            "name": "polymarket",
            "display_name": "Polymarket",
            "status": polymarket_status,
            "last_success_at": get_timestamp(polymarket_status),
            "last_error": None,
            "record_count_24h": 25,
            "freshness_indicator": get_freshness(polymarket_status),
        },
        {
            "name": "news",
            "display_name": "News",
            "status": news_status,
            "last_success_at": get_timestamp(news_status),
            "last_error": None if news_status == "ok" else "Connection refused",
            "record_count_24h": 50 if news_status != "error" else 0,
            "freshness_indicator": get_freshness(news_status),
        },
        {
            "name": "sec",
            "display_name": "SEC Filings",
            "status": sec_status,
            "last_success_at": get_timestamp(sec_status) if sec_status != "error" else None,
            "last_error": "SEC API unavailable" if sec_status == "error" else None,
            "record_count_24h": 10 if sec_status != "error" else 0,
            "freshness_indicator": get_freshness(sec_status) if sec_status != "error" else "unknown",
        },
    ]

    # Count statuses
    healthy_count = sum(1 for s in sources if s["status"] == "ok")
    degraded_count = sum(1 for s in sources if s["status"] == "degraded")
    error_count = sum(1 for s in sources if s["status"] == "error")

    return {
        "overall": {
            "total_sources": len(sources),
            "healthy_count": healthy_count,
            "degraded_count": degraded_count,
            "error_count": error_count,
        },
        "sources": sources,
        "last_check_at": now,
    }


class TestGetSystemStatus:
    """Tests for GET /api/system/status endpoint."""

    def test_get_status_success(self, client, mock_system_service):
        """Test getting system status successfully."""
        mock_status = create_mock_status_response()
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "overall" in data
        assert "sources" in data
        assert "last_check_at" in data

    def test_get_status_overall_summary(self, client, mock_system_service):
        """Test overall health summary in response."""
        mock_status = create_mock_status_response(
            equities_status="ok",
            crypto_status="ok",
            congress_status="ok",
            hedgefund_status="degraded",
            polymarket_status="ok",
            news_status="ok",
            sec_status="error",
        )
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()
        overall = data["overall"]

        assert overall["total_sources"] == 7
        assert overall["healthy_count"] == 5
        assert overall["degraded_count"] == 1
        assert overall["error_count"] == 1

    def test_get_status_source_details(self, client, mock_system_service):
        """Test per-source health details in response."""
        mock_status = create_mock_status_response()
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()
        sources = data["sources"]

        # Verify all expected sources are present
        source_names = {s["name"] for s in sources}
        expected_sources = {"equities", "crypto", "congress", "hedgefund", "polymarket", "news", "sec"}
        assert source_names == expected_sources

        # Verify source structure
        for source in sources:
            assert "name" in source
            assert "display_name" in source
            assert "status" in source
            assert source["status"] in ["ok", "degraded", "error"]
            assert "last_success_at" in source
            assert "last_error" in source
            assert "record_count_24h" in source
            assert "freshness_indicator" in source

    def test_get_status_all_healthy(self, client, mock_system_service):
        """Test response when all sources are healthy."""
        mock_status = create_mock_status_response(
            equities_status="ok",
            crypto_status="ok",
            congress_status="ok",
            hedgefund_status="ok",
            polymarket_status="ok",
            news_status="ok",
            sec_status="ok",
        )
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()
        overall = data["overall"]

        assert overall["healthy_count"] == 7
        assert overall["degraded_count"] == 0
        assert overall["error_count"] == 0

    def test_get_status_all_degraded(self, client, mock_system_service):
        """Test response when all sources are degraded."""
        mock_status = create_mock_status_response(
            equities_status="degraded",
            crypto_status="degraded",
            congress_status="degraded",
            hedgefund_status="degraded",
            polymarket_status="degraded",
            news_status="degraded",
            sec_status="degraded",
        )
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()
        overall = data["overall"]

        assert overall["healthy_count"] == 0
        assert overall["degraded_count"] == 7
        assert overall["error_count"] == 0

    def test_get_status_all_error(self, client, mock_system_service):
        """Test response when all sources are in error state."""
        mock_status = create_mock_status_response(
            equities_status="error",
            crypto_status="error",
            congress_status="error",
            hedgefund_status="error",
            polymarket_status="error",
            news_status="error",
            sec_status="error",
        )
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()
        overall = data["overall"]

        assert overall["healthy_count"] == 0
        assert overall["degraded_count"] == 0
        assert overall["error_count"] == 7

    def test_get_status_service_error(self, client, mock_system_service):
        """Test error handling when service fails."""
        mock_system_service.get_system_status.side_effect = Exception("Database error")

        response = client.get("/api/system/status")

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


class TestStatusDetermination:
    """Tests for status determination logic."""

    def test_status_ok_recent_success(self, client, mock_system_service):
        """Test that recent success (< 1h) results in 'ok' status."""
        mock_status = create_mock_status_response(equities_status="ok")
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()
        equities = next(s for s in data["sources"] if s["name"] == "equities")

        assert equities["status"] == "ok"
        assert equities["freshness_indicator"] == "fresh"

    def test_status_degraded_stale_success(self, client, mock_system_service):
        """Test that stale success (1-24h) results in 'degraded' status."""
        mock_status = create_mock_status_response(hedgefund_status="degraded")
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()
        hedgefund = next(s for s in data["sources"] if s["name"] == "hedgefund")

        assert hedgefund["status"] == "degraded"
        assert hedgefund["freshness_indicator"] == "stale"

    def test_status_error_no_recent_success(self, client, mock_system_service):
        """Test that no recent success (> 24h) results in 'error' status."""
        mock_status = create_mock_status_response(sec_status="error")
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()
        sec = next(s for s in data["sources"] if s["name"] == "sec")

        assert sec["status"] == "error"


class TestSourceHealthDetails:
    """Tests for source-specific health details."""

    def test_source_includes_last_error(self, client, mock_system_service):
        """Test that sources include last error message."""
        mock_status = create_mock_status_response(sec_status="error")
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()
        sec = next(s for s in data["sources"] if s["name"] == "sec")

        assert sec["last_error"] is not None
        assert "SEC API unavailable" in sec["last_error"]

    def test_source_includes_record_count(self, client, mock_system_service):
        """Test that sources include record count for last 24h."""
        mock_status = create_mock_status_response()
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()

        for source in data["sources"]:
            assert "record_count_24h" in source
            assert isinstance(source["record_count_24h"], int)
            assert source["record_count_24h"] >= 0

    def test_source_includes_display_name(self, client, mock_system_service):
        """Test that sources include human-readable display names."""
        mock_status = create_mock_status_response()
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()

        # Check specific display names
        equities = next(s for s in data["sources"] if s["name"] == "equities")
        assert equities["display_name"] == "Market Data (Equities)"

        crypto = next(s for s in data["sources"] if s["name"] == "crypto")
        assert crypto["display_name"] == "Market Data (Crypto)"

        congress = next(s for s in data["sources"] if s["name"] == "congress")
        assert congress["display_name"] == "Congress Trades"

    def test_source_includes_freshness_indicator(self, client, mock_system_service):
        """Test that sources include freshness indicator."""
        mock_status = create_mock_status_response()
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()

        for source in data["sources"]:
            assert "freshness_indicator" in source
            assert source["freshness_indicator"] in ["fresh", "stale", "unknown"]


class TestLastCheckTimestamp:
    """Tests for last_check_at timestamp."""

    def test_last_check_at_is_present(self, client, mock_system_service):
        """Test that last_check_at timestamp is included."""
        mock_status = create_mock_status_response()
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()

        assert "last_check_at" in data
        assert data["last_check_at"] is not None

    def test_last_check_at_is_recent(self, client, mock_system_service):
        """Test that last_check_at is a recent timestamp."""
        now = datetime.now(timezone.utc)
        mock_status = create_mock_status_response()
        mock_status["last_check_at"] = now
        mock_system_service.get_system_status.return_value = mock_status

        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()

        # Parse the timestamp and verify it's recent (within last minute)
        last_check = datetime.fromisoformat(data["last_check_at"].replace("Z", "+00:00"))
        time_diff = (now - last_check).total_seconds()
        assert abs(time_diff) < 60  # Within last minute
