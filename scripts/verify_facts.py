
import sys
import os
from pathlib import Path
import logging
from datetime import datetime
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path.cwd()))

from src.tradz.reporting.fact_generator import FactGenerator
from src.tradz.models import Signal, Observation, SourceType
from src.tradz.database import init_database

logging.basicConfig(level=logging.INFO)

def verify_facts():
    db_path = Path("data/test_verify_facts.duckdb")
    if db_path.exists():
        os.remove(db_path)
        
    print("Initialize DB...")
    db = init_database(db_path)
    
    # 1. Create Dummy Signals
    print("Creating dummy signals...")
    signal = {
        'symbol': 'AAPL',
        'ticker': 'AAPL',
        'score': 85,
        'anomaly_score': 92.5,
        'catalyst_score': 60.0,
        'flow_score': 50.0,
        'confidence_score': 80.0,
        'metrics': {
            'day_return': 5.2,
            'week_return': 10.1,
            'volume_ratio': 2.5
        }
    }
    
    # 2. Create Dummy Observations
    print("Creating dummy observations...")
    obs = Observation(
        id=uuid4(),
        source=SourceType.NEWS,
        entity_ticker="AAPL",
        summary="Apple announces new AI features",
        quality_score=0.95, # High quality to trigger inclusion
        observed_at=datetime.utcnow()
    )
    
    # 3. Generate Facts
    print("Generating Fact Table...")
    gen = FactGenerator(db)
    fact_table = gen.generate_fact_table([signal], [obs])
    
    facts = fact_table.facts
    print(f"Generated {len(facts)} facts")
    
    # 4. Verify Content
    found_score = False
    found_return = False
    found_obs = False
    
    for f in facts:
        print(f"Fact: {f.category} - {f.fact_id}: {f.value} {f.unit or ''}")
        
        if f.category == 'score' and f.value == 92.5:
            found_score = True
        if f.category == 'metric' and f.value == 5.2:
            found_return = True
        if f.category == 'observation' and "AI features" in str(f.value):
            found_obs = True
            
    if found_score and found_return and found_obs:
        print("✅ All expected facts found!")
        success = True
    else:
        print("❌ Missing expected facts")
        success = False
        
    db.close()
    if db_path.exists():
        os.remove(db_path)
        
    return success

if __name__ == "__main__":
    success = verify_facts()
    sys.exit(0 if success else 1)
