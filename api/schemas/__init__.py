"""
Pydantic schemas package.
"""
from .signals import Signal, SignalMetrics, SignalsResponse
from .sources import (
    EquityData,
    CryptoData,
    CongressTrade,
    HedgeFundFiling,
    PolymarketMarket,
    NewsArticle,
)
from .events import (
    EventStatusFilter,
    EventSortBy,
    EventListItem,
    EventsListResponse,
    EventDetail,
    FourDScores,
    EntityBrief,
    ObservationSummary,
    FactEntry,
)
from .system import (
    SourceStatus,
    SourceHealth,
    OverallHealth,
    SystemStatusResponse,
)

__all__ = [
    "Signal",
    "SignalMetrics",
    "SignalsResponse",
    "EquityData",
    "CryptoData",
    "CongressTrade",
    "HedgeFundFiling",
    "PolymarketMarket",
    "NewsArticle",
    "EventStatusFilter",
    "EventSortBy",
    "EventListItem",
    "EventsListResponse",
    "EventDetail",
    "FourDScores",
    "EntityBrief",
    "ObservationSummary",
    "FactEntry",
    "SourceStatus",
    "SourceHealth",
    "OverallHealth",
    "SystemStatusResponse",
]
