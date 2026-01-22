"""
Tests for reports HTML endpoint.
"""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from api.main import app

client = TestClient(app)


def test_get_report_html_not_found():
    """Test HTML endpoint returns 404 for non-existent report."""
    with patch('api.services.aggregator_service.aggregator_service.load_historical_data', return_value=None):
        response = client.get("/api/reports/2023-01-01/html")
        assert response.status_code == 404
        assert "not found" in response.text.lower()


def test_get_report_html_invalid_date():
    """Test HTML endpoint returns 400 for invalid date format."""
    response = client.get("/api/reports/invalid-date/html")
    assert response.status_code == 400
    assert "invalid date format" in response.text.lower()


def test_get_report_html_success():
    """Test HTML endpoint returns HTML content for existing report."""
    # Mock the report data
    mock_data = {
        "executive_summary": "Test summary",
        "top_events": [
            {
                "title": "Test Event",
                "entity_id": "AAPL",
                "attention_score": 75.5,
                "scores": {
                    "anomaly_score": 80,
                    "catalyst_score": 70,
                    "flow_score": 60,
                    "confidence_score": 85
                },
                "observation_count": 5
            }
        ],
        "trade_ideas": [
            {
                "symbol": "AAPL",
                "direction": "long",
                "event_title": "AAPL Opportunity",
                "entry_zone": "150.00",
                "target": "160.00",
                "stop_loss": "145.00",
                "time_horizon": "1-3 days",
                "invalidation": "Break below 142"
            }
        ],
        "data_quality": [
            {
                "name": "Equities",
                "status": "ok",
                "record_count_24h": 150,
                "last_success_at": "2023-01-01T12:00:00+00:00"
            }
        ],
        "generation_method": "claude"
    }

    with patch('api.services.aggregator_service.aggregator_service.load_historical_data', return_value=mock_data):
        with patch('api.routers.reports.brief_service', None):  # Skip brief service
            response = client.get("/api/reports/2023-01-01/html")

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/html; charset=utf-8"
            assert "<!DOCTYPE html>" in response.text
            assert "Tradz Daily Brief" in response.text
            assert "2023-01-01" in response.text
            assert "Test Event" in response.text
            assert "AAPL Opportunity" in response.text


def test_get_latest_report_html():
    """Test latest HTML endpoint returns HTML content."""
    mock_report = {
        "date": "2023-01-01",
        "directory": "reports"
    }

    mock_data = {
        "executive_summary": "Latest report summary",
        "top_events": [],
        "generation_method": "template"
    }

    with patch('api.routers.reports.list_reports', return_value=[mock_report]):
        with patch('api.services.aggregator_service.aggregator_service.load_historical_data', return_value=mock_data):
            with patch('api.routers.reports.brief_service', None):
                response = client.get("/api/reports/latest/html")

                assert response.status_code == 200
                assert response.headers["content-type"] == "text/html; charset=utf-8"
                assert "<!DOCTYPE html>" in response.text
                assert "Latest report summary" in response.text


def test_get_report_with_brief_service():
    """Test HTML endpoint uses brief service when available."""
    mock_brief_response = MagicMock()
    mock_brief_response.brief = {
        "executive_summary": "Brief service summary",
        "top_events": [],
        "trade_ideas": [],
        "generation_method": "claude",
        "data_quality": []
    }

    mock_brief_service = MagicMock()
    mock_brief_service.get_brief_by_date = MagicMock(return_value=mock_brief_response)

    with patch('api.routers.reports.brief_service', mock_brief_service):
        with patch('api.services.aggregator_service.aggregator_service.load_historical_data', side_effect=Exception("Should not be called")):
            response = client.get("/api/reports/2023-01-01/html")

            assert response.status_code == 200
            assert "Brief service summary" in response.text
