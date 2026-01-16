"""
Data aggregator for multi-source signal collection.
Orchestrates fetching from all data sources and combines results.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .sources import (
    EquitiesDataSource,
    CryptoDataSource,
    CongressDataSource,
    HedgeFundDataSource,
    PolymarketDataSource,
    NewsDataSource,
    SECFilingsDataSource,
)

logger = logging.getLogger(__name__)


class DataAggregator:
    """Aggregates data from multiple sources for report generation."""

    def __init__(self, config: Dict):
        """
        Initialize data aggregator.

        Args:
            config: Configuration dict from config.yaml
        """
        self.config = config
        self.data_dir = Path(config.get('data_dir', 'data'))
        self.data_dir.mkdir(exist_ok=True)

    def fetch_all(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch data from all enabled sources.

        Args:
            date: Report date (defaults to today)

        Returns:
            Dict with all aggregated data
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"Starting data aggregation for {date}")

        data = {
            'date': date,
            'generated_at': datetime.now().isoformat(),
            'sources': {},
            'errors': [],
        }

        # Fetch equities
        equities_data = self._fetch_equities()
        data['sources']['equities'] = equities_data

        # Fetch crypto
        crypto_data = self._fetch_crypto()
        data['sources']['crypto'] = crypto_data

        # Fetch congress trades
        if self.config.get('congress', {}).get('enabled', True):
            congress_data = self._fetch_congress()
            data['sources']['congress'] = congress_data

        # Fetch hedge fund 13F
        if self.config.get('hedgefunds', {}).get('enabled', True):
            hedgefunds_data = self._fetch_hedgefunds()
            data['sources']['hedgefunds'] = hedgefunds_data

        # Fetch Polymarket
        if self.config.get('polymarket', {}).get('enabled', True):
            polymarket_data = self._fetch_polymarket()
            data['sources']['polymarket'] = polymarket_data

        # Fetch news
        if self.config.get('news', {}).get('enabled', True):
            news_data = self._fetch_news()
            data['sources']['news'] = news_data

        # Fetch SEC filings
        if self.config.get('sec_filings', {}).get('enabled', True):
            sec_data = self._fetch_sec_filings()
            data['sources']['sec_filings'] = sec_data

        # Fetch broker data (if enabled)
        if self.config.get('broker', {}).get('enabled', False):
            broker_data = self._fetch_broker()
            data['sources']['broker'] = broker_data

        # Add summary
        data['summary'] = self._generate_summary(data)

        logger.info(f"Data aggregation complete. Sources: {len(data['sources'])}")
        return data

    def _fetch_equities(self) -> Dict:
        """Fetch equities data."""
        try:
            tickers = self.config.get('equities', {}).get('tickers', [])
            if not tickers:
                return {'error': 'No tickers configured'}

            source = EquitiesDataSource(
                max_retries=self.config.get('max_retries', 3),
                retry_delay=self.config.get('retry_delay', 2)
            )

            data = source.get_latest_data(tickers, days=60)

            # Convert DataFrames to serializable format
            result = {}
            for ticker, df in data.items():
                if df is not None and not df.empty:
                    result[ticker] = {
                        'last_price': float(df['Close'].iloc[-1]),
                        'day_return': float((df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100) if len(df) > 1 else 0,
                        'week_return': float((df['Close'].iloc[-1] / df['Close'].iloc[-7] - 1) * 100) if len(df) >= 7 else 0,
                        'volume': int(df['Volume'].iloc[-1]),
                        'data_points': len(df),
                    }

            logger.info(f"Fetched data for {len(result)}/{len(tickers)} equities")
            return {'data': result, 'count': len(result)}

        except Exception as e:
            logger.error(f"Error fetching equities: {e}")
            return {'error': str(e)}

    def _fetch_crypto(self) -> Dict:
        """Fetch crypto data."""
        try:
            pairs = self.config.get('crypto', {}).get('pairs', [])
            if not pairs:
                return {'error': 'No pairs configured'}

            source = CryptoDataSource(
                exchange_id=self.config.get('crypto', {}).get('exchange', 'binance'),
                max_retries=self.config.get('max_retries', 3),
                retry_delay=self.config.get('retry_delay', 2)
            )

            data = source.get_latest_data(pairs, days=60)

            # Convert DataFrames to serializable format
            result = {}
            for pair, df in data.items():
                if df is not None and not df.empty:
                    result[pair] = {
                        'last_price': float(df['Close'].iloc[-1]),
                        'day_return': float((df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100) if len(df) > 1 else 0,
                        'week_return': float((df['Close'].iloc[-1] / df['Close'].iloc[-7] - 1) * 100) if len(df) >= 7 else 0,
                        'volume': float(df['Volume'].iloc[-1]),
                        'data_points': len(df),
                    }

            logger.info(f"Fetched data for {len(result)}/{len(pairs)} crypto pairs")
            return {'data': result, 'count': len(result)}

        except Exception as e:
            logger.error(f"Error fetching crypto: {e}")
            return {'error': str(e)}

    def _fetch_congress(self) -> Dict:
        """Fetch congress trading data."""
        try:
            congress_config = self.config.get('congress', {})
            source = CongressDataSource(
                lookback_days=congress_config.get('lookback_days', 30),
                min_amount=congress_config.get('min_amount', 15000)
            )

            trades = source.fetch_recent_trades()
            summary = source.get_summary()

            # Get watchlist overlap
            tickers = self.config.get('equities', {}).get('tickers', [])
            overlap = source.get_watchlist_overlap(tickers)

            source.close()

            logger.info(f"Fetched {len(trades)} congress trades")
            return {
                'trades': trades[:50],  # Limit for JSON size
                'summary': summary,
                'watchlist_overlap': overlap,
                'count': len(trades),
            }

        except Exception as e:
            logger.error(f"Error fetching congress data: {e}")
            return {'error': str(e)}

    def _fetch_hedgefunds(self) -> Dict:
        """Fetch hedge fund 13F data."""
        try:
            hf_config = self.config.get('hedgefunds', {})

            # Convert notable_funds list to dict if needed
            notable_funds = None
            if 'notable_funds' in hf_config:
                notable_funds_list = hf_config['notable_funds']
                # If it's a list of CIKs, use default names
                if isinstance(notable_funds_list, list):
                    notable_funds = {cik: f"Fund {cik}" for cik in notable_funds_list}

            source = HedgeFundDataSource(
                notable_funds=notable_funds,
                min_position_change_pct=hf_config.get('min_position_change_pct', 25.0)
            )

            summary = source.get_fund_summary()
            source.close()

            logger.info(f"Fetched {summary.get('filings_found', 0)} hedge fund 13F filings")
            return summary

        except Exception as e:
            logger.error(f"Error fetching hedge fund data: {e}")
            return {'error': str(e)}

    def _fetch_polymarket(self) -> Dict:
        """Fetch Polymarket data."""
        try:
            pm_config = self.config.get('polymarket', {})
            source = PolymarketDataSource(
                categories=pm_config.get('categories'),
                max_markets=pm_config.get('max_markets', 20)
            )

            summary = source.get_summary()
            source.close()

            logger.info(f"Fetched {summary.get('total_markets', 0)} Polymarket markets")
            return summary

        except Exception as e:
            logger.error(f"Error fetching Polymarket data: {e}")
            return {'error': str(e)}

    def _fetch_news(self) -> Dict:
        """Fetch news data."""
        try:
            news_config = self.config.get('news', {})
            source = NewsDataSource(
                max_articles_per_ticker=news_config.get('max_articles_per_ticker', 10)
            )

            # Fetch for watchlist tickers
            tickers = self.config.get('equities', {}).get('tickers', [])[:10]  # Limit to top 10
            news_by_ticker = source.fetch_news_for_watchlist(tickers)

            # Get market headlines
            headlines = source.get_market_headlines()

            summary = source.get_summary(news_by_ticker)
            source.close()

            logger.info(f"Fetched {summary.get('total_articles', 0)} news articles")
            return {
                'by_ticker': news_by_ticker,
                'headlines': headlines[:10],
                'summary': summary,
            }

        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return {'error': str(e)}

    def _fetch_sec_filings(self) -> Dict:
        """Fetch SEC filings data."""
        try:
            sec_config = self.config.get('sec_filings', {})
            source = SECFilingsDataSource()

            # Fetch for watchlist tickers
            tickers = self.config.get('equities', {}).get('tickers', [])[:10]  # Limit
            form_types = sec_config.get('form_types', ['10-K', '10-Q', '8-K'])

            filings_by_ticker = source.get_filings_for_watchlist(tickers, form_types)
            summary = source.get_summary(filings_by_ticker)
            source.close()

            logger.info(f"Fetched {summary.get('total_filings', 0)} SEC filings")
            return {
                'by_ticker': filings_by_ticker,
                'summary': summary,
            }

        except Exception as e:
            logger.error(f"Error fetching SEC filings: {e}")
            return {'error': str(e)}

    def _fetch_broker(self) -> Dict:
        """Fetch broker data (if configured)."""
        try:
            broker_config = self.config.get('broker', {})
            broker_type = broker_config.get('type', 'ibkr')

            if broker_type == 'ibkr':
                from .sources.brokers import IBKRBroker

                broker = IBKRBroker(
                    host=broker_config.get('host'),
                    port=broker_config.get('port'),
                    client_id=broker_config.get('client_id')
                )

                if broker.authenticate():
                    summary = broker.get_portfolio_summary()
                    broker.disconnect()
                    logger.info(f"Fetched {summary.get('positions_count', 0)} positions from IBKR")
                    return summary
                else:
                    return {'error': 'Failed to connect to IBKR'}

            return {'error': f'Unknown broker type: {broker_type}'}

        except ImportError:
            return {'error': 'IBKR integration not available (ib_insync not installed)'}
        except Exception as e:
            logger.error(f"Error fetching broker data: {e}")
            return {'error': str(e)}

    def _generate_summary(self, data: Dict) -> Dict:
        """Generate summary of aggregated data."""
        sources = data.get('sources', {})

        summary = {
            'sources_fetched': len(sources),
            'sources_with_errors': sum(1 for s in sources.values() if 'error' in s),
        }

        # Equities summary
        if 'equities' in sources and 'data' in sources['equities']:
            eq_data = sources['equities']['data']
            summary['equities_count'] = len(eq_data)
            if eq_data:
                top_gainer = max(eq_data.items(), key=lambda x: x[1].get('day_return', 0))
                top_loser = min(eq_data.items(), key=lambda x: x[1].get('day_return', 0))
                summary['top_equity_gainer'] = {'ticker': top_gainer[0], 'return': top_gainer[1].get('day_return', 0)}
                summary['top_equity_loser'] = {'ticker': top_loser[0], 'return': top_loser[1].get('day_return', 0)}

        # Congress summary
        if 'congress' in sources and 'watchlist_overlap' in sources['congress']:
            overlap = sources['congress']['watchlist_overlap']
            summary['congress_watchlist_matches'] = len(overlap)
            if overlap:
                summary['congress_notable'] = [
                    {'ticker': t['ticker'], 'member': t['member'], 'type': t['type']}
                    for t in overlap[:5]
                ]

        # Polymarket summary
        if 'polymarket' in sources and 'high_probability_events' in sources['polymarket']:
            events = sources['polymarket']['high_probability_events']
            summary['polymarket_high_prob_events'] = len(events)

        return summary

    def save_data(self, data: Dict, date: Optional[str] = None) -> Path:
        """
        Save aggregated data to JSON file.

        Args:
            data: Aggregated data dict
            date: Date string for filename

        Returns:
            Path to saved file
        """
        if date is None:
            date = data.get('date', datetime.now().strftime('%Y-%m-%d'))

        filepath = self.data_dir / f"{date}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)

        logger.info(f"Saved aggregated data to {filepath}")
        return filepath

    def load_data(self, date: str) -> Optional[Dict]:
        """
        Load previously saved data.

        Args:
            date: Date string

        Returns:
            Data dict or None
        """
        filepath = self.data_dir / f"{date}.json"

        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
