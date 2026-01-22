"""
Tests for DailyBriefPersister class.

Tests cover:
- File persistence (markdown and JSON)
- Database persistence
- Idempotent behavior (overwrite on regeneration)
- Error handling
"""
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.tradz.events.daily_brief_generator import (
    DailyBriefContent,
    DataQualitySummary,
    EventSummary,
    OpenLoop,
    ResearchIdeaSummary,
    SourceHealthSummary,
    TradeIdeaSummary,
)
from src.tradz.events.daily_brief_persister import (
    DailyBriefPersister,
    PersistenceResult,
)


def _utcnow() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def create_sample_content(date: Optional[datetime] = None) -> DailyBriefContent:
    """Create sample DailyBriefContent for testing."""
    actual_date = date if date is not None else _utcnow()

    return DailyBriefContent(
        date=actual_date,
        executive_summary="Today's top signal is AAPL with attention score 85. Additional notable activity in TSLA. High conviction signals suggest reviewing trade ideas.",
        top_events=[
            EventSummary(
                event_id="event-001",
                title="AAPL Surges 8% on Earnings Beat",
                ticker="AAPL",
                event_type="market_anomaly",
                attention_score=85.0,
                anomaly_score=90.0,
                catalyst_score=80.0,
                flow_score=70.0,
                confidence_score=85.0,
                observation_count=5,
                last_update_at=actual_date,
            ),
            EventSummary(
                event_id="event-002",
                title="TSLA Volume Spike Detected",
                ticker="TSLA",
                event_type="flow_congress",
                attention_score=72.0,
                anomaly_score=65.0,
                catalyst_score=60.0,
                flow_score=80.0,
                confidence_score=70.0,
                observation_count=3,
                last_update_at=actual_date,
            ),
        ],
        trade_ideas=[
            TradeIdeaSummary(
                event_id="event-001",
                ticker="AAPL",
                direction="long",
                entry_zone="$175-180",
                target="$200",
                stop_loss="$165",
                confidence_level=85.0,
                rationale="Strong earnings beat with positive guidance",
            ),
        ],
        research_ideas=[
            ResearchIdeaSummary(
                event_id="event-002",
                ticker="TSLA",
                questions=["What drove the volume spike?", "Is this institutional buying?"],
                evidence_to_watch=["Upcoming earnings", "Production numbers"],
                current_score=72.0,
                potential_score=85.0,
            ),
        ],
        open_loops=[
            OpenLoop(
                loop_id="loop-001",
                event_id="event-002",
                question="What drove the volume spike?",
                created_at=actual_date,
                status="open",
            ),
        ],
        data_quality=DataQualitySummary(
            total_sources=7,
            healthy_count=6,
            degraded_count=1,
            error_count=0,
            sources=[
                SourceHealthSummary(
                    name="equities",
                    display_name="Equities",
                    status="ok",
                    record_count_24h=100,
                    freshness_indicator="fresh",
                ),
                SourceHealthSummary(
                    name="crypto",
                    display_name="Crypto",
                    status="degraded",
                    record_count_24h=50,
                    freshness_indicator="stale",
                ),
            ],
            overall_status="degraded",
            quality_message="1 source(s) have stale data. Some signals may be outdated.",
        ),
        generation_method="template",
    )


def create_minimal_content(date: Optional[datetime] = None) -> DailyBriefContent:
    """Create minimal DailyBriefContent for testing."""
    actual_date = date if date is not None else _utcnow()

    return DailyBriefContent(
        date=actual_date,
        executive_summary="No significant events to report.",
        generation_method="template",
    )


