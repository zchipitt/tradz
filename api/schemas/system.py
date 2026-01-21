"""
Pydantic schemas for system status API.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SourceStatus(str, Enum):
    """Health status for a data source."""
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


class SourceHealth(BaseModel):
    """Health information for a single data source."""
    name: str = Field(..., description="Source name (e.g., 'congress', 'news')")
    display_name: str = Field(..., description="Human-readable source name")
    status: SourceStatus = Field(..., description="Health status: ok, degraded, or error")
    last_success_at: Optional[datetime] = Field(
        None, description="Timestamp of last successful data fetch"
    )
    last_error: Optional[str] = Field(None, description="Last error message if any")
    record_count_24h: int = Field(
        0, description="Number of records ingested in the last 24 hours"
    )
    freshness_indicator: str = Field(
        "unknown", description="Data freshness: fresh, stale, or unknown"
    )


class OverallHealth(BaseModel):
    """Overall system health summary."""
    total_sources: int = Field(..., description="Total number of data sources")
    healthy_count: int = Field(..., description="Number of healthy (ok) sources")
    degraded_count: int = Field(..., description="Number of degraded sources")
    error_count: int = Field(..., description="Number of sources in error state")


class SystemStatusResponse(BaseModel):
    """Response schema for system status endpoint."""
    overall: OverallHealth = Field(..., description="Overall system health summary")
    sources: List[SourceHealth] = Field(..., description="Health status per data source")
    last_check_at: datetime = Field(..., description="Timestamp of this status check")
