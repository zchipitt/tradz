"""
DuckDB database layer for tradz intelligence system.

Provides:
- Database initialization and schema creation
- CRUD operations for observations, events, and signals
- Query helpers for analytics and reporting
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import duckdb

from .models import (
    Entity, EntityType,
    Observation, SourceType,
    Event, EventType, EventStatus,
    Signal,
)

logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "tradz.duckdb"


class Database:
    """
    DuckDB database manager for tradz.
    
    Handles connection management, schema initialization, and CRUD operations.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to DuckDB file. Defaults to data/tradz.duckdb
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[duckdb.DuckDBPyConnection] = None
    
    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = duckdb.connect(str(self.db_path))
        return self._conn
    
    def close(self):
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def init_schema(self):
        """
        Initialize database schema.
        
        Creates all tables if they don't exist.
        """
        logger.info(f"Initializing database schema at {self.db_path}")
        
        # Entities table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id VARCHAR PRIMARY KEY,
                entity_type VARCHAR NOT NULL,
                ticker VARCHAR,
                cik VARCHAR,
                name VARCHAR,
                aliases JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for entity lookups
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_entities_ticker ON entities(ticker)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_entities_cik ON entities(cik)
        """)
        
        # Observations table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id VARCHAR PRIMARY KEY,
                source VARCHAR NOT NULL,
                entity_id VARCHAR,
                entity_ticker VARCHAR,
                effective_at TIMESTAMP,
                observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                freshness_score DOUBLE DEFAULT 1.0,
                quality_score DOUBLE DEFAULT 1.0,
                summary VARCHAR,
                payload JSON,
                FOREIGN KEY (entity_id) REFERENCES entities(id)
            )
        """)
        
        # Create indexes for observation queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_observations_source ON observations(source)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_observations_ticker ON observations(entity_ticker)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_observations_observed_at ON observations(observed_at)
        """)
        
        # Events table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id VARCHAR PRIMARY KEY,
                primary_entity_id VARCHAR,
                primary_ticker VARCHAR,
                title VARCHAR NOT NULL,
                event_type VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'open',
                confidence DOUBLE DEFAULT 0.5,
                start_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (primary_entity_id) REFERENCES entities(id)
            )
        """)
        
        # Create indexes for event queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_ticker ON events(primary_ticker)
        """)
        
        # Event-Observation linking table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS event_observations (
                event_id VARCHAR NOT NULL,
                observation_id VARCHAR NOT NULL,
                linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (event_id, observation_id),
                FOREIGN KEY (event_id) REFERENCES events(id),
                FOREIGN KEY (observation_id) REFERENCES observations(id)
            )
        """)
        
        # Signals table (daily output)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id VARCHAR PRIMARY KEY,
                signal_date DATE NOT NULL,
                entity_id VARCHAR,
                ticker VARCHAR,
                asset_type VARCHAR DEFAULT 'equity',
                event_id VARCHAR,
                anomaly_score DOUBLE DEFAULT 50.0,
                catalyst_score DOUBLE DEFAULT 50.0,
                flow_score DOUBLE DEFAULT 50.0,
                confidence_score DOUBLE DEFAULT 50.0,
                attention_score DOUBLE,
                explanation JSON,
                evidence_ids JSON,
                metrics JSON,
                why JSON,
                caveats JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities(id),
                FOREIGN KEY (event_id) REFERENCES events(id)
            )
        """)
        
        # Create indexes for signal queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_date ON signals(signal_date)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_ticker ON signals(ticker)
        """)
        
        # Run history table (for observability)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS run_history (
                run_id VARCHAR PRIMARY KEY,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status VARCHAR DEFAULT 'running',
                observations_count INTEGER DEFAULT 0,
                events_count INTEGER DEFAULT 0,
                signals_count INTEGER DEFAULT 0,
                errors JSON,
                metadata JSON
            )
        """)
        
        logger.info("Database schema initialized successfully")
    
    # =========================================================================
    # Entity Operations
    # =========================================================================
    
    def insert_entity(self, entity: Entity) -> str:
        """Insert an entity, returning its ID."""
        self.conn.execute("""
            INSERT INTO entities (id, entity_type, ticker, cik, name, aliases, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                ticker = EXCLUDED.ticker,
                cik = EXCLUDED.cik,
                name = EXCLUDED.name,
                aliases = EXCLUDED.aliases
        """, [
            str(entity.id),
            entity.entity_type.value,
            entity.ticker,
            entity.cik,
            entity.name,
            json.dumps(entity.aliases),
            entity.created_at,
        ])
        return str(entity.id)
    
    def get_entity_by_ticker(self, ticker: str) -> Optional[Entity]:
        """Get entity by ticker symbol."""
        result = self.conn.execute("""
            SELECT id, entity_type, ticker, cik, name, aliases, created_at
            FROM entities WHERE ticker = ?
        """, [ticker]).fetchone()
        
        if result:
            return Entity(
                id=UUID(result[0]),
                entity_type=EntityType(result[1]),
                ticker=result[2],
                cik=result[3],
                name=result[4],
                aliases=json.loads(result[5]) if result[5] else [],
                created_at=result[6],
            )
        return None
    
    def get_entity_by_cik(self, cik: str) -> Optional[Entity]:
        """Get entity by CIK number."""
        result = self.conn.execute("""
            SELECT id, entity_type, ticker, cik, name, aliases, created_at
            FROM entities WHERE cik = ?
        """, [cik]).fetchone()
        
        if result:
            return Entity(
                id=UUID(result[0]),
                entity_type=EntityType(result[1]),
                ticker=result[2],
                cik=result[3],
                name=result[4],
                aliases=json.loads(result[5]) if result[5] else [],
                created_at=result[6],
            )
        return None
    
    # =========================================================================
    # Observation Operations
    # =========================================================================
    
    def insert_observation(self, obs: Observation) -> str:
        """Insert an observation, returning its ID."""
        self.conn.execute("""
            INSERT INTO observations (
                id, source, entity_id, entity_ticker, effective_at, observed_at,
                freshness_score, quality_score, summary, payload
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING
        """, [
            str(obs.id),
            obs.source.value,
            str(obs.entity_id) if obs.entity_id else None,
            obs.entity_ticker,
            obs.effective_at,
            obs.observed_at,
            obs.freshness_score,
            obs.quality_score,
            obs.summary,
            json.dumps(obs.payload),
        ])
        return str(obs.id)
    
    def insert_observations(self, observations: List[Observation]) -> int:
        """Batch insert observations, returning count inserted."""
        for obs in observations:
            self.insert_observation(obs)
        return len(observations)
    
    def get_observations_by_ticker(
        self,
        ticker: str,
        source: Optional[SourceType] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Observation]:
        """Get observations for a ticker."""
        query = "SELECT * FROM observations WHERE entity_ticker = ?"
        params: List[Any] = [ticker]
        
        if source:
            query += " AND source = ?"
            params.append(source.value)
        
        if since:
            query += " AND observed_at >= ?"
            params.append(since)
        
        query += " ORDER BY observed_at DESC LIMIT ?"
        params.append(limit)
        
        results = self.conn.execute(query, params).fetchall()
        return [self._row_to_observation(r) for r in results]
    
    def get_observations_by_date(
        self,
        date: datetime,
        source: Optional[SourceType] = None
    ) -> List[Observation]:
        """Get all observations from a specific date."""
        query = "SELECT * FROM observations WHERE DATE(observed_at) = DATE(?)"
        params: List[Any] = [date]
        
        if source:
            query += " AND source = ?"
            params.append(source.value)
        
        query += " ORDER BY observed_at DESC"
        results = self.conn.execute(query, params).fetchall()
        return [self._row_to_observation(r) for r in results]
    
    def _row_to_observation(self, row) -> Observation:
        """Convert database row to Observation object."""
        return Observation(
            id=UUID(row[0]),
            source=SourceType(row[1]),
            entity_id=UUID(row[2]) if row[2] else None,
            entity_ticker=row[3],
            effective_at=row[4],
            observed_at=row[5],
            freshness_score=row[6],
            quality_score=row[7],
            summary=row[8],
            payload=json.loads(row[9]) if row[9] else {},
        )
    
    # =========================================================================
    # Event Operations
    # =========================================================================
    
    def insert_event(self, event: Event) -> str:
        """Insert an event, returning its ID."""
        self.conn.execute("""
            INSERT INTO events (
                id, primary_entity_id, primary_ticker, title, event_type,
                status, confidence, start_at, last_update_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                confidence = EXCLUDED.confidence,
                last_update_at = EXCLUDED.last_update_at
        """, [
            str(event.id),
            str(event.primary_entity_id) if event.primary_entity_id else None,
            event.primary_ticker,
            event.title,
            event.event_type.value,
            event.status.value,
            event.confidence,
            event.start_at,
            event.last_update_at,
        ])
        return str(event.id)
    
    def link_observation_to_event(self, event_id: UUID, observation_id: UUID):
        """Link an observation to an event."""
        self.conn.execute("""
            INSERT INTO event_observations (event_id, observation_id)
            VALUES (?, ?)
            ON CONFLICT DO NOTHING
        """, [str(event_id), str(observation_id)])
    
    def get_open_events(self) -> List[Event]:
        """Get all events with status 'open'."""
        results = self.conn.execute("""
            SELECT id, primary_entity_id, primary_ticker, title, event_type,
                   status, confidence, start_at, last_update_at
            FROM events WHERE status = 'open'
            ORDER BY last_update_at DESC
        """).fetchall()
        return [self._row_to_event(r) for r in results]
    
    def get_events_by_ticker(self, ticker: str, include_closed: bool = False) -> List[Event]:
        """Get events for a ticker."""
        query = "SELECT * FROM events WHERE primary_ticker = ?"
        params: List[Any] = [ticker]
        
        if not include_closed:
            query += " AND status = 'open'"
        
        query += " ORDER BY last_update_at DESC"
        results = self.conn.execute(query, params).fetchall()
        return [self._row_to_event(r) for r in results]
    
    def update_event_status(self, event_id: UUID, status: EventStatus):
        """Update event status."""
        self.conn.execute("""
            UPDATE events SET status = ?, last_update_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, [status.value, str(event_id)])
    
    def _row_to_event(self, row) -> Event:
        """Convert database row to Event object."""
        return Event(
            id=UUID(row[0]),
            primary_entity_id=UUID(row[1]) if row[1] else None,
            primary_ticker=row[2],
            title=row[3],
            event_type=EventType(row[4]),
            status=EventStatus(row[5]),
            confidence=row[6],
            start_at=row[7],
            last_update_at=row[8],
        )
    
    # =========================================================================
    # Signal Operations
    # =========================================================================
    
    def insert_signal(self, signal: Signal) -> str:
        """Insert a signal, returning its ID."""
        signal_date = signal.signal_date
        if isinstance(signal_date, datetime):
            signal_date = signal_date.date()
        
        self.conn.execute("""
            INSERT INTO signals (
                id, signal_date, entity_id, ticker, asset_type, event_id,
                anomaly_score, catalyst_score, flow_score, confidence_score,
                attention_score, explanation, evidence_ids, metrics, why, caveats
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                anomaly_score = EXCLUDED.anomaly_score,
                catalyst_score = EXCLUDED.catalyst_score,
                flow_score = EXCLUDED.flow_score,
                confidence_score = EXCLUDED.confidence_score,
                attention_score = EXCLUDED.attention_score,
                explanation = EXCLUDED.explanation,
                evidence_ids = EXCLUDED.evidence_ids,
                metrics = EXCLUDED.metrics,
                why = EXCLUDED.why,
                caveats = EXCLUDED.caveats
        """, [
            str(signal.id),
            signal_date,
            str(signal.entity_id) if signal.entity_id else None,
            signal.ticker,
            signal.asset_type,
            str(signal.event_id) if signal.event_id else None,
            signal.anomaly_score,
            signal.catalyst_score,
            signal.flow_score,
            signal.confidence_score,
            signal.attention_score,
            json.dumps(signal.explanation),
            json.dumps([str(eid) for eid in signal.evidence_ids]),
            json.dumps(signal.metrics),
            json.dumps(signal.why),
            json.dumps(signal.caveats),
        ])
        return str(signal.id)
    
    def insert_signals(self, signals: List[Signal]) -> int:
        """Batch insert signals, returning count inserted."""
        for sig in signals:
            self.insert_signal(sig)
        return len(signals)
    
    def get_signals_by_date(self, date: datetime) -> List[Signal]:
        """Get all signals for a specific date."""
        signal_date = date.date() if isinstance(date, datetime) else date
        results = self.conn.execute("""
            SELECT * FROM signals WHERE signal_date = ?
            ORDER BY attention_score DESC
        """, [signal_date]).fetchall()
        return [self._row_to_signal(r) for r in results]
    
    def get_signal_history(
        self,
        ticker: str,
        days: int = 30
    ) -> List[Signal]:
        """Get signal history for a ticker."""
        results = self.conn.execute("""
            SELECT * FROM signals
            WHERE ticker = ? AND signal_date >= CURRENT_DATE - INTERVAL ? DAY
            ORDER BY signal_date DESC
        """, [ticker, days]).fetchall()
        return [self._row_to_signal(r) for r in results]
    
    def _row_to_signal(self, row) -> Signal:
        """Convert database row to Signal object."""
        return Signal(
            id=UUID(row[0]),
            signal_date=row[1],
            entity_id=UUID(row[2]) if row[2] else None,
            ticker=row[3],
            asset_type=row[4],
            event_id=UUID(row[5]) if row[5] else None,
            anomaly_score=row[6],
            catalyst_score=row[7],
            flow_score=row[8],
            confidence_score=row[9],
            explanation=json.loads(row[11]) if row[11] else {},
            evidence_ids=[UUID(eid) for eid in json.loads(row[12])] if row[12] else [],
            metrics=json.loads(row[13]) if row[13] else {},
            why=json.loads(row[14]) if row[14] else [],
            caveats=json.loads(row[15]) if row[15] else [],
        )
    
    # =========================================================================
    # Run History Operations
    # =========================================================================
    
    def start_run(self, run_id: str, metadata: Optional[Dict] = None) -> str:
        """Record the start of a nightly run."""
        self.conn.execute("""
            INSERT INTO run_history (run_id, metadata)
            VALUES (?, ?)
        """, [run_id, json.dumps(metadata or {})])
        return run_id
    
    def complete_run(
        self,
        run_id: str,
        observations_count: int = 0,
        events_count: int = 0,
        signals_count: int = 0,
        errors: Optional[List[str]] = None
    ):
        """Record the completion of a nightly run."""
        status = "completed" if not errors else "completed_with_errors"
        self.conn.execute("""
            UPDATE run_history SET
                completed_at = CURRENT_TIMESTAMP,
                status = ?,
                observations_count = ?,
                events_count = ?,
                signals_count = ?,
                errors = ?
            WHERE run_id = ?
        """, [
            status,
            observations_count,
            events_count,
            signals_count,
            json.dumps(errors or []),
            run_id,
        ])
    
    # =========================================================================
    # Analytics Queries
    # =========================================================================
    
    def get_observation_counts_by_source(self, since: Optional[datetime] = None) -> Dict[str, int]:
        """Get count of observations by source."""
        query = "SELECT source, COUNT(*) FROM observations"
        params: List[Any] = []
        
        if since:
            query += " WHERE observed_at >= ?"
            params.append(since)
        
        query += " GROUP BY source"
        results = self.conn.execute(query, params).fetchall()
        return {row[0]: row[1] for row in results}
    
    def get_top_tickers_by_observations(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Get tickers with most observations in recent days."""
        results = self.conn.execute("""
            SELECT entity_ticker, COUNT(*) as obs_count, 
                   COUNT(DISTINCT source) as source_count
            FROM observations
            WHERE observed_at >= CURRENT_DATE - INTERVAL ? DAY
              AND entity_ticker IS NOT NULL
            GROUP BY entity_ticker
            ORDER BY obs_count DESC
            LIMIT ?
        """, [days, limit]).fetchall()
        return [
            {"ticker": r[0], "observation_count": r[1], "source_count": r[2]}
            for r in results
        ]


# Singleton database instance
_db_instance: Optional[Database] = None


def get_database(db_path: Optional[Path] = None) -> Database:
    """Get or create database singleton."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
        _db_instance.init_schema()
    return _db_instance


def init_database(db_path: Optional[Path] = None) -> Database:
    """Initialize database (creates new instance)."""
    db = Database(db_path)
    db.init_schema()
    return db
