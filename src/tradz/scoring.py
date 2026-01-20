"""
Scoring module for calculating 4-dimensional signal scores.

Dimensions:
1. Anomaly: Statistical deviation from history (Price/Vol/Volatility)
2. Catalyst: External events driving action (News/Events)
3. Flow: Money movement (Institutions/Insiders)
4. Confidence: Data quality and verification
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .models import Observation, SourceType

logger = logging.getLogger(__name__)


class Scorer:
    """Calculates component scores for Signals."""

    def __init__(self):
        pass

    from uuid import UUID

    def calculate_scores(
        self,
        df: pd.DataFrame,
        observations: List[Observation]
    ) -> Tuple[float, float, float, float, List[UUID]]:
        """
        Calculate all 4 scores and collect evidence IDs.

        Args:
            df: OHLCV DataFrame
            observations: List of observations for this entity

        Returns:
            Tuple of (anomaly, catalyst, flow, confidence, evidence_ids)
        """
        anomaly, _ = self.calculate_anomaly(df)
        catalyst, cat_ids = self.calculate_catalyst(observations)
        flow, flow_ids = self.calculate_flow(observations)
        confidence, _ = self.calculate_confidence(observations, df)
        
        # Combine evidence IDs
        # We include IDs that contributed to scores (catalyst, flow)
        evidence_ids = list(set(cat_ids + flow_ids))
        
        return anomaly, catalyst, flow, confidence, evidence_ids

    def calculate_anomaly(self, df: pd.DataFrame) -> Tuple[float, List[UUID]]:
        """
        Calculate Market Anomaly Score (0-100).
        Based on Z-scores of returns, volume, and volatility.
        """
        if df.empty or len(df) < 30:
            return 50.0, []

        try:
            # 1. Price Return Z-Score
            returns = df['Close'].pct_change().dropna()
            if len(returns) < 2:
                return 50.0, []
                
            last_return = returns.iloc[-1]
            mean_return = returns.mean()
            std_return = returns.std()
            
            z_price = (last_return - mean_return) / std_return if std_return > 0 else 0
            
            # 2. Volume Z-Score
            volumes = df['Volume'].dropna()
            last_vol = volumes.iloc[-1]
            mean_vol = volumes.mean()
            std_vol = volumes.std()
            
            z_vol = (last_vol - mean_vol) / std_vol if std_vol > 0 else 0
            
            # 3. Volatility Z-Score (change in vol)
            # 7-day vol vs 30-day vol
            vol_7d = returns.tail(7).std()
            vol_30d = returns.tail(30).std()
            
            z_volatility = 0.0
            if vol_30d > 0:
                # How many std devs is the current 7d vol away from "normal" 30d vol?
                # This is a simplification.
                ratio = vol_7d / vol_30d
                z_volatility = (ratio - 1.0) * 3.0  # boost sensitivity
                
            # Combine Z-scores
            # Price move is most important, then volume
            combined_z = (abs(z_price) * 0.5) + (z_vol * 0.3) + (z_volatility * 0.2)
            
            # Map Z to 0-100
            # Z=0 -> 50
            # Z=2 -> 80
            # Z=3 -> 95
            score = 50 + (combined_z * 15)
            return min(max(score, 0), 100), []
            
        except Exception as e:
            logger.error(f"Error calculating anomaly score: {e}")
            return 50.0, []

    def calculate_catalyst(self, observations: List[Observation]) -> Tuple[float, List[UUID]]:
        """
        Calculate Catalyst Score (0-100).
        Based on news, SEC filings, Polymarket events.
        """
        score = 50.0  # Baseline
        evidence_ids = []
        
        # Weights for different sources
        weights = {
            SourceType.SEC: 20,       # Validated filing
            SourceType.NEWS: 10,      # News article
            SourceType.POLYMARKET: 15, # Prediction market
            SourceType.X_SENTIMENT: 5, # Social sentiment
        }
        
        # Consider last 24h observations mostly, decay older ones
        now = datetime.utcnow()
        
        try:
            for obs in observations:
                age_days = (now - obs.observed_at).days + (now - obs.observed_at).seconds / 86400
                if age_days > 3:
                    continue
                    
                # Decay factor: 1.0 at 0h, 0.5 at 24h
                decay = max(0, 1.0 - (age_days / 2.0))
                
                impact = weights.get(obs.source, 5) * decay * obs.quality_score
                
                # Check specifics
                if obs.source == SourceType.SEC:
                    payload = obs.payload or {}
                    form = payload.get('form', '')
                    if form == '8-K':
                        impact *= 1.5  # 8-K is material event
                        
                score += impact
                
                # Keep track if impact meaningful
                if impact > 1.0:
                    evidence_ids.append(obs.id)
                
            return min(max(score, 0), 100), evidence_ids
            
        except Exception as e:
            logger.error(f"Error calculating catalyst score: {e}")
            return 50.0, []

    def calculate_flow(self, observations: List[Observation]) -> Tuple[float, List[UUID]]:
        """
        Calculate Flow Score (0-100).
        Based on Congress trading and Hedge Fund filings.
        """
        score = 50.0
        evidence_ids = []
        
        try:
            for obs in observations:
                impact = 0.0
                if obs.source == SourceType.CONGRESS:
                    payload = obs.payload or {}
                    # Recent purchase?
                    to_date = payload.get('transaction_date')
                    # check freshness? Congress is usually old.
                    
                    tx_type = payload.get('type', '').lower()
                    amount = payload.get('amount', 0)
                    
                    # Purchase increases score, Sale decreases? 
                    # Actually Flow Score usually means "Activity" or "Smart Money Interest"
                    # High Score = Bullish Flow? Or just High Flow?
                    # Let's assume High Score = Bullish Flow for now.
                    
                    if 'purchase' in tx_type:
                        impact = 15 * obs.freshness_score
                        score += impact
                    elif 'sale' in tx_type:
                        impact = -10 * obs.freshness_score
                        score += impact # subtract, but add to score formula?
                        # wait, if score decreases, do we track it? Yes.
                        
                elif obs.source == SourceType.HEDGEFUND:
                    # 13F is very old usually
                    impact = 5 * obs.freshness_score
                    score += impact
                
                if abs(impact) > 1.0:
                    evidence_ids.append(obs.id)
                    
            return min(max(score, 0), 100), evidence_ids
            
        except Exception as e:
            logger.error(f"Error calculating flow score: {e}")
            return 50.0, []

    def calculate_confidence(self, observations: List[Observation], df: pd.DataFrame) -> Tuple[float, List[UUID]]:
        """
        Calculate Confidence Score (0-100).
        Based on data quality, source count, and freshness.
        """
        score = 50.0
        
        try:
            # 1. Base confidence from quantitative data
            if not df.empty and len(df) > 30:
                score += 10
            
            if not df.empty:
                missing = df['Close'].isna().sum()
                if missing == 0:
                    score += 10
                else:
                    score -= 5 * missing
            
            # 2. Confidence from verification (multiple sources)
            sources = set(obs.source for obs in observations)
            score += len(sources) * 5
            
            # 3. Penalize unknown
            if not observations and len(df) < 5:
                return 10.0, []
                
            # 4. Freshness
            # If we have very recent high quality observations
            recent_hq = sum(1 for obs in observations 
                           if obs.freshness_score > 0.8 and obs.quality_score > 0.8)
            score += recent_hq * 5
            
            return min(max(score, 0), 100), []
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 50.0, []