class TestPersistenceResult:
    """Tests for PersistenceResult dataclass."""

    def test_to_dict(self):
        """Test PersistenceResult.to_dict() serialization."""
        result = PersistenceResult(
            success=True,
            brief_id="test-id",
            date="2024-01-21",
            report_path_md="/path/to/report.md",
            report_path_json="/path/to/report.json",
            db_updated=True,
            error=None,
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["brief_id"] == "test-id"
        assert data["date"] == "2024-01-21"
        assert data["report_path_md"] == "/path/to/report.md"
        assert data["report_path_json"] == "/path/to/report.json"
        assert data["db_updated"] is True
        assert data["error"] is None

    def test_to_dict_with_error(self):
        """Test PersistenceResult.to_dict() with error."""
        result = PersistenceResult(
            success=False,
            brief_id="test-id",
            date="2024-01-21",
            error="File write failed",
        )

        data = result.to_dict()

        assert data["success"] is False
        assert data["error"] == "File write failed"


class TestDailyBriefPersister:
    """Tests for DailyBriefPersister class."""

    def test_init_default(self):
        """Test default initialization."""
        persister = DailyBriefPersister()

        assert persister.reports_dir == Path("reports")
        assert persister._db is None

    def test_init_custom_dir(self):
        """Test initialization with custom directory."""
        persister = DailyBriefPersister(reports_dir="custom/reports")

        assert persister.reports_dir == Path("custom/reports")

    def test_init_with_db(self):
        """Test initialization with database instance."""
        mock_db = MagicMock()
        persister = DailyBriefPersister(db=mock_db)

        assert persister._db is mock_db

    def test_get_date_string(self):
        """Test date string extraction."""
        persister = DailyBriefPersister()
        date = datetime(2024, 1, 21, 12, 30, 45, tzinfo=timezone.utc)

        result = persister._get_date_string(date)

        assert result == "2024-01-21"


class TestSaveToFiles:
    """Tests for save_to_files() method."""

    def test_save_creates_directory(self):
        """Test that save_to_files creates reports directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir) / "reports"
            persister = DailyBriefPersister(reports_dir=str(reports_dir))
            content = create_minimal_content()

            persister.save_to_files(content)

            assert reports_dir.exists()

    def test_save_creates_md_file(self):
        """Test that save_to_files creates markdown file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            date = datetime(2024, 1, 21, tzinfo=timezone.utc)
            content = create_sample_content(date)

            result = persister.save_to_files(content)

            md_path = Path(result["report_path_md"])
            assert md_path.exists()
            assert md_path.name == "2024-01-21.md"

    def test_save_creates_json_file(self):
        """Test that save_to_files creates JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            date = datetime(2024, 1, 21, tzinfo=timezone.utc)
            content = create_sample_content(date)

            result = persister.save_to_files(content)

            json_path = Path(result["report_path_json"])
            assert json_path.exists()
            assert json_path.name == "2024-01-21.json"

    def test_md_file_contains_header(self):
        """Test that markdown file contains proper header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            date = datetime(2024, 1, 21, tzinfo=timezone.utc)
            content = create_sample_content(date)

            result = persister.save_to_files(content)

            md_content = Path(result["report_path_md"]).read_text()
            assert "# Tradz Daily Brief - 2024-01-21" in md_content
            assert "Generation method: template" in md_content

    def test_md_file_contains_executive_summary(self):
        """Test that markdown file contains executive summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            content = create_sample_content()

            result = persister.save_to_files(content)

            md_content = Path(result["report_path_md"]).read_text()
            assert "## Executive Summary" in md_content
            assert "Today's top signal is AAPL" in md_content

    def test_md_file_contains_top_events(self):
        """Test that markdown file contains top events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            content = create_sample_content()

            result = persister.save_to_files(content)

            md_content = Path(result["report_path_md"]).read_text()
            assert "## Top Events" in md_content
            assert "AAPL Surges 8% on Earnings Beat" in md_content
            assert "TSLA Volume Spike Detected" in md_content

    def test_md_file_contains_trade_ideas(self):
        """Test that markdown file contains trade ideas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            content = create_sample_content()

            result = persister.save_to_files(content)

            md_content = Path(result["report_path_md"]).read_text()
            assert "## Trade Ideas" in md_content
            assert "Entry Zone" in md_content
            assert "$175-180" in md_content

    def test_md_file_contains_research_ideas(self):
        """Test that markdown file contains research ideas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            content = create_sample_content()

            result = persister.save_to_files(content)

            md_content = Path(result["report_path_md"]).read_text()
            assert "## Research Ideas" in md_content
            assert "Questions to Verify" in md_content
            assert "What drove the volume spike?" in md_content

    def test_md_file_contains_open_loops(self):
        """Test that markdown file contains open loops."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            content = create_sample_content()

            result = persister.save_to_files(content)

            md_content = Path(result["report_path_md"]).read_text()
            assert "## Open Loops" in md_content

    def test_md_file_contains_data_quality(self):
        """Test that markdown file contains data quality section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            content = create_sample_content()

            result = persister.save_to_files(content)

            md_content = Path(result["report_path_md"]).read_text()
            assert "## Data Quality" in md_content
            assert "DEGRADED" in md_content
            assert "Equities" in md_content

    def test_json_file_is_valid(self):
        """Test that JSON file contains valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            content = create_sample_content()

            result = persister.save_to_files(content)

            json_content = Path(result["report_path_json"]).read_text()
            data = json.loads(json_content)

            assert "executive_summary" in data
            assert "top_events" in data
            assert "metadata" in data

    def test_json_file_contains_metadata(self):
        """Test that JSON file contains metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            content = create_sample_content()
            brief_id = uuid4()

            result = persister.save_to_files(content, brief_id=brief_id)

            json_content = Path(result["report_path_json"]).read_text()
            data = json.loads(json_content)

            assert data["metadata"]["brief_id"] == str(brief_id)
            assert "generated_at" in data["metadata"]
            assert data["metadata"]["version"] == "1.0"

    def test_save_overwrites_existing_files(self):
        """Test idempotent behavior - files are overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            date = datetime(2024, 1, 21, tzinfo=timezone.utc)

            # First save
            content1 = create_minimal_content(date)
            content1.executive_summary = "First summary"
            persister.save_to_files(content1)

            # Second save with different content
            content2 = create_minimal_content(date)
            content2.executive_summary = "Second summary"
            result = persister.save_to_files(content2)

            # Verify content was overwritten
            md_content = Path(result["report_path_md"]).read_text()
            assert "Second summary" in md_content
            assert "First summary" not in md_content


class TestSaveToDatabase:
    """Tests for save_to_database() method."""

    def test_save_calls_insert_daily_brief(self):
        """Test that save_to_database calls database insert method."""
        mock_db = MagicMock()
        persister = DailyBriefPersister(db=mock_db)
        content = create_minimal_content()
        brief_id = uuid4()

        persister.save_to_database(content, brief_id)

        mock_db.insert_daily_brief.assert_called_once()

    def test_save_passes_correct_brief_id(self):
        """Test that brief_id is passed correctly to database."""
        mock_db = MagicMock()
        persister = DailyBriefPersister(db=mock_db)
        content = create_minimal_content()
        brief_id = uuid4()

        persister.save_to_database(content, brief_id)

        call_args = mock_db.insert_daily_brief.call_args[0][0]
        assert call_args.id == brief_id

    def test_save_passes_run_id(self):
        """Test that run_id is passed correctly to database."""
        mock_db = MagicMock()
        persister = DailyBriefPersister(db=mock_db)
        content = create_minimal_content()
        brief_id = uuid4()
        run_id = "run-123"

        persister.save_to_database(content, brief_id, run_id=run_id)

        call_args = mock_db.insert_daily_brief.call_args[0][0]
        assert call_args.run_id == run_id

    def test_save_passes_file_paths(self):
        """Test that file paths are passed correctly to database."""
        mock_db = MagicMock()
        persister = DailyBriefPersister(db=mock_db)
        content = create_minimal_content()
        brief_id = uuid4()

        persister.save_to_database(
            content,
            brief_id,
            report_path_md="/path/to/report.md",
            report_path_json="/path/to/report.json",
        )

        call_args = mock_db.insert_daily_brief.call_args[0][0]
        assert call_args.report_path_md == "/path/to/report.md"
        assert call_args.report_path_json == "/path/to/report.json"

    def test_save_passes_generation_method(self):
        """Test that generation_method is passed correctly."""
        mock_db = MagicMock()
        persister = DailyBriefPersister(db=mock_db)
        content = create_minimal_content()
        content.generation_method = "claude"
        brief_id = uuid4()

        persister.save_to_database(content, brief_id)

        call_args = mock_db.insert_daily_brief.call_args[0][0]
        assert call_args.generation_method == "claude"

    def test_save_returns_true_on_success(self):
        """Test that save returns True on successful insert."""
        mock_db = MagicMock()
        persister = DailyBriefPersister(db=mock_db)
        content = create_minimal_content()
        brief_id = uuid4()

        result = persister.save_to_database(content, brief_id)

        assert result is True

    def test_save_raises_on_db_error(self):
        """Test that save raises exception on database error."""
        mock_db = MagicMock()
        mock_db.insert_daily_brief.side_effect = Exception("DB error")
        persister = DailyBriefPersister(db=mock_db)
        content = create_minimal_content()
        brief_id = uuid4()

        with pytest.raises(Exception, match="DB error"):
            persister.save_to_database(content, brief_id)


class TestPersist:
    """Tests for persist() method (combined operation)."""

    def test_persist_returns_result(self):
        """Test that persist returns PersistenceResult."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_db = MagicMock()
            persister = DailyBriefPersister(reports_dir=tmpdir, db=mock_db)
            content = create_minimal_content()

            result = persister.persist(content)

            assert isinstance(result, PersistenceResult)

    def test_persist_success(self):
        """Test successful persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_db = MagicMock()
            persister = DailyBriefPersister(reports_dir=tmpdir, db=mock_db)
            content = create_minimal_content()

            result = persister.persist(content)

            assert result.success is True
            assert result.report_path_md is not None
            assert result.report_path_json is not None
            assert result.db_updated is True
            assert result.error is None

    def test_persist_sets_brief_id(self):
        """Test that persist generates brief_id if not provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_db = MagicMock()
            persister = DailyBriefPersister(reports_dir=tmpdir, db=mock_db)
            content = create_minimal_content()

            result = persister.persist(content)

            assert result.brief_id is not None
            assert len(result.brief_id) > 0

    def test_persist_uses_provided_brief_id(self):
        """Test that persist uses provided brief_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_db = MagicMock()
            persister = DailyBriefPersister(reports_dir=tmpdir, db=mock_db)
            content = create_minimal_content()
            brief_id = uuid4()

            result = persister.persist(content, brief_id=brief_id)

            assert result.brief_id == str(brief_id)

    def test_persist_passes_run_id(self):
        """Test that persist passes run_id to database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_db = MagicMock()
            persister = DailyBriefPersister(reports_dir=tmpdir, db=mock_db)
            content = create_minimal_content()
            run_id = "run-456"

            persister.persist(content, run_id=run_id)

            call_args = mock_db.insert_daily_brief.call_args[0][0]
            assert call_args.run_id == run_id

    def test_persist_sets_date(self):
        """Test that persist extracts date from content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_db = MagicMock()
            persister = DailyBriefPersister(reports_dir=tmpdir, db=mock_db)
            date = datetime(2024, 1, 21, tzinfo=timezone.utc)
            content = create_minimal_content(date)

            result = persister.persist(content)

            assert result.date == "2024-01-21"

    def test_persist_handles_file_error(self):
        """Test that persist handles file write errors gracefully."""
        # Use a non-writable directory
        persister = DailyBriefPersister(reports_dir="/root/nonexistent/reports")
        mock_db = MagicMock()
        persister._db = mock_db
        content = create_minimal_content()

        result = persister.persist(content)

        assert result.success is False
        assert result.error is not None

    def test_persist_handles_db_error(self):
        """Test that persist handles database errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_db = MagicMock()
            mock_db.insert_daily_brief.side_effect = Exception("DB error")
            persister = DailyBriefPersister(reports_dir=tmpdir, db=mock_db)
            content = create_minimal_content()

            result = persister.persist(content)

            assert result.success is False
            assert "DB error" in result.error


class TestIdempotentBehavior:
    """Tests for idempotent regeneration behavior."""

    def test_regenerate_overwrites_md_file(self):
        """Test that regenerating overwrites existing MD file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_db = MagicMock()
            persister = DailyBriefPersister(reports_dir=tmpdir, db=mock_db)
            date = datetime(2024, 1, 21, tzinfo=timezone.utc)

            # First generation
            content1 = create_minimal_content(date)
            content1.executive_summary = "First generation summary"
            persister.persist(content1)

            # Second generation (regenerate)
            content2 = create_minimal_content(date)
            content2.executive_summary = "Regenerated summary"
            result = persister.persist(content2)

            # Verify file was overwritten
            md_content = Path(result.report_path_md).read_text()
            assert "Regenerated summary" in md_content
            assert "First generation" not in md_content

    def test_regenerate_overwrites_json_file(self):
        """Test that regenerating overwrites existing JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_db = MagicMock()
            persister = DailyBriefPersister(reports_dir=tmpdir, db=mock_db)
            date = datetime(2024, 1, 21, tzinfo=timezone.utc)

            # First generation
            content1 = create_minimal_content(date)
            content1.executive_summary = "First generation summary"
            persister.persist(content1)

            # Second generation (regenerate)
            content2 = create_minimal_content(date)
            content2.executive_summary = "Regenerated summary"
            result = persister.persist(content2)

            # Verify file was overwritten
            json_content = Path(result.report_path_json).read_text()
            data = json.loads(json_content)
            assert data["executive_summary"] == "Regenerated summary"

    def test_regenerate_updates_db_record(self):
        """Test that regenerating updates database record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_db = MagicMock()
            persister = DailyBriefPersister(reports_dir=tmpdir, db=mock_db)
            date = datetime(2024, 1, 21, tzinfo=timezone.utc)

            # First generation
            content1 = create_minimal_content(date)
            persister.persist(content1)

            # Second generation (regenerate)
            content2 = create_minimal_content(date)
            content2.generation_method = "claude"
            persister.persist(content2)

            # Verify insert was called twice (database handles ON CONFLICT UPDATE)
            assert mock_db.insert_daily_brief.call_count == 2


class TestMinimalContent:
    """Tests for handling minimal/empty content."""

    def test_persist_minimal_content(self):
        """Test persisting minimal content with no events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_db = MagicMock()
            persister = DailyBriefPersister(reports_dir=tmpdir, db=mock_db)
            content = DailyBriefContent(generation_method="template")

            result = persister.persist(content)

            assert result.success is True

    def test_md_file_handles_empty_events(self):
        """Test that markdown handles empty events gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            content = DailyBriefContent(generation_method="template")

            result = persister.save_to_files(content)

            md_content = Path(result["report_path_md"]).read_text()
            assert "No events to report" in md_content

    def test_md_file_handles_no_trade_ideas(self):
        """Test that markdown handles no trade ideas gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            content = DailyBriefContent(generation_method="template")

            result = persister.save_to_files(content)

            md_content = Path(result["report_path_md"]).read_text()
            assert "No trade ideas" in md_content

    def test_md_file_handles_no_data_quality(self):
        """Test that markdown handles missing data quality gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persister = DailyBriefPersister(reports_dir=tmpdir)
            content = DailyBriefContent(data_quality=None, generation_method="template")

            result = persister.save_to_files(content)

            md_content = Path(result["report_path_md"]).read_text()
            assert "Data quality information not available" in md_content
