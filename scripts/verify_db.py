
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path.cwd()))

from src.tradz.database import init_database
from src.tradz.models import Observation, SourceType

def verify_database():
    try:
        # 1. Initialize DB
        print("Initializing database...")
        db_path = Path("data/test_verify.duckdb")
        if db_path.exists():
            os.remove(db_path)
            
        db = init_database(db_path)
        
        # 2. Check Tables
        print("\nChecking tables...")
        tables = db.conn.execute("SHOW TABLES").fetchall()
        table_names = [t[0] for t in tables]
        expected_tables = ['entities', 'observations', 'events', 'event_observations', 'signals', 'run_history']
        
        missing = [t for t in expected_tables if t not in table_names]
        if missing:
            print(f"❌ Missing tables: {missing}")
            return False
        print(f"✅ All tables present: {table_names}")
        
        # 3. Test Observation Insert
        print("\nTesting observation insert...")
        obs = Observation(
            source=SourceType.NEWS,
            entity_ticker="AAPL",
            summary="Test observation",
            quality_score=0.9
        )
        
        obs_id = db.insert_observation(obs)
        print(f"Inserted observation: {obs_id}")
        
        fetched = db.get_observations_by_ticker("AAPL")
        if len(fetched) == 1 and fetched[0].id == obs.id:
            print("✅ Observation fetch successful")
        else:
            print("❌ Observation fetch failed")
            return False
            
        # 4. Cleanup
        db.close()
        if db_path.exists():
            os.remove(db_path)
            
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
