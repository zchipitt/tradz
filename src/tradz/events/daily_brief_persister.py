"""
Daily brief persistence module.

Provides:
- DailyBriefPersister: Saves daily briefs to files and database
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from ..database import Database, get_database
from ..models import DailyBrief
from .daily_brief_generator import DailyBriefContent

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass
class PersistenceResult:
    """Result of daily brief persistence operation."""
    success: bool
    brief_id: str
    date: str
    report_path_md: Optional[str] = None
    report_path_json: Optional[str] = None
    db_updated: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "brief_id": self.brief_id,
            "date": self.date,
            "report_path_md": self.report_path_md,
            "report_path_json": self.report_path_json,
            "db_updated": self.db_updated,
            "error": self.error,
        }


class DailyBriefPersister:
    """
    Persists daily briefs to files and database.

    Provides:
    - save_to_files(): Save MD and JSON reports to reports/{date}.md and .json
    - save_to_database(): Insert/update record in daily_briefs table
    - persist(): Combined operation for both file and database persistence

    File paths use ISO date format: YYYY-MM-DD
    Idempotent: regenerating same date overwrites files and updates DB record
    """

    def __init__(
        self,
        reports_dir: str = "reports",
        db: Optional[Database] = None,
    ):
        """
        Initialize DailyBriefPersister.

        Args:
            reports_dir: Directory for storing report files.
            db: Optional database instance. Uses get_database() if not provided.
        """
        self.reports_dir = Path(reports_dir)
        self._db = db

    @property
    def db(self) -> Database:
        """Lazily get database instance."""
        if self._db is None:
            self._db = get_database()
        return self._db

    def persist(
        self,
        content: DailyBriefContent,
        run_id: Optional[str] = None,
        brief_id: Optional[UUID] = None,
    ) -> PersistenceResult:
        """
        Persist daily brief to both files and database.

        This is the main entry point for persistence. It:
        1. Saves markdown report to reports/{date}.md
        2. Saves JSON data to reports/{date}.json
        3. Inserts/updates record in daily_briefs table

        Args:
            content: DailyBriefContent to persist.
            run_id: Optional run_id to link to run_history table.
            brief_id: Optional UUID for the brief. Generated if not provided.

        Returns:
            PersistenceResult with paths and status.
        """
        date_str = self._get_date_string(content.date)
        brief_id = brief_id or uuid4()

        logger.info(f"Persisting daily brief for {date_str} (brief_id={brief_id})")

        result = PersistenceResult(
            success=False,
            brief_id=str(brief_id),
            date=date_str,
        )

        try:
            # Save files
            file_result = self.save_to_files(content, brief_id)
            result.report_path_md = file_result.get("report_path_md")
            result.report_path_json = file_result.get("report_path_json")

            # Save to database
            db_result = self.save_to_database(
                content=content,
                brief_id=brief_id,
                run_id=run_id,
                report_path_md=result.report_path_md,
                report_path_json=result.report_path_json,
            )
            result.db_updated = db_result

            result.success = True
            logger.info(
                f"Daily brief persisted: md={result.report_path_md}, "
                f"json={result.report_path_json}, db={result.db_updated}"
            )

        except Exception as e:
            result.error = str(e)
            logger.error(f"Failed to persist daily brief: {e}")

        return result

    def save_to_files(
        self,
        content: DailyBriefContent,
        brief_id: Optional[UUID] = None,
    ) -> Dict[str, str]:
        """
        Save daily brief to markdown and JSON files.

        Files are saved to:
        - reports/{date}.md - Markdown report
        - reports/{date}.json - JSON data

        Args:
            content: DailyBriefContent to save.
            brief_id: Optional brief ID for metadata.

        Returns:
            Dict with 'report_path_md' and 'report_path_json' keys.
        """
        date_str = self._get_date_string(content.date)

        # Ensure reports directory exists
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Generate file paths
        md_path = self.reports_dir / f"{date_str}.md"
        json_path = self.reports_dir / f"{date_str}.json"

        # Generate markdown content
        markdown = self._render_markdown(content, brief_id)

        # Generate JSON content
        json_data = self._prepare_json(content, brief_id)

        # Write files (overwrites existing - idempotent)
        md_path.write_text(markdown, encoding="utf-8")
        logger.debug(f"Saved markdown report to {md_path}")

        json_path.write_text(
            json.dumps(json_data, indent=2, default=str),
            encoding="utf-8"
        )
        logger.debug(f"Saved JSON data to {json_path}")

        return {
            "report_path_md": str(md_path),
            "report_path_json": str(json_path),
        }

    def save_to_database(
        self,
        content: DailyBriefContent,
        brief_id: UUID,
        run_id: Optional[str] = None,
        report_path_md: Optional[str] = None,
        report_path_json: Optional[str] = None,
    ) -> bool:
        """
        Save daily brief to database.

        Uses INSERT ... ON CONFLICT DO UPDATE for idempotent behavior.
        If a record exists for the same date, it will be updated.

        Args:
            content: DailyBriefContent to save.
            brief_id: UUID for the brief record.
            run_id: Optional run_id to link to run_history.
            report_path_md: Path to markdown report file.
            report_path_json: Path to JSON data file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create DailyBrief model
            brief = DailyBrief(
                id=brief_id,
                date=content.date,
                summary_json=content.to_dict(),
                report_path_md=report_path_md,
                report_path_json=report_path_json,
                generation_method=content.generation_method,
                created_at=_utcnow(),
                run_id=run_id,
            )

            # Insert/update via database method
            self.db.insert_daily_brief(brief)
            logger.debug(f"Saved daily brief to database: id={brief_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to save daily brief to database: {e}")
            raise

    def _get_date_string(self, date: datetime) -> str:
        """
        Get ISO date string from datetime.

        Args:
            date: Datetime to convert.

        Returns:
            Date string in YYYY-MM-DD format.
        """
        return date.strftime("%Y-%m-%d")

    def _render_markdown(
        self,
        content: DailyBriefContent,
        brief_id: Optional[UUID] = None,
    ) -> str:
        """
        Render DailyBriefContent as markdown report.

        Args:
            content: Content to render.
            brief_id: Optional brief ID for metadata.

        Returns:
            Markdown string.
        """
        date_str = self._get_date_string(content.date)
        lines = []

        # Header
        lines.append(f"# Tradz Daily Brief - {date_str}\n")
        lines.append(f"*Generated at {_utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*")
        if brief_id:
            lines.append(f"*Brief ID: {brief_id}*")
        lines.append(f"*Generation method: {content.generation_method}*\n")
        lines.append("---\n")

        # Executive Summary
        lines.append("## Executive Summary\n")
        if content.executive_summary:
            lines.append(content.executive_summary)
        else:
            lines.append("*No executive summary generated.*")
        lines.append("\n---\n")

        # Top Events
        lines.append("## Top Events\n")
        if content.top_events:
            for i, event in enumerate(content.top_events, 1):
                lines.append(f"### {i}. {event.title}\n")
                lines.append(f"- **Ticker**: {event.ticker or 'N/A'}")
                lines.append(f"- **Event Type**: {event.event_type}")
                lines.append(f"- **Attention Score**: {event.attention_score:.0f}")
                lines.append(f"- **4D Scores**: Anomaly={event.anomaly_score:.0f}, "
                           f"Catalyst={event.catalyst_score:.0f}, "
                           f"Flow={event.flow_score:.0f}, "
                           f"Confidence={event.confidence_score:.0f}")
                lines.append(f"- **Observations**: {event.observation_count}")
                if event.last_update_at:
                    lines.append(f"- **Last Update**: {event.last_update_at.strftime('%Y-%m-%d %H:%M')}")
                lines.append("")
        else:
            lines.append("*No events to report.*\n")
        lines.append("---\n")

        # Trade Ideas
        lines.append("## Trade Ideas\n")
        if content.trade_ideas:
            for idea in content.trade_ideas:
                lines.append(f"### {idea.ticker or 'Unknown'} - {idea.direction.upper()}\n")
                lines.append(f"- **Entry Zone**: {idea.entry_zone}")
                lines.append(f"- **Target**: {idea.target}")
                lines.append(f"- **Stop Loss**: {idea.stop_loss}")
                lines.append(f"- **Confidence**: {idea.confidence_level:.0f}%")
                lines.append(f"- **Rationale**: {idea.rationale}")
                lines.append("")
        else:
            lines.append("*No trade ideas - events did not pass quality gates.*\n")
        lines.append("---\n")

        # Research Ideas
        lines.append("## Research Ideas\n")
        if content.research_ideas:
            for idea in content.research_ideas:
                lines.append(f"### {idea.ticker or 'Unknown'}\n")
                lines.append(f"- **Current Score**: {idea.current_score:.0f}")
                lines.append(f"- **Potential Score**: {idea.potential_score:.0f}")
                lines.append("- **Questions to Verify**:")
                for q in idea.questions:
                    lines.append(f"  - {q}")
                lines.append("- **Evidence to Watch**:")
                for e in idea.evidence_to_watch:
                    lines.append(f"  - {e}")
                lines.append("")
        else:
            lines.append("*No research ideas identified.*\n")
        lines.append("---\n")

        # Open Loops
        lines.append("## Open Loops\n")
        if content.open_loops:
            for loop in content.open_loops:
                status_emoji = {"open": "\u2b55", "in_progress": "\U0001f534", "resolved": "\u2705"}.get(loop.status, "\u2754")
                lines.append(f"- {status_emoji} [{loop.status}] {loop.question}")
                if loop.event_id:
                    lines.append(f"  - Related event: {loop.event_id}")
        else:
            lines.append("*No open loops to track.*\n")
        lines.append("---\n")

        # Data Quality
        lines.append("## Data Quality\n")
        if content.data_quality:
            dq = content.data_quality
            lines.append(f"**Overall Status**: {dq.overall_status.upper()}\n")
            lines.append(f"{dq.quality_message}\n")
            lines.append(f"- Healthy Sources: {dq.healthy_count}/{dq.total_sources}")
            if dq.degraded_count > 0:
                lines.append(f"- Degraded Sources: {dq.degraded_count}")
            if dq.error_count > 0:
                lines.append(f"- Error Sources: {dq.error_count}")
            lines.append("\n| Source | Status | Records (24h) | Freshness |")
            lines.append("|--------|--------|---------------|-----------|")
            for src in dq.sources:
                status_icon = {"ok": "\u2705", "degraded": "\u26a0\ufe0f", "error": "\u274c"}.get(src.status, "\u2754")
                lines.append(f"| {src.display_name} | {status_icon} {src.status} | {src.record_count_24h} | {src.freshness_indicator} |")
        else:
            lines.append("*Data quality information not available.*\n")
        lines.append("\n---\n")

        # Footer
        lines.append(f"\n*Report generated by tradz automated system.*")

        return "\n".join(lines)

    def _prepare_json(
        self,
        content: DailyBriefContent,
        brief_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Prepare JSON data for file storage.

        Args:
            content: Content to serialize.
            brief_id: Optional brief ID for metadata.

        Returns:
            Dict suitable for JSON serialization.
        """
        data = content.to_dict()
        data["metadata"] = {
            "brief_id": str(brief_id) if brief_id else None,
            "generated_at": _utcnow().isoformat(),
            "version": "1.0",
        }
        return data
