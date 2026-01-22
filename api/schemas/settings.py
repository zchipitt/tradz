"""
Pydantic schemas for settings API (US-025).
"""
from typing import Optional
from pydantic import BaseModel, Field


class QualityGateSettings(BaseModel):
    """Quality gate threshold settings."""

    min_confidence: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Minimum confidence score (0-100) required to pass the confidence gate",
    )
    min_sources: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Minimum number of unique data sources required",
    )
    min_anomaly: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Minimum anomaly score (0-100) required",
    )
    min_catalyst: float = Field(
        default=40.0,
        ge=0.0,
        le=100.0,
        description="Minimum catalyst score (0-100) required",
    )
    require_invalidation: bool = Field(
        default=True,
        description="Whether an invalidation condition must be definable",
    )


class QualityGateSettingsResponse(BaseModel):
    """Response for GET /api/settings/gates."""

    settings: QualityGateSettings
    defaults: QualityGateSettings = Field(
        description="Default values for reference"
    )


class UpdateQualityGateSettingsRequest(BaseModel):
    """Request body for PUT /api/settings/gates."""

    min_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Minimum confidence score (0-100)",
    )
    min_sources: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Minimum number of unique data sources",
    )
    min_anomaly: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Minimum anomaly score (0-100)",
    )
    min_catalyst: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Minimum catalyst score (0-100)",
    )
    require_invalidation: Optional[bool] = Field(
        default=None,
        description="Whether an invalidation condition must be definable",
    )


class UpdateQualityGateSettingsResponse(BaseModel):
    """Response for PUT /api/settings/gates."""

    settings: QualityGateSettings
    updated_fields: list[str] = Field(
        description="List of fields that were updated"
    )
    message: str = Field(
        default="Settings updated successfully",
        description="Status message",
    )
