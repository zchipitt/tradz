"""
Settings service for managing application configuration (US-025).

Handles reading and writing quality gate thresholds to config.yaml.
"""
import logging
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

import yaml

from src.tradz.events.quality_gate import QualityGateConfig

logger = logging.getLogger(__name__)

# Default path to config.yaml (relative to project root)
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


class SettingsService:
    """
    Service for managing application settings.

    Provides thread-safe read/write access to quality gate thresholds
    stored in config.yaml.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize settings service.

        Args:
            config_path: Path to config.yaml. Uses default if not provided.
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._lock = Lock()

    def _read_config(self) -> Dict[str, Any]:
        """
        Read configuration from YAML file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            return yaml.safe_load(f) or {}

    def _write_config(self, config: Dict[str, Any]) -> None:
        """
        Write configuration to YAML file.

        Args:
            config: Configuration dictionary to write.
        """
        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def get_quality_gate_settings(self) -> Dict[str, Any]:
        """
        Get current quality gate threshold settings.

        Returns:
            Dictionary with quality gate settings.
        """
        with self._lock:
            config = self._read_config()
            quality_gates = config.get("quality_gates", {})

            # Return current settings with defaults for missing values
            defaults = self.get_quality_gate_defaults()
            return {
                "min_confidence": quality_gates.get("min_confidence", defaults["min_confidence"]),
                "min_sources": quality_gates.get("min_sources", defaults["min_sources"]),
                "min_anomaly": quality_gates.get("min_anomaly", defaults["min_anomaly"]),
                "min_catalyst": quality_gates.get("min_catalyst", defaults["min_catalyst"]),
                "require_invalidation": quality_gates.get(
                    "require_invalidation", defaults["require_invalidation"]
                ),
            }

    def get_quality_gate_defaults(self) -> Dict[str, Any]:
        """
        Get default quality gate threshold settings.

        Returns:
            Dictionary with default quality gate settings.
        """
        # Use QualityGateConfig defaults
        default_config = QualityGateConfig()
        return {
            "min_confidence": default_config.min_confidence,
            "min_sources": default_config.min_sources,
            "min_anomaly": default_config.min_anomaly,
            "min_catalyst": default_config.min_catalyst,
            "require_invalidation": default_config.has_invalidation,
        }

    def update_quality_gate_settings(
        self,
        min_confidence: Optional[float] = None,
        min_sources: Optional[int] = None,
        min_anomaly: Optional[float] = None,
        min_catalyst: Optional[float] = None,
        require_invalidation: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update quality gate threshold settings.

        Only provided values are updated; others remain unchanged.

        Args:
            min_confidence: Minimum confidence score (0-100).
            min_sources: Minimum number of unique sources (1-10).
            min_anomaly: Minimum anomaly score (0-100).
            min_catalyst: Minimum catalyst score (0-100).
            require_invalidation: Whether invalidation condition is required.

        Returns:
            Dictionary with updated settings and list of changed fields.

        Raises:
            ValueError: If any value is out of valid range.
        """
        # Validate ranges
        if min_confidence is not None and not (0 <= min_confidence <= 100):
            raise ValueError("min_confidence must be between 0 and 100")
        if min_sources is not None and not (1 <= min_sources <= 10):
            raise ValueError("min_sources must be between 1 and 10")
        if min_anomaly is not None and not (0 <= min_anomaly <= 100):
            raise ValueError("min_anomaly must be between 0 and 100")
        if min_catalyst is not None and not (0 <= min_catalyst <= 100):
            raise ValueError("min_catalyst must be between 0 and 100")

        with self._lock:
            config = self._read_config()

            # Initialize quality_gates section if it doesn't exist
            if "quality_gates" not in config:
                config["quality_gates"] = {}

            quality_gates = config["quality_gates"]
            updated_fields = []

            # Update only provided fields
            if min_confidence is not None:
                quality_gates["min_confidence"] = min_confidence
                updated_fields.append("min_confidence")

            if min_sources is not None:
                quality_gates["min_sources"] = min_sources
                updated_fields.append("min_sources")

            if min_anomaly is not None:
                quality_gates["min_anomaly"] = min_anomaly
                updated_fields.append("min_anomaly")

            if min_catalyst is not None:
                quality_gates["min_catalyst"] = min_catalyst
                updated_fields.append("min_catalyst")

            if require_invalidation is not None:
                quality_gates["require_invalidation"] = require_invalidation
                updated_fields.append("require_invalidation")

            # Write back to config file
            self._write_config(config)

            # Return updated settings
            return {
                "settings": self.get_quality_gate_settings(),
                "updated_fields": updated_fields,
            }

    def reset_quality_gate_settings(self) -> Dict[str, Any]:
        """
        Reset quality gate settings to defaults.

        Returns:
            Dictionary with reset settings.
        """
        with self._lock:
            config = self._read_config()

            # Remove quality_gates section to use defaults
            if "quality_gates" in config:
                del config["quality_gates"]

            self._write_config(config)

            return {
                "settings": self.get_quality_gate_defaults(),
                "updated_fields": [
                    "min_confidence",
                    "min_sources",
                    "min_anomaly",
                    "min_catalyst",
                    "require_invalidation",
                ],
            }

    def get_quality_gate_config(self) -> QualityGateConfig:
        """
        Get QualityGateConfig object for use in quality gate evaluation.

        This is the bridge between settings and the QualityGate class.

        Returns:
            QualityGateConfig with current settings.
        """
        settings = self.get_quality_gate_settings()
        return QualityGateConfig(
            min_confidence=settings["min_confidence"],
            min_sources=settings["min_sources"],
            min_anomaly=settings["min_anomaly"],
            min_catalyst=settings["min_catalyst"],
            has_invalidation=settings["require_invalidation"],
        )


# Singleton instance
settings_service = SettingsService()
