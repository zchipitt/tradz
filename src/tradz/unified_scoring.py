"""
Unified multi-asset scoring module for cross-asset comparability.

Provides asset-type-specific scorers that all normalize to 0-100 scale
using percentile ranking for fair comparison across:
- Equities (stocks)
- Crypto (digital assets)
- Polymarket (prediction markets)

Each scorer implements 4-dimensional scoring:
1. Anomaly: Statistical deviation from normal behavior
2. Catalyst: External events driving price action
3. Flow: Money/position movement signals
4. Confidence: Data quality and cross-source verification
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import pandas as pd

from .models import AssetType, Observation, SourceType

logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    """
    Asset-specific weights for calculating attention score.

    Different asset types have different weight distributions based on
    which dimensions are most predictive for that asset class.
    """
    anomaly: float = 0.30
    catalyst: float = 0.30
    flow: float = 0.25
    confidence: float = 0.15

    def validate(self) -> bool:
        """Ensure weights sum to 1.0."""
        total = self.anomaly + self.catalyst + self.flow + self.confidence
        return abs(total - 1.0) < 0.001


# Asset-specific weight configurations
EQUITY_WEIGHTS = ScoringWeights(
    anomaly=0.30,    # Price/volume anomalies
    catalyst=0.30,   # News, filings, earnings
    flow=0.25,       # Congress, 13F, insider
    confidence=0.15  # Data quality
)

CRYPTO_WEIGHTS = ScoringWeights(
    anomaly=0.35,    # Crypto more volatile, anomalies matter more
    catalyst=0.25,   # Less formal catalysts
    flow=0.25,       # Exchange flows, whale activity
    confidence=0.15  # Data quality
)

POLYMARKET_WEIGHTS = ScoringWeights(
    anomaly=0.30,    # Odds movements
    catalyst=0.40,   # Events are the core driver (polls, news)
    flow=0.15,       # Large trades, smart money
    confidence=0.15  # Data quality
)


@dataclass
class AnomalyComponents:
    """Components that make up the anomaly score."""
    price_component: float = 0.0
    volume_component: float = 0.0
    volatility_component: float = 0.0
    # Crypto-specific
    onchain_component: float = 0.0
    funding_rate_component: float = 0.0
    # Polymarket-specific
    poll_divergence_component: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "price": self.price_component,
            "volume": self.volume_component,
            "volatility": self.volatility_component,
            "onchain": self.onchain_component,
            "funding_rate": self.funding_rate_component,
            "poll_divergence": self.poll_divergence_component,
        }


@dataclass
class FlowComponents:
    """Components that make up the flow score."""
    # Equity-specific
    congress_component: float = 0.0
    hedgefund_component: float = 0.0
    insider_component: float = 0.0
    # Crypto-specific
    exchange_flow_component: float = 0.0
    whale_activity_component: float = 0.0
    institutional_component: float = 0.0
    # Polymarket-specific
    large_trades_component: float = 0.0
    liquidity_change_component: float = 0.0
    smart_money_component: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "congress": self.congress_component,
            "hedgefund": self.hedgefund_component,
            "insider": self.insider_component,
            "exchange_flow": self.exchange_flow_component,
            "whale_activity": self.whale_activity_component,
            "institutional": self.institutional_component,
            "large_trades": self.large_trades_component,
            "liquidity_change": self.liquidity_change_component,
            "smart_money": self.smart_money_component,
        }


@dataclass
class ScoringResult:
    """Result of scoring calculation with component breakdown."""
    anomaly_score: float = 50.0
    catalyst_score: float = 50.0
    flow_score: float = 50.0
    confidence_score: float = 50.0
    attention_score: float = 50.0

    evidence_ids: List[UUID] = field(default_factory=list)
    anomaly_components: AnomalyComponents = field(default_factory=AnomalyComponents)
    flow_components: FlowComponents = field(default_factory=FlowComponents)

    # Percentile ranks (0-100) for cross-asset comparison
    anomaly_percentile: float = 50.0
    catalyst_percentile: float = 50.0
    flow_percentile: float = 50.0
    confidence_percentile: float = 50.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_score": self.anomaly_score,
            "catalyst_score": self.catalyst_score,
            "flow_score": self.flow_score,
            "confidence_score": self.confidence_score,
            "attention_score": self.attention_score,
            "evidence_ids": [str(eid) for eid in self.evidence_ids],
            "anomaly_components": self.anomaly_components.to_dict(),
            "flow_components": self.flow_components.to_dict(),
            "percentiles": {
                "anomaly": self.anomaly_percentile,
                "catalyst": self.catalyst_percentile,
                "flow": self.flow_percentile,
                "confidence": self.confidence_percentile,
            }
        }


class BaseScorer(ABC):
    """
    Abstract base class for asset-specific scorers.

    Each scorer must implement the 4 dimension calculations with
    asset-appropriate logic.
    """

    def __init__(self, weights: ScoringWeights):
        self.weights = weights
        if not weights.validate():
            raise ValueError("Scoring weights must sum to 1.0")

    @property
    @abstractmethod
    def asset_type(self) -> AssetType:
        """Return the asset type this scorer handles."""
        pass

    def calculate_scores(
        self,
        df: pd.DataFrame,
        observations: List[Observation],
        historical_scores: Optional[Dict[str, List[float]]] = None
    ) -> ScoringResult:
        """
        Calculate all 4 scores and attention score.

        Args:
            df: OHLCV DataFrame for the asset
            observations: List of observations for this entity
            historical_scores: Optional historical scores for percentile ranking

        Returns:
            ScoringResult with all scores and component breakdown
        """
        result = ScoringResult()

        # Calculate each dimension
        anomaly, anomaly_ids, anomaly_components = self.calculate_anomaly(df, observations)
        catalyst, catalyst_ids = self.calculate_catalyst(observations)
        flow, flow_ids, flow_components = self.calculate_flow(observations)
        confidence, _ = self.calculate_confidence(observations, df)

        result.anomaly_score = anomaly
        result.catalyst_score = catalyst
        result.flow_score = flow
        result.confidence_score = confidence
        result.anomaly_components = anomaly_components
        result.flow_components = flow_components

        # Collect evidence IDs
        result.evidence_ids = list(set(anomaly_ids + catalyst_ids + flow_ids))

        # Calculate percentile ranks if historical data provided
        if historical_scores:
            result.anomaly_percentile = self._calculate_percentile(
                anomaly, historical_scores.get("anomaly", [])
            )
            result.catalyst_percentile = self._calculate_percentile(
                catalyst, historical_scores.get("catalyst", [])
            )
            result.flow_percentile = self._calculate_percentile(
                flow, historical_scores.get("flow", [])
            )
            result.confidence_percentile = self._calculate_percentile(
                confidence, historical_scores.get("confidence", [])
            )
        else:
            # Without historical data, percentile equals raw score
            result.anomaly_percentile = anomaly
            result.catalyst_percentile = catalyst
            result.flow_percentile = flow
            result.confidence_percentile = confidence

        # Calculate weighted attention score
        result.attention_score = self._calculate_attention_score(result)

        return result

    def _calculate_attention_score(self, result: ScoringResult) -> float:
        """Calculate weighted attention score."""
        score = (
            result.anomaly_score * self.weights.anomaly +
            result.catalyst_score * self.weights.catalyst +
            result.flow_score * self.weights.flow +
            result.confidence_score * self.weights.confidence
        )
        return min(max(score, 0), 100)

    def _calculate_percentile(
        self,
        score: float,
        historical: List[float]
    ) -> float:
        """
        Calculate percentile rank of score within historical distribution.

        Args:
            score: Current score to rank
            historical: List of historical scores

        Returns:
            Percentile rank (0-100)
        """
        if not historical:
            return score  # No history, return raw score

        # Count how many historical scores are below current
        below_count = sum(1 for h in historical if h < score)
        percentile = (below_count / len(historical)) * 100
        return min(max(percentile, 0), 100)

    @abstractmethod
    def calculate_anomaly(
        self,
        df: pd.DataFrame,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID], AnomalyComponents]:
        """Calculate anomaly score with component breakdown."""
        pass

    @abstractmethod
    def calculate_catalyst(
        self,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID]]:
        """Calculate catalyst score."""
        pass

    @abstractmethod
    def calculate_flow(
        self,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID], FlowComponents]:
        """Calculate flow score with component breakdown."""
        pass

    @abstractmethod
    def calculate_confidence(
        self,
        observations: List[Observation],
        df: pd.DataFrame
    ) -> Tuple[float, List[UUID]]:
        """Calculate confidence score."""
        pass

    def _calculate_z_score(
        self,
        value: float,
        series: Any,  # pd.Series - using Any to avoid pandas type issues
        min_len: int = 5
    ) -> float:
        """Calculate z-score of value relative to series."""
        if len(series) < min_len:
            return 0.0
        mean = float(series.mean())
        std = float(series.std())
        if std == 0:
            return 0.0
        return (value - mean) / std

    def _z_to_score(self, z: float, base: float = 50.0, scale: float = 15.0) -> float:
        """
        Convert z-score to 0-100 score.

        Z=0 -> base (50)
        Z=2 -> base + 2*scale (80)
        Z=3 -> base + 3*scale (95)
        """
        score = base + (z * scale)
        return min(max(score, 0), 100)


class EquityScorer(BaseScorer):
    """
    Scorer for equity (stock) assets.

    Anomaly: price (40%) + volume (30%) + volatility (20%) + insider (10%)
    Catalyst: SEC filings, news, polymarket events
    Flow: Congress trades, 13F filings, broker data
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        super().__init__(weights or EQUITY_WEIGHTS)

    @property
    def asset_type(self) -> AssetType:
        return AssetType.EQUITY

    def calculate_anomaly(
        self,
        df: pd.DataFrame,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID], AnomalyComponents]:
        """
        Calculate equity anomaly score.

        Weights: price (40%) + volume (30%) + volatility (20%) + insider activity (10%)
        """
        components = AnomalyComponents()

        if df.empty or len(df) < 30:
            return 50.0, [], components

        try:
            # 1. Price Return Z-Score (40%)
            returns = df['Close'].pct_change().dropna()
            if len(returns) < 2:
                return 50.0, [], components

            z_price = self._calculate_z_score(returns.iloc[-1], returns)
            components.price_component = abs(z_price)

            # 2. Volume Z-Score (30%)
            volumes = df['Volume'].dropna()
            z_vol = self._calculate_z_score(volumes.iloc[-1], volumes)
            components.volume_component = z_vol

            # 3. Volatility change (20%)
            vol_7d = returns.tail(7).std()
            vol_30d = returns.tail(30).std()
            if vol_30d > 0:
                ratio = vol_7d / vol_30d
                z_volatility = (ratio - 1.0) * 3.0
            else:
                z_volatility = 0.0
            components.volatility_component = z_volatility

            # 4. Insider activity signal (10%) - from observations
            insider_signal = 0.0
            for obs in observations:
                if obs.source == SourceType.CONGRESS:
                    payload = obs.payload or {}
                    tx_type = payload.get('type', '').lower()
                    if 'purchase' in tx_type:
                        insider_signal += 0.5
                    elif 'sale' in tx_type:
                        insider_signal -= 0.3
            insider_signal = min(max(insider_signal, -1), 1)

            # Combine components with weights
            combined_z = (
                abs(z_price) * 0.40 +
                z_vol * 0.30 +
                z_volatility * 0.20 +
                insider_signal * 0.10
            )

            score = self._z_to_score(combined_z)
            return score, [], components

        except Exception as e:
            logger.error(f"Error calculating equity anomaly score: {e}")
            return 50.0, [], components

    def calculate_catalyst(
        self,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID]]:
        """
        Calculate equity catalyst score.

        Weights:
        - SEC filings: 20 (8-K: 30)
        - News: 10
        - Polymarket: 15
        - X Sentiment: 5
        """
        score = 50.0
        evidence_ids = []

        weights = {
            SourceType.SEC: 20,
            SourceType.NEWS: 10,
            SourceType.POLYMARKET: 15,
            SourceType.X_SENTIMENT: 5,
        }

        now = datetime.now(timezone.utc)

        try:
            for obs in observations:
                age_days = (now - obs.observed_at).total_seconds() / 86400
                if age_days > 3:
                    continue

                # Decay: 1.0 at 0h, 0.5 at 24h
                decay = max(0, 1.0 - (age_days / 2.0))
                impact = weights.get(obs.source, 5) * decay * obs.quality_score

                # 8-K filings are material events
                if obs.source == SourceType.SEC:
                    payload = obs.payload or {}
                    if payload.get('form') == '8-K':
                        impact *= 1.5

                score += impact
                if impact > 1.0:
                    evidence_ids.append(obs.id)

            return min(max(score, 0), 100), evidence_ids

        except Exception as e:
            logger.error(f"Error calculating equity catalyst score: {e}")
            return 50.0, []

    def calculate_flow(
        self,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID], FlowComponents]:
        """
        Calculate equity flow score.

        Weights:
        - Congress trades: 40%
        - 13F filings: 35%
        - Insider (Form 4): 25%
        """
        score = 50.0
        evidence_ids = []
        components = FlowComponents()

        try:
            congress_impact = 0.0
            hedgefund_impact = 0.0
            insider_impact = 0.0

            for obs in observations:
                impact = 0.0
                if obs.source == SourceType.CONGRESS:
                    payload = obs.payload or {}
                    tx_type = payload.get('type', '').lower()

                    if 'purchase' in tx_type:
                        impact = 15 * obs.freshness_score
                        congress_impact += impact
                    elif 'sale' in tx_type:
                        impact = -10 * obs.freshness_score
                        congress_impact += impact

                    if abs(impact) > 1.0:
                        evidence_ids.append(obs.id)

                elif obs.source == SourceType.HEDGEFUND:
                    impact = 5 * obs.freshness_score
                    hedgefund_impact += impact
                    if impact > 1.0:
                        evidence_ids.append(obs.id)

            # Normalize impacts to 0-50 range for contribution
            components.congress_component = min(max(congress_impact, -25), 25)
            components.hedgefund_component = min(hedgefund_impact, 25)
            components.insider_component = min(insider_impact, 15)

            # Weight contributions
            flow_delta = (
                components.congress_component * 0.40 +
                components.hedgefund_component * 0.35 +
                components.insider_component * 0.25
            )

            score += flow_delta
            return min(max(score, 0), 100), evidence_ids, components

        except Exception as e:
            logger.error(f"Error calculating equity flow score: {e}")
            return 50.0, [], components

    def calculate_confidence(
        self,
        observations: List[Observation],
        df: pd.DataFrame
    ) -> Tuple[float, List[UUID]]:
        """
        Calculate equity confidence score.

        Based on data quality, source diversity, and freshness.
        """
        score = 50.0

        try:
            # Base confidence from quantitative data
            if not df.empty and len(df) > 30:
                score += 10

            if not df.empty:
                missing = df['Close'].isna().sum()
                if missing == 0:
                    score += 10
                else:
                    score -= min(5 * missing, 20)

            # Source diversity bonus
            sources = set(obs.source for obs in observations)
            score += min(len(sources) * 5, 20)

            # Penalize lack of data
            if not observations and len(df) < 5:
                return 10.0, []

            # Freshness bonus
            recent_hq = sum(
                1 for obs in observations
                if obs.freshness_score > 0.8 and obs.quality_score > 0.8
            )
            score += min(recent_hq * 5, 15)

            return min(max(score, 0), 100), []

        except Exception as e:
            logger.error(f"Error calculating equity confidence score: {e}")
            return 50.0, []


