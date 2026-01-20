"""
Congress member trading disclosures.
Data sources:
- House Stock Watcher API (https://housestockwatcher.com)
- Senate Stock Watcher API (https://senatestockwatcher.com)
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class CongressDataSource:
    """Fetches congressional trading disclosures."""

    # Public APIs for congressional trades
    HOUSE_API = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
    SENATE_API = "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json"

    def __init__(self, lookback_days: int = 30, min_amount: int = 15000):
        """
        Initialize Congress data source.

        Args:
            lookback_days: How many days back to fetch trades
            min_amount: Minimum trade amount to include ($)
        """
        self.lookback_days = lookback_days
        self.min_amount = min_amount
        self.client = httpx.Client(timeout=30.0)

    def fetch_recent_trades(self) -> List[Dict]:
        """
        Fetch recent congressional trades from both chambers.

        Returns:
            List of normalized trade records
        """
        all_trades = []
        errors = []
        cutoff_date = datetime.now() - timedelta(days=self.lookback_days)

        # Fetch House trades
        try:
            house_trades = self._fetch_house_trades(cutoff_date)
            all_trades.extend(house_trades)
            logger.info(f"Fetched {len(house_trades)} House trades")
        except Exception as e:
            logger.error(f"Failed to fetch House trades: {e}")
            errors.append(f"House: {e}")

        # Fetch Senate trades
        try:
            senate_trades = self._fetch_senate_trades(cutoff_date)
            all_trades.extend(senate_trades)
            logger.info(f"Fetched {len(senate_trades)} Senate trades")
        except Exception as e:
            logger.error(f"Failed to fetch Senate trades: {e}")
            errors.append(f"Senate: {e}")

        # If both failed, raise an exception to be caught by the aggregator
        if not all_trades and errors:
            raise Exception(f"Failed to fetch trades. Sources returned: {'; '.join(errors)}")

        # Sort by transaction date (newest first)
        all_trades.sort(
            key=lambda x: x.get('transaction_date', ''),
            reverse=True
        )

        return all_trades

    def _fetch_house_trades(self, cutoff_date: datetime) -> List[Dict]:
        """Fetch House of Representatives trades."""
        trades = []

        resp = self.client.get(self.HOUSE_API)
        resp.raise_for_status()
        data = resp.json()

        for trade in data:
            trade_date = self._parse_date(trade.get('transaction_date'))
            if trade_date and trade_date >= cutoff_date:
                normalized = self._normalize_house_trade(trade)
                if normalized:
                    trades.append(normalized)

        return trades

    def _fetch_senate_trades(self, cutoff_date: datetime) -> List[Dict]:
        """Fetch Senate trades."""
        trades = []

        resp = self.client.get(self.SENATE_API)
        resp.raise_for_status()
        data = resp.json()

        for trade in data:
            trade_date = self._parse_date(trade.get('transaction_date'))
            if trade_date and trade_date >= cutoff_date:
                normalized = self._normalize_senate_trade(trade)
                if normalized:
                    trades.append(normalized)

        return trades

    def _normalize_house_trade(self, trade: Dict) -> Optional[Dict]:
        """Normalize House trade to standard format."""
        ticker = trade.get('ticker', '').upper().strip()
        if not ticker or ticker == '--':
            return None

        amount = self._parse_amount(trade.get('amount', ''))

        return {
            'ticker': ticker,
            'member': trade.get('representative', 'Unknown'),
            'chamber': 'House',
            'party': trade.get('party', ''),
            'state': trade.get('state', ''),
            'type': self._normalize_type(trade.get('type', '')),
            'amount_min': amount,
            'amount_str': trade.get('amount', ''),
            'transaction_date': trade.get('transaction_date', ''),
            'disclosure_date': trade.get('disclosure_date', ''),
            'description': trade.get('asset_description', ''),
        }

    def _normalize_senate_trade(self, trade: Dict) -> Optional[Dict]:
        """Normalize Senate trade to standard format."""
        ticker = trade.get('ticker', '').upper().strip()
        if not ticker or ticker == '--':
            return None

        amount = self._parse_amount(trade.get('amount', ''))

        return {
            'ticker': ticker,
            'member': trade.get('senator', 'Unknown'),
            'chamber': 'Senate',
            'party': trade.get('party', ''),
            'state': trade.get('state', ''),
            'type': self._normalize_type(trade.get('type', '')),
            'amount_min': amount,
            'amount_str': trade.get('amount', ''),
            'transaction_date': trade.get('transaction_date', ''),
            'disclosure_date': trade.get('disclosure_date', ''),
            'description': trade.get('asset_description', ''),
        }

    def _normalize_type(self, type_str: str) -> str:
        """Normalize trade type to 'purchase' or 'sale'."""
        type_lower = type_str.lower()
        if 'purchase' in type_lower or 'buy' in type_lower:
            return 'purchase'
        elif 'sale' in type_lower or 'sell' in type_lower:
            return 'sale'
        elif 'exchange' in type_lower:
            return 'exchange'
        return type_str

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None

        formats = ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S']
        for fmt in formats:
            try:
                return datetime.strptime(date_str[:10], fmt[:10] if len(fmt) > 10 else fmt)
            except ValueError:
                continue
        return None

    def _parse_amount(self, amount_str: str) -> int:
        """
        Parse amount range to minimum value.
        Handles formats like "$1,001 - $15,000"
        """
        if not amount_str:
            return 0

        amount_str = amount_str.replace('$', '').replace(',', '')
        parts = amount_str.split('-')

        try:
            return int(float(parts[0].strip()))
        except ValueError:
            return 0

    def get_trades_by_ticker(self, ticker: str) -> List[Dict]:
        """Get all recent trades for a specific ticker."""
        trades = self.fetch_recent_trades()
        return [t for t in trades if t.get('ticker', '').upper() == ticker.upper()]

    def get_notable_buys(self, min_amount: Optional[int] = None) -> List[Dict]:
        """
        Get notable purchases above threshold.

        Args:
            min_amount: Minimum amount (uses instance default if not specified)

        Returns:
            List of notable purchase trades
        """
        threshold = min_amount or self.min_amount
        trades = self.fetch_recent_trades()

        return [
            t for t in trades
            if t.get('type') == 'purchase'
            and t.get('amount_min', 0) >= threshold
        ]

    def get_watchlist_overlap(self, watchlist: List[str]) -> List[Dict]:
        """
        Find trades that overlap with a watchlist.

        Args:
            watchlist: List of ticker symbols to check

        Returns:
            List of trades matching the watchlist
        """
        watchlist_upper = {t.upper() for t in watchlist}
        trades = self.fetch_recent_trades()

        return [
            t for t in trades
            if t.get('ticker', '').upper() in watchlist_upper
        ]

    def get_summary(self) -> Dict:
        """
        Get summary statistics of recent trades.

        Returns:
            Dict with summary info
        """
        trades = self.fetch_recent_trades()

        if not trades:
            return {
                'total_trades': 0,
                'house_trades': 0,
                'senate_trades': 0,
                'purchases': 0,
                'sales': 0,
                'top_tickers': [],
                'top_members': [],
            }

        # Count by chamber
        house_trades = [t for t in trades if t['chamber'] == 'House']
        senate_trades = [t for t in trades if t['chamber'] == 'Senate']

        # Count by type
        purchases = [t for t in trades if t['type'] == 'purchase']
        sales = [t for t in trades if t['type'] == 'sale']

        # Top tickers
        ticker_counts: Dict[str, int] = {}
        for t in trades:
            ticker = t.get('ticker', '')
            ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1

        top_tickers = sorted(
            ticker_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Top members
        member_counts: Dict[str, int] = {}
        for t in trades:
            member = t.get('member', '')
            member_counts[member] = member_counts.get(member, 0) + 1

        top_members = sorted(
            member_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            'total_trades': len(trades),
            'house_trades': len(house_trades),
            'senate_trades': len(senate_trades),
            'purchases': len(purchases),
            'sales': len(sales),
            'top_tickers': top_tickers,
            'top_members': top_members,
            'lookback_days': self.lookback_days,
        }

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
