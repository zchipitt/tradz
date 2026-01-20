"""
Signal generation module.
Calculates trading signals based on price movement, volatility, volume,
and cross-referenced observations (News, Congress, SEC, etc.).
"""
import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .models import Signal, Observation, EntityType
from .scoring import Scorer
from .database import Database, get_database

logger = logging.getLogger(__name__)


class SignalGenerator:
    """Generates trading signals from OHLCV data and multi-source observations."""

    def __init__(self, config: Dict, db: Optional[Database] = None):
        self.config = config
        self.thresholds = config.get('thresholds', {})
        self.db = db or get_database()
        self.scorer = Scorer()

    def calculate_returns(self, df: pd.DataFrame) -> pd.Series:
        """Calculate daily returns."""
        return df['Close'].pct_change()

    def calculate_volatility(self, returns: pd.Series, window: int = 7) -> float:
        """Calculate rolling volatility."""
        return returns.tail(window).std() * np.sqrt(252)  # Annualized

    def calculate_volume_ratio(self, df: pd.DataFrame, window: int = 30) -> float:
        """Calculate current volume vs average volume."""
        if len(df) < window:
            return 1.0
        avg_volume = df['Volume'].tail(window).mean()
        current_volume = df['Volume'].iloc[-1]
        return current_volume / avg_volume if avg_volume > 0 else 1.0

    def analyze_asset(
        self,
        symbol: str,
        df: pd.DataFrame,
        observations: List[Observation]
    ) -> Dict:
        """
        Analyze a single asset and generate signal.

        Returns:
            Dict representation of Signal object
        """
        if df.empty or len(df) < 2:
            return self._create_empty_signal(symbol).to_dict()

        try:
            # 1. Calculate base metrics (Legacy + Supporting Data)
            metrics = self._calculate_base_metrics(df, symbol)
            
            # 2. Calculate 4-dimensional scores
            anomaly, catalyst, flow, confidence, evidence_ids = self.scorer.calculate_scores(df, observations)
            
            # 3. Create Signal object
            signal = Signal(
                entity_id=None, # Filled later if possible or matched
                ticker=symbol,
                signal_date=datetime.utcnow(),
                # Scores
                anomaly_score=anomaly,
                catalyst_score=catalyst,
                flow_score=flow,
                confidence_score=confidence,
                # Context
                metrics=metrics,
                explanation={"summary": self._generate_explanation(metrics, anomaly, catalyst, flow)},
                evidence_ids=evidence_ids,
                caveats=self._generate_caveats(df, symbol)
            )
            
            # Save to DB if we can resolve entity?
            # For now, just return dict for aggregator
            
            # Convert to dict and add legacy fields for frontend compatibility
            signal_dict = signal.to_dict()
            signal_dict['symbol'] = symbol
            signal_dict['score'] = int(signal.attention_score) # Legacy score compatibility
            signal_dict['why'] = self._generate_legacy_rationale(metrics) # Legacy why compatibility
            
            return signal_dict

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return self._create_empty_signal(symbol, error=str(e)).to_dict()

    def _calculate_base_metrics(self, df: pd.DataFrame, symbol: str) -> Dict:
        """Calculate raw technical metrics."""
        returns = self.calculate_returns(df)
        
        # safely get values
        day_return = returns.iloc[-1] if len(returns) > 0 else 0
        week_return = (df['Close'].iloc[-1] / df['Close'].iloc[-7] - 1) if len(df) >= 7 else 0
        
        vol_7d = self.calculate_volatility(returns, window=7) if len(df) >= 7 else 0
        vol_30d = self.calculate_volatility(returns, window=30) if len(df) >= 30 else vol_7d
        vol_change = (vol_7d / vol_30d - 1) if vol_30d > 0 else 0
        
        volume_ratio = self.calculate_volume_ratio(df)
        
        return {
            'day_return': round(day_return * 100, 2),
            'week_return': round(week_return * 100, 2),
            'volatility_7d': round(vol_7d * 100, 2),
            'volatility_30d': round(vol_30d * 100, 2),
            'volatility_change': round(vol_change * 100, 2),
            'volume_ratio': round(volume_ratio, 2),
            'last_price': round(df['Close'].iloc[-1], 2)
        }

    def _create_empty_signal(self, symbol: str, error: str = "") -> Signal:
        return Signal(
            entity_ticker=symbol,
            explanation=f"Insufficient data or error: {error}" if error else "Insufficient data",
            metrics={},
            anomaly_score=0,
            catalyst_score=0,
            flow_score=0,
            confidence_score=0
        )

    def _generate_explanation(
        self,
        metrics: Dict,
        anomaly: float,
        catalyst: float,
        flow: float
    ) -> str:
        """Generate summary explanation based on scores."""
        parts = []
        if anomaly > 70:
            parts.append(f"High anomaly ({anomaly:.0f})")
        if catalyst > 60:
            parts.append(f"Strong catalyst ({catalyst:.0f})")
        if flow > 60:
            parts.append(f"Positive flow ({flow:.0f})")
            
        if not parts:
            parts.append("Neutral activity")
            
        return ", ".join(parts)
        
    def _generate_legacy_rationale(self, metrics: Dict) -> List[str]:
        """Generate human-readable rationale (legacy format)."""
        why = []
        if abs(metrics.get('day_return', 0)) > 3:
            direction = "up" if metrics['day_return'] > 0 else "down"
            why.append(f"Strong 1-day move: {direction} {abs(metrics['day_return']):.1f}%")
        
        if metrics.get('volume_ratio', 1) > 1.5:
            why.append(f"High volume: {metrics['volume_ratio']:.1f}x average")
            
        return why

    def _generate_caveats(self, df: pd.DataFrame, symbol: str) -> List[str]:
        """Generate data quality and risk caveats."""
        caveats = []
        if len(df) < 30:
            caveats.append(f"Limited data: only {len(df)} days available")
        missing = df['Close'].isna().sum()
        if missing > 0:
            caveats.append(f"Missing {missing} data points")
        return caveats

    def generate_signals(
        self,
        equity_data: Dict[str, pd.DataFrame],
        crypto_data: Dict[str, pd.DataFrame]
    ) -> Dict:
        """
        Generate signals for all assets.

        Args:
            equity_data: Dict of ticker -> DataFrame
            crypto_data: Dict of pair -> DataFrame

        Returns:
            Dict with top_equities, top_crypto, and all_signals
        """
        all_signals = []

        # Process equities
        for symbol, df in equity_data.items():
            # fetch observations (last 5 days)
            observations = self.db.get_observations_by_ticker(
                symbol, 
                since=datetime.utcnow() - timedelta(days=5)
            )
            
            signal_dict = self.analyze_asset(symbol, df, observations)
            signal_dict['asset_type'] = 'equity'
            all_signals.append(signal_dict)
            
            # Also insert into DB as Signal object?
            # Currently just returning dicts for aggregator
            # In Phase 3 refinement we should insert.

        # Process crypto
        for symbol, df in crypto_data.items():
            observations = self.db.get_observations_by_ticker(
                symbol,
                since=datetime.utcnow() - timedelta(days=5)
            )
            
            signal_dict = self.analyze_asset(symbol, df, observations)
            signal_dict['asset_type'] = 'crypto'
            all_signals.append(signal_dict)

        # Sort by attention_score (mapped to 'score' key)
        all_signals.sort(key=lambda x: x.get('score', 0), reverse=True)

        # Get top signals
        top_equities = [s for s in all_signals if s['asset_type'] == 'equity'][:5]
        top_crypto = [s for s in all_signals if s['asset_type'] == 'crypto'][:5]

        return {
            'top_equities': top_equities,
            'top_crypto': top_crypto,
            'all_signals': all_signals
        }
