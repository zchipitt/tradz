"""
Pydantic schemas for events endpoints.
"""
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class EventStatusFilter(str, Enum):
    """Event status filter options."""
    ACTIVE = "active"  # new + ongoing
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ALL = "all"


class TimelineSourceFilter(str, Enum):
    """Timeline observation source filter options."""
    ALL = "all"
    MARKET = "market"  # equities, crypto
    NEWS = "news"
    SEC = "sec"
    CONGRESS = "congress"
    HEDGEFUND = "13f"  # alias for hedgefund/13f
    POLYMARKET = "polymarket"


class EventSortBy(str, Enum):
    """Event sort options."""
    ATTENTION_SCORE = "attention_score"
    LAST_UPDATE = "last_update_at"
    CREATED = "start_at"


class EventTypeResponse(str, Enum):
    """Event type enumeration for API responses."""
    CATALYST = "catalyst"
    RISK = "risk"
    FLOW = "flow"
    MACRO = "macro"
    MARKET_ANOMALY = "market_anomaly"
    CATALYST_NEWS = "catalyst_news"
    CATALYST_FILING = "catalyst_filing"
    FLOW_CONGRESS = "flow_congress"
    FLOW_13F = "flow_13f"
    PREDICTION_SHIFT = "prediction_shift"
    MIXED = "mixed"
    UNCERTAIN = "uncertain"


class EventStatusResponse(str, Enum):
    """Event status enumeration for API responses."""
    OPEN = "open"
    CLOSED = "closed"
    EXPIRED = "expired"
    NEW = "new"
    ONGOING = "ongoing"
    STALE = "stale"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class FourDScores(BaseModel):
    """4-dimensional scores for an event."""
    anomaly_score: float = Field(..., ge=0, le=100, description="Market anomaly score (0-100)")
    catalyst_score: float = Field(..., ge=0, le=100, description="Catalyst score (0-100)")
    flow_score: float = Field(..., ge=0, le=100, description="Flow score (0-100)")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score (0-100)")


class EntityBrief(BaseModel):
    """Brief entity information for event responses."""
    entity_id: Optional[str] = Field(None, description="Entity UUID")
    ticker: Optional[str] = Field(None, description="Ticker symbol")
    name: Optional[str] = Field(None, description="Entity name")


class FactEntry(BaseModel):
    """Fact entry from observations."""
    fact_id: str = Field(..., description="Unique fact identifier")
    fact_type: str = Field(..., description="Type of fact")
    label: str = Field(..., description="Human-readable label")
    value: Any = Field(None, description="Fact value")
    unit: Optional[str] = Field(None, description="Value unit")
    source: str = Field("", description="Source name")
    timestamp: Optional[datetime] = Field(None, description="Fact timestamp")


class EventListItem(BaseModel):
    """Event item for list responses."""
    event_id: str = Field(..., description="Event UUID")
    entity_id: Optional[str] = Field(None, description="Primary entity UUID")
    ticker: Optional[str] = Field(None, description="Primary ticker symbol")
    title: str = Field(..., description="Event title")
    event_type: EventTypeResponse = Field(..., description="Event type classification")
    status: EventStatusResponse = Field(..., description="Event status")
    attention_score: float = Field(..., description="Composite attention score (0-100)")
    scores: FourDScores = Field(..., description="4D scores breakdown")
    observation_count: int = Field(..., description="Number of linked observations")
    last_update_at: datetime = Field(..., description="Last update timestamp")
    start_at: datetime = Field(..., description="Event start timestamp")
    pinned: bool = Field(False, description="Whether event is pinned")
    snoozed_until: Optional[datetime] = Field(None, description="Snooze until timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "entity_id": "123e4567-e89b-12d3-a456-426614174001",
                "ticker": "NVDA",
                "title": "NVDA Surges 8% on Strong Earnings Beat",
                "event_type": "market_anomaly",
                "status": "new",
                "attention_score": 85.5,
                "scores": {
                    "anomaly_score": 90.0,
                    "catalyst_score": 80.0,
                    "flow_score": 75.0,
                    "confidence_score": 85.0
                },
                "observation_count": 5,
                "last_update_at": "2026-01-21T10:30:00Z",
                "start_at": "2026-01-21T08:00:00Z",
                "pinned": False,
                "snoozed_until": None
            }
        }


class EventsListResponse(BaseModel):
    """Response for GET /api/events."""
    events: List[EventListItem] = Field(..., description="List of events")
    total_count: int = Field(..., description="Total number of events matching filter")
    offset: int = Field(..., description="Current offset")
    limit: int = Field(..., description="Current limit")

    class Config:
        json_schema_extra = {
            "example": {
                "events": [],
                "total_count": 0,
                "offset": 0,
                "limit": 20
            }
        }


class ObservationSummary(BaseModel):
    """Observation summary for event detail."""
    observation_id: str = Field(..., description="Observation UUID")
    source: str = Field(..., description="Source type")
    title: Optional[str] = Field(None, description="Observation title")
    summary: str = Field("", description="Observation summary")
    timestamp: datetime = Field(..., description="Observation timestamp")
    source_url: Optional[str] = Field(None, description="Source URL")
    fact_entries: List[FactEntry] = Field(default_factory=list, description="Extracted facts")


class EventActionType(str, Enum):
    """Allowed event actions."""
    PIN = "pin"
    UNPIN = "unpin"
    SNOOZE = "snooze"
    DISMISS = "dismiss"
    RESOLVE = "resolve"


