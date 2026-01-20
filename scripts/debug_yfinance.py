#!/usr/bin/env python3
"""
Direct test of yfinance news functionality.
"""
import yfinance as yf

print("Testing yfinance news directly...")
print("=" * 60)

ticker = yf.Ticker("AAPL")
print(f"Ticker: AAPL")
print(f"Info available: {bool(ticker.info)}")

# Check if news is available
try:
    news = ticker.news
    print(f"News attribute type: {type(news)}")
    print(f"News count: {len(news) if news else 0}")
    
    if news:
        print("\nFirst article:")
        print(news[0])
    else:
        print("\n⚠️ No news returned")
        
except AttributeError as e:
    print(f"❌ AttributeError: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 60)
