"""
Tests for Settings API endpoints (US-025).

Tests cover:
- GET /api/settings/gates: Get current quality gate thresholds
- PUT /api/settings/gates: Update quality gate thresholds
- DELETE /api/settings/gates: Reset to defaults
- Validation of threshold ranges (0-100 for scores, 1-10 for sources)
- Persistence to config.yaml
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
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
def mock_settings_service():
    """Create mock settings service."""
    with patch("api.routers.settings.settings_service") as mock:
        yield mock


@pytest.fixture
def _mock_settings_service():
    """Create mock settings service (unused fixture for validation tests)."""
    with patch("api.routers.settings.settings_service") as mock:
        yield mock


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        config = {
            "timezone": "America/New_York",
            "equities": {"tickers": ["AAPL", "MSFT"]},
        }
        yaml.dump(config, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


# ==================================================
# Test GET /api/settings/gates
# ==================================================


class TestGetQualityGateSettings:
    """Tests for GET /api/settings/gates endpoint."""

    def test_get_settings_returns_defaults_when_not_configured(
        self, client, mock_settings_service
    ):
        """Test getting settings when no custom config exists."""
        # Return defaults
        mock_settings_service.get_quality_gate_settings.return_value = {
            "min_confidence": 70.0,
            "min_sources": 2,
            "min_anomaly": 50.0,
            "min_catalyst": 40.0,
            "require_invalidation": True,
        }
        mock_settings_service.get_quality_gate_defaults.return_value = {
            "min_confidence": 70.0,
            "min_sources": 2,
            "min_anomaly": 50.0,
            "min_catalyst": 40.0,
            "require_invalidation": True,
        }

        response = client.get("/api/settings/gates")
        assert response.status_code == 200

        data = response.json()
        assert "settings" in data
        assert "defaults" in data

        settings = data["settings"]
        assert settings["min_confidence"] == 70.0
        assert settings["min_sources"] == 2
        assert settings["min_anomaly"] == 50.0
        assert settings["min_catalyst"] == 40.0
        assert settings["require_invalidation"] is True

    def test_get_settings_returns_custom_values(
        self, client, mock_settings_service
    ):
        """Test getting settings when custom config exists."""
        mock_settings_service.get_quality_gate_settings.return_value = {
            "min_confidence": 80.0,
            "min_sources": 3,
            "min_anomaly": 60.0,
            "min_catalyst": 50.0,
            "require_invalidation": False,
        }
        mock_settings_service.get_quality_gate_defaults.return_value = {
            "min_confidence": 70.0,
            "min_sources": 2,
            "min_anomaly": 50.0,
            "min_catalyst": 40.0,
            "require_invalidation": True,
        }

        response = client.get("/api/settings/gates")
        assert response.status_code == 200

        data = response.json()
        settings = data["settings"]
        defaults = data["defaults"]

        # Custom values
        assert settings["min_confidence"] == 80.0
        assert settings["min_sources"] == 3
        assert settings["min_anomaly"] == 60.0
        assert settings["min_catalyst"] == 50.0
        assert settings["require_invalidation"] is False

        # Defaults for reference
        assert defaults["min_confidence"] == 70.0
        assert defaults["min_sources"] == 2

    def test_get_settings_handles_config_error(
        self, client, mock_settings_service
    ):
        """Test error handling when config file is missing."""
        mock_settings_service.get_quality_gate_settings.side_effect = (
            FileNotFoundError("Config file not found")
        )

        response = client.get("/api/settings/gates")
        assert response.status_code == 500
        assert "Configuration error" in response.json()["detail"]


# ==================================================
# Test PUT /api/settings/gates
# ==================================================


class TestUpdateQualityGateSettings:
    """Tests for PUT /api/settings/gates endpoint."""

    def test_update_single_field(self, client, mock_settings_service):
        """Test updating a single field."""
        mock_settings_service.update_quality_gate_settings.return_value = {
            "settings": {
                "min_confidence": 75.0,
                "min_sources": 2,
                "min_anomaly": 50.0,
                "min_catalyst": 40.0,
                "require_invalidation": True,
            },
            "updated_fields": ["min_confidence"],
        }

        response = client.put(
            "/api/settings/gates",
            json={"min_confidence": 75.0},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["settings"]["min_confidence"] == 75.0
        assert "min_confidence" in data["updated_fields"]
        assert len(data["updated_fields"]) == 1

    def test_update_multiple_fields(self, client, mock_settings_service):
        """Test updating multiple fields at once."""
        mock_settings_service.update_quality_gate_settings.return_value = {
            "settings": {
                "min_confidence": 80.0,
                "min_sources": 4,
                "min_anomaly": 60.0,
                "min_catalyst": 55.0,
                "require_invalidation": False,
            },
            "updated_fields": [
                "min_confidence",
                "min_sources",
                "min_anomaly",
                "min_catalyst",
                "require_invalidation",
            ],
        }

        response = client.put(
            "/api/settings/gates",
            json={
                "min_confidence": 80.0,
                "min_sources": 4,
                "min_anomaly": 60.0,
                "min_catalyst": 55.0,
                "require_invalidation": False,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["updated_fields"]) == 5

    def test_update_no_changes(self, client, mock_settings_service):
        """Test update with empty body makes no changes."""
        mock_settings_service.update_quality_gate_settings.return_value = {
            "settings": {
                "min_confidence": 70.0,
                "min_sources": 2,
                "min_anomaly": 50.0,
                "min_catalyst": 40.0,
                "require_invalidation": True,
            },
            "updated_fields": [],
        }

        response = client.put("/api/settings/gates", json={})
        assert response.status_code == 200

        data = response.json()
        assert data["updated_fields"] == []
        assert "No changes made" in data["message"]

    def test_update_validates_min_confidence_too_low(
        self, client, _mock_settings_service
    ):
        """Test that min_confidence below 0 is rejected."""
        response = client.put(
            "/api/settings/gates",
            json={"min_confidence": -5.0},
        )
        assert response.status_code == 422  # Validation error

    def test_update_validates_min_confidence_too_high(
        self, client, _mock_settings_service
    ):
        """Test that min_confidence above 100 is rejected."""
        response = client.put(
            "/api/settings/gates",
            json={"min_confidence": 150.0},
        )
        assert response.status_code == 422  # Validation error

    def test_update_validates_min_sources_too_low(
        self, client, _mock_settings_service
    ):
        """Test that min_sources below 1 is rejected."""
        response = client.put(
            "/api/settings/gates",
            json={"min_sources": 0},
        )
        assert response.status_code == 422  # Validation error

    def test_update_validates_min_sources_too_high(
        self, client, _mock_settings_service
    ):
        """Test that min_sources above 10 is rejected."""
        response = client.put(
            "/api/settings/gates",
            json={"min_sources": 15},
        )
        assert response.status_code == 422  # Validation error

    def test_update_validates_min_anomaly_range(
        self, client, _mock_settings_service
    ):
        """Test that min_anomaly must be 0-100."""
        response = client.put(
            "/api/settings/gates",
            json={"min_anomaly": 120.0},
        )
        assert response.status_code == 422  # Validation error

    def test_update_validates_min_catalyst_range(
        self, client, _mock_settings_service
    ):
        """Test that min_catalyst must be 0-100."""
        response = client.put(
            "/api/settings/gates",
            json={"min_catalyst": -10.0},
        )
        assert response.status_code == 422  # Validation error

    def test_update_handles_service_value_error(
        self, client, mock_settings_service
    ):
        """Test handling of service-level validation errors."""
        mock_settings_service.update_quality_gate_settings.side_effect = (
            ValueError("Invalid value")
        )

        response = client.put(
            "/api/settings/gates",
            json={"min_confidence": 75.0},
        )
        assert response.status_code == 400
        assert "Invalid value" in response.json()["detail"]


# ==================================================
# Test DELETE /api/settings/gates (Reset to defaults)
# ==================================================


class TestResetQualityGateSettings:
    """Tests for DELETE /api/settings/gates endpoint."""

    def test_reset_to_defaults(self, client, mock_settings_service):
        """Test resetting settings to defaults."""
        mock_settings_service.reset_quality_gate_settings.return_value = {
            "settings": {
                "min_confidence": 70.0,
                "min_sources": 2,
                "min_anomaly": 50.0,
                "min_catalyst": 40.0,
                "require_invalidation": True,
            },
            "updated_fields": [
                "min_confidence",
                "min_sources",
                "min_anomaly",
                "min_catalyst",
                "require_invalidation",
            ],
        }

        response = client.delete("/api/settings/gates")
        assert response.status_code == 200

        data = response.json()
        assert data["settings"]["min_confidence"] == 70.0
        assert data["settings"]["min_sources"] == 2
        assert data["settings"]["min_anomaly"] == 50.0
        assert data["settings"]["min_catalyst"] == 40.0
        assert data["settings"]["require_invalidation"] is True
        assert "reset to defaults" in data["message"].lower()


# ==================================================
# Test SettingsService directly
# ==================================================


class TestSettingsService:
    """Tests for SettingsService class."""

    def test_get_settings_from_file(self, temp_config_file):
        """Test reading settings from config file."""
        from api.services.settings_service import SettingsService

        # Write quality_gates to temp config
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)
        config["quality_gates"] = {
            "min_confidence": 85.0,
            "min_sources": 3,
        }
        with open(temp_config_file, "w") as f:
            yaml.dump(config, f)

        service = SettingsService(config_path=temp_config_file)
        settings = service.get_quality_gate_settings()

        assert settings["min_confidence"] == 85.0
        assert settings["min_sources"] == 3
        # Defaults for missing values
        assert settings["min_anomaly"] == 50.0
        assert settings["min_catalyst"] == 40.0
        assert settings["require_invalidation"] is True

    def test_update_settings_persists_to_file(self, temp_config_file):
        """Test that updates are persisted to config file."""
        from api.services.settings_service import SettingsService

        service = SettingsService(config_path=temp_config_file)

        # Update settings
        service.update_quality_gate_settings(
            min_confidence=90.0,
            min_sources=5,
        )

        # Read back from file
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert "quality_gates" in config
        assert config["quality_gates"]["min_confidence"] == 90.0
        assert config["quality_gates"]["min_sources"] == 5

    def test_reset_removes_quality_gates_section(self, temp_config_file):
        """Test that reset removes the quality_gates section."""
        from api.services.settings_service import SettingsService

        # First add quality_gates
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)
        config["quality_gates"] = {"min_confidence": 90.0}
        with open(temp_config_file, "w") as f:
            yaml.dump(config, f)

        service = SettingsService(config_path=temp_config_file)
        service.reset_quality_gate_settings()

        # Verify removed
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)
        assert "quality_gates" not in config

    def test_get_quality_gate_config_returns_config_object(self, temp_config_file):
        """Test get_quality_gate_config returns QualityGateConfig."""
        from api.services.settings_service import SettingsService
        from src.tradz.events.quality_gate import QualityGateConfig

        # Write custom settings
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)
        config["quality_gates"] = {
            "min_confidence": 75.0,
            "min_sources": 4,
            "require_invalidation": False,
        }
        with open(temp_config_file, "w") as f:
            yaml.dump(config, f)

        service = SettingsService(config_path=temp_config_file)
        gate_config = service.get_quality_gate_config()

        assert isinstance(gate_config, QualityGateConfig)
        assert gate_config.min_confidence == 75.0
        assert gate_config.min_sources == 4
        assert gate_config.has_invalidation is False

    def test_service_validates_min_confidence_range(self, temp_config_file):
        """Test service-level validation of min_confidence."""
        from api.services.settings_service import SettingsService

        service = SettingsService(config_path=temp_config_file)

        with pytest.raises(ValueError, match="min_confidence must be between"):
            service.update_quality_gate_settings(min_confidence=150.0)

    def test_service_validates_min_sources_range(self, temp_config_file):
        """Test service-level validation of min_sources."""
        from api.services.settings_service import SettingsService

        service = SettingsService(config_path=temp_config_file)

        with pytest.raises(ValueError, match="min_sources must be between"):
            service.update_quality_gate_settings(min_sources=0)

    def test_update_returns_updated_fields(self, temp_config_file):
        """Test that update returns list of updated fields."""
        from api.services.settings_service import SettingsService

        service = SettingsService(config_path=temp_config_file)
        result = service.update_quality_gate_settings(
            min_confidence=80.0,
            min_anomaly=55.0,
        )

        assert "updated_fields" in result
        assert "min_confidence" in result["updated_fields"]
        assert "min_anomaly" in result["updated_fields"]
        assert len(result["updated_fields"]) == 2

    def test_config_file_not_found(self):
        """Test error when config file doesn't exist."""
        from api.services.settings_service import SettingsService

        service = SettingsService(config_path=Path("/nonexistent/config.yaml"))

        with pytest.raises(FileNotFoundError):
            service.get_quality_gate_settings()


