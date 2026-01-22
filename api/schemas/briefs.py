"""
Pydantic schemas for Daily Brief API endpoints.

Defines request and response models for:
- GET /api/briefs/{date} - Get brief by date
- GET /api/briefs/latest - Get most recent brief
- GET /api/briefs - List available briefs
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class EventSummaryItem(BaseModel):
    """Event summary for daily brief."""
    event_id: str = Field(..., description="Event UUID")
    title: str = Field(..., description="Event title")
    ticker: Optional[str] = Field(None, description="Primary ticker")
    event_type: str = Field(..., description="Event type (e.g., market_anomaly)")
    attention_score: float = Field(..., description="Attention score 0-100")
    anomaly_score: float = Field(..., description="Anomaly score 0-100")
    catalyst_score: float = Field(..., description="Catalyst score 0-100")
    flow_score: float = Field(..., description="Flow score 0-100")
    confidence_score: float = Field(..., description="Confidence score 0-100")
    observation_count: int = Field(..., description="Number of observations")
    last_update_at: Optional[datetime] = Field(None, description="Last update timestamp")


class TradeIdeaItem(BaseModel):
    """Trade idea summary."""
    event_id: str = Field(..., description="Event UUID")
    ticker: Optional[str] = Field(None, description="Primary ticker")
    direction: str = Field(..., description="Trade direction (long/short)")
    entry_zone: str = Field(..., description="Entry price zone")
    target: str = Field(..., description="Target price")
    stop_loss: str = Field(..., description="Stop loss level")
    confidence_level: float = Field(..., description="Confidence level 0-100")
    rationale: str = Field(..., description="Trade rationale")


class ResearchIdeaItem(BaseModel):
    """Research idea summary for events that failed gates."""
    event_id: str = Field(..., description="Event UUID")
    ticker: Optional[str] = Field(None, description="Primary ticker")
    questions: List[str] = Field(default_factory=list, description="Questions to verify")
    evidence_to_watch: List[str] = Field(default_factory=list, description="Evidence to monitor")
    current_score: float = Field(..., description="Current attention score")
    potential_score: float = Field(..., description="Estimated potential score")


class OpenLoopItem(BaseModel):
    """Open question or unresolved issue."""
    loop_id: str = Field(..., description="Loop ID")
    event_id: Optional[str] = Field(None, description="Related event ID")
    question: str = Field(..., description="Open question")
    created_at: datetime = Field(..., description="Creation timestamp")
    status: str = Field(..., description="Status: open/in_progress/resolved")


class SourceHealthItem(BaseModel):
    """Source health summary."""
    name: str = Field(..., description="Source identifier")
    display_name: str = Field(..., description="Human-readable name")
    status: str = Field(..., description="Status: ok/degraded/error")
    record_count_24h: int = Field(..., description="Records in last 24h")
    freshness_indicator: str = Field(..., description="Freshness: fresh/stale/unknown")


class DataQualitySection(BaseModel):
    """Data quality summary section."""
    total_sources: int = Field(..., description="Total number of sources")
    healthy_count: int = Field(..., description="Healthy sources count")
    degraded_count: int = Field(..., description="Degraded sources count")
    error_count: int = Field(..., description="Error sources count")
    sources: List[SourceHealthItem] = Field(default_factory=list, description="Per-source details")
    overall_status: str = Field(..., description="Overall status: ok/degraded/error")
    quality_message: str = Field(..., description="Human-readable quality message")


class BriefDetail(BaseModel):
    """Full daily brief response for a specific date."""
    id: str = Field(..., description="Brief UUID")
    date: datetime = Field(..., description="Brief date")
    executive_summary: str = Field(..., description="Executive summary text")
    top_events: List[EventSummaryItem] = Field(..., description="Top 5 events")
    trade_ideas: List[TradeIdeaItem] = Field(..., description="Trade ideas")
    research_ideas: List[ResearchIdeaItem] = Field(..., description="Research ideas")
    open_loops: List[OpenLoopItem] = Field(..., description="Open loops")
    data_quality: Optional[DataQualitySection] = Field(None, description="Data quality summary")
    generation_method: str = Field(..., description="Generation method: claude/template")
    created_at: datetime = Field(..., description="Creation timestamp")
    run_id: Optional[str] = Field(None, description="Linked run history ID")


class BriefSummary(BaseModel):
    """Summary of a brief for listing."""
    id: str = Field(..., description="Brief UUID")
    date: datetime = Field(..., description="Brief date")
    generation_method: str = Field(..., description="Generation method: claude/template")
    created_at: datetime = Field(..., description="Creation timestamp")
    event_count: int = Field(..., description="Number of events in brief")
    trade_idea_count: int = Field(..., description="Number of trade ideas")
    top_entity: Optional[str] = Field(None, description="Top entity (ticker)")
    report_path_md: Optional[str] = Field(None, description="Markdown report path")
    report_path_json: Optional[str] = Field(None, description="JSON report path")
    run_id: Optional[str] = Field(None, description="Linked run history ID")


class GetBriefResponse(BaseModel):
    """Response model for GET /api/briefs/{date}."""
    brief: Optional[BriefDetail] = Field(None, description="Daily brief for the date")


class GetLatestBriefResponse(BaseModel):
    """Response model for GET /api/briefs/latest."""
    brief: Optional[BriefDetail] = Field(None, description="Most recent daily brief")


class ListBriefsResponse(BaseModel):
    """Response model for GET /api/briefs."""
    briefs: List[BriefSummary] = Field(default_factory=list, description="List of available briefs")
    total_count: int = Field(..., description="Total number of briefs")


# Error response schemas
class BriefNotFoundError(BaseModel):
    """Error response when brief is not found."""
    error: str = Field("Brief not found for date", description="Error message")
    date: str = Field(..., description="Requested date")


class InvalidDateError(BaseModel):
    """Error response for invalid date format."""
    error: str = Field("Invalid date format", description="Error message")
    message: str = Field(..., description="Validation error details")
