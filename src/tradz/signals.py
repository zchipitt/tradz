"""
Signal generation module.
Calculates trading signals based on price movement, volatility, and volume.
"""
import logging
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SignalGenerator:
    """Generates trading signals from OHLCV data."""

    def __init__(self, config: Dict):
        self.config = config
        self.thresholds = config.get('thresholds', {})

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

    def analyze_asset(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Analyze a single asset and generate signal.

        Returns:
            Dict with signal data including score, metrics, and rationale
        """
        if df.empty or len(df) < 2:
            return {
                'symbol': symbol,
                'score': 0,
                'metrics': {},
                'why': ['Insufficient data'],
                'caveats': ['Data unavailable or incomplete']
            }

        try:
            # Calculate metrics
            returns = self.calculate_returns(df)

            # 1-day return
            day_return = returns.iloc[-1] if not pd.isna(returns.iloc[-1]) else 0

            # 7-day return
            week_return = (df['Close'].iloc[-1] / df['Close'].iloc[-7] - 1) if len(df) >= 7 else 0

            # 7-day volatility
            vol_7d = self.calculate_volatility(returns, window=7) if len(df) >= 7 else 0

            # 30-day volatility (baseline)
            vol_30d = self.calculate_volatility(returns, window=30) if len(df) >= 30 else vol_7d

            # Volatility change
            vol_change = (vol_7d / vol_30d - 1) if vol_30d > 0 else 0

            # Volume ratio
            volume_ratio = self.calculate_volume_ratio(df)

            # Build metrics dict
            metrics = {
                'day_return': round(day_return * 100, 2),
                'week_return': round(week_return * 100, 2),
                'volatility_7d': round(vol_7d * 100, 2),
                'volatility_30d': round(vol_30d * 100, 2),
                'volatility_change': round(vol_change * 100, 2),
                'volume_ratio': round(volume_ratio, 2),
                'last_price': round(df['Close'].iloc[-1], 2)
            }

            # Calculate signal score (0-100)
            score = self._calculate_score(metrics)

            # Generate rationale
            why = self._generate_rationale(metrics)

            # Data quality caveats
            caveats = self._generate_caveats(df, symbol)

            return {
                'symbol': symbol,
                'score': score,
                'metrics': metrics,
                'why': why,
                'caveats': caveats
            }

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'score': 0,
                'metrics': {},
                'why': ['Analysis error'],
                'caveats': [f'Error: {str(e)}']
            }

    def _calculate_score(self, metrics: Dict) -> int:
        """Calculate signal score based on metrics."""
        score = 50  # Baseline

        # Momentum signals
        if abs(metrics['day_return']) > 5:
            score += 15
        elif abs(metrics['day_return']) > 3:
            score += 10

        if abs(metrics['week_return']) > 10:
            score += 10
        elif abs(metrics['week_return']) > 5:
            score += 5

        # Volatility signals
        if metrics['volatility_change'] > 50:
            score += 15
        elif metrics['volatility_change'] > 25:
            score += 10

        # Volume signals
        if metrics['volume_ratio'] > 2.0:
            score += 10
        elif metrics['volume_ratio'] > 1.5:
            score += 5

        return min(max(score, 0), 100)

    def _generate_rationale(self, metrics: Dict) -> List[str]:
        """Generate human-readable rationale for the signal."""
        why = []

        # Price movement
        if abs(metrics['day_return']) > 3:
            direction = "up" if metrics['day_return'] > 0 else "down"
            why.append(f"Strong 1-day move: {direction} {abs(metrics['day_return']):.1f}%")

        if abs(metrics['week_return']) > 5:
            direction = "gained" if metrics['week_return'] > 0 else "lost"
            why.append(f"7-day momentum: {direction} {abs(metrics['week_return']):.1f}%")

        # Volatility
        if metrics['volatility_change'] > 25:
            why.append(f"Volatility spike: up {metrics['volatility_change']:.0f}% vs 30d avg")

        # Volume
        if metrics['volume_ratio'] > 1.5:
            why.append(f"High volume: {metrics['volume_ratio']:.1f}x average")

        if not why:
            why.append("Moderate activity, no strong signals")

        return why

    def _generate_caveats(self, df: pd.DataFrame, symbol: str) -> List[str]:
        """Generate data quality and risk caveats."""
        caveats = []

        # Data completeness
        if len(df) < 30:
            caveats.append(f"Limited data: only {len(df)} days available")

        # Missing data
        missing = df['Close'].isna().sum()
        if missing > 0:
            caveats.append(f"Missing {missing} data points")

        # Data source
        caveats.append("Data from free sources (yfinance/ccxt), may have delays or gaps")

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
            signal = self.analyze_asset(symbol, df)
            signal['asset_type'] = 'equity'
            all_signals.append(signal)

        # Process crypto
        for symbol, df in crypto_data.items():
            signal = self.analyze_asset(symbol, df)
            signal['asset_type'] = 'crypto'
            all_signals.append(signal)

        # Sort by score
        all_signals.sort(key=lambda x: x['score'], reverse=True)

        # Get top signals
        top_equities = [s for s in all_signals if s['asset_type'] == 'equity'][:5]
        top_crypto = [s for s in all_signals if s['asset_type'] == 'crypto'][:5]

        return {
            'top_equities': top_equities,
            'top_crypto': top_crypto,
            'all_signals': all_signals
        }
