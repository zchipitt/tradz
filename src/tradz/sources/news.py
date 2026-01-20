"""
News aggregation from multiple sources.
- Yahoo Finance (free, via yfinance)
- NewsAPI (optional, requires API key)
"""
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class NewsDataSource:
    """Aggregates news from multiple sources."""

    NEWSAPI_BASE = "https://newsapi.org/v2"

    def __init__(self, max_articles_per_ticker: int = 10):
        """
        Initialize news data source.

        Args:
            max_articles_per_ticker: Maximum articles to fetch per ticker
        """
        self.max_articles = max_articles_per_ticker
        self.newsapi_key = os.getenv('NEWSAPI_KEY', '')
        self.client = httpx.Client(timeout=30.0)

    def fetch_company_news(self, ticker: str, company_name: Optional[str] = None) -> List[Dict]:
        """
        Fetch recent news for a company.

        Args:
            ticker: Stock ticker symbol
            company_name: Company name for better search (optional)

        Returns:
            List of news articles
        """
        news = []

        # Try Yahoo Finance first (free, no API key needed)
        yahoo_news = self._fetch_from_yahoo(ticker)
        news.extend(yahoo_news)

        # Try NewsAPI if available and we need more articles
        if self.newsapi_key and len(news) < self.max_articles:
            query = company_name or ticker
            newsapi_articles = self._fetch_from_newsapi(query)
            news.extend(newsapi_articles)

        # Deduplicate and limit
        news = self._deduplicate_news(news)
        return news[:self.max_articles]

    def _fetch_from_yahoo(self, ticker: str) -> List[Dict]:
        """Fetch news from Yahoo Finance via yfinance."""
        try:
            import yfinance as yf

            stock = yf.Ticker(ticker)
            raw_news = stock.news or []

            articles = []
            for item in raw_news[:self.max_articles]:
                # yfinance returns news with nested 'content' object
                content = item.get('content', {})
                
                # Extract URL from canonicalUrl or clickThroughUrl
                url = ''
                if 'canonicalUrl' in content:
                    url = content['canonicalUrl'].get('url', '')
                elif 'clickThroughUrl' in content:
                    url = content['clickThroughUrl'].get('url', '')
                
                # Extract provider name
                provider = content.get('provider', {})
                source = provider.get('displayName', 'Yahoo Finance')
                
                # Parse timestamp
                pub_date = content.get('pubDate', '')
                
                articles.append({
                    'title': content.get('title', ''),
                    'source': source,
                    'url': url,
                    'published_at': pub_date,
                    'description': content.get('summary', ''),
                    'ticker': ticker,
                    'source_api': 'yahoo',
                })

            logger.info(f"Fetched {len(articles)} articles for {ticker} from Yahoo")
            return articles

        except Exception as e:
            logger.error(f"Yahoo news error for {ticker}: {e}")
            return []

    def _fetch_from_newsapi(self, query: str) -> List[Dict]:
        """Fetch from NewsAPI."""
        if not self.newsapi_key:
            return []

        try:
            resp = self.client.get(
                f"{self.NEWSAPI_BASE}/everything",
                params={
                    'q': query,
                    'sortBy': 'publishedAt',
                    'pageSize': self.max_articles,
                    'apiKey': self.newsapi_key,
                    'language': 'en',
                }
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get('status') != 'ok':
                logger.warning(f"NewsAPI returned status: {data.get('status')}")
                return []

            articles = []
            for a in data.get('articles', []):
                articles.append({
                    'title': a.get('title', ''),
                    'source': a.get('source', {}).get('name', 'Unknown'),
                    'url': a.get('url', ''),
                    'published_at': a.get('publishedAt', ''),
                    'description': a.get('description', ''),
                    'ticker': '',
                    'source_api': 'newsapi',
                })

            logger.info(f"Fetched {len(articles)} articles for '{query}' from NewsAPI")
            return articles

        except httpx.HTTPError as e:
            logger.error(f"NewsAPI HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return []

    def get_market_headlines(self) -> List[Dict]:
        """
        Get general market headlines.

        Returns:
            List of market news articles
        """
        # Use major market ETFs and indices for general news
        market_tickers = ['SPY', 'QQQ', 'DIA']
        all_news = []

        for ticker in market_tickers:
            news = self._fetch_from_yahoo(ticker)
            all_news.extend(news)

        # Also try NewsAPI with market terms
        if self.newsapi_key:
            market_news = self._fetch_from_newsapi('stock market OR S&P 500 OR Federal Reserve')
            all_news.extend(market_news)

        return self._deduplicate_news(all_news)[:20]

    def fetch_news_for_watchlist(self, tickers: List[str]) -> Dict[str, List[Dict]]:
        """
        Fetch news for all tickers in a watchlist.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dict mapping ticker to list of articles
        """
        results = {}

        for ticker in tickers:
            try:
                news = self.fetch_company_news(ticker)
                if news:
                    results[ticker] = news
            except Exception as e:
                logger.error(f"Error fetching news for {ticker}: {e}")
                results[ticker] = []

        return results

    def _format_timestamp(self, timestamp: Optional[int]) -> str:
        """Convert Unix timestamp to ISO format string."""
        if not timestamp:
            return ''
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.isoformat()
        except Exception:
            return ''

    def _deduplicate_news(self, news: List[Dict]) -> List[Dict]:
        """Remove duplicate news items by title."""
        seen_titles = set()
        unique = []

        for item in news:
            title = item.get('title', '').strip().lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique.append(item)

        return unique

    def get_summary(self, news_by_ticker: Dict[str, List[Dict]]) -> Dict:
        """
        Get summary of fetched news.

        Args:
            news_by_ticker: Dict mapping ticker to articles

        Returns:
            Summary dict
        """
        total_articles = sum(len(articles) for articles in news_by_ticker.values())
        tickers_with_news = [t for t, articles in news_by_ticker.items() if articles]

        # Count by source
        source_counts: Dict[str, int] = {}
        for articles in news_by_ticker.values():
            for a in articles:
                source = a.get('source', 'Unknown')
                source_counts[source] = source_counts.get(source, 0) + 1

        top_sources = sorted(
            source_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'total_articles': total_articles,
            'tickers_with_news': len(tickers_with_news),
            'top_sources': top_sources,
            'newsapi_available': bool(self.newsapi_key),
        }

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