class CryptoScorer(BaseScorer):
    """
    Scorer for crypto assets.

    Anomaly: price (35%) + volume (25%) + onchain activity (25%) + funding rate (15%)
    Flow: exchange flow (40%) + whale activity (35%) + institutional (25%)
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        super().__init__(weights or CRYPTO_WEIGHTS)

    @property
    def asset_type(self) -> AssetType:
        return AssetType.CRYPTO

    def calculate_anomaly(
        self,
        df: pd.DataFrame,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID], AnomalyComponents]:
        """
        Calculate crypto anomaly score.

        Weights: price (35%) + volume (25%) + onchain activity (25%) + funding rate (15%)
        """
        components = AnomalyComponents()
        evidence_ids = []

        if df.empty or len(df) < 10:  # Crypto has less history requirement
            return 50.0, [], components

        try:
            # 1. Price Return Z-Score (35%)
            returns = df['Close'].pct_change().dropna()
            if len(returns) < 2:
                return 50.0, [], components

            z_price = self._calculate_z_score(returns.iloc[-1], returns)
            components.price_component = abs(z_price)

            # 2. Volume Z-Score (25%)
            volumes = df['Volume'].dropna()
            z_vol = self._calculate_z_score(volumes.iloc[-1], volumes)
            components.volume_component = z_vol

            # 3. Onchain activity (25%) - from observations
            onchain_signal = 0.0
            for obs in observations:
                if obs.source == SourceType.CRYPTO:
                    payload = obs.payload or {}
                    # Look for onchain metrics
                    active_addresses = payload.get('active_addresses_change', 0)
                    transaction_volume = payload.get('transaction_volume_change', 0)
                    onchain_signal += (active_addresses + transaction_volume) / 2
                    if abs(onchain_signal) > 0.5:
                        evidence_ids.append(obs.id)

            onchain_signal = min(max(onchain_signal, -2), 2)
            components.onchain_component = onchain_signal

            # 4. Funding rate (15%) - from observations
            funding_signal = 0.0
            for obs in observations:
                if obs.source == SourceType.CRYPTO:
                    payload = obs.payload or {}
                    funding_rate = payload.get('funding_rate', 0)
                    # Extreme funding rates are anomalous
                    if abs(funding_rate) > 0.01:  # >1% funding is extreme
                        funding_signal = (funding_rate * 100) / 0.03  # Normalize to ~1 at 0.03%
                        evidence_ids.append(obs.id)

            funding_signal = min(max(funding_signal, -2), 2)
            components.funding_rate_component = funding_signal

            # Combine components with weights
            combined_z = (
                abs(z_price) * 0.35 +
                z_vol * 0.25 +
                abs(onchain_signal) * 0.25 +
                abs(funding_signal) * 0.15
            )

            score = self._z_to_score(combined_z)
            return score, evidence_ids, components

        except Exception as e:
            logger.error(f"Error calculating crypto anomaly score: {e}")
            return 50.0, [], components

    def calculate_catalyst(
        self,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID]]:
        """
        Calculate crypto catalyst score.

        Weights:
        - News: 15
        - Polymarket: 20 (prediction markets are big in crypto)
        - X Sentiment: 10 (crypto is very social)
        """
        score = 50.0
        evidence_ids = []

        weights = {
            SourceType.NEWS: 15,
            SourceType.POLYMARKET: 20,
            SourceType.X_SENTIMENT: 10,
        }

        now = datetime.now(timezone.utc)

        try:
            for obs in observations:
                age_days = (now - obs.observed_at).total_seconds() / 86400
                if age_days > 3:
                    continue

                decay = max(0, 1.0 - (age_days / 2.0))
                impact = weights.get(obs.source, 5) * decay * obs.quality_score

                score += impact
                if impact > 1.0:
                    evidence_ids.append(obs.id)

            return min(max(score, 0), 100), evidence_ids

        except Exception as e:
            logger.error(f"Error calculating crypto catalyst score: {e}")
            return 50.0, []

    def calculate_flow(
        self,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID], FlowComponents]:
        """
        Calculate crypto flow score.

        Weights:
        - Exchange flow (40%): net inflow/outflow to exchanges
        - Whale activity (35%): large holder movements
        - Institutional (25%): known institutional activity
        """
        score = 50.0
        evidence_ids = []
        components = FlowComponents()

        try:
            exchange_impact = 0.0
            whale_impact = 0.0
            institutional_impact = 0.0

            for obs in observations:
                if obs.source == SourceType.CRYPTO:
                    payload = obs.payload or {}

                    # Exchange flows (negative = bullish, positive = bearish)
                    exchange_netflow = payload.get('exchange_netflow', 0)
                    if exchange_netflow != 0:
                        # Inverse: outflow (negative) is bullish
                        exchange_impact -= exchange_netflow / 1000  # Normalize
                        evidence_ids.append(obs.id)

                    # Whale activity
                    whale_txs = payload.get('whale_transactions', 0)
                    if whale_txs > 0:
                        whale_impact += whale_txs / 10  # Normalize
                        evidence_ids.append(obs.id)

                    # Institutional activity
                    inst_flow = payload.get('institutional_flow', 0)
                    if inst_flow != 0:
                        institutional_impact += inst_flow / 100
                        evidence_ids.append(obs.id)

            # Normalize impacts
            components.exchange_flow_component = min(max(exchange_impact, -25), 25)
            components.whale_activity_component = min(whale_impact, 25)
            components.institutional_component = min(max(institutional_impact, -15), 15)

            # Weight contributions
            flow_delta = (
                components.exchange_flow_component * 0.40 +
                components.whale_activity_component * 0.35 +
                components.institutional_component * 0.25
            )

            score += flow_delta
            return min(max(score, 0), 100), evidence_ids, components

        except Exception as e:
            logger.error(f"Error calculating crypto flow score: {e}")
            return 50.0, [], components

    def calculate_confidence(
        self,
        observations: List[Observation],
        df: pd.DataFrame
    ) -> Tuple[float, List[UUID]]:
        """
        Calculate crypto confidence score.

        Crypto data is generally noisier, so we adjust confidence accordingly.
        """
        score = 45.0  # Slightly lower baseline for crypto

        try:
            # Data availability
            if not df.empty and len(df) > 10:
                score += 10

            if not df.empty:
                missing = df['Close'].isna().sum()
                if missing == 0:
                    score += 10
                else:
                    score -= min(5 * missing, 15)

            # Source diversity (fewer sources available for crypto)
            sources = set(obs.source for obs in observations)
            score += min(len(sources) * 7, 20)

            # Penalize unknown
            if not observations and len(df) < 5:
                return 10.0, []

            # Freshness is more important for crypto (24/7 market)
            recent_hq = sum(
                1 for obs in observations
                if obs.freshness_score > 0.9 and obs.quality_score > 0.7
            )
            score += min(recent_hq * 6, 18)

            return min(max(score, 0), 100), []

        except Exception as e:
            logger.error(f"Error calculating crypto confidence score: {e}")
            return 45.0, []


class PolymarketScorer(BaseScorer):
    """
    Scorer for Polymarket prediction market assets.

    Anomaly: price move (50%) + volume spike (30%) + poll divergence (20%)
    Flow: large trades (50%) + liquidity change (30%) + smart money (20%)
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        super().__init__(weights or POLYMARKET_WEIGHTS)

    @property
    def asset_type(self) -> AssetType:
        return AssetType.POLYMARKET

    def calculate_anomaly(
        self,
        df: pd.DataFrame,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID], AnomalyComponents]:
        """
        Calculate polymarket anomaly score.

        Weights: price move (50%) + volume spike (30%) + poll divergence (20%)
        """
        components = AnomalyComponents()
        evidence_ids = []

        # Polymarket may not have traditional OHLCV
        price_z = 0.0
        volume_z = 0.0
        poll_divergence = 0.0

        try:
            # 1. Price (odds) movement (50%)
            if not df.empty and 'Close' in df.columns and len(df) >= 5:
                returns = df['Close'].pct_change().dropna()
                if len(returns) >= 2:
                    price_z = self._calculate_z_score(returns.iloc[-1], returns)
            components.price_component = abs(price_z)

            # 2. Volume spike (30%)
            if not df.empty and 'Volume' in df.columns and len(df) >= 5:
                volumes = df['Volume'].dropna()
                if len(volumes) >= 2:
                    volume_z = self._calculate_z_score(volumes.iloc[-1], volumes)
            components.volume_component = volume_z

            # 3. Poll divergence (20%) - from observations
            for obs in observations:
                if obs.source == SourceType.POLYMARKET:
                    payload = obs.payload or {}
                    market_odds = payload.get('odds', 0)
                    poll_avg = payload.get('poll_average', 0)

                    if market_odds > 0 and poll_avg > 0:
                        # Divergence between market and polls
                        divergence = abs(market_odds - poll_avg) / max(poll_avg, 0.1)
                        poll_divergence = divergence * 2  # Scale up
                        evidence_ids.append(obs.id)

            poll_divergence = min(poll_divergence, 3)
            components.poll_divergence_component = poll_divergence

            # Combine with weights
            combined_z = (
                abs(price_z) * 0.50 +
                volume_z * 0.30 +
                poll_divergence * 0.20
            )

            score = self._z_to_score(combined_z)
            return score, evidence_ids, components

        except Exception as e:
            logger.error(f"Error calculating polymarket anomaly score: {e}")
            return 50.0, [], components

    def calculate_catalyst(
        self,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID]]:
        """
        Calculate polymarket catalyst score.

        Catalysts are the PRIMARY driver for prediction markets:
        - News about the event: 25
        - Poll releases: 20
        - Official announcements: 30
        """
        score = 50.0
        evidence_ids = []

        weights = {
            SourceType.NEWS: 25,
            SourceType.POLYMARKET: 15,  # Internal market events
        }

        now = datetime.now(timezone.utc)

        try:
            for obs in observations:
                age_days = (now - obs.observed_at).total_seconds() / 86400
                if age_days > 2:  # Faster decay for prediction markets
                    continue

                # Faster decay for prediction markets (events matter NOW)
                decay = max(0, 1.0 - (age_days / 1.5))
                impact = weights.get(obs.source, 5) * decay * obs.quality_score

                # Check for high-impact polymarket events
                if obs.source == SourceType.POLYMARKET:
                    payload = obs.payload or {}
                    if payload.get('is_resolution', False):
                        impact *= 2.0  # Resolution is major catalyst
                    if payload.get('new_poll_release', False):
                        impact *= 1.5

                score += impact
                if impact > 1.0:
                    evidence_ids.append(obs.id)

            return min(max(score, 0), 100), evidence_ids

        except Exception as e:
            logger.error(f"Error calculating polymarket catalyst score: {e}")
            return 50.0, []

    def calculate_flow(
        self,
        observations: List[Observation]
    ) -> Tuple[float, List[UUID], FlowComponents]:
        """
        Calculate polymarket flow score.

        Weights:
        - Large trades (50%): Big bets moving the market
        - Liquidity change (30%): Market depth changes
        - Smart money (20%): Known sharp bettors
        """
        score = 50.0
        evidence_ids = []
        components = FlowComponents()

        try:
            large_trades_impact = 0.0
            liquidity_impact = 0.0
            smart_money_impact = 0.0

            for obs in observations:
                if obs.source == SourceType.POLYMARKET:
                    payload = obs.payload or {}

                    # Large trades
                    trade_size = payload.get('trade_size', 0)
                    if trade_size > 10000:  # $10k+ is significant
                        large_trades_impact += (trade_size / 10000) * 5
                        evidence_ids.append(obs.id)

                    # Liquidity changes
                    liquidity_delta = payload.get('liquidity_change_pct', 0)
                    if abs(liquidity_delta) > 10:  # >10% change
                        liquidity_impact += liquidity_delta / 10
                        evidence_ids.append(obs.id)

                    # Smart money indicators
                    is_known_sharp = payload.get('known_sharp_trader', False)
                    if is_known_sharp:
                        trade_direction = payload.get('trade_direction', 'unknown')
                        if trade_direction == 'yes':
                            smart_money_impact += 10
                        elif trade_direction == 'no':
                            smart_money_impact -= 10
                        evidence_ids.append(obs.id)

            # Normalize
            components.large_trades_component = min(large_trades_impact, 30)
            components.liquidity_change_component = min(max(liquidity_impact, -20), 20)
            components.smart_money_component = min(max(smart_money_impact, -15), 15)

            # Weight contributions
            flow_delta = (
                components.large_trades_component * 0.50 +
                components.liquidity_change_component * 0.30 +
                components.smart_money_component * 0.20
            )

            score += flow_delta
            return min(max(score, 0), 100), evidence_ids, components

        except Exception as e:
            logger.error(f"Error calculating polymarket flow score: {e}")
            return 50.0, [], components

    def calculate_confidence(
        self,
        observations: List[Observation],
        df: pd.DataFrame
    ) -> Tuple[float, List[UUID]]:
        """
        Calculate polymarket confidence score.

        Polymarket data is relatively clean but may have limited history.
        """
        score = 50.0

        try:
            # Data availability
            if not df.empty and len(df) > 5:
                score += 10

            # Market liquidity matters for confidence
            for obs in observations:
                if obs.source == SourceType.POLYMARKET:
                    payload = obs.payload or {}
                    liquidity = payload.get('total_liquidity', 0)
                    if liquidity > 100000:  # $100k+ is liquid
                        score += 15
                    elif liquidity > 10000:
                        score += 8

                    # Volume also indicates market quality
                    volume_24h = payload.get('volume_24h', 0)
                    if volume_24h > 50000:
                        score += 10

            # Penalize thin markets
            if not observations:
                return 30.0, []

            # Freshness
            recent_hq = sum(
                1 for obs in observations
                if obs.freshness_score > 0.8 and obs.quality_score > 0.8
            )
            score += min(recent_hq * 5, 15)

            return min(max(score, 0), 100), []

        except Exception as e:
            logger.error(f"Error calculating polymarket confidence score: {e}")
            return 50.0, []


