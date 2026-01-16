"""
Crypto data source using ccxt.
Fetches cryptocurrency data from major exchanges with fallback support.
"""
import logging
import time
from typing import Dict, List, Optional
import pandas as pd
import ccxt

logger = logging.getLogger(__name__)


class CryptoDataSource:
    """Fetches crypto data from exchanges using ccxt."""

    def __init__(
        self,
        exchange_id: str = "binance",
        max_retries: int = 3,
        retry_delay: int = 2,
        fallback_exchanges: Optional[List[str]] = None
    ):
        self.exchange_id = exchange_id
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.fallback_exchanges = fallback_exchanges or ["coinbase", "kraken"]
        self.exchange = None

    def _init_exchange(self, exchange_id: str) -> Optional[ccxt.Exchange]:
        """Initialize exchange instance with error handling."""
        try:
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({
                'enableRateLimit': True,
                'timeout': 10000,
            })
            logger.info(f"Initialized exchange: {exchange_id}")
            return exchange
        except Exception as e:
            logger.error(f"Failed to initialize {exchange_id}: {str(e)}")
            return None

    def _get_working_exchange(self) -> Optional[ccxt.Exchange]:
        """Get a working exchange, trying fallbacks if needed."""
        if self.exchange:
            return self.exchange

        # Try primary exchange
        self.exchange = self._init_exchange(self.exchange_id)
        if self.exchange:
            return self.exchange

        # Try fallback exchanges
        for fallback in self.fallback_exchanges:
            logger.warning(f"Trying fallback exchange: {fallback}")
            self.exchange = self._init_exchange(fallback)
            if self.exchange:
                return self.exchange

        logger.error("No working exchange found")
        return None

    def fetch_data(self, pairs: List[str], timeframe: str = "1d", limit: int = 60) -> Dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data for multiple trading pairs.

        Args:
            pairs: List of trading pairs (e.g., ['BTC/USDT', 'ETH/USDT'])
            timeframe: Candlestick timeframe (e.g., '1d', '1h')
            limit: Number of candles to fetch

        Returns:
            Dict mapping pair to DataFrame with OHLCV data
        """
        exchange = self._get_working_exchange()
        if not exchange:
            logger.error("No exchange available for data fetching")
            return {}

        results = {}

        for pair in pairs:
            logger.info(f"Fetching data for {pair}...")

            for attempt in range(self.max_retries):
                try:
                    # Fetch OHLCV data
                    ohlcv = exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)

                    if not ohlcv:
                        logger.warning(f"{pair}: No data returned")
                        break

                    # Convert to DataFrame
                    df = pd.DataFrame(
                        ohlcv,
                        columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
                    )
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)

                    results[pair] = df
                    logger.info(f"{pair}: Fetched {len(df)} candles")
                    break

                except ccxt.NetworkError as e:
                    logger.error(f"{pair}: Network error on attempt {attempt + 1} - {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        logger.error(f"{pair}: All retries exhausted")

                except ccxt.ExchangeError as e:
                    logger.error(f"{pair}: Exchange error - {str(e)}")
                    break

                except Exception as e:
                    logger.error(f"{pair}: Unexpected error - {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        logger.error(f"{pair}: All retries exhausted")

        return results

    def get_latest_data(self, pairs: List[str], days: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Get latest N days of data for trading pairs.

        Args:
            pairs: List of trading pairs
            days: Number of days to fetch

        Returns:
            Dict mapping pair to DataFrame
        """
        return self.fetch_data(pairs, timeframe="1d", limit=days)
