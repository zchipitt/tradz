"""
Open Loops router for tracking unresolved questions.
"""
from fastapi import APIRouter, HTTPException, Query

from api.schemas.loops import (
    OpenLoopStatusFilter,
    OpenLoopStatusResponse,
    EventSummaryBrief,
    OpenLoopListItem,
    OpenLoopsListResponse,
    OpenLoopDetail,
    CreateOpenLoopRequest,
    UpdateOpenLoopRequest,
    OpenLoopCreateResponse,
    OpenLoopUpdateResponse,
    OpenLoopDeleteResponse,
)
from api.services.loop_service import loop_service

router = APIRouter()


@router.get("", response_model=OpenLoopsListResponse)
async def get_loops(
    status: OpenLoopStatusFilter = Query(
        OpenLoopStatusFilter.ALL,
        description="Filter by status: all, open, in_progress, resolved, stale"
    ),
) -> OpenLoopsListResponse:
    """
    Get all open loops with optional status filtering.

    Returns list of open loops sorted by creation date (newest first).
    Includes related event summary for each loop if linked to an event.
    """
    try:
        loops_data, total_count = loop_service.get_loops(status_filter=status.value)

        loops = []
        for loop_dict in loops_data:
            # Build event summary if present
            event_summary = None
            if loop_dict.get("event_summary"):
                es = loop_dict["event_summary"]
                event_summary = EventSummaryBrief(
                    event_id=es["event_id"],
                    title=es.get("title"),
                    attention_score=es.get("attention_score"),
                    status=es.get("status"),
                )

            loop_item = OpenLoopListItem(
                loop_id=loop_dict["loop_id"],
                event_id=loop_dict.get("event_id"),
                question=loop_dict["question"],
                created_at=loop_dict["created_at"],
                status=OpenLoopStatusResponse(loop_dict["status"]),
                progress_notes_count=loop_dict.get("progress_notes_count", 0),
                resolved_at=loop_dict.get("resolved_at"),
                event_summary=event_summary,
            )
            loops.append(loop_item)

        return OpenLoopsListResponse(
            loops=loops,
            total_count=total_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{loop_id}", response_model=OpenLoopDetail)
async def get_loop_by_id(loop_id: str) -> OpenLoopDetail:
    """
    Get detailed information about a specific open loop.

    Returns loop details including full progress notes history and
    related event summary if linked to an event.
    """
    try:
        loop_dict = loop_service.get_loop_by_id(loop_id)

        if loop_dict is None:
            raise HTTPException(status_code=404, detail=f"Open loop {loop_id} not found")

        # Build event summary if present
        event_summary = None
        if loop_dict.get("event_summary"):
            es = loop_dict["event_summary"]
            event_summary = EventSummaryBrief(
                event_id=es["event_id"],
                title=es.get("title"),
                attention_score=es.get("attention_score"),
                status=es.get("status"),
            )

        return OpenLoopDetail(
            loop_id=loop_dict["loop_id"],
            event_id=loop_dict.get("event_id"),
            question=loop_dict["question"],
            created_at=loop_dict["created_at"],
            status=OpenLoopStatusResponse(loop_dict["status"]),
            progress_notes=loop_dict.get("progress_notes", []),
            resolved_at=loop_dict.get("resolved_at"),
            event_summary=event_summary,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=OpenLoopCreateResponse)
async def create_loop(request: CreateOpenLoopRequest) -> OpenLoopCreateResponse:
    """
    Create a new open loop manually.

    An open loop tracks an unresolved question that may require further
    research or monitoring. Can optionally be linked to an event.
    """
    try:
        result = loop_service.create_loop(
            question=request.question,
            event_id=request.event_id,
        )

        return OpenLoopCreateResponse(
            loop_id=result["loop_id"],
            question=result["question"],
            status=OpenLoopStatusResponse(result["status"]),
            created_at=result["created_at"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{loop_id}", response_model=OpenLoopUpdateResponse)
async def update_loop(
    loop_id: str,
    request: UpdateOpenLoopRequest,
) -> OpenLoopUpdateResponse:
    """
    Update an open loop's status or add a progress note.

    Use this to:
    - Change status (open -> in_progress -> resolved)
    - Add progress notes to track research progress
    - Mark a loop as resolved when the question is answered
    """
    try:
        result = loop_service.update_loop(
            loop_id=loop_id,
            status=request.status.value if request.status else None,
            progress_note=request.progress_note,
        )

        return OpenLoopUpdateResponse(
            loop_id=result["loop_id"],
            status=OpenLoopStatusResponse(result["status"]),
            progress_notes_count=result["progress_notes_count"],
            updated=result["updated"],
            message=result["message"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{loop_id}", response_model=OpenLoopDeleteResponse)
async def delete_loop(loop_id: str) -> OpenLoopDeleteResponse:
    """
    Delete an open loop.

    Permanently removes the open loop and all its progress notes.
    This action cannot be undone.
    """
    try:
        result = loop_service.delete_loop(loop_id)

        return OpenLoopDeleteResponse(
            loop_id=result["loop_id"],
            deleted=result["deleted"],
            message=result["message"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
