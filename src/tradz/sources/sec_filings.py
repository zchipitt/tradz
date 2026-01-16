"""
SEC filings data (10-K, 10-Q, 8-K) from EDGAR.
"""
import logging
import os
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class SECFilingsDataSource:
    """Fetches SEC filings from EDGAR."""

    SEC_BASE = "https://data.sec.gov"

    def __init__(self, user_agent: Optional[str] = None):
        """
        Initialize SEC filings data source.

        Args:
            user_agent: Required by SEC - format: "AppName/Version (email)"
        """
        self.user_agent = user_agent or os.getenv(
            'SEC_USER_AGENT',
            'Tradz/1.0 (contact@example.com)'
        )
        self.client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": self.user_agent}
        )
        # Cache for CIK lookups
        self._cik_cache: Dict[str, str] = {}
        self._ticker_map: Optional[Dict[str, str]] = None

    def _load_ticker_map(self) -> Dict[str, str]:
        """Load ticker to CIK mapping from SEC."""
        if self._ticker_map is not None:
            return self._ticker_map

        try:
            resp = self.client.get(f"{self.SEC_BASE}/files/company_tickers.json")
            resp.raise_for_status()
            data = resp.json()

            self._ticker_map = {}
            for entry in data.values():
                ticker = entry.get('ticker', '').upper()
                cik = str(entry.get('cik_str', '')).zfill(10)
                if ticker and cik:
                    self._ticker_map[ticker] = cik

            logger.info(f"Loaded {len(self._ticker_map)} ticker-CIK mappings")
            return self._ticker_map

        except Exception as e:
            logger.error(f"Failed to load ticker map: {e}")
            self._ticker_map = {}
            return self._ticker_map

    def get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Get CIK number for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            10-digit CIK or None
        """
        ticker_upper = ticker.upper()

        # Check cache
        if ticker_upper in self._cik_cache:
            return self._cik_cache[ticker_upper]

        # Load ticker map and lookup
        ticker_map = self._load_ticker_map()
        cik = ticker_map.get(ticker_upper)

        if cik:
            self._cik_cache[ticker_upper] = cik

        return cik

    def get_recent_filings(
        self,
        ticker: str,
        form_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent filings for a company.

        Args:
            ticker: Stock ticker symbol
            form_types: List of form types to filter (e.g., ['10-K', '10-Q', '8-K'])
            limit: Maximum number of filings to return

        Returns:
            List of filing records
        """
        if form_types is None:
            form_types = ['10-K', '10-Q', '8-K']

        cik = self.get_company_cik(ticker)
        if not cik:
            logger.warning(f"Could not find CIK for {ticker}")
            return []

        try:
            url = f"{self.SEC_BASE}/submissions/CIK{cik}.json"
            resp = self.client.get(url)
            resp.raise_for_status()
            data = resp.json()

            filings = []
            recent = data.get('filings', {}).get('recent', {})

            forms = recent.get('form', [])
            filing_dates = recent.get('filingDate', [])
            accession_numbers = recent.get('accessionNumber', [])
            primary_documents = recent.get('primaryDocument', [])

            for i, form in enumerate(forms):
                if form in form_types:
                    filings.append({
                        'ticker': ticker,
                        'company_name': data.get('name', ''),
                        'form': form,
                        'filing_date': filing_dates[i] if i < len(filing_dates) else '',
                        'accession_number': accession_numbers[i] if i < len(accession_numbers) else '',
                        'primary_document': primary_documents[i] if i < len(primary_documents) else '',
                        'cik': cik,
                    })

                    if len(filings) >= limit:
                        break

            logger.info(f"Found {len(filings)} filings for {ticker}")
            return filings

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching filings for {ticker}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching filings for {ticker}: {e}")
            return []

    def get_filing_url(self, filing: Dict) -> str:
        """
        Get the URL to view a filing on SEC website.

        Args:
            filing: Filing dict from get_recent_filings

        Returns:
            URL string
        """
        cik = filing.get('cik', '').lstrip('0')
        accession = filing.get('accession_number', '').replace('-', '')
        document = filing.get('primary_document', '')

        if cik and accession and document:
            return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"
        return ''

    def extract_key_metrics(self, ticker: str) -> Optional[Dict]:
        """
        Extract key financial metrics from company facts (XBRL).

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict with key metrics or None
        """
        cik = self.get_company_cik(ticker)
        if not cik:
            return None

        try:
            url = f"{self.SEC_BASE}/api/xbrl/companyfacts/CIK{cik}.json"
            resp = self.client.get(url)
            resp.raise_for_status()
            data = resp.json()

            facts = data.get('facts', {}).get('us-gaap', {})

            metrics = {
                'ticker': ticker,
                'company_name': data.get('entityName', ''),
                'revenues': self._get_latest_fact(facts, 'Revenues'),
                'net_income': self._get_latest_fact(facts, 'NetIncomeLoss'),
                'total_assets': self._get_latest_fact(facts, 'Assets'),
                'stockholders_equity': self._get_latest_fact(facts, 'StockholdersEquity'),
                'eps_basic': self._get_latest_fact(facts, 'EarningsPerShareBasic'),
                'eps_diluted': self._get_latest_fact(facts, 'EarningsPerShareDiluted'),
            }

            # Filter out None values
            metrics = {k: v for k, v in metrics.items() if v is not None}

            return metrics if len(metrics) > 2 else None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error extracting metrics for {ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting metrics for {ticker}: {e}")
            return None

    def _get_latest_fact(self, facts: Dict, concept: str) -> Optional[float]:
        """
        Get latest value for a financial concept.

        Args:
            facts: Facts dict from company facts API
            concept: XBRL concept name

        Returns:
            Latest value or None
        """
        if concept not in facts:
            return None

        units = facts[concept].get('units', {})

        # Try USD first, then shares, then pure
        for unit_type in ['USD', 'shares', 'pure', 'USD/shares']:
            if unit_type in units:
                values = units[unit_type]
                if values:
                    # Get most recent annual (10-K) value
                    annual_values = [
                        v for v in values
                        if v.get('form') == '10-K' and v.get('val') is not None
                    ]
                    if annual_values:
                        latest = max(annual_values, key=lambda x: x.get('end', ''))
                        return latest.get('val')

                    # Fall back to most recent quarterly
                    quarterly_values = [
                        v for v in values
                        if v.get('form') == '10-Q' and v.get('val') is not None
                    ]
                    if quarterly_values:
                        latest = max(quarterly_values, key=lambda x: x.get('end', ''))
                        return latest.get('val')

        return None

    def get_filings_for_watchlist(
        self,
        tickers: List[str],
        form_types: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get recent filings for all tickers in watchlist.

        Args:
            tickers: List of ticker symbols
            form_types: Form types to filter

        Returns:
            Dict mapping ticker to list of filings
        """
        results = {}

        for ticker in tickers:
            try:
                filings = self.get_recent_filings(ticker, form_types, limit=5)
                if filings:
                    results[ticker] = filings
            except Exception as e:
                logger.error(f"Error fetching filings for {ticker}: {e}")

        return results

    def get_summary(self, filings_by_ticker: Dict[str, List[Dict]]) -> Dict:
        """
        Get summary of fetched filings.

        Args:
            filings_by_ticker: Dict mapping ticker to filings

        Returns:
            Summary dict
        """
        total_filings = sum(len(f) for f in filings_by_ticker.values())

        # Count by form type
        form_counts: Dict[str, int] = {}
        for filings in filings_by_ticker.values():
            for f in filings:
                form = f.get('form', 'Unknown')
                form_counts[form] = form_counts.get(form, 0) + 1

        return {
            'total_filings': total_filings,
            'tickers_with_filings': len(filings_by_ticker),
            'form_counts': form_counts,
        }

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
