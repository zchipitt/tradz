"""
Settings API router (US-025).

Provides endpoints for managing application settings including quality gate thresholds.
"""
from fastapi import APIRouter, HTTPException

from api.schemas.settings import (
    QualityGateSettings,
    QualityGateSettingsResponse,
    UpdateQualityGateSettingsRequest,
    UpdateQualityGateSettingsResponse,
)
from api.services.settings_service import settings_service

router = APIRouter()


@router.get(
    "/gates",
    response_model=QualityGateSettingsResponse,
    summary="Get quality gate settings",
    description="Returns current quality gate threshold settings along with default values for reference.",
)
async def get_quality_gate_settings() -> QualityGateSettingsResponse:
    """
    Get current quality gate threshold settings.

    Returns:
        Current settings and default values for each threshold:
        - min_confidence: Minimum confidence score (0-100)
        - min_sources: Minimum number of unique data sources
        - min_anomaly: Minimum anomaly score (0-100)
        - min_catalyst: Minimum catalyst score (0-100)
        - require_invalidation: Whether invalidation condition is required
    """
    try:
        current_settings = settings_service.get_quality_gate_settings()
        default_settings = settings_service.get_quality_gate_defaults()

        return QualityGateSettingsResponse(
            settings=QualityGateSettings(**current_settings),
            defaults=QualityGateSettings(**default_settings),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/gates",
    response_model=UpdateQualityGateSettingsResponse,
    summary="Update quality gate settings",
    description="Update quality gate threshold settings. Only provided fields are updated.",
)
async def update_quality_gate_settings(
    request: UpdateQualityGateSettingsRequest,
) -> UpdateQualityGateSettingsResponse:
    """
    Update quality gate threshold settings.

    Only fields that are provided in the request body will be updated.
    Omitted fields retain their current values.

    Valid ranges:
    - min_confidence: 0-100
    - min_sources: 1-10
    - min_anomaly: 0-100
    - min_catalyst: 0-100
    - require_invalidation: true/false

    Changes take effect immediately for new evaluations.
    """
    try:
        result = settings_service.update_quality_gate_settings(
            min_confidence=request.min_confidence,
            min_sources=request.min_sources,
            min_anomaly=request.min_anomaly,
            min_catalyst=request.min_catalyst,
            require_invalidation=request.require_invalidation,
        )

        return UpdateQualityGateSettingsResponse(
            settings=QualityGateSettings(**result["settings"]),
            updated_fields=result["updated_fields"],
            message=f"Updated {len(result['updated_fields'])} field(s) successfully"
            if result["updated_fields"]
            else "No changes made",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/gates",
    response_model=UpdateQualityGateSettingsResponse,
    summary="Reset quality gate settings to defaults",
    description="Reset all quality gate thresholds to their default values.",
)
async def reset_quality_gate_settings() -> UpdateQualityGateSettingsResponse:
    """
    Reset quality gate settings to default values.

    This removes any custom configuration and restores:
    - min_confidence: 70.0
    - min_sources: 2
    - min_anomaly: 50.0
    - min_catalyst: 40.0
    - require_invalidation: true
    """
    try:
        result = settings_service.reset_quality_gate_settings()

        return UpdateQualityGateSettingsResponse(
            settings=QualityGateSettings(**result["settings"]),
            updated_fields=result["updated_fields"],
            message="Settings reset to defaults",
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
