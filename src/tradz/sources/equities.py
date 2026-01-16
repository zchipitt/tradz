"""
Equities data source using yfinance.
Fetches US stock market data with retry logic and error handling.
"""
import logging
import time
from typing import Dict, List, Optional
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class EquitiesDataSource:
    """Fetches US equities data from Yahoo Finance."""

    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def fetch_data(self, tickers: List[str], period: str = "60d") -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple tickers.

        Args:
            tickers: List of stock symbols (e.g., ['AAPL', 'GOOGL'])
            period: Period to fetch (e.g., '60d', '3mo')

        Returns:
            Dict mapping ticker to DataFrame with OHLCV data
        """
        results = {}

        for ticker in tickers:
            logger.info(f"Fetching data for {ticker}...")

            for attempt in range(self.max_retries):
                try:
                    stock = yf.Ticker(ticker)
                    df = stock.history(period=period, timeout=10)

                    if df.empty:
                        logger.warning(f"{ticker}: No data returned")
                        break

                    # Validate required columns
                    required_cols = ['Close', 'Volume']
                    if not all(col in df.columns for col in required_cols):
                        logger.warning(f"{ticker}: Missing required columns")
                        break

                    results[ticker] = df
                    logger.info(f"{ticker}: Fetched {len(df)} days of data")
                    break

                except Exception as e:
                    logger.error(f"{ticker}: Attempt {attempt + 1} failed - {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        logger.error(f"{ticker}: All retries exhausted")

        return results

    def get_latest_data(self, tickers: List[str], days: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Get latest N days of data for tickers.

        Args:
            tickers: List of stock symbols
            days: Number of days to fetch

        Returns:
            Dict mapping ticker to DataFrame
        """
        return self.fetch_data(tickers, period=f"{days}d")
