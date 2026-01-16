"""
Data sources for trading signals.
"""
from .equities import EquitiesDataSource
from .crypto import CryptoDataSource
from .congress import CongressDataSource
from .hedgefunds import HedgeFundDataSource
from .polymarket import PolymarketDataSource
from .news import NewsDataSource
from .sec_filings import SECFilingsDataSource

__all__ = [
    'EquitiesDataSource',
    'CryptoDataSource',
    'CongressDataSource',
    'HedgeFundDataSource',
    'PolymarketDataSource',
    'NewsDataSource',
    'SECFilingsDataSource',
]
