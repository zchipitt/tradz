"""
API configuration and settings.
"""
import os
from pathlib import Path
from functools import lru_cache

import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API settings loaded from environment variables."""

    # API settings
    api_title: str = "Tradz API"
    api_version: str = "1.0.0"
    api_description: str = "Trading Intelligence Dashboard API"

    # CORS settings
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
    ]

    # Cache settings
    cache_ttl_seconds: int = 300  # 5 minutes

    # Project paths
    project_root: Path = Path(__file__).parent.parent
    config_path: Path = project_root / "config.yaml"
    data_dir: Path = project_root / "data"
    reports_dir: Path = project_root / "reports"

    class Config:
        env_prefix = "TRADZ_"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def load_config() -> dict:
    """Load configuration from config.yaml."""
    settings = get_settings()
    config_path = settings.config_path

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
