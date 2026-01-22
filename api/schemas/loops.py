"""
Pydantic schemas for open loops endpoints.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class OpenLoopStatusFilter(str, Enum):
    """Open loop status filter options."""
    ALL = "all"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    STALE = "stale"


class OpenLoopStatusResponse(str, Enum):
    """Open loop status enumeration for API responses."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    STALE = "stale"


class EventSummaryBrief(BaseModel):
    """Brief event summary for open loop responses."""
    event_id: str = Field(..., description="Event UUID")
    title: Optional[str] = Field(None, description="Event title")
    attention_score: Optional[float] = Field(None, description="Event attention score")
    status: Optional[str] = Field(None, description="Event status")


class OpenLoopListItem(BaseModel):
    """Open loop item for list responses."""
    loop_id: str = Field(..., description="Open loop UUID")
    event_id: Optional[str] = Field(None, description="Related event UUID")
    question: str = Field(..., description="The open question/loop")
    created_at: datetime = Field(..., description="Creation timestamp")
    status: OpenLoopStatusResponse = Field(..., description="Loop status")
    progress_notes_count: int = Field(0, description="Number of progress notes")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    event_summary: Optional[EventSummaryBrief] = Field(None, description="Related event summary")

    class Config:
        json_schema_extra = {
            "example": {
                "loop_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_id": "123e4567-e89b-12d3-a456-426614174001",
                "question": "Is there additional corroborating evidence from independent sources?",
                "created_at": "2026-01-21T10:30:00Z",
                "status": "open",
                "progress_notes_count": 2,
                "resolved_at": None,
                "event_summary": {
                    "event_id": "123e4567-e89b-12d3-a456-426614174001",
                    "title": "NVDA Surges 8% on Strong Earnings Beat",
                    "attention_score": 85.5,
                    "status": "new"
                }
            }
        }


class OpenLoopsListResponse(BaseModel):
    """Response for GET /api/loops."""
    loops: List[OpenLoopListItem] = Field(..., description="List of open loops")
    total_count: int = Field(..., description="Total number of loops matching filter")

    class Config:
        json_schema_extra = {
            "example": {
                "loops": [],
                "total_count": 0
            }
        }


class OpenLoopDetail(BaseModel):
    """Detailed open loop response for GET /api/loops/{loop_id}."""
    loop_id: str = Field(..., description="Open loop UUID")
    event_id: Optional[str] = Field(None, description="Related event UUID")
    question: str = Field(..., description="The open question/loop")
    created_at: datetime = Field(..., description="Creation timestamp")
    status: OpenLoopStatusResponse = Field(..., description="Loop status")
    progress_notes: List[str] = Field(default_factory=list, description="Progress notes history")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    event_summary: Optional[EventSummaryBrief] = Field(None, description="Related event summary")

    class Config:
        json_schema_extra = {
            "example": {
                "loop_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_id": "123e4567-e89b-12d3-a456-426614174001",
                "question": "Is there additional corroborating evidence from independent sources?",
                "created_at": "2026-01-21T10:30:00Z",
                "status": "in_progress",
                "progress_notes": [
                    "2026-01-21: Checked SEC filings, no new disclosures found",
                    "2026-01-22: News articles corroborate earnings beat"
                ],
                "resolved_at": None,
                "event_summary": {
                    "event_id": "123e4567-e89b-12d3-a456-426614174001",
                    "title": "NVDA Surges 8% on Strong Earnings Beat",
                    "attention_score": 85.5,
                    "status": "new"
                }
            }
        }


class CreateOpenLoopRequest(BaseModel):
    """Request body for POST /api/loops."""
    question: str = Field(..., min_length=1, max_length=1000, description="The open question to track")
    event_id: Optional[str] = Field(None, description="Related event UUID (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the implications of the Fed rate decision?",
                "event_id": "123e4567-e89b-12d3-a456-426614174001"
            }
        }


class UpdateOpenLoopRequest(BaseModel):
    """Request body for PATCH /api/loops/{loop_id}."""
    status: Optional[OpenLoopStatusResponse] = Field(None, description="New status")
    progress_note: Optional[str] = Field(None, max_length=500, description="Progress note to add")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "in_progress",
                "progress_note": "Found additional SEC filing evidence"
            }
        }


class OpenLoopCreateResponse(BaseModel):
    """Response for POST /api/loops."""
    loop_id: str = Field(..., description="Created loop UUID")
    question: str = Field(..., description="The open question")
    status: OpenLoopStatusResponse = Field(..., description="Initial status")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "loop_id": "123e4567-e89b-12d3-a456-426614174000",
                "question": "What are the implications of the Fed rate decision?",
                "status": "open",
                "created_at": "2026-01-21T10:30:00Z"
            }
        }


class OpenLoopUpdateResponse(BaseModel):
    """Response for PATCH /api/loops/{loop_id}."""
    loop_id: str = Field(..., description="Loop UUID")
    status: OpenLoopStatusResponse = Field(..., description="Current status")
    progress_notes_count: int = Field(..., description="Total number of progress notes")
    updated: bool = Field(..., description="Whether any updates were made")
    message: str = Field(..., description="Human-readable result message")

    class Config:
        json_schema_extra = {
            "example": {
                "loop_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "in_progress",
                "progress_notes_count": 3,
                "updated": True,
                "message": "Status updated to in_progress and progress note added"
            }
        }


class OpenLoopDeleteResponse(BaseModel):
    """Response for DELETE /api/loops/{loop_id}."""
    loop_id: str = Field(..., description="Deleted loop UUID")
    deleted: bool = Field(..., description="Whether deletion succeeded")
    message: str = Field(..., description="Human-readable result message")

    class Config:
        json_schema_extra = {
            "example": {
                "loop_id": "123e4567-e89b-12d3-a456-426614174000",
                "deleted": True,
                "message": "Open loop deleted successfully"
            }
        }
