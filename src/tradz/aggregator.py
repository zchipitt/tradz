"""
Data aggregator for multi-source signal collection.
Orchestrates fetching from all data sources and combines results.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .sources import (
    EquitiesDataSource,
    CryptoDataSource,
    CongressDataSource,
    HedgeFundDataSource,
    PolymarketDataSource,
    NewsDataSource,
    SECFilingsDataSource,
)
from .models import Observation, SourceType
from .database import Database, get_database
from .entity_resolver import EntityResolver

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

    # =========================================================================
    # Observation Extraction (New Data Layer)
    # =========================================================================

    def extract_observations(
        self,
        data: Dict,
        resolver: Optional[EntityResolver] = None
    ) -> List[Observation]:
        """
        Extract standardized Observations from aggregated data.

        This converts the raw fetched data into Observation objects
        that can be stored in the database for querying and analysis.

        Args:
            data: Aggregated data dict from fetch_all()
            resolver: EntityResolver instance to link entity IDs

        Returns:
            List of Observation objects
        """
        observations: List[Observation] = []
        sources = data.get('sources', {})
        observed_at = datetime.fromisoformat(data.get('generated_at', datetime.now().isoformat()))

        # Helper to resolve entity ID if resolver is available
        def resolve_id(ticker: Optional[str]) -> Optional[str]:
            if not ticker or not resolver:
                return None
            entity = resolver.resolve_ticker(ticker)
            return entity.id if entity else None

        # Extract equities observations
        if 'equities' in sources and 'data' in sources['equities']:
            for ticker, eq_data in sources['equities']['data'].items():
                obs = Observation(
                    source=SourceType.EQUITIES,
                    entity_ticker=ticker,
                    entity_id=resolve_id(ticker),
                    observed_at=observed_at,
                    effective_at=observed_at,
                    freshness_score=1.0,
                    quality_score=1.0 if eq_data.get('data_points', 0) >= 30 else 0.7,
                    summary=f"{ticker}: ${eq_data.get('last_price', 0):.2f}, day {eq_data.get('day_return', 0):+.1f}%",
                    payload=eq_data,
                )
                observations.append(obs)

        # Extract crypto observations
        if 'crypto' in sources and 'data' in sources['crypto']:
            for pair, cr_data in sources['crypto']['data'].items():
                obs = Observation(
                    source=SourceType.CRYPTO,
                    entity_ticker=pair,
                    # Crypto entities might not be in SEC map, we skip resolve_id for now 
                    # or extend resolver to handle crypto pairs
                    observed_at=observed_at,
                    effective_at=observed_at,
                    freshness_score=1.0,
                    quality_score=1.0 if cr_data.get('data_points', 0) >= 30 else 0.7,
                    summary=f"{pair}: ${cr_data.get('last_price', 0):.2f}, day {cr_data.get('day_return', 0):+.1f}%",
                    payload=cr_data,
                )
                observations.append(obs)

        # Extract congress trade observations
        if 'congress' in sources and 'trades' in sources['congress']:
            for trade in sources['congress'].get('trades', []):
                effective_at = None
                if trade.get('transaction_date'):
                    try:
                        effective_at = datetime.fromisoformat(trade['transaction_date'])
                    except (ValueError, TypeError):
                        pass

                # Congress disclosures have ~45 day delay, lower freshness
                days_delay = (observed_at - effective_at).days if effective_at else 45
                freshness = max(0.1, 1.0 - (days_delay / 60))

                ticker = trade.get('ticker')
                obs = Observation(
                    source=SourceType.CONGRESS,
                    entity_ticker=ticker,
                    entity_id=resolve_id(ticker),
                    observed_at=observed_at,
                    effective_at=effective_at,
                    freshness_score=freshness,
                    quality_score=0.9,
                    summary=f"{trade.get('member')}: {trade.get('type')} {trade.get('ticker')} ({trade.get('amount_range', 'unknown')})",
                    payload=trade,
                )
                observations.append(obs)

        # Extract hedge fund 13F observations
        if 'hedgefunds' in sources and 'filings' in sources['hedgefunds']:
            for filing in sources['hedgefunds'].get('filings', []):
                # 13F filings are quarterly, even lower freshness
                obs = Observation(
                    source=SourceType.HEDGEFUND,
                    entity_ticker=None,  # 13F covers multiple tickers
                    observed_at=observed_at,
                    effective_at=None,
                    freshness_score=0.5,  # Quarterly delay
                    quality_score=0.95,  # Official SEC filing
                    summary=f"13F filing from {filing.get('fund_name', 'Unknown')}",
                    payload=filing,
                )
                observations.append(obs)

        # Extract Polymarket observations
        if 'polymarket' in sources and 'markets' in sources['polymarket']:
            for market in sources['polymarket'].get('markets', []):
                # Try to extract ticker from market question
                question = market.get('question', '')
                entities = resolver.extract_entities_from_text(question) if resolver else []
                primary_entity = entities[0] if entities else None

                obs = Observation(
                    source=SourceType.POLYMARKET,
                    entity_ticker=primary_entity.ticker if primary_entity else None,
                    entity_id=primary_entity.id if primary_entity else None,
                    observed_at=observed_at,
                    effective_at=observed_at,
                    freshness_score=1.0,  # Real-time
                    quality_score=0.7,  # Prediction market, not confirmed
                    summary=f"{market.get('question', 'Unknown')}: {market.get('probability', 0)*100:.0f}%",
                    payload=market,
                )
                observations.append(obs)

        # Extract news observations
        if 'news' in sources and 'by_ticker' in sources['news']:
            for ticker, articles in sources['news'].get('by_ticker', {}).items():
                for article in articles[:5]:  # Limit per ticker
                    obs = Observation(
                        source=SourceType.NEWS,
                        entity_ticker=ticker,
                        entity_id=resolve_id(ticker),
                        observed_at=observed_at,
                        effective_at=observed_at,
                        freshness_score=0.95,  # News is recent
                        quality_score=0.6,  # Unverified news
                        summary=article.get('title', '')[:200],
                        payload=article,
                    )
                    observations.append(obs)

        # Extract SEC filing observations
        if 'sec_filings' in sources and 'by_ticker' in sources['sec_filings']:
            for ticker, filings in sources['sec_filings'].get('by_ticker', {}).items():
                for filing in filings:
                    # 8-K is more recent/important than 10-K/10-Q
                    form_type = filing.get('form', '')
                    quality = 0.95 if form_type == '8-K' else 0.9
                    
                    obs = Observation(
                        source=SourceType.SEC,
                        entity_ticker=ticker,
                        entity_id=resolve_id(ticker),
                        observed_at=observed_at,
                        effective_at=None,
                        freshness_score=0.8,
                        quality_score=quality,
                        summary=f"{ticker} {form_type}: {filing.get('description', '')[:100]}",
                        payload=filing,
                    )
                    observations.append(obs)

        logger.info(f"Extracted {len(observations)} observations from aggregated data")
        return observations

    def save_observations(
        self,
        observations: List[Observation],
        db: Optional[Database] = None
    ) -> int:
        """
        Save observations to the database.

        Args:
            observations: List of Observation objects
            db: Database instance (uses singleton if not provided)

        Returns:
            Count of observations saved
        """
        if db is None:
            db = get_database()

        count = db.insert_observations(observations)
        logger.info(f"Saved {count} observations to database")
        return count

    def fetch_and_store(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch all data and store both as JSON and in database.

        This is the primary entry point for the new data layer,
        combining backward-compatible JSON storage with the new
        DuckDB observation storage.

        Args:
            date: Report date (defaults to today)

        Returns:
            Dict with aggregated data and observation count
        """
        # Fetch all data (existing behavior)
        data = self.fetch_all(date)

        # Save to JSON (backward compatibility)
        self.save_data(data, date)

        # Initialize resolver for linking
        db = get_database()
        resolver = EntityResolver(db)

        # Extract and save observations (new behavior)
        observations = self.extract_observations(data, resolver)
        obs_count = self.save_observations(observations, db)

        # Add observation count to returned data
        data['observations_count'] = obs_count

        return data

