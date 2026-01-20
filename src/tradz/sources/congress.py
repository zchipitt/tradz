"""
Congress member trading disclosures.
Multi-source data aggregation with automatic fallback:
1. Capitol Trades (primary) - Free web scraping
2. Quiver Quantitative API (secondary) - Free tier with API key
3. Finnhub API (tertiary) - Free tier with API key
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class CongressDataSource:
    """Fetches congressional trading disclosures from multiple sources."""

    # Capitol Trades - primary source (free, no API key)
    CAPITOL_TRADES_URL = "https://www.capitoltrades.com/trades"

    # Quiver Quantitative - secondary source (requires API key)
    QUIVER_API_URL = "https://api.quiverquant.com/beta/historical/congresstrading"

    # Finnhub - tertiary source (requires API key)
    FINNHUB_API_URL = "https://finnhub.io/api/v1/stock/congressional-trading"

    def __init__(
        self,
        lookback_days: int = 30,
        min_amount: int = 15000,
        quiver_api_key: Optional[str] = None,
        finnhub_api_key: Optional[str] = None,
    ):
        """
        Initialize Congress data source.

        Args:
            lookback_days: How many days back to fetch trades
            min_amount: Minimum trade amount to include ($)
            quiver_api_key: Quiver Quantitative API key (optional)
            finnhub_api_key: Finnhub API key (optional)
        """
        self.lookback_days = lookback_days
        self.min_amount = min_amount
        self.quiver_api_key = quiver_api_key
        self.finnhub_api_key = finnhub_api_key
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            },
        )
        self._active_source = None

    def fetch_recent_trades(self) -> List[Dict]:
        """
        Fetch recent congressional trades with automatic fallback.

        Tries sources in order:
        1. Capitol Trades (free web scraping)
        2. Quiver Quantitative API (if API key provided)
        3. Finnhub API (if API key provided)

        Returns:
            List of normalized trade records
        """
        errors = []
        cutoff_date = datetime.now() - timedelta(days=self.lookback_days)

        # Try Capitol Trades first (free, no API key required)
        try:
            trades = self._fetch_capitol_trades(cutoff_date)
            if trades:
                self._active_source = "Capitol Trades"
                logger.info(f"Fetched {len(trades)} trades from Capitol Trades")
                return self._sort_trades(trades)
        except Exception as e:
            logger.warning(f"Capitol Trades failed: {e}")
            errors.append(f"Capitol Trades: {e}")

        # Try Quiver Quantitative API
        if self.quiver_api_key:
            try:
                trades = self._fetch_quiver_trades(cutoff_date)
                if trades:
                    self._active_source = "Quiver Quantitative"
                    logger.info(f"Fetched {len(trades)} trades from Quiver Quantitative")
                    return self._sort_trades(trades)
            except Exception as e:
                logger.warning(f"Quiver Quantitative failed: {e}")
                errors.append(f"Quiver: {e}")

        # Try Finnhub API
        if self.finnhub_api_key:
            try:
                trades = self._fetch_finnhub_trades(cutoff_date)
                if trades:
                    self._active_source = "Finnhub"
                    logger.info(f"Fetched {len(trades)} trades from Finnhub")
                    return self._sort_trades(trades)
            except Exception as e:
                logger.warning(f"Finnhub failed: {e}")
                errors.append(f"Finnhub: {e}")

        # All sources failed
        if errors:
            raise Exception(
                f"All congress data sources failed: {'; '.join(errors)}. "
                f"Consider adding API keys for Quiver Quantitative or Finnhub."
            )

        return []

    def _sort_trades(self, trades: List[Dict]) -> List[Dict]:
        """Sort trades by transaction date (newest first)."""
        trades.sort(
            key=lambda x: x.get('transaction_date', ''),
            reverse=True
        )
        return trades

    # =========================================================================
    # CAPITOL TRADES (Primary - Free)
    # =========================================================================
    def _fetch_capitol_trades(self, cutoff_date: datetime) -> List[Dict]:
        """
        Fetch trades from Capitol Trades via web scraping.

        Capitol Trades provides free access to congressional trading data
        with data going back 3 years.
        """
        trades = []
        page = 1
        max_pages = 10  # Limit to avoid excessive requests

        while page <= max_pages:
            url = f"{self.CAPITOL_TRADES_URL}?page={page}"
            resp = self.client.get(url)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, 'html.parser')
            trade_rows = soup.select('table tbody tr, .trade-row, [data-trade-id]')

            if not trade_rows:
                # Try alternative selectors for different page structures
                trade_rows = soup.select('div.trade, article.trade-item')

            if not trade_rows:
                # No more trades found
                break

            page_trades = []
            for row in trade_rows:
                trade = self._parse_capitol_trade_row(row)
                if trade:
                    trade_date = self._parse_date(trade.get('transaction_date', ''))
                    # Note: Capitol Trades sorts by PUBLICATION date, not transaction date
                    # So newer transactions can appear on later pages
                    if trade_date and trade_date >= cutoff_date:
                        page_trades.append(trade)
                    # Don't early-terminate - trades are not sorted by transaction date

            # If we got some trades on this page, continue to next page
            # Stop if no trade rows found (end of data)
            if not trade_rows:
                break

            trades.extend(page_trades)
            page += 1

        return trades

    def _parse_capitol_trade_row(self, row) -> Optional[Dict]:
        """Parse a single trade row from Capitol Trades HTML."""
        try:
            # Extract text content, handling different HTML structures
            text_content = row.get_text(separator=' | ', strip=True)

            # Try to extract from table cells
            cells = row.select('td')
            if len(cells) >= 5:
                return self._parse_table_cells(cells)

            # Try to extract from structured divs
            return self._parse_structured_divs(row, text_content)

        except Exception as e:
            logger.debug(f"Failed to parse trade row: {e}")
            return None

    def _parse_table_cells(self, cells) -> Optional[Dict]:
        """Parse trade from table cells.

        Capitol Trades table structure (10 columns):
        0: Politician (Name | Party | Chamber | State)
        1: Traded Issuer (Company Name | TICKER:EXCHANGE)
        2: Published (time | date)
        3: Traded (day month | year)
        4: Filed After (days | count)
        5: Owner
        6: Type (buy/sell/exchange)
        7: Size (amount range like "1K-15K")
        8: Price
        9: Link
        """
        try:
            if len(cells) < 8:
                return None

            # Extract politician info (cell 0)
            politician_text = cells[0].get_text(separator=' | ', strip=True)
            politician_parts = [p.strip() for p in politician_text.split('|')]

            member_name = politician_parts[0] if len(politician_parts) > 0 else "Unknown"
            party = politician_parts[1] if len(politician_parts) > 1 else ""
            chamber = politician_parts[2] if len(politician_parts) > 2 else "House"
            state = politician_parts[3] if len(politician_parts) > 3 else ""

            # Normalize party
            if 'Republican' in party:
                party = 'R'
            elif 'Democrat' in party:
                party = 'D'
            elif 'Independent' in party:
                party = 'I'

            # Extract issuer/ticker (cell 1)
            issuer_text = cells[1].get_text(separator=' | ', strip=True)
            issuer_parts = [p.strip() for p in issuer_text.split('|')]
            description = issuer_parts[0] if len(issuer_parts) > 0 else ""

            # Extract ticker from "TICKER:EXCHANGE" format
            ticker = None
            if len(issuer_parts) > 1:
                ticker_exchange = issuer_parts[1]
                # Handle formats like "LLYVK:US", "AAPL:US"
                if ':' in ticker_exchange:
                    ticker = ticker_exchange.split(':')[0].strip()
                else:
                    ticker = ticker_exchange.strip()

            if not ticker:
                ticker = self._extract_ticker(issuer_text)

            # Skip invalid or non-stock tickers
            invalid_tickers = {'N/A', 'NA', '--', 'UNKNOWN', 'NONE', ''}
            if not ticker or len(ticker) > 10 or ticker.upper() in invalid_tickers:
                return None

            # Extract traded date (cell 3 - "16 Dec | 2025")
            traded_text = cells[3].get_text(separator=' ', strip=True)
            # Parse date like "16 Dec 2025"
            transaction_date = self._parse_capitol_date(traded_text)

            # Extract trade type (cell 6)
            trade_type = cells[6].get_text(strip=True) if len(cells) > 6 else ""

            # Extract amount/size (cell 7)
            amount_str = cells[7].get_text(strip=True) if len(cells) > 7 else ""
            amount_min = self._parse_capitol_amount(amount_str)

            return {
                'ticker': ticker.upper(),
                'member': member_name,
                'chamber': chamber,
                'party': party,
                'state': state,
                'type': self._normalize_type(trade_type),
                'amount_min': amount_min,
                'amount_str': amount_str,
                'transaction_date': transaction_date,
                'disclosure_date': cells[2].get_text(strip=True) if len(cells) > 2 else "",
                'description': description,
                'source': 'Capitol Trades',
            }
        except Exception as e:
            logger.debug(f"Failed to parse table cells: {e}")
            return None

    def _parse_capitol_date(self, date_text: str) -> str:
        """Parse Capitol Trades date format like '16 Dec 2025'."""
        try:
            # Clean up the text
            date_text = date_text.replace('|', ' ').strip()
            # Try different formats
            for fmt in ['%d %b %Y', '%d %B %Y', '%b %d %Y', '%B %d %Y']:
                try:
                    dt = datetime.strptime(date_text, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return date_text
        except Exception:
            return date_text

    def _parse_capitol_amount(self, amount_str: str) -> int:
        """Parse Capitol Trades amount format like '1K-15K' or '15K-50K'."""
        if not amount_str:
            return 0

        # Convert K/M suffixes
        amount_str = amount_str.upper().replace(',', '').replace('$', '')

        # Get the lower bound (first number)
        parts = amount_str.replace('–', '-').split('-')
        if not parts:
            return 0

        first_part = parts[0].strip()

        try:
            if 'K' in first_part:
                return int(float(first_part.replace('K', '')) * 1000)
            elif 'M' in first_part:
                return int(float(first_part.replace('M', '')) * 1000000)
            else:
                return int(float(first_part))
        except ValueError:
            return 0

    def _parse_structured_divs(self, row, text_content: str) -> Optional[Dict]:
        """Parse trade from structured div elements."""
        try:
            # Look for specific data attributes or classes
            ticker_elem = row.select_one('[data-ticker], .ticker, .symbol')
            member_elem = row.select_one('[data-politician], .politician, .member-name')
            date_elem = row.select_one('[data-date], .trade-date, .transaction-date')
            type_elem = row.select_one('[data-type], .trade-type, .transaction-type')
            amount_elem = row.select_one('[data-amount], .amount, .trade-amount')

            ticker = ticker_elem.get_text(strip=True) if ticker_elem else ""
            if not ticker:
                # Try to extract from text content
                ticker = self._extract_ticker(text_content)

            if not ticker:
                return None

            return {
                'ticker': ticker.upper(),
                'member': member_elem.get_text(strip=True) if member_elem else "Unknown",
                'chamber': "House",  # Default, hard to determine from scraping
                'party': "",
                'state': "",
                'type': self._normalize_type(type_elem.get_text(strip=True) if type_elem else ""),
                'amount_min': self._parse_amount(amount_elem.get_text(strip=True) if amount_elem else ""),
                'amount_str': amount_elem.get_text(strip=True) if amount_elem else "",
                'transaction_date': date_elem.get_text(strip=True) if date_elem else "",
                'disclosure_date': "",
                'description': "",
                'source': 'Capitol Trades',
            }
        except Exception as e:
            logger.debug(f"Failed to parse structured divs: {e}")
            return None

    def _extract_ticker(self, text: str) -> Optional[str]:
        """Extract stock ticker from text."""
        # Common patterns: "AAPL", "(AAPL)", "AAPL - Apple Inc"
        patterns = [
            r'\(([A-Z]{1,5})\)',  # (AAPL)
            r'\b([A-Z]{1,5})\b(?:\s*-|\s*\|)',  # AAPL - or AAPL |
            r'^([A-Z]{1,5})\s',  # AAPL at start
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                ticker = match.group(1)
                # Filter out common non-ticker words
                if ticker not in {'THE', 'AND', 'FOR', 'INC', 'LLC', 'ETF', 'USD', 'EUR'}:
                    return ticker

        return None

    # =========================================================================
    # QUIVER QUANTITATIVE (Secondary)
    # =========================================================================
    def _fetch_quiver_trades(self, cutoff_date: datetime) -> List[Dict]:
        """
        Fetch trades from Quiver Quantitative API.

        Requires API key. Get a free trial at https://api.quiverquant.com
        Use code 'TWITTER' for 1 month free.
        """
        headers = {
            "Authorization": f"Bearer {self.quiver_api_key}",
            "Accept": "application/json",
        }

        resp = self.client.get(self.QUIVER_API_URL, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        trades = []
        for trade in data:
            trade_date = self._parse_date(trade.get('TransactionDate') or trade.get('Date'))
            if trade_date and trade_date >= cutoff_date:
                normalized = self._normalize_quiver_trade(trade)
                if normalized:
                    trades.append(normalized)

        return trades

    def _normalize_quiver_trade(self, trade: Dict) -> Optional[Dict]:
        """Normalize Quiver Quantitative trade to standard format."""
        ticker = (trade.get('Ticker') or trade.get('ticker', '')).upper().strip()
        if not ticker or ticker == '--' or ticker == 'N/A':
            return None

        # Quiver uses Representative/Senator field
        member = trade.get('Representative') or trade.get('Senator') or trade.get('Name', 'Unknown')
        chamber = 'Senate' if trade.get('Senator') else 'House'

        return {
            'ticker': ticker,
            'member': member,
            'chamber': chamber,
            'party': trade.get('Party', ''),
            'state': trade.get('State', ''),
            'type': self._normalize_type(trade.get('Transaction') or trade.get('Type', '')),
            'amount_min': self._parse_quiver_amount(trade.get('Range') or trade.get('Amount', '')),
            'amount_str': trade.get('Range') or trade.get('Amount', ''),
            'transaction_date': trade.get('TransactionDate') or trade.get('Date', ''),
            'disclosure_date': trade.get('ReportDate', ''),
            'description': trade.get('Description', ''),
            'source': 'Quiver Quantitative',
        }

    def _parse_quiver_amount(self, amount_str: str) -> int:
        """Parse Quiver amount format."""
        if not amount_str:
            return 0

        # Quiver uses ranges like "$1,001 - $15,000" or "$15,001 - $50,000"
        return self._parse_amount(amount_str)

    # =========================================================================
    # FINNHUB (Tertiary)
    # =========================================================================
    def _fetch_finnhub_trades(self, cutoff_date: datetime) -> List[Dict]:
        """
        Fetch trades from Finnhub API.

        Note: Finnhub requires a symbol parameter, so we fetch for common tickers.
        Get a free API key at https://finnhub.io
        """
        trades = []
        # Common tickers that congress members frequently trade
        popular_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
            'JPM', 'BAC', 'GS', 'JNJ', 'UNH', 'PFE', 'XOM', 'CVX',
        ]

        for ticker in popular_tickers:
            try:
                resp = self.client.get(
                    self.FINNHUB_API_URL,
                    params={
                        'symbol': ticker,
                        'token': self.finnhub_api_key,
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for trade in data.get('data', []):
                        trade_date = self._parse_date(trade.get('transactionDate'))
                        if trade_date and trade_date >= cutoff_date:
                            normalized = self._normalize_finnhub_trade(trade, ticker)
                            if normalized:
                                trades.append(normalized)
            except Exception as e:
                logger.debug(f"Finnhub fetch failed for {ticker}: {e}")
                continue

        return trades

    def _normalize_finnhub_trade(self, trade: Dict, ticker: str) -> Optional[Dict]:
        """Normalize Finnhub trade to standard format."""
        return {
            'ticker': ticker,
            'member': trade.get('name', 'Unknown'),
            'chamber': 'House',  # Finnhub doesn't always specify
            'party': '',
            'state': '',
            'type': self._normalize_type(trade.get('transactionType', '')),
            'amount_min': trade.get('amountFrom', 0),
            'amount_str': f"${trade.get('amountFrom', 0):,} - ${trade.get('amountTo', 0):,}",
            'transaction_date': trade.get('transactionDate', ''),
            'disclosure_date': trade.get('filingDate', ''),
            'description': trade.get('assetName', ''),
            'source': 'Finnhub',
        }

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    def _normalize_type(self, type_str: str) -> str:
        """Normalize trade type to 'purchase' or 'sale'."""
        if not type_str:
            return 'unknown'
        type_lower = type_str.lower()
        if 'purchase' in type_lower or 'buy' in type_lower:
            return 'purchase'
        elif 'sale' in type_lower or 'sell' in type_lower or 'sold' in type_lower:
            return 'sale'
        elif 'exchange' in type_lower:
            return 'exchange'
        return type_str

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None

        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%B %d, %Y',  # December 15, 2025
            '%b %d, %Y',  # Dec 15, 2025
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str[:len(fmt.replace('%Y', '2025').replace('%m', '12').replace('%d', '25').replace('%B', 'December').replace('%b', 'Dec').replace('%H', '00').replace('%M', '00').replace('%S', '00').replace('T', 'T').replace('Z', 'Z'))], fmt)
            except ValueError:
                continue

        # Try parsing with just the date part
        try:
            return datetime.strptime(date_str[:10], '%Y-%m-%d')
        except ValueError:
            pass

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

    # =========================================================================
    # PUBLIC API METHODS
    # =========================================================================
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
        try:
            trades = self.fetch_recent_trades()
        except Exception as e:
            logger.error(f"Failed to fetch trades for summary: {e}")
            return {
                'total_trades': 0,
                'house_trades': 0,
                'senate_trades': 0,
                'purchases': 0,
                'sales': 0,
                'top_tickers': [],
                'top_members': [],
                'active_source': None,
                'error': str(e),
            }

        if not trades:
            return {
                'total_trades': 0,
                'house_trades': 0,
                'senate_trades': 0,
                'purchases': 0,
                'sales': 0,
                'top_tickers': [],
                'top_members': [],
                'active_source': self._active_source,
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
            'active_source': self._active_source,
        }

    def get_active_source(self) -> Optional[str]:
        """Get the currently active data source."""
        return self._active_source

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