class UnifiedScorer:
    """
    Unified scoring interface that routes to asset-specific scorers.

    Provides cross-asset comparability through percentile ranking.
    """

    def __init__(self):
        self._scorers: Dict[AssetType, BaseScorer] = {
            AssetType.EQUITY: EquityScorer(),
            AssetType.CRYPTO: CryptoScorer(),
            AssetType.POLYMARKET: PolymarketScorer(),
            AssetType.INDEX: EquityScorer(),  # Indexes use equity scorer
            AssetType.COMMODITY: EquityScorer(),  # Commodities use equity scorer
        }

        # Historical score storage for percentile calculation
        self._historical_scores: Dict[AssetType, Dict[str, List[float]]] = {
            asset_type: {"anomaly": [], "catalyst": [], "flow": [], "confidence": []}
            for asset_type in AssetType
        }

    def get_scorer(self, asset_type: AssetType) -> BaseScorer:
        """Get the appropriate scorer for an asset type."""
        return self._scorers.get(asset_type, self._scorers[AssetType.EQUITY])

    def calculate_scores(
        self,
        asset_type: AssetType,
        df: pd.DataFrame,
        observations: List[Observation],
        use_percentiles: bool = True
    ) -> ScoringResult:
        """
        Calculate scores for an asset using the appropriate scorer.

        Args:
            asset_type: Type of asset to score
            df: OHLCV DataFrame
            observations: List of observations
            use_percentiles: Whether to use percentile ranking

        Returns:
            ScoringResult with all scores
        """
        scorer = self.get_scorer(asset_type)

        historical = None
        if use_percentiles:
            historical = self._historical_scores.get(asset_type)

        result = scorer.calculate_scores(df, observations, historical)

        # Update historical scores
        self._update_historical(asset_type, result)

        return result

    def _update_historical(
        self,
        asset_type: AssetType,
        result: ScoringResult,
        max_history: int = 1000
    ) -> None:
        """Update historical scores for percentile calculation."""
        history = self._historical_scores[asset_type]

        history["anomaly"].append(result.anomaly_score)
        history["catalyst"].append(result.catalyst_score)
        history["flow"].append(result.flow_score)
        history["confidence"].append(result.confidence_score)

        # Trim to max size
        for key in history:
            if len(history[key]) > max_history:
                history[key] = history[key][-max_history:]

    def compare_cross_asset(
        self,
        results: List[Tuple[AssetType, ScoringResult]]
    ) -> List[Tuple[AssetType, ScoringResult, float]]:
        """
        Compare scores across different asset types.

        Returns results sorted by normalized attention score,
        using percentile ranking for fair comparison.

        Args:
            results: List of (asset_type, ScoringResult) tuples

        Returns:
            List of (asset_type, ScoringResult, normalized_score) sorted by score
        """
        if not results:
            return []

        # Calculate normalized scores using percentiles
        normalized = []
        for asset_type, result in results:
            # Use percentile-based attention score
            normalized_score = (
                result.anomaly_percentile * 0.30 +
                result.catalyst_percentile * 0.30 +
                result.flow_percentile * 0.25 +
                result.confidence_percentile * 0.15
            )
            normalized.append((asset_type, result, normalized_score))

        # Sort by normalized score descending
        normalized.sort(key=lambda x: x[2], reverse=True)
        return normalized

    def get_attention_score_weights(self, asset_type: AssetType) -> ScoringWeights:
        """Get the attention score weights for an asset type."""
        scorer = self.get_scorer(asset_type)
        return scorer.weights
