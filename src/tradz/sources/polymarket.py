"""
Polymarket prediction market data.
Fetches event probabilities for market-relevant predictions.
"""
import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class PolymarketDataSource:
    """Fetches prediction market data from Polymarket."""

    # Polymarket APIs
    GAMMA_API = "https://gamma-api.polymarket.com"
    CLOB_API = "https://clob.polymarket.com"

    # Categories relevant to trading
    RELEVANT_CATEGORIES = [
        'Economics',
        'Crypto',
        'Business',
        'Politics',
        'Finance',
    ]

    def __init__(
        self,
        categories: Optional[List[str]] = None,
        max_markets: int = 20
    ):
        """
        Initialize Polymarket data source.

        Args:
            categories: Categories to filter (uses defaults if not specified)
            max_markets: Maximum markets to fetch
        """
        self.categories = categories or self.RELEVANT_CATEGORIES
        self.max_markets = max_markets
        self.client = httpx.Client(timeout=30.0)

    def fetch_active_markets(self, limit: int = 50) -> List[Dict]:
        """
        Fetch active prediction markets.

        Args:
            limit: Maximum markets to fetch

        Returns:
            List of market data
        """
        try:
            resp = self.client.get(
                f"{self.GAMMA_API}/markets",
                params={
                    "limit": limit,
                    "active": True,
                    "closed": False,
                }
            )
            resp.raise_for_status()
            markets = resp.json()

            logger.info(f"Fetched {len(markets)} active markets from Polymarket")
            return markets

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching Polymarket markets: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching Polymarket markets: {e}")
            return []

    def get_market_by_id(self, market_id: str) -> Optional[Dict]:
        """
        Get details for a specific market.

        Args:
            market_id: Market condition ID

        Returns:
            Market data or None
        """
        try:
            resp = self.client.get(f"{self.GAMMA_API}/markets/{market_id}")
            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            logger.error(f"Error fetching market {market_id}: {e}")
            return None

    def get_trading_relevant_markets(self) -> List[Dict]:
        """
        Get markets relevant to trading decisions.

        Returns:
            List of relevant markets with prices
        """
        markets = self.fetch_active_markets(limit=100)

        relevant = []
        for market in markets:
            # Check category
            category = market.get('category', '')
            tags = market.get('tags', [])

            is_relevant = (
                category in self.categories or
                any(tag in self.categories for tag in tags)
            )

            if is_relevant:
                # Extract key info
                processed = self._process_market(market)
                if processed:
                    relevant.append(processed)

            if len(relevant) >= self.max_markets:
                break

        logger.info(f"Found {len(relevant)} trading-relevant markets")
        return relevant

    def _process_market(self, market: Dict) -> Optional[Dict]:
        """
        Process raw market data into clean format.

        Args:
            market: Raw market data

        Returns:
            Processed market data or None
        """
        try:
            # Get outcomes and prices
            outcomes = market.get('outcomes', [])
            outcome_prices = market.get('outcomePrices', [])

            if not outcomes:
                return None

            # Build outcomes list with prices
            outcome_data = []
            for i, outcome in enumerate(outcomes):
                price = float(outcome_prices[i]) if i < len(outcome_prices) else 0.5
                outcome_data.append({
                    'name': outcome,
                    'price': price,
                    'probability_pct': round(price * 100, 1),
                })

            return {
                'id': market.get('id', ''),
                'condition_id': market.get('conditionId', ''),
                'question': market.get('question', ''),
                'description': market.get('description', '')[:500],  # Truncate
                'category': market.get('category', ''),
                'tags': market.get('tags', []),
                'outcomes': outcome_data,
                'volume': market.get('volume', 0),
                'liquidity': market.get('liquidity', 0),
                'end_date': market.get('endDate', ''),
                'created_at': market.get('createdAt', ''),
                'url': f"https://polymarket.com/event/{market.get('slug', '')}",
            }

        except Exception as e:
            logger.error(f"Error processing market: {e}")
            return None

    def search_markets(self, query: str) -> List[Dict]:
        """
        Search for markets matching a query.

        Args:
            query: Search query

        Returns:
            List of matching markets
        """
        try:
            resp = self.client.get(
                f"{self.GAMMA_API}/markets",
                params={
                    "limit": 20,
                    "active": True,
                    "closed": False,
                    # Note: Gamma API search may vary
                }
            )
            resp.raise_for_status()
            markets = resp.json()

            # Filter by query in question or description
            query_lower = query.lower()
            matches = []

            for market in markets:
                question = market.get('question', '').lower()
                description = market.get('description', '').lower()

                if query_lower in question or query_lower in description:
                    processed = self._process_market(market)
                    if processed:
                        matches.append(processed)

            return matches

        except Exception as e:
            logger.error(f"Error searching markets for '{query}': {e}")
            return []

    def find_company_related_markets(self, company_name: str) -> List[Dict]:
        """
        Find markets related to a specific company.

        Args:
            company_name: Company name to search

        Returns:
            List of related markets
        """
        return self.search_markets(company_name)

    def get_high_volume_markets(self, min_volume: float = 100000) -> List[Dict]:
        """
        Get high-volume markets.

        Args:
            min_volume: Minimum volume threshold

        Returns:
            List of high-volume markets
        """
        markets = self.fetch_active_markets(limit=100)

        high_volume = []
        for market in markets:
            volume = market.get('volume', 0)
            try:
                if float(volume) >= min_volume:
                    processed = self._process_market(market)
                    if processed:
                        high_volume.append(processed)
            except (ValueError, TypeError):
                continue

        # Sort by volume descending
        high_volume.sort(key=lambda x: x.get('volume', 0), reverse=True)

        return high_volume[:self.max_markets]

    def get_summary(self) -> Dict:
        """
        Get summary of Polymarket data.

        Returns:
            Summary dict
        """
        relevant_markets = self.get_trading_relevant_markets()

        # Group by category
        by_category: Dict[str, int] = {}
        for m in relevant_markets:
            cat = m.get('category', 'Other')
            by_category[cat] = by_category.get(cat, 0) + 1

        # Find high probability events (>80% or <20%)
        high_probability = []
        for m in relevant_markets:
            for outcome in m.get('outcomes', []):
                prob = outcome.get('probability_pct', 50)
                if prob >= 80 or prob <= 20:
                    high_probability.append({
                        'question': m.get('question', ''),
                        'outcome': outcome.get('name', ''),
                        'probability': prob,
                    })

        return {
            'total_markets': len(relevant_markets),
            'by_category': by_category,
            'high_probability_events': high_probability[:10],
            'markets': relevant_markets,
        }

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
