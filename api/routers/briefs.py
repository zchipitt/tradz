"""
Daily Brief API endpoints.

Provides endpoints for:
- GET /api/briefs/{date} - Get brief by date
- GET /api/briefs/latest - Get most recent brief
- GET /api/briefs - List available briefs
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..schemas.briefs import (
    BriefNotFoundError,
    GetBriefResponse,
    GetLatestBriefResponse,
    InvalidDateError,
    ListBriefsResponse,
)
from ..services.brief_service import BriefService, get_brief_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["briefs"])


@router.get(
    "/{date}",
    response_model=GetBriefResponse,
    responses={
        404: {"model": BriefNotFoundError},
        400: {"model": InvalidDateError},
    },
    summary="Get daily brief by date",
    description="Retrieve the daily brief for a specific date in YYYY-MM-DD format",
)
async def get_brief_by_date(
    date: str,
    brief_service: BriefService = Depends(get_brief_service),
) -> GetBriefResponse:
    """
    Get daily brief for a specific date.

    Args:
        date: Date in YYYY-MM-DD format
        brief_service: Injected BriefService instance

    Returns:
        GetBriefResponse with brief data or None if not found
    """
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid date format",
                "message": "Date must be in YYYY-MM-DD format",
            },
        )

    brief = brief_service.get_brief_by_date(date)

    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Brief not found for date",
                "date": date,
            },
        )

    return GetBriefResponse(brief=brief)


@router.get(
    "/latest",
    response_model=GetLatestBriefResponse,
    responses={
        404: {"description": "No briefs found"},
    },
    summary="Get the most recent daily brief",
    description="Retrieve the most recently generated daily brief",
)
async def get_latest_brief(
    brief_service: BriefService = Depends(get_brief_service),
) -> GetLatestBriefResponse:
    """
    Get the most recent daily brief.

    Args:
        brief_service: Injected BriefService instance

    Returns:
        GetLatestBriefResponse with the most recent brief

    Raises:
        HTTPException: If no briefs exist in the database
    """
    brief = brief_service.get_latest_brief()

    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No briefs found in database",
        )

    return GetLatestBriefResponse(brief=brief)


@router.get(
    "/",
    response_model=ListBriefsResponse,
    summary="List daily briefs",
    description="List all available daily briefs with pagination",
)
async def list_briefs(
    limit: Optional[int] = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of briefs to return (1-100)",
    ),
    offset: Optional[int] = Query(
        default=0,
        ge=0,
        description="Number of briefs to skip for pagination",
    ),
    brief_service: BriefService = Depends(get_brief_service),
) -> ListBriefsResponse:
    """
    List available daily briefs with pagination.

    Args:
        limit: Maximum number of briefs to return
        offset: Number of briefs to skip
        brief_service: Injected BriefService instance

    Returns:
        ListBriefsResponse with paginated briefs
    """
    try:
        briefs, total_count = brief_service.list_briefs(limit=limit, offset=offset)

        return ListBriefsResponse(
            briefs=briefs,
            total_count=total_count,
        )

    except Exception as e:
        logger.error(f"Error listing briefs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list briefs",
        )