# ==================================================
# Integration Tests
# ==================================================


class TestSettingsIntegration:
    """Integration tests for settings functionality."""

    def test_changes_take_effect_immediately(self, temp_config_file):
        """Test that settings changes affect gate evaluation immediately."""
        from api.services.settings_service import SettingsService

        # Setup with low thresholds
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)
        config["quality_gates"] = {"min_confidence": 30.0}
        with open(temp_config_file, "w") as f:
            yaml.dump(config, f)

        service = SettingsService(config_path=temp_config_file)

        # Get config and create gate
        gate_config_1 = service.get_quality_gate_config()
        assert gate_config_1.min_confidence == 30.0

        # Update threshold
        service.update_quality_gate_settings(min_confidence=95.0)

        # Get new config - should reflect changes
        gate_config_2 = service.get_quality_gate_config()
        assert gate_config_2.min_confidence == 95.0

    def test_partial_update_preserves_other_settings(self, temp_config_file):
        """Test that partial updates don't affect other settings."""
        from api.services.settings_service import SettingsService

        # Setup with multiple settings
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)
        config["quality_gates"] = {
            "min_confidence": 80.0,
            "min_sources": 4,
            "min_anomaly": 60.0,
        }
        with open(temp_config_file, "w") as f:
            yaml.dump(config, f)

        service = SettingsService(config_path=temp_config_file)

        # Update only min_confidence
        service.update_quality_gate_settings(min_confidence=90.0)

        # Verify other settings unchanged
        settings = service.get_quality_gate_settings()
        assert settings["min_confidence"] == 90.0
        assert settings["min_sources"] == 4
        assert settings["min_anomaly"] == 60.0

    def test_preserves_other_config_sections(self, temp_config_file):
        """Test that updates don't affect other config sections."""
        from api.services.settings_service import SettingsService

        service = SettingsService(config_path=temp_config_file)

        # Update quality gates
        service.update_quality_gate_settings(min_confidence=85.0)

        # Verify other sections preserved
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert "timezone" in config
        assert config["timezone"] == "America/New_York"
        assert "equities" in config
        assert "AAPL" in config["equities"]["tickers"]
