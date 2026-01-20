"""
Data models for tradz intelligence system.

Defines the core data structures: Entity, Observation, Event, Signal.
These models map to DuckDB tables and are used throughout the data pipeline.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class EntityType(str, Enum):
    """Types of entities in the system."""
    TICKER = "ticker"
    CIK = "cik"
    PERSON = "person"
    FUND = "fund"
    MARKET = "market"


class SourceType(str, Enum):
    """Data source types."""
    EQUITIES = "equities"
    CRYPTO = "crypto"
    CONGRESS = "congress"
    HEDGEFUND = "hedgefund"
    POLYMARKET = "polymarket"
    NEWS = "news"
    SEC = "sec"
    BROKER = "broker"
    X_SENTIMENT = "x_sentiment"


class EventType(str, Enum):
    """Types of trackable events."""
    CATALYST = "catalyst"  # Potential price catalyst
    RISK = "risk"  # Risk event
    FLOW = "flow"  # Money/position flow
    MACRO = "macro"  # Macroeconomic event


class EventStatus(str, Enum):
    """Event lifecycle status."""
    OPEN = "open"
    CLOSED = "closed"
    EXPIRED = "expired"


@dataclass
class Entity:
    """
    Entity represents a mappable object across data sources.
    
    Examples:
    - A stock ticker (AAPL) with CIK (0000320193) and name (Apple Inc.)
    - A Congress member with standardized name
    - A hedge fund with CIK
    """
    id: UUID = field(default_factory=uuid4)
    entity_type: EntityType = EntityType.TICKER
    ticker: Optional[str] = None
    cik: Optional[str] = None
    name: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "entity_type": self.entity_type.value,
            "ticker": self.ticker,
            "cik": self.cik,
            "name": self.name,
            "aliases": self.aliases,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Observation:
    """
    Observation is the minimal fact unit from any data source.
    
    Examples:
    - A news article about AAPL
    - A Congress member trade disclosure
    - A Polymarket probability change
    - A price/volume anomaly detection
    """
    id: UUID = field(default_factory=uuid4)
    source: SourceType = SourceType.EQUITIES
    entity_id: Optional[UUID] = None
    entity_ticker: Optional[str] = None  # For quick reference without join
    
    # Temporal
    effective_at: Optional[datetime] = None  # When the event actually happened
    observed_at: datetime = field(default_factory=datetime.utcnow)  # When we captured it
    
    # Quality metrics
    freshness_score: float = 1.0  # 0-1, how recent/timely
    quality_score: float = 1.0  # 0-1, data completeness/reliability
    
    # Content
    summary: str = ""  # Short machine-generated summary
    payload: Dict[str, Any] = field(default_factory=dict)  # Raw data
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "source": self.source.value,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "entity_ticker": self.entity_ticker,
            "effective_at": self.effective_at.isoformat() if self.effective_at else None,
            "observed_at": self.observed_at.isoformat(),
            "freshness_score": self.freshness_score,
            "quality_score": self.quality_score,
            "summary": self.summary,
            "payload": self.payload,
        }


@dataclass
class Event:
    """
    Event aggregates related observations into a trackable story.
    
    Examples:
    - "NFLX potential M&A catalyst" - links Congress trades, news, options activity
    - "Fed rate decision impact" - links Polymarket, news, sector movements
    """
    id: UUID = field(default_factory=uuid4)
    primary_entity_id: Optional[UUID] = None
    primary_ticker: Optional[str] = None  # For quick reference
    
    title: str = ""
    event_type: EventType = EventType.CATALYST
    status: EventStatus = EventStatus.OPEN
    confidence: float = 0.5  # 0-1, how confident we are in the event thesis
    
    start_at: datetime = field(default_factory=datetime.utcnow)
    last_update_at: datetime = field(default_factory=datetime.utcnow)
    
    # Linked observations (stored in event_observations table)
    observation_ids: List[UUID] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "primary_entity_id": str(self.primary_entity_id) if self.primary_entity_id else None,
            "primary_ticker": self.primary_ticker,
            "title": self.title,
            "event_type": self.event_type.value,
            "status": self.status.value,
            "confidence": self.confidence,
            "start_at": self.start_at.isoformat(),
            "last_update_at": self.last_update_at.isoformat(),
        }


@dataclass
class Signal:
    """
    Signal is the daily output for a ticker/asset with 4-dimensional scoring.
    
    Dimensions:
    - anomaly_score: Market behavior anomaly (z-score based)
    - catalyst_score: Presence of catalysts (news, filings, Polymarket)
    - flow_score: Money/position flows (Congress, 13F, broker)
    - confidence_score: Evidence quality and cross-source verification
    """
    id: UUID = field(default_factory=uuid4)
    signal_date: datetime = field(default_factory=datetime.utcnow)
    
    entity_id: Optional[UUID] = None
    ticker: Optional[str] = None
    asset_type: str = "equity"  # equity, crypto
    
    # Event link (if signal is part of a tracked event)
    event_id: Optional[UUID] = None
    
    # Four-dimensional scores (0-100 each)
    anomaly_score: float = 50.0
    catalyst_score: float = 50.0
    flow_score: float = 50.0
    confidence_score: float = 50.0
    
    # Composite attention score for sorting
    @property
    def attention_score(self) -> float:
        """Weighted composite score for ranking."""
        return (
            self.anomaly_score * 0.3 +
            self.catalyst_score * 0.3 +
            self.flow_score * 0.25 +
            self.confidence_score * 0.15
        )
    
    # Explanation
    explanation: Dict[str, Any] = field(default_factory=dict)
    evidence_ids: List[UUID] = field(default_factory=list)  # Linked observation IDs
    
    # Legacy compatibility
    why: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "signal_date": self.signal_date.isoformat() if isinstance(self.signal_date, datetime) else self.signal_date,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "ticker": self.ticker,
            "asset_type": self.asset_type,
            "event_id": str(self.event_id) if self.event_id else None,
            "anomaly_score": self.anomaly_score,
            "catalyst_score": self.catalyst_score,
            "flow_score": self.flow_score,
            "confidence_score": self.confidence_score,
            "attention_score": self.attention_score,
            "explanation": self.explanation,
            "evidence_ids": [str(eid) for eid in self.evidence_ids],
            "why": self.why,
            "caveats": self.caveats,
            "metrics": self.metrics,
        }
    
    # Legacy compatibility for existing code
    @property
    def symbol(self) -> str:
        return self.ticker or ""
    
    @property
    def score(self) -> int:
        """Legacy single score for backward compatibility."""
        return int(self.attention_score)


@dataclass
class FactTableEntry:
    """
    A single fact for the dual-channel report generation.
    
    These are deterministic values that LLM cannot modify.
    """
    fact_id: str
    category: str  # price, volume, news, filing, etc.
    ticker: Optional[str] = None
    value: Any = None
    unit: Optional[str] = None  # %, $, x, etc.
    source_url: Optional[str] = None
    observation_id: Optional[UUID] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "category": self.category,
            "ticker": self.ticker,
            "value": self.value,
            "unit": self.unit,
            "source_url": self.source_url,
            "observation_id": str(self.observation_id) if self.observation_id else None,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class FactTable:
    """
    Collection of facts for report generation.
    
    LLM must reference these values; it cannot invent new numbers.
    """
    report_date: datetime = field(default_factory=datetime.utcnow)
    facts: List[FactTableEntry] = field(default_factory=list)
    
    def get_facts_by_ticker(self, ticker: str) -> List[FactTableEntry]:
        return [f for f in self.facts if f.ticker == ticker]
    
    def get_facts_by_category(self, category: str) -> List[FactTableEntry]:
        return [f for f in self.facts if f.category == category]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_date": self.report_date.isoformat(),
            "facts": [f.to_dict() for f in self.facts],
        }
