
import sys
import os
from pathlib import Path
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path.cwd()))

from src.tradz.database import init_database
from src.tradz.models import Observation, SourceType
from src.tradz.signals import SignalGenerator

logging.basicConfig(level=logging.INFO)

def verify_signals():
    db_path = Path("data/test_verify_signals.duckdb")
    if db_path.exists():
        os.remove(db_path)
        
    print("Initialize DB...")
    db = init_database(db_path)
    
    # 1. Insert Observations
    print("Inserting test observations...")
    obs = Observation(
        source=SourceType.NEWS,
        entity_ticker="AAPL",
        summary="Apple announces new AI features",
        quality_score=0.9,
        observed_at=datetime.utcnow()
    )
    db.insert_observation(obs)
    
    # 2. Create Dummy Market Data
    print("Creating dummy market data...")
    dates = pd.date_range(end=datetime.now(), periods=60)
    
    # Create an anomaly: sharp jump at the end
    close = [100.0] * 58 + [102.0, 110.0] # 10% jump
    volume = [1000] * 58 + [1200, 5000]
    
    df = pd.DataFrame({
        'Close': close,
        'Volume': volume
    }, index=dates)
    
    equity_data = {"AAPL": df}
    crypto_data = {}
    
    # 3. Generate Signals
    print("Generating signals...")
    config = {"thresholds": {}}
    gen = SignalGenerator(config, db)
    
    results = gen.generate_signals(equity_data, crypto_data)
    
    signals = results['all_signals']
    print(f"Generated {len(signals)} signals")
    
    if not signals:
        print("❌ No signals generated")
        return False
        
    aapl_signal = signals[0]
    print(f"AAPL Signal: {aapl_signal}")
    
    # Verify scores
    metrics = aapl_signal['metrics']
    print(f"Metrics: {metrics}")
    
    # Check if anomaly score is high (due to price jump)
    # The signal dict doesn't have 'anomaly_score' key directly in the legacy dict,
    # but I added `Signal.to_dict()` fields to it?
    # In `signals.py`: returns `signal.to_dict()` + legacy keys.
    # `Signal.to_dict()` should have `anomaly_score`.
    
    print(f"Anomaly Score: {aapl_signal.get('anomaly_score')}")
    print(f"Catalyst Score: {aapl_signal.get('catalyst_score')}")
    
    if aapl_signal.get('anomaly_score', 0) > 60:
        print("✅ Anomaly score reflects price jump")
    else:
        print(f"❌ Anomaly score too low: {aapl_signal.get('anomaly_score')}")
        return False
        
    if aapl_signal.get('catalyst_score', 0) > 50:
        print("✅ Catalyst score reflects news observation")
    else:
        print(f"❌ Catalyst score too low: {aapl_signal.get('catalyst_score')}")
        return False
        
    db.close()
    if db_path.exists():
        os.remove(db_path)
    return True

if __name__ == "__main__":
    success = verify_signals()
    sys.exit(0 if success else 1)
