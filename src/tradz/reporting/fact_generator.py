"""
Fact Generator module.
Responsible for converting Signals and Observations into a deterministic FactTable.
These facts serve as the ground truth for LLM narrative generation.
"""
import logging
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

from ..models import FactTable, FactTableEntry, Observation
from ..database import Database

logger = logging.getLogger(__name__)

class FactGenerator:
    """Generates deterministic facts from system data."""
    
    def __init__(self, db: Database):
        self.db = db
        
    def generate_fact_table(
        self, 
        signals: List[Dict], # Signal dicts from aggregator
        observations: List[Observation]
    ) -> FactTable:
        """
        Generate a complete FactTable for the reporting period.
        """
        facts = []
        
        # 1. Generate Signal Facts
        for sig in signals:
            facts.extend(self._extract_signal_facts(sig))
            
        # 2. Generate Observation Facts (for top/important ones)
        # We might not want every single observation, only those linked to signals
        # or those with high quality/freshness.
        
        # Filter observations that are "notable"
        notable_obs = [o for o in observations if o.quality_score > 0.7]
        for obs in notable_obs:
            facts.extend(self._extract_observation_facts(obs))
            
        return FactTable(
            report_date=datetime.utcnow(),
            facts=facts
        )
        
    def _extract_signal_facts(self, signal: Dict) -> List[FactTableEntry]:
        """Convert a signal dict into a list of facts."""
        facts = []
        ticker = signal.get('ticker') or signal.get('symbol')
        if not ticker:
            return []
            
        # Fact: Scores
        for score_type in ['anomaly_score', 'catalyst_score', 'flow_score', 'confidence_score']:
            val = signal.get(score_type)
            if val is not None:
                facts.append(FactTableEntry(
                    fact_id=f"score-{ticker}-{score_type}",
                    category="score",
                    ticker=ticker,
                    value=round(float(val), 1),
                    unit="0-100",
                    timestamp=datetime.utcnow()
                ))
                
        # Fact: Metrics
        metrics = signal.get('metrics', {})
        for key, val in metrics.items():
            # handle numpy floats
            try:
                val_float = float(val)
            except:
                continue
                
            unit = "%" if "return" in key or "change" in key else "msg"
            if "price" in key: unit = "$"
            if "ratio" in key: unit = "x"
            
            facts.append(FactTableEntry(
                fact_id=f"metric-{ticker}-{key}",
                category="metric",
                ticker=ticker,
                value=val_float,
                unit=unit,
                timestamp=datetime.utcnow()
            ))
            
        return facts
        
    def _extract_observation_facts(self, obs: Observation) -> List[FactTableEntry]:
        """Convert an observation into a fact."""
        facts = []
        
        # Provide the summary as a text fact
        facts.append(FactTableEntry(
            fact_id=f"obs-{obs.id}",
            category="observation",
            ticker=obs.entity_ticker,
            value=obs.summary or str(obs.payload),
            source_url=obs.payload.get('url'),
            observation_id=obs.id,
            timestamp=obs.observed_at
        ))
        
        return facts
