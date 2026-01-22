"""
Events router for event-driven trading signal endpoints.
"""
from fastapi import APIRouter, HTTPException, Query

from api.schemas.events import (
    EventStatusFilter,
    EventSortBy,
    EventListItem,
    EventsListResponse,
    EventDetail,
    FourDScores,
    EntityBrief,
    ObservationSummary,
    FactEntry,
    EventTypeResponse,
    EventStatusResponse,
    EventActionType,
    EventActionRequest,
    EventActionResponse,
)
from api.services.event_service import event_service

router = APIRouter()


@router.get("", response_model=EventsListResponse)
async def get_events(
    status: EventStatusFilter = Query(
        EventStatusFilter.ACTIVE,
        description="Filter by status: active (new+ongoing), resolved, dismissed, all"
    ),
    sort: EventSortBy = Query(
        EventSortBy.ATTENTION_SCORE,
        description="Sort by: attention_score (default), last_update_at, start_at"
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of events to return (1-100)"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of events to skip for pagination"
    ),
) -> EventsListResponse:
    """
    Get list of events with filtering, sorting, and pagination.

    Returns events matching the specified filters, sorted by the specified field.
    Active status includes events with status 'new' or 'ongoing' that are not snoozed.
    """
    try:
        events_data, total_count = event_service.get_events(
            status_filter=status.value,
            sort_by=sort.value,
            limit=limit,
            offset=offset,
        )

        events = []
        for event_dict in events_data:
            event_item = EventListItem(
                event_id=event_dict["event_id"],
                entity_id=event_dict.get("entity_id"),
                ticker=event_dict.get("ticker"),
                title=event_dict["title"],
                event_type=EventTypeResponse(event_dict["event_type"]),
                status=EventStatusResponse(event_dict["status"]),
                attention_score=event_dict["attention_score"],
                scores=FourDScores(**event_dict["scores"]),
                observation_count=event_dict["observation_count"],
                last_update_at=event_dict["last_update_at"],
                start_at=event_dict["start_at"],
                pinned=event_dict.get("pinned", False),
                snoozed_until=event_dict.get("snoozed_until"),
            )
            events.append(event_item)

        return EventsListResponse(
            events=events,
            total_count=total_count,
            offset=offset,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}", response_model=EventDetail)
async def get_event_by_id(event_id: str) -> EventDetail:
    """
    Get detailed information about a specific event.

    Returns event details including linked observations, facts, and entity information.
    """
    try:
        event_dict = event_service.get_event_by_id(event_id)

        if event_dict is None:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

        # Convert observations to ObservationSummary
        observations = []
        for obs_dict in event_dict.get("observations", []):
            fact_entries = [
                FactEntry(**fact) for fact in obs_dict.get("fact_entries", [])
            ]
            obs_summary = ObservationSummary(
                observation_id=obs_dict["observation_id"],
                source=obs_dict["source"],
                title=obs_dict.get("title"),
                summary=obs_dict.get("summary", ""),
                timestamp=obs_dict["timestamp"],
                source_url=obs_dict.get("source_url"),
                fact_entries=fact_entries,
            )
            observations.append(obs_summary)

        # Build entity brief
        entity_data = event_dict.get("entity", {})
        entity = EntityBrief(
            entity_id=entity_data.get("entity_id"),
            ticker=entity_data.get("ticker"),
            name=entity_data.get("name"),
        )

        return EventDetail(
            event_id=event_dict["event_id"],
            entity=entity,
            title=event_dict["title"],
            event_type=EventTypeResponse(event_dict["event_type"]),
            status=EventStatusResponse(event_dict["status"]),
            attention_score=event_dict["attention_score"],
            scores=FourDScores(**event_dict["scores"]),
            start_at=event_dict["start_at"],
            last_update_at=event_dict["last_update_at"],
            resolved_at=event_dict.get("resolved_at"),
            pinned=event_dict.get("pinned", False),
            snoozed_until=event_dict.get("snoozed_until"),
            dismissed_reason=event_dict.get("dismissed_reason"),
            title_source=event_dict.get("title_source", "template"),
            parent_event_id=event_dict.get("parent_event_id"),
            observation_count=event_dict["observation_count"],
            observations=observations,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{event_id}/actions", response_model=EventActionResponse)
async def perform_event_action(
    event_id: str,
    request: EventActionRequest,
) -> EventActionResponse:
    """
    Perform an action on an event.

    Supported actions:
    - pin: Pin event to top of list
    - unpin: Remove pin from event
    - snooze: Hide event for specified duration (default 24h)
    - dismiss: Mark event as dismissed with optional reason
    - resolve: Mark event as resolved
    """
    try:
        result = event_service.perform_action(
            event_id=event_id,
            action=request.action.value,
            duration_hours=request.duration_hours,
            reason=request.reason,
        )

        return EventActionResponse(
            event_id=result["event_id"],
            action=EventActionType(result["action"]),
            success=result["success"],
            message=result["message"],
            new_status=EventStatusResponse(result["new_status"]) if result.get("new_status") else None,
            pinned=result.get("pinned"),
            snoozed_until=result.get("snoozed_until"),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
