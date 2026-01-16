"""
Hedge fund 13F filings from SEC EDGAR.
Tracks institutional holdings and changes.
"""
import logging
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

import httpx

logger = logging.getLogger(__name__)


@dataclass
class HoldingChange:
    """Represents a change in fund holdings."""
    cik: str
    fund_name: str
    ticker: str
    company_name: str
    shares_current: int
    shares_previous: int
    change_pct: float
    market_value: float
    filing_date: str

    def to_dict(self) -> Dict:
        return asdict(self)


class HedgeFundDataSource:
    """Fetches 13F filings from SEC EDGAR."""

    # Notable funds to track (CIK numbers)
    DEFAULT_NOTABLE_FUNDS = {
        '0001067983': 'Berkshire Hathaway',
        '0001350694': 'Citadel Advisors',
        '0001336528': 'Renaissance Technologies',
        '0001649339': 'Tiger Global',
        '0001056389': 'Bridgewater Associates',
        '0001541617': 'Pershing Square',
        '0001079114': 'Appaloosa Management',
        '0001167483': 'Icahn Associates',
        '0001364742': 'Greenlight Capital',
        '0001061768': 'Third Point',
    }

    SEC_EDGAR_BASE = "https://data.sec.gov"

    def __init__(
        self,
        notable_funds: Optional[Dict[str, str]] = None,
        min_position_change_pct: float = 25.0,
        user_agent: Optional[str] = None
    ):
        """
        Initialize hedge fund data source.

        Args:
            notable_funds: Dict of CIK -> Fund Name to track
            min_position_change_pct: Minimum position change to report
            user_agent: Required by SEC
        """
        self.notable_funds = notable_funds or self.DEFAULT_NOTABLE_FUNDS
        self.min_position_change_pct = min_position_change_pct
        self.user_agent = user_agent or os.getenv(
            'SEC_USER_AGENT',
            'Tradz/1.0 (contact@example.com)'
        )
        self.client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": self.user_agent}
        )

    def fetch_latest_13f(self, cik: str) -> Optional[Dict]:
        """
        Fetch latest 13F filing for a fund.

        Args:
            cik: Fund CIK number

        Returns:
            Filing info dict or None
        """
        cik_padded = cik.zfill(10)

        try:
            url = f"{self.SEC_EDGAR_BASE}/submissions/CIK{cik_padded}.json"
            resp = self.client.get(url)
            resp.raise_for_status()
            data = resp.json()

            # Find most recent 13F-HR filing
            filings = data.get('filings', {}).get('recent', {})
            forms = filings.get('form', [])
            accession_numbers = filings.get('accessionNumber', [])
            filing_dates = filings.get('filingDate', [])

            for i, form in enumerate(forms):
                if form == '13F-HR':
                    return {
                        'cik': cik_padded,
                        'fund_name': data.get('name', self.notable_funds.get(cik_padded, 'Unknown')),
                        'accession_number': accession_numbers[i] if i < len(accession_numbers) else '',
                        'filing_date': filing_dates[i] if i < len(filing_dates) else '',
                        'form': form,
                    }

            logger.warning(f"No 13F-HR found for CIK {cik}")
            return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching 13F for CIK {cik}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching 13F for CIK {cik}: {e}")
            return None

    def get_all_latest_filings(self) -> List[Dict]:
        """
        Get latest 13F filings for all notable funds.

        Returns:
            List of filing info dicts
        """
        filings = []

        for cik, fund_name in self.notable_funds.items():
            filing = self.fetch_latest_13f(cik)
            if filing:
                filings.append(filing)
            else:
                logger.warning(f"Could not fetch 13F for {fund_name} (CIK: {cik})")

        logger.info(f"Fetched {len(filings)}/{len(self.notable_funds)} 13F filings")
        return filings

    def get_holdings_from_13f(self, cik: str, accession_number: str) -> List[Dict]:
        """
        Parse holdings from a 13F filing.

        Note: Full implementation would parse the XML filing.
        This is a simplified version that returns filing metadata.

        Args:
            cik: Fund CIK
            accession_number: Filing accession number

        Returns:
            List of holdings (simplified)
        """
        # Full implementation would:
        # 1. Fetch the 13F XML file
        # 2. Parse the infotable
        # 3. Extract holdings with CUSIP, shares, value

        # For now, return the filing URL
        cik_clean = cik.lstrip('0')
        accession_clean = accession_number.replace('-', '')

        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}"

        return [{
            'cik': cik,
            'accession_number': accession_number,
            'filing_url': filing_url,
            'note': 'Full holdings parsing requires XML processing',
        }]

    def get_fund_summary(self) -> Dict:
        """
        Get summary of tracked funds and their latest filings.

        Returns:
            Summary dict
        """
        filings = self.get_all_latest_filings()

        # Group by filing date
        by_date: Dict[str, List[Dict]] = {}
        for f in filings:
            date = f.get('filing_date', 'Unknown')
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(f)

        return {
            'tracked_funds': len(self.notable_funds),
            'filings_found': len(filings),
            'latest_filings': filings,
            'filings_by_date': by_date,
            'min_position_change_pct': self.min_position_change_pct,
        }

    def check_watchlist_holdings(self, watchlist: List[str]) -> Dict:
        """
        Check if any notable funds hold watchlist stocks.

        Note: This requires full 13F parsing which is complex.
        Returns placeholder data structure.

        Args:
            watchlist: List of ticker symbols

        Returns:
            Dict with watchlist overlap info
        """
        # Full implementation would:
        # 1. Fetch all 13F filings
        # 2. Parse holdings for each
        # 3. Match against watchlist via CUSIP mapping

        return {
            'watchlist': watchlist,
            'fund_count': len(self.notable_funds),
            'note': 'Full watchlist matching requires CUSIP mapping',
            'latest_filings': self.get_all_latest_filings(),
        }

    def get_filing_url(self, cik: str, accession_number: str) -> str:
        """
        Get URL for viewing a 13F filing.

        Args:
            cik: Fund CIK
            accession_number: Filing accession number

        Returns:
            SEC EDGAR URL
        """
        cik_clean = cik.lstrip('0')
        accession_clean = accession_number.replace('-', '')
        return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_clean}&type=13F-HR&dateb=&owner=include&count=10"

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
