"""
Reports router for historical report endpoints.
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from api.config import get_settings
from api.services.aggregator_service import aggregator_service

router = APIRouter()


@router.get("")
async def list_reports(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of reports to return")
) -> List[Dict[str, Any]]:
    """
    List available reports.

    Returns list of report dates sorted by most recent first.
    """
    settings = get_settings()
    data_dir = settings.data_dir
    reports_dir = settings.reports_dir

    reports = []

    # Check both data and reports directories
    for directory in [data_dir, reports_dir]:
        if directory.exists():
            for file in directory.glob("*.json"):
                # Extract date from filename (YYYY-MM-DD.json)
                date_str = file.stem
                try:
                    # Validate it's a date
                    datetime.strptime(date_str, "%Y-%m-%d")
                    stat = file.stat()
                    reports.append({
                        "date": date_str,
                        "file": str(file.name),
                        "directory": str(directory.name),
                        "size_bytes": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
                except ValueError:
                    # Not a date-formatted filename, skip
                    continue

    # Remove duplicates (prefer reports dir over data dir)
    seen_dates = set()
    unique_reports = []
    for report in sorted(reports, key=lambda x: (x["date"], x["directory"] == "reports"), reverse=True):
        if report["date"] not in seen_dates:
            seen_dates.add(report["date"])
            unique_reports.append(report)

    return unique_reports[:limit]


@router.get("/latest")
async def get_latest_report() -> Dict[str, Any]:
    """
    Get the most recent report.

    Returns the latest available report data.
    """
    reports = await list_reports(limit=1)
    if not reports:
        raise HTTPException(status_code=404, detail="No reports available")

    date = reports[0]["date"]
    return await get_report_by_date(date)


@router.get("/{date}")
async def get_report_by_date(date: str) -> Dict[str, Any]:
    """
    Get report for a specific date.

    Args:
        date: Date string (YYYY-MM-DD)
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Try to load from aggregator
    data = aggregator_service.load_historical_data(date)
    if data:
        return data

    # Not found
    raise HTTPException(status_code=404, detail=f"Report for {date} not found")
