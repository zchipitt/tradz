
import sys
import os
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path.cwd()))

from src.tradz.database import init_database
from src.tradz.entity_resolver import EntityResolver

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)

def verify_entity_resolver():
    db_path = Path("data/test_verify.duckdb")
    if db_path.exists():
        os.remove(db_path)
        
    print("Initialize DB...")
    db = init_database(db_path)
    
    resolver = EntityResolver(db)
    
    print("Syncing SEC tickers (this might take a few seconds)...")
    resolver.initialize_reference_data()
    
    # Test resolution
    print("\nTesting resolution...")
    
    # Check simple ticker
    aapl = resolver.resolve_ticker("AAPL")
    if aapl and aapl.name == "Apple Inc.":
        print("✅ Resolved AAPL -> Apple Inc.")
    else:
        print(f"❌ Failed to resolve AAPL: {aapl}")
        return False
        
    # Check CIK resolution
    cik_entity = resolver.resolve_cik("0000320193") # Apple CIK
    if cik_entity and cik_entity.ticker == "AAPL":
         print("✅ Resolved CIK 0000320193 -> AAPL")
    else:
         print(f"❌ Failed to resolve CIK: {cik_entity}")
         return False

    # Check text extraction
    text = "I think $TSLA is going up but $MSFT might drop."
    entities = resolver.extract_entities_from_text(text)
    tickers = sorted([e.ticker for e in entities])
    if tickers == ["MSFT", "TSLA"]:
        print(f"✅ Extracted entities: {tickers}")
    else:
        print(f"❌ Failed extraction. Got: {tickers}")
        return False
        
    db.close()
    if db_path.exists():
        os.remove(db_path)
    return True

if __name__ == "__main__":
    success = verify_entity_resolver()
    sys.exit(0 if success else 1)
