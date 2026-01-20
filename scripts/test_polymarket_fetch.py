
import sys
import os
import logging
import json

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from tradz.sources.polymarket import PolymarketDataSource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fetch():
    print("Testing Polymarket Fetch...")
    
    with PolymarketDataSource() as source:
        print("\n1. Testing fetch_active_markets...")
        markets = source.fetch_active_markets(limit=20) 
        print(f"Fetched {len(markets)} markets")
        
        print("\n2. Testing get_trading_relevant_markets...")
        relevant = source.get_trading_relevant_markets()
        print(f"Fetched {len(relevant)} relevant markets")
        
        if relevant:
            for i, m in enumerate(relevant[:5]):
                cat = m.get('category')
                print(f"Market {i} Category Type: {type(cat)}")
                print(f"Market {i} Category Value: {cat}")
                
                # Check outcomes just in case
                outcomes = m.get('outcomes', [])
                print(f"Market {i} Outcomes Type: {type(outcomes)}")
                if outcomes:
                     print(f"Market {i} Outcome 0 Type: {type(outcomes[0])}")
                     print(f"Market {i} Outcome 0 keys: {outcomes[0].keys()}")
                
                if not isinstance(cat, (str, type(None))):
                    print(f"WARNING: Category is not a string! It is {type(cat)}")

if __name__ == "__main__":
    test_fetch()
