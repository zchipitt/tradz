"""
Reports router for historical report endpoints.
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from jinja2 import Template

from api.config import get_settings
from api.services.aggregator_service import aggregator_service

try:
    from api.services.brief_service import brief_service
except ImportError:
    brief_service = None  # type: ignore

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


@router.get("/{date}/html", response_class=HTMLResponse)
async def get_report_html(date: str) -> str:
    """
    Get report as HTML page for traditional web interface.

    Returns styled HTML suitable for direct browser viewing.

    Args:
        date: Date string (YYYY-MM-DD)
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Try to load brief data
    brief_data: Union[Dict[str, Any], Any, None] = None
    if brief_service is not None:
        try:
            brief_response = brief_service.get_brief_by_date(date)
            if brief_response and hasattr(brief_response, 'brief'):
                brief_data = brief_response.brief
        except Exception:
            # Fallback to aggregator if brief service fails
            pass

    # Fallback to aggregator if brief service not available or fails
    if brief_data is None:
        brief_data = aggregator_service.load_historical_data(date)

    if brief_data is None:
        raise HTTPException(status_code=404, detail=f"Report for {date} not found")

    # Load and render HTML template
    template_path = Path(__file__).parent.parent / "templates" / "daily_brief.html"
    if not template_path.exists():
        raise HTTPException(status_code=500, detail="HTML template not found")

    try:
        with open(template_path, "r") as f:
            template = Template(f.read())

        # Prepare template data
        template_data = {
            "date": date,
            "generation_method": "Manual",
            "executive_summary": "",
            "top_events": [],
            "trade_ideas": [],
            "research_ideas": [],
            "open_loops": [],
            "data_quality": [],
            "data_stats": {"total_sources": 0, "healthy_count": 0, "degraded_count": 0, "error_count": 0},
            "generated_at": datetime.now(datetime.timezone.utc).isoformat(),
        }

        # Map brief data to template
        if hasattr(brief_data, '__dict__'):
            # Pydantic model or dataclass
            data_dict = brief_data.__dict__
        elif isinstance(brief_data, dict):
            data_dict = brief_data
        else:
            data_dict = {}

        # Generation method
        gen_method = data_dict.get('generation_method', 'manual') if data_dict else 'manual'
        template_data["generation_method"] = gen_method

        # Executive summary
        exec_summary = data_dict.get('executive_summary', '') if data_dict else ''
        template_data["executive_summary"] = exec_summary

        # Handle different data structures
        top_events = data_dict.get('top_events', []) if data_dict else []
        if not top_events and data_dict.get('signals'):
            # Fallback to legacy signals format
            top_events = data_dict['signals'][:5]
        template_data["top_events"] = top_events

        # Extract trade ideas
        trade_ideas = data_dict.get('trade_ideas', []) if data_dict else []
        if not trade_ideas and data_dict.get('recommendations'):
            # Fallback to legacy format
            trade_ideas = [
                {
                    'symbol': r.get('symbol', 'N/A'),
                    'direction': 'long' if r.get('score', 0) > 50 else 'short',
                    'event_title': f"{r.get('symbol', 'N/A')} Opportunity",
                    'entry_zone': str(r.get('price', 'Market')),
                    'target': str(r.get('target', 'N/A')),
                    'stop_loss': str(r.get('stop', 'N/A')),
                    'time_horizon': '1-3 days',
                    'invalidation': 'Market structure break'
                } for r in data_dict.get('recommendations', [])
            ]
        template_data["trade_ideas"] = trade_ideas

        # Extract research ideas
        template_data["research_ideas"] = data_dict.get('research_ideas', []) if data_dict else []

        # Extract open loops
        template_data["open_loops"] = data_dict.get('open_loops', []) if data_dict else []

        # Extract data quality and calculate stats
        data_quality = data_dict.get('data_quality', []) if data_dict else []
        template_data["data_quality"] = data_quality

        stats = {'total_sources': 0, 'healthy_count': 0, 'degraded_count': 0, 'error_count': 0}
        for source in data_quality:
            if isinstance(source, dict):
                stats['total_sources'] += 1
                source_status = source.get('status')
                if source_status == 'ok':
                    stats['healthy_count'] += 1
                elif source_status == 'degraded':
                    stats['degraded_count'] += 1
                elif source_status == 'error':
                    stats['error_count'] += 1
        template_data["data_stats"] = stats

        # Render template
        return template.render(**template_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering HTML: {str(e)}")


@router.get("/latest/html", response_class=HTMLResponse)
async def get_latest_report_html() -> str:
    """
    Get the most recent report as HTML page.

    Returns styled HTML suitable for direct browser viewing.
    """
    reports = await list_reports(limit=1)
    if not reports:
        raise HTTPException(status_code=404, detail="No reports available")

    date = reports[0]["date"]
    return await get_report_html(date)