class EventActionRequest(BaseModel):
    """Request body for POST /api/events/{event_id}/actions."""
    action: EventActionType = Field(..., description="Action to perform")
    duration_hours: int = Field(24, ge=1, le=168, description="Snooze duration in hours (for snooze action)")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for dismiss action")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "snooze",
                "duration_hours": 24,
                "reason": None
            }
        }


class EventActionResponse(BaseModel):
    """Response for POST /api/events/{event_id}/actions."""
    event_id: str = Field(..., description="Event UUID")
    action: EventActionType = Field(..., description="Action that was performed")
    success: bool = Field(..., description="Whether action succeeded")
    message: str = Field(..., description="Human-readable result message")
    new_status: Optional[EventStatusResponse] = Field(None, description="New event status if changed")
    pinned: Optional[bool] = Field(None, description="New pinned state if changed")
    snoozed_until: Optional[datetime] = Field(None, description="New snooze timestamp if snoozed")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "action": "snooze",
                "success": True,
                "message": "Event snoozed for 24 hours",
                "new_status": None,
                "pinned": None,
                "snoozed_until": "2026-01-22T10:30:00Z"
            }
        }


class EventDetail(BaseModel):
    """Detailed event response for GET /api/events/{event_id}."""
    event_id: str = Field(..., description="Event UUID")
    entity: EntityBrief = Field(..., description="Primary entity information")
    title: str = Field(..., description="Event title")
    event_type: EventTypeResponse = Field(..., description="Event type classification")
    status: EventStatusResponse = Field(..., description="Event status")
    attention_score: float = Field(..., description="Composite attention score (0-100)")
    scores: FourDScores = Field(..., description="4D scores breakdown")

    # Temporal fields
    start_at: datetime = Field(..., description="Event start timestamp")
    last_update_at: datetime = Field(..., description="Last update timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")

    # User actions
    pinned: bool = Field(False, description="Whether event is pinned")
    snoozed_until: Optional[datetime] = Field(None, description="Snooze until timestamp")
    dismissed_reason: Optional[str] = Field(None, description="Dismissal reason")

    # Title metadata
    title_source: str = Field("template", description="Title generation source (llm/template)")

    # Hierarchy
    parent_event_id: Optional[str] = Field(None, description="Parent event UUID if secondary")

    # Observations and facts
    observation_count: int = Field(..., description="Number of linked observations")
    observations: List[ObservationSummary] = Field(default_factory=list, description="Recent observations")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "entity": {
                    "entity_id": "123e4567-e89b-12d3-a456-426614174001",
                    "ticker": "NVDA",
                    "name": "NVIDIA Corporation"
                },
                "title": "NVDA Surges 8% on Strong Earnings Beat",
                "event_type": "market_anomaly",
                "status": "new",
                "attention_score": 85.5,
                "scores": {
                    "anomaly_score": 90.0,
                    "catalyst_score": 80.0,
                    "flow_score": 75.0,
                    "confidence_score": 85.0
                },
                "start_at": "2026-01-21T08:00:00Z",
                "last_update_at": "2026-01-21T10:30:00Z",
                "resolved_at": None,
                "pinned": False,
                "snoozed_until": None,
                "dismissed_reason": None,
                "title_source": "llm",
                "parent_event_id": None,
                "observation_count": 5,
                "observations": []
            }
        }


class TimelineObservation(BaseModel):
    """Observation item for timeline response."""
    observation_id: str = Field(..., description="Observation UUID")
    source: str = Field(..., description="Source type (equities, crypto, news, sec, congress, hedgefund, polymarket)")
    observation_type: str = Field("", description="Specific observation type within source")
    timestamp: datetime = Field(..., description="Observation timestamp (observed_at)")
    title: Optional[str] = Field(None, description="Observation title")
    summary: str = Field("", description="Observation summary")
    fact_entries: List[FactEntry] = Field(default_factory=list, description="Extracted facts")
    source_url: Optional[str] = Field(None, description="Source URL for external link")

    class Config:
        json_schema_extra = {
            "example": {
                "observation_id": "123e4567-e89b-12d3-a456-426614174000",
                "source": "news",
                "observation_type": "article",
                "timestamp": "2026-01-21T10:30:00Z",
                "title": "NVDA Beats Q4 Earnings Expectations",
                "summary": "NVIDIA reported Q4 revenue of $22.1B, beating estimates...",
                "fact_entries": [
                    {
                        "fact_id": "12345678_headline",
                        "fact_type": "headline",
                        "label": "Headline",
                        "value": "NVDA Beats Q4 Earnings Expectations",
                        "unit": None,
                        "source": "news",
                        "timestamp": "2026-01-21T10:30:00Z"
                    }
                ],
                "source_url": "https://example.com/article/123"
            }
        }


class TimelineResponse(BaseModel):
    """Response for GET /api/events/{event_id}/timeline."""
    event_id: str = Field(..., description="Event UUID")
    observations: List[TimelineObservation] = Field(..., description="Observations sorted by timestamp desc")
    total_count: int = Field(..., description="Total number of observations matching filter")
    offset: int = Field(..., description="Current offset")
    limit: int = Field(..., description="Current limit")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "observations": [],
                "total_count": 15,
                "offset": 0,
                "limit": 20
            }
        }
