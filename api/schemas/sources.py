"""
Pydantic schemas for data sources.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EquityData(BaseModel):
    """Equity asset data."""
    symbol: str
    last_price: float
    day_return: float
    week_return: float
    volume: int
    data_points: int


class EquitiesResponse(BaseModel):
    """Response containing equities data."""
    data: Dict[str, EquityData]
    count: int
    error: Optional[str] = None


class CryptoData(BaseModel):
    """Cryptocurrency data."""
    symbol: str
    last_price: float
    day_return: float
    week_return: float
    volume: float
    data_points: int


class CryptoResponse(BaseModel):
    """Response containing crypto data."""
    data: Dict[str, CryptoData]
    count: int
    error: Optional[str] = None


class CongressTrade(BaseModel):
    """Congress member trade."""
    ticker: str
    member: str
    chamber: str  # 'House' or 'Senate'
    party: Optional[str] = None
    state: Optional[str] = None
    trade_type: str = Field(..., alias="type")  # 'purchase', 'sale', 'exchange'
    amount_str: str
    transaction_date: Optional[str] = None
    disclosure_date: Optional[str] = None
    description: Optional[str] = None

    class Config:
        populate_by_name = True


class CongressResponse(BaseModel):
    """Response containing congress trades."""
    trades: List[CongressTrade] = []
    summary: Optional[Dict[str, Any]] = None
    watchlist_overlap: List[CongressTrade] = []
    count: int = 0
    error: Optional[str] = None


class HedgeFundFiling(BaseModel):
    """Hedge fund 13F filing."""
    cik: str
    fund_name: str
    accession_number: Optional[str] = None
    filing_date: Optional[str] = None


class HedgeFundResponse(BaseModel):
    """Response containing hedge fund data."""
    filings: List[HedgeFundFiling] = []
    filings_found: int = 0
    notable_funds: List[str] = []
    error: Optional[str] = None


class PolymarketOutcome(BaseModel):
    """Polymarket outcome option."""
    name: str
    price: float
    probability_pct: float


class PolymarketMarket(BaseModel):
    """Polymarket prediction market."""
    id: str
    question: str
    category: Optional[str] = None
    outcomes: List[PolymarketOutcome] = []
    volume: Optional[float] = None
    url: Optional[str] = None


class PolymarketResponse(BaseModel):
    """Response containing Polymarket data."""
    markets: List[PolymarketMarket] = []
    high_probability_events: List[Dict[str, Any]] = []
    total_markets: int = 0
    error: Optional[str] = None


class NewsArticle(BaseModel):
    """News article."""
    title: str
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[str] = None
    ticker: Optional[str] = None


class NewsResponse(BaseModel):
    """Response containing news data."""
    by_ticker: Dict[str, List[NewsArticle]] = {}
    headlines: List[NewsArticle] = []
    total_articles: int = 0
    error: Optional[str] = None


class SECFiling(BaseModel):
    """SEC filing."""
    ticker: str
    form_type: str
    filing_date: Optional[str] = None
    accession_number: Optional[str] = None
    url: Optional[str] = None


class SECResponse(BaseModel):
    """Response containing SEC filings."""
    by_ticker: Dict[str, List[SECFiling]] = {}
    total_filings: int = 0
    error: Optional[str] = None
