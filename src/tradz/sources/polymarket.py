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
    # Note: These must match the 'label' values returned by Polymarket API tags
    RELEVANT_CATEGORIES = [
        'Economy',    # API returns 'Economy' not 'Economics'
        'Crypto',
        'Business',
        'Politics',
        'Finance',
        'Stocks',
        'Tech',
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
            # We use the events endpoint because the markets endpoint often lacks 
            # category/tag information which is crucial for filtering.
            resp = self.client.get(
                f"{self.GAMMA_API}/events",
                params={
                    "limit": limit,
                    "active": True,
                    "closed": False,
                }
            )
            resp.raise_for_status()
            events = resp.json()

            all_markets = []
            for event in events:
                # Extract event-level metadata
                category = event.get('category')
                params_tags = event.get('tags', [])
                
                # Convert tags to strings if they are dicts
                event_tags = []
                for tag in params_tags:
                    if isinstance(tag, dict):
                        if 'label' in tag:
                            event_tags.append(tag['label'])
                        elif 'slug' in tag:
                            event_tags.append(tag['slug'])
                    elif isinstance(tag, str):
                        event_tags.append(tag)
                
                # Each event can have multiple markets
                event_markets = event.get('markets', [])
                for market in event_markets:
                    if not market.get('category') and category:
                        market['category'] = str(category) if category else ''
                    elif market.get('category'):
                        # Ensure existing category is string too
                        market['category'] = str(market.get('category'))
                    
                    # Handle market level tags
                    raw_market_tags = market.get('tags', [])
                    market_tags = []
                    for tag in raw_market_tags:
                        if isinstance(tag, dict):
                            if 'label' in tag:
                                market_tags.append(tag['label'])
                            elif 'slug' in tag:
                                market_tags.append(tag['slug'])
                        elif isinstance(tag, str):
                            market_tags.append(tag)

                    # Merge tags
                    if event_tags:
                        market_tags = list(set(market_tags + event_tags))
                    
                    market['tags'] = market_tags
                    # Add event metadata for grouping
                    market['event_title'] = event.get('title')
                    market['event_id'] = str(event.get('id'))
                    market['event_slug'] = event.get('slug', '')  # Event-level slug for URL
                    market['event_image'] = event.get('image')
                    all_markets.append(market)

            logger.info(f"Fetched {len(all_markets)} active markets from Polymarket events")
            return all_markets

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

            # Find matching category from tags
            matched_category = None
            if category in self.categories:
                matched_category = category
            else:
                for tag in tags:
                    if tag in self.categories:
                        matched_category = tag
                        break

            if matched_category:
                # Extract key info
                processed = self._process_market(market)
                if processed:
                    # Set the matched category for proper categorization
                    if not processed.get('category'):
                        processed['category'] = matched_category
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
            if isinstance(outcomes, str):
                try:
                    import json
                    outcomes = json.loads(outcomes)
                except:
                    outcomes = []

            outcome_prices = market.get('outcomePrices', [])
            if isinstance(outcome_prices, str):
                try:
                    import json
                    outcome_prices = json.loads(outcome_prices)
                except:
                    outcome_prices = []

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
                # Use event_slug for event URL (correct), fall back to market slug
                'url': f"https://polymarket.com/event/{market.get('event_slug') or market.get('slug', '')}",
                'event_title': market.get('event_title', ''),
                'event_id': market.get('event_id', ''),
                'event_slug': market.get('event_slug', ''),  # Store for frontend use
                'event_image': market.get('event_image', ''),
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
