"""
Data models for tradz intelligence system.

Defines the core data structures: Entity, Observation, Event, Signal.
These models map to DuckDB tables and are used throughout the data pipeline.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    """Helper for timezone-aware UTC datetime (for dataclass default_factory)."""
    return datetime.now(timezone.utc)


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
    # Original types
    CATALYST = "catalyst"  # Potential price catalyst
    RISK = "risk"  # Risk event
    FLOW = "flow"  # Money/position flow
    MACRO = "macro"  # Macroeconomic event
    # New event types for event builder
    MARKET_ANOMALY = "market_anomaly"  # Significant price/volume anomaly
    CATALYST_NEWS = "catalyst_news"  # News-driven catalyst
    CATALYST_FILING = "catalyst_filing"  # SEC filing catalyst
    FLOW_CONGRESS = "flow_congress"  # Congressional trading activity
    FLOW_13F = "flow_13f"  # Institutional 13F filings
    PREDICTION_SHIFT = "prediction_shift"  # Polymarket probability changes
    MIXED = "mixed"  # Multiple signal types
    UNCERTAIN = "uncertain"  # Cannot classify


class EventStatus(str, Enum):
    """Event lifecycle status."""
    # Original statuses
    OPEN = "open"
    CLOSED = "closed"
    EXPIRED = "expired"
    # New statuses for event state machine
    NEW = "new"  # Just created
    ONGOING = "ongoing"  # Active with updates
    STALE = "stale"  # No updates for 72h+
    RESOLVED = "resolved"  # User marked resolved
    DISMISSED = "dismissed"  # User dismissed


class EventActionType(str, Enum):
    """Types of user actions on events."""
    PIN = "pin"
    UNPIN = "unpin"
    SNOOZE = "snooze"
    DISMISS = "dismiss"
    RESOLVE = "resolve"


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

    # Content - basic
    summary: str = ""  # Short machine-generated summary
    payload: Dict[str, Any] = field(default_factory=dict)  # Raw data

    # Content - extended fields for richer metadata
    source_url: Optional[str] = None  # URL to original source
    title: Optional[str] = None  # Human-readable title for the observation
    raw_payload: Optional[Dict[str, Any]] = None  # Full unprocessed payload (if truncated)
    fact_entries: List[Dict[str, Any]] = field(default_factory=list)  # Extracted FactTableEntry data
    entity_mapping_confidence: float = 1.0  # 0-1, confidence in entity resolution
    payload_truncated: bool = False  # Whether payload was truncated

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
            "source_url": self.source_url,
            "title": self.title,
            "raw_payload": self.raw_payload,
            "fact_entries": self.fact_entries,
            "entity_mapping_confidence": self.entity_mapping_confidence,
            "payload_truncated": self.payload_truncated,
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
    status: EventStatus = EventStatus.NEW
    confidence: float = 0.5  # 0-1, how confident we are in the event thesis

    # Temporal fields
    start_at: datetime = field(default_factory=datetime.utcnow)
    last_update_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    # Event hierarchy (for Primary/Secondary events)
    parent_event_id: Optional[UUID] = None

    # User actions
    pinned: bool = False
    snoozed_until: Optional[datetime] = None
    dismissed_reason: Optional[str] = None

    # Title generation metadata
    title_template: Optional[str] = None  # Template used if LLM failed
    title_source: str = "template"  # "llm" or "template"

    # 4D scores for attention calculation
    anomaly_score: float = 50.0
    catalyst_score: float = 50.0
    flow_score: float = 50.0
    confidence_score: float = 50.0

    # Linked observations (stored in event_observations table)
    observation_ids: List[UUID] = field(default_factory=list)

    @property
    def attention_score(self) -> float:
        """
        Calculate attention score from 4D scores with coverage bonus.

        Formula: 0.3*anomaly + 0.3*catalyst + 0.25*flow + 0.15*confidence + coverage_bonus
        Coverage bonus: +5 per independent source, max +20
        """
        base_score = (
            self.anomaly_score * 0.3 +
            self.catalyst_score * 0.3 +
            self.flow_score * 0.25 +
            self.confidence_score * 0.15
        )
        # Coverage bonus calculated from unique sources in observation_ids
        # This is approximated here; actual calculation happens in EventBuilder
        return min(base_score, 100.0)

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
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "parent_event_id": str(self.parent_event_id) if self.parent_event_id else None,
            "pinned": self.pinned,
            "snoozed_until": self.snoozed_until.isoformat() if self.snoozed_until else None,
            "dismissed_reason": self.dismissed_reason,
            "title_template": self.title_template,
            "title_source": self.title_source,
            "anomaly_score": self.anomaly_score,
            "catalyst_score": self.catalyst_score,
            "flow_score": self.flow_score,
            "confidence_score": self.confidence_score,
            "attention_score": self.attention_score,
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


class FactType(str, Enum):
    """Types of facts extracted from observations."""
    # Market facts
    PRICE = "price"
    PRICE_CHANGE = "price_change"
    VOLUME = "volume"
    VOLUME_VS_AVG = "volume_vs_avg"
    VOLATILITY = "volatility"

    # Congress facts
    POLITICIAN = "politician"
    PARTY = "party"
    TRADE_TYPE = "trade_type"
    AMOUNT_RANGE = "amount_range"
    TRADE_DATE = "trade_date"

    # SEC facts
    FILING_TYPE = "filing_type"
    FILED_DATE = "filed_date"
    FORM_URL = "form_url"
    KEY_ITEM = "key_item"

    # News facts
    HEADLINE = "headline"
    PUBLISHER = "publisher"
    PUBLISHED_AT = "published_at"
    SENTIMENT_SCORE = "sentiment_score"

    # Polymarket facts
    MARKET_QUESTION = "market_question"
    PROBABILITY = "probability"
    PROBABILITY_CHANGE = "probability_change"

    # General
    TICKER = "ticker"
    OTHER = "other"


@dataclass
class FactTableEntry:
    """
    A single fact for the dual-channel report generation.

    These are deterministic values that LLM cannot modify.
    Extracted from observations to prevent AI fabrication in reports.
    """
    fact_id: str
    fact_type: str  # Use FactType enum values
    label: str  # Human-readable label for the fact
    value: Any = None
    unit: Optional[str] = None  # %, $, x, etc.
    source: str = ""  # Source name (e.g., "Capitol Trades", "Yahoo Finance")
    timestamp: datetime = field(default_factory=datetime.utcnow)
    observation_id: Optional[UUID] = None

    # Legacy fields for backward compatibility
    category: Optional[str] = None  # Alias for fact_type
    ticker: Optional[str] = None
    source_url: Optional[str] = None

    def __post_init__(self):
        """Set category from fact_type for backward compatibility."""
        if self.category is None:
            self.category = self.fact_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "fact_type": self.fact_type,
            "label": self.label,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "observation_id": str(self.observation_id) if self.observation_id else None,
            # Legacy fields
            "category": self.category,
            "ticker": self.ticker,
            "source_url": self.source_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactTableEntry":
        """Create FactTableEntry from dictionary."""
        return cls(
            fact_id=data.get("fact_id", ""),
            fact_type=data.get("fact_type", data.get("category", "other")),
            label=data.get("label", ""),
            value=data.get("value"),
            unit=data.get("unit"),
            source=data.get("source", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
            observation_id=UUID(data["observation_id"]) if data.get("observation_id") else None,
            ticker=data.get("ticker"),
            source_url=data.get("source_url"),
        )


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


@dataclass
class DailyBrief:
    """
    Daily brief containing structured summary of events and trade ideas.

    Stored in the daily_briefs table and rendered to markdown/JSON reports.
    """
    id: UUID = field(default_factory=uuid4)
    date: datetime = field(default_factory=datetime.utcnow)

    # Structured content
    summary_json: Dict[str, Any] = field(default_factory=dict)

    # File paths for generated reports
    report_path_md: Optional[str] = None
    report_path_json: Optional[str] = None

    # Generation metadata
    generation_method: str = "template"  # "claude" or "template"
    created_at: datetime = field(default_factory=datetime.utcnow)
    run_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "date": self.date.isoformat() if isinstance(self.date, datetime) else str(self.date),
            "summary_json": self.summary_json,
            "report_path_md": self.report_path_md,
            "report_path_json": self.report_path_json,
            "generation_method": self.generation_method,
            "created_at": self.created_at.isoformat(),
            "run_id": self.run_id,
        }


@dataclass
class EventTypeHistory:
    """
    Tracks event type transitions for audit and analysis.

    Stored in the event_type_history table.
    """
    id: UUID = field(default_factory=uuid4)
    event_id: UUID = field(default_factory=uuid4)
    old_type: Optional[str] = None
    new_type: str = ""
    changed_at: datetime = field(default_factory=datetime.utcnow)
    trigger_observation_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "event_id": str(self.event_id),
            "old_type": self.old_type,
            "new_type": self.new_type,
            "changed_at": self.changed_at.isoformat(),
            "trigger_observation_id": str(self.trigger_observation_id) if self.trigger_observation_id else None,
        }


@dataclass
class EventAction:
    """
    Records user actions on events for audit and history.

    Stored in the event_actions table.
    All actions are logged with timestamp and optional user context.
    """
    id: UUID = field(default_factory=uuid4)
    event_id: UUID = field(default_factory=uuid4)
    action_type: EventActionType = EventActionType.PIN
    performed_at: datetime = field(default_factory=_utcnow)

    # Action-specific fields
    duration_hours: Optional[int] = None  # For snooze action
    reason: Optional[str] = None  # For dismiss action
    previous_status: Optional[str] = None  # Status before action
    new_status: Optional[str] = None  # Status after action
    previous_pinned: Optional[bool] = None  # Pinned state before action
    new_pinned: Optional[bool] = None  # Pinned state after action
    snoozed_until: Optional[datetime] = None  # For snooze action

    # User context (for future multi-user support)
    user_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "event_id": str(self.event_id),
            "action_type": self.action_type.value,
            "performed_at": self.performed_at.isoformat(),
            "duration_hours": self.duration_hours,
            "reason": self.reason,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "previous_pinned": self.previous_pinned,
            "new_pinned": self.new_pinned,
            "snoozed_until": self.snoozed_until.isoformat() if self.snoozed_until else None,
            "user_id": self.user_id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
        }
