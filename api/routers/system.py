"""
System status API router.
"""
from fastapi import APIRouter, HTTPException

from api.schemas.system import SystemStatusResponse, SourceHealth, OverallHealth
from api.services.system_service import system_service

router = APIRouter()


@router.get(
    "/status",
    response_model=SystemStatusResponse,
    summary="Get system status",
    description="Returns health status for all data sources including record counts and freshness indicators.",
)
async def get_system_status() -> SystemStatusResponse:
    """
    Get health status for all data sources.

    Status determination:
    - **ok**: Last successful data fetch within the last hour
    - **degraded**: Last successful data fetch within the last 24 hours
    - **error**: No successful data fetch in the last 24 hours

    Returns overall health summary and per-source details including:
    - name: Source identifier
    - display_name: Human-readable source name
    - status: ok, degraded, or error
    - last_success_at: Timestamp of last successful fetch
    - last_error: Most recent error message if any
    - record_count_24h: Number of records ingested in last 24 hours
    - freshness_indicator: fresh, stale, or unknown
    """
    try:
        status_data = system_service.get_system_status()

        # Convert dict to response model
        sources = [
            SourceHealth(
                name=s["name"],
                display_name=s["display_name"],
                status=s["status"],
                last_success_at=s["last_success_at"],
                last_error=s["last_error"],
                record_count_24h=s["record_count_24h"],
                freshness_indicator=s["freshness_indicator"],
            )
            for s in status_data["sources"]
        ]

        overall = OverallHealth(
            total_sources=status_data["overall"]["total_sources"],
            healthy_count=status_data["overall"]["healthy_count"],
            degraded_count=status_data["overall"]["degraded_count"],
            error_count=status_data["overall"]["error_count"],
        )

        return SystemStatusResponse(
            overall=overall,
            sources=sources,
            last_check_at=status_data["last_check_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
