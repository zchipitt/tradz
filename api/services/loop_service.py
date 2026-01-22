"""
Service layer for open loops API.
"""
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from src.tradz.database import get_database
from src.tradz.models import OpenLoop, OpenLoopStatus


class LoopService:
    """Service for managing open loops."""

    def __init__(self):
        self.db = get_database()

    def get_loops(
        self,
        status_filter: str = "all",
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get open loops with optional status filtering.

        Args:
            status_filter: Filter by status (all, open, in_progress, resolved, stale)

        Returns:
            Tuple of (list of loop dicts with event summaries, total count)
        """
        # Map filter to OpenLoopStatus
        status = None
        if status_filter != "all":
            try:
                status = OpenLoopStatus(status_filter)
            except ValueError:
                pass  # Invalid filter, treat as all

        loops = self.db.get_open_loops(status=status)
        total_count = len(loops)

        # Enrich with event summaries
        result = []
        for loop in loops:
            loop_dict = self._loop_to_dict(loop)

            # Add event summary if event_id exists
            if loop.event_id:
                event_summary = self._get_event_summary(loop.event_id)
                loop_dict["event_summary"] = event_summary
            else:
                loop_dict["event_summary"] = None

            result.append(loop_dict)

        return result, total_count

    def get_loop_by_id(self, loop_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific open loop.

        Args:
            loop_id: The open loop UUID string

        Returns:
            Dictionary with loop details and event summary, or None if not found
        """
        try:
            loop_uuid = UUID(loop_id)
        except ValueError:
            return None

        loop = self.db.get_open_loop_by_id(loop_uuid)
        if loop is None:
            return None

        loop_dict = self._loop_to_detail_dict(loop)

        # Add event summary if event_id exists
        if loop.event_id:
            event_summary = self._get_event_summary(loop.event_id)
            loop_dict["event_summary"] = event_summary
        else:
            loop_dict["event_summary"] = None

        return loop_dict

    def create_loop(
        self,
        question: str,
        event_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new open loop.

        Args:
            question: The open question to track
            event_id: Optional related event UUID string

        Returns:
            Dictionary with created loop details

        Raises:
            ValueError: If event_id is invalid or event not found
        """
        # Validate event_id if provided
        event_uuid = None
        if event_id:
            try:
                event_uuid = UUID(event_id)
            except ValueError:
                raise ValueError(f"Invalid event_id format: {event_id}")

            # Check if event exists
            event = self.db.get_event_by_id(event_uuid)
            if event is None:
                raise ValueError(f"Event {event_id} not found")

        # Create the open loop
        loop = OpenLoop(
            event_id=event_uuid,
            question=question,
            status=OpenLoopStatus.OPEN,
        )

        loop_id = self.db.insert_open_loop(loop)

        return {
            "loop_id": loop_id,
            "question": loop.question,
            "status": loop.status.value,
            "created_at": loop.created_at.isoformat(),
        }

    def update_loop(
        self,
        loop_id: str,
        status: Optional[str] = None,
        progress_note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an open loop's status or add a progress note.

        Args:
            loop_id: The open loop UUID string
            status: New status (optional)
            progress_note: Progress note to add (optional)

        Returns:
            Dictionary with update result

        Raises:
            ValueError: If loop not found or invalid status
        """
        try:
            loop_uuid = UUID(loop_id)
        except ValueError:
            raise ValueError(f"Invalid loop_id format: {loop_id}")

        # Check if loop exists
        loop = self.db.get_open_loop_by_id(loop_uuid)
        if loop is None:
            raise ValueError(f"Open loop {loop_id} not found")

        updates_made = []
        current_status = loop.status
        current_notes_count = len(loop.progress_notes)

        # Update status if provided
        if status:
            try:
                new_status = OpenLoopStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}")

            success = self.db.update_open_loop_status(loop_uuid, new_status)
            if success:
                current_status = new_status
                updates_made.append(f"Status updated to {status}")

        # Add progress note if provided
        if progress_note:
            success = self.db.add_progress_note(loop_uuid, progress_note)
            if success:
                current_notes_count += 1
                updates_made.append("Progress note added")

        updated = len(updates_made) > 0
        message = " and ".join(updates_made) if updated else "No updates made"

        return {
            "loop_id": loop_id,
            "status": current_status.value,
            "progress_notes_count": current_notes_count,
            "updated": updated,
            "message": message,
        }

    def delete_loop(self, loop_id: str) -> Dict[str, Any]:
        """
        Delete an open loop.

        Args:
            loop_id: The open loop UUID string

        Returns:
            Dictionary with deletion result

        Raises:
            ValueError: If loop not found
        """
        try:
            loop_uuid = UUID(loop_id)
        except ValueError:
            raise ValueError(f"Invalid loop_id format: {loop_id}")

        # Check if loop exists
        loop = self.db.get_open_loop_by_id(loop_uuid)
        if loop is None:
            raise ValueError(f"Open loop {loop_id} not found")

        deleted = self.db.delete_open_loop(loop_uuid)

        return {
            "loop_id": loop_id,
            "deleted": deleted,
            "message": "Open loop deleted successfully" if deleted else "Failed to delete open loop",
        }

    def _loop_to_dict(self, loop: OpenLoop) -> Dict[str, Any]:
        """Convert OpenLoop to list item dictionary."""
        return {
            "loop_id": str(loop.id),
            "event_id": str(loop.event_id) if loop.event_id else None,
            "question": loop.question,
            "created_at": loop.created_at.isoformat(),
            "status": loop.status.value,
            "progress_notes_count": len(loop.progress_notes),
            "resolved_at": loop.resolved_at.isoformat() if loop.resolved_at else None,
        }

    def _loop_to_detail_dict(self, loop: OpenLoop) -> Dict[str, Any]:
        """Convert OpenLoop to detail dictionary with full progress notes."""
        return {
            "loop_id": str(loop.id),
            "event_id": str(loop.event_id) if loop.event_id else None,
            "question": loop.question,
            "created_at": loop.created_at.isoformat(),
            "status": loop.status.value,
            "progress_notes": loop.progress_notes,
            "resolved_at": loop.resolved_at.isoformat() if loop.resolved_at else None,
        }

    def _get_event_summary(self, event_id: UUID) -> Optional[Dict[str, Any]]:
        """Get brief event summary for enriching loop responses."""
        event = self.db.get_event_by_id(event_id)
        if event is None:
            return None

        return {
            "event_id": str(event.id),
            "title": event.title,
            "attention_score": event.attention_score,
            "status": event.status.value if event.status else None,
        }


# Singleton instance
loop_service = LoopService()
