#!/usr/bin/env python3
"""
Test news fetching - verify Yahoo Finance integration works.
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tradz.sources.news import NewsDataSource


def test_yahoo_finance():
    """Test Yahoo Finance news fetching."""
    print("=" * 60)
    print("Testing Yahoo Finance News Integration")
    print("=" * 60)
    
    news_source = NewsDataSource(max_articles_per_ticker=5)
    
    # Test 1: Single ticker news
    print("\n[TEST 1] Fetching news for AAPL...")
    aapl_news = news_source.fetch_company_news("AAPL", company_name="Apple")
    print(f"✓ Retrieved {len(aapl_news)} articles for AAPL")
    
    if aapl_news:
        print("\nSample article:")
        article = aapl_news[0]
        print(f"  Title: {article.get('title', 'N/A')[:80]}...")
        print(f"  Source: {article.get('source', 'N/A')}")
        print(f"  URL: {article.get('url', 'N/A')[:60]}...")
        print(f"  Published: {article.get('published_at', 'N/A')}")
        print(f"  Source API: {article.get('source_api', 'N/A')}")
    else:
        print("⚠️  No articles found for AAPL")
    
    # Test 2: Multiple tickers
    print("\n[TEST 2] Fetching news for watchlist...")
    watchlist = ['NVDA', 'TSLA', 'MSFT']
    news_by_ticker = news_source.fetch_news_for_watchlist(watchlist)
    
    for ticker, articles in news_by_ticker.items():
        print(f"  {ticker}: {len(articles)} articles")
    
    # Test 3: Market headlines
    print("\n[TEST 3] Fetching market headlines...")
    headlines = news_source.get_market_headlines()
    print(f"✓ Retrieved {len(headlines)} market headlines")
    
    # Test 4: Summary
    print("\n[TEST 4] News summary...")
    summary = news_source.get_summary(news_by_ticker)
    print(f"  Total articles: {summary['total_articles']}")
    print(f"  Tickers with news: {summary['tickers_with_news']}")
    print(f"  NewsAPI available: {summary['newsapi_available']}")
    print(f"  Top sources: {summary['top_sources'][:3]}")
    
    # Verify Yahoo Finance is working
    print("\n" + "=" * 60)
    if aapl_news and all(a.get('source_api') == 'yahoo' for a in aapl_news):
        print("✅ SUCCESS: Yahoo Finance integration working correctly")
        print("✅ No NewsAPI key required - fallback working as expected")
    elif aapl_news:
        print("⚠️  WARNING: Some articles not from Yahoo Finance")
        apis = set(a.get('source_api') for a in aapl_news)
        print(f"   APIs used: {apis}")
    else:
        print("❌ FAILURE: No news data retrieved")
        return False
    
    print("=" * 60)
    news_source.close()
    return True


if __name__ == "__main__":
    try:
        success = test_yahoo_finance()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
