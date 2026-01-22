"""Tests for the unified multi-asset scoring module."""

from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd
import pytest

from src.tradz.models import AssetType, Observation, SourceType
from src.tradz.unified_scoring import (
    AnomalyComponents,
    CryptoScorer,
    EquityScorer,
    FlowComponents,
    PolymarketScorer,
    ScoringResult,
    ScoringWeights,
    UnifiedScorer,
    CRYPTO_WEIGHTS,
    EQUITY_WEIGHTS,
    POLYMARKET_WEIGHTS,
)


# ============================================================================
# Test ScoringWeights
# ============================================================================

class TestScoringWeights:
    """Tests for ScoringWeights dataclass."""

    def test_default_weights_validate(self):
        """Default weights should sum to 1.0."""
        weights = ScoringWeights()
        assert weights.validate()

    def test_equity_weights_validate(self):
        """EQUITY_WEIGHTS should sum to 1.0."""
        assert EQUITY_WEIGHTS.validate()

    def test_crypto_weights_validate(self):
        """CRYPTO_WEIGHTS should sum to 1.0."""
        assert CRYPTO_WEIGHTS.validate()

    def test_polymarket_weights_validate(self):
        """POLYMARKET_WEIGHTS should sum to 1.0."""
        assert POLYMARKET_WEIGHTS.validate()

    def test_invalid_weights_fail_validation(self):
        """Weights that don't sum to 1.0 should fail validation."""
        weights = ScoringWeights(anomaly=0.5, catalyst=0.5, flow=0.5, confidence=0.5)
        assert not weights.validate()

    def test_crypto_weights_higher_anomaly(self):
        """Crypto weights should have higher anomaly weight than equity."""
        assert CRYPTO_WEIGHTS.anomaly > EQUITY_WEIGHTS.anomaly

    def test_polymarket_weights_higher_catalyst(self):
        """Polymarket weights should have higher catalyst weight than others."""
        assert POLYMARKET_WEIGHTS.catalyst > EQUITY_WEIGHTS.catalyst
        assert POLYMARKET_WEIGHTS.catalyst > CRYPTO_WEIGHTS.catalyst


# ============================================================================
# Test AnomalyComponents and FlowComponents
# ============================================================================

class TestComponents:
    """Tests for component dataclasses."""

    def test_anomaly_components_to_dict(self):
        """AnomalyComponents.to_dict() returns all fields."""
        components = AnomalyComponents(
            price_component=1.5,
            volume_component=0.8,
            volatility_component=0.3,
        )
        d = components.to_dict()
        assert d["price"] == 1.5
        assert d["volume"] == 0.8
        assert d["volatility"] == 0.3
        assert "onchain" in d
        assert "funding_rate" in d
        assert "poll_divergence" in d

    def test_flow_components_to_dict(self):
        """FlowComponents.to_dict() returns all fields."""
        components = FlowComponents(
            congress_component=10.0,
            hedgefund_component=5.0,
            whale_activity_component=15.0,
        )
        d = components.to_dict()
        assert d["congress"] == 10.0
        assert d["hedgefund"] == 5.0
        assert d["whale_activity"] == 15.0
        assert "exchange_flow" in d
        assert "large_trades" in d


# ============================================================================
# Test ScoringResult
# ============================================================================

class TestScoringResult:
    """Tests for ScoringResult dataclass."""

    def test_default_values(self):
        """Default ScoringResult has baseline scores of 50."""
        result = ScoringResult()
        assert result.anomaly_score == 50.0
        assert result.catalyst_score == 50.0
        assert result.flow_score == 50.0
        assert result.confidence_score == 50.0
        assert result.attention_score == 50.0

    def test_to_dict_includes_all_fields(self):
        """to_dict() includes all important fields."""
        result = ScoringResult(
            anomaly_score=75.0,
            catalyst_score=60.0,
            flow_score=55.0,
            confidence_score=80.0,
            attention_score=70.0,
        )
        d = result.to_dict()
        assert d["anomaly_score"] == 75.0
        assert d["catalyst_score"] == 60.0
        assert d["flow_score"] == 55.0
        assert d["confidence_score"] == 80.0
        assert d["attention_score"] == 70.0
        assert "evidence_ids" in d
        assert "anomaly_components" in d
        assert "flow_components" in d
        assert "percentiles" in d


# ============================================================================
# Helper functions
# ============================================================================

def create_ohlcv_df(
    days: int = 60,
    base_price: float = 100.0,
    volatility: float = 0.02,
    base_volume: int = 1000000,
) -> pd.DataFrame:
    """Create a sample OHLCV DataFrame for testing."""
    dates = pd.date_range(end=datetime.now(timezone.utc), periods=days, freq='D')

    # Generate price series with random walk
    import random
    random.seed(42)

    prices = [base_price]
    for _ in range(days - 1):
        change = random.gauss(0, volatility)
        prices.append(prices[-1] * (1 + change))

    volumes = [base_volume * (1 + random.uniform(-0.3, 0.3)) for _ in range(days)]

    df = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': [p * 1.01 for p in prices],
        'Low': [p * 0.99 for p in prices],
        'Close': prices,
        'Volume': volumes,
    })
    df.set_index('Date', inplace=True)
    return df


def create_observation(
    source: SourceType,
    payload: dict | None = None,
    freshness: float = 0.9,
    quality: float = 0.9,
) -> Observation:
    """Create a test observation."""
    return Observation(
        id=uuid4(),
        entity_id=uuid4(),
        source=source,
        payload=payload or {},
        observed_at=datetime.now(timezone.utc),
        freshness_score=freshness,
        quality_score=quality,
    )


# ============================================================================
# Test EquityScorer
# ============================================================================

class TestEquityScorer:
    """Tests for EquityScorer."""

    def test_asset_type_is_equity(self):
        """EquityScorer handles EQUITY assets."""
        scorer = EquityScorer()
        assert scorer.asset_type == AssetType.EQUITY

    def test_uses_equity_weights(self):
        """EquityScorer uses EQUITY_WEIGHTS by default."""
        scorer = EquityScorer()
        assert scorer.weights.anomaly == EQUITY_WEIGHTS.anomaly

    def test_custom_weights(self):
        """EquityScorer can use custom weights."""
        custom = ScoringWeights(anomaly=0.40, catalyst=0.25, flow=0.20, confidence=0.15)
        scorer = EquityScorer(weights=custom)
        assert scorer.weights.anomaly == 0.40

    def test_calculate_anomaly_empty_df(self):
        """Empty DataFrame returns baseline score."""
        scorer = EquityScorer()
        df = pd.DataFrame()
        score, ids, components = scorer.calculate_anomaly(df, [])
        assert score == 50.0
        assert ids == []

    def test_calculate_anomaly_short_df(self):
        """Short DataFrame returns baseline score."""
        scorer = EquityScorer()
        df = create_ohlcv_df(days=10)
        score, ids, components = scorer.calculate_anomaly(df, [])
        assert score == 50.0

    def test_calculate_anomaly_normal_df(self):
        """Normal DataFrame returns calculated score."""
        scorer = EquityScorer()
        df = create_ohlcv_df(days=60)
        score, ids, components = scorer.calculate_anomaly(df, [])
        assert 0 <= score <= 100
        assert components.price_component >= 0
        assert components.volume_component != 0  # Should have some value

    def test_calculate_anomaly_with_congress_observations(self):
        """Congress observations affect insider component."""
        scorer = EquityScorer()
        df = create_ohlcv_df(days=60)

        # Add a purchase observation
        obs = create_observation(
            SourceType.CONGRESS,
            payload={'type': 'Purchase', 'amount': 100000},
        )

        score, ids, components = scorer.calculate_anomaly(df, [obs])
        assert 0 <= score <= 100

    def test_calculate_catalyst_baseline(self):
        """No observations returns baseline score."""
        scorer = EquityScorer()
        score, ids = scorer.calculate_catalyst([])
        assert score == 50.0
        assert ids == []

    def test_calculate_catalyst_with_sec_filing(self):
        """SEC filing increases catalyst score."""
        scorer = EquityScorer()

        obs = create_observation(
            SourceType.SEC,
            payload={'form': '10-K'},
        )

        score, ids = scorer.calculate_catalyst([obs])
        assert score > 50.0
        assert len(ids) > 0

    def test_calculate_catalyst_8k_boost(self):
        """8-K filings get extra boost."""
        scorer = EquityScorer()

        obs_10k = create_observation(SourceType.SEC, payload={'form': '10-K'})
        obs_8k = create_observation(SourceType.SEC, payload={'form': '8-K'})

        score_10k, _ = scorer.calculate_catalyst([obs_10k])
        score_8k, _ = scorer.calculate_catalyst([obs_8k])

        assert score_8k > score_10k  # 8-K gets 1.5x boost

    def test_calculate_flow_baseline(self):
        """No observations returns baseline score."""
        scorer = EquityScorer()
        score, ids, components = scorer.calculate_flow([])
        assert score == 50.0
        assert ids == []

    def test_calculate_flow_congress_purchase(self):
        """Congress purchase increases flow score."""
        scorer = EquityScorer()

        obs = create_observation(
            SourceType.CONGRESS,
            payload={'type': 'Purchase'},
        )

        score, ids, components = scorer.calculate_flow([obs])
        assert score > 50.0
        assert components.congress_component > 0

    def test_calculate_flow_congress_sale(self):
        """Congress sale decreases flow score."""
        scorer = EquityScorer()

        obs = create_observation(
            SourceType.CONGRESS,
            payload={'type': 'Sale'},
        )

        score, ids, components = scorer.calculate_flow([obs])
        assert score < 50.0
        assert components.congress_component < 0

    def test_calculate_confidence_baseline(self):
        """No data returns low confidence."""
        scorer = EquityScorer()
        df = pd.DataFrame()
        score, ids = scorer.calculate_confidence([], df)
        assert score == 10.0

    def test_calculate_confidence_with_good_data(self):
        """Good data increases confidence."""
        scorer = EquityScorer()
        df = create_ohlcv_df(days=60)

        obs = create_observation(SourceType.SEC)

        score, ids = scorer.calculate_confidence([obs], df)
        assert score > 60.0  # Good data should give decent confidence

    def test_calculate_scores_full(self):
        """Full score calculation returns all components."""
        scorer = EquityScorer()
        df = create_ohlcv_df(days=60)

        obs = create_observation(SourceType.SEC, payload={'form': '8-K'})

        result = scorer.calculate_scores(df, [obs])

        assert 0 <= result.anomaly_score <= 100
        assert 0 <= result.catalyst_score <= 100
        assert 0 <= result.flow_score <= 100
        assert 0 <= result.confidence_score <= 100
        assert 0 <= result.attention_score <= 100
        assert len(result.evidence_ids) > 0


# ============================================================================
# Test CryptoScorer
# ============================================================================

class TestCryptoScorer:
    """Tests for CryptoScorer."""

    def test_asset_type_is_crypto(self):
        """CryptoScorer handles CRYPTO assets."""
        scorer = CryptoScorer()
        assert scorer.asset_type == AssetType.CRYPTO

    def test_uses_crypto_weights(self):
        """CryptoScorer uses CRYPTO_WEIGHTS by default."""
        scorer = CryptoScorer()
        assert scorer.weights.anomaly == CRYPTO_WEIGHTS.anomaly

    def test_calculate_anomaly_empty_df(self):
        """Empty DataFrame returns baseline score."""
        scorer = CryptoScorer()
        df = pd.DataFrame()
        score, ids, components = scorer.calculate_anomaly(df, [])
        assert score == 50.0

    def test_calculate_anomaly_with_onchain_data(self):
        """Onchain data affects anomaly score."""
        scorer = CryptoScorer()
        df = create_ohlcv_df(days=30)

        obs = create_observation(
            SourceType.CRYPTO,
            payload={
                'active_addresses_change': 0.5,
                'transaction_volume_change': 0.3,
            },
        )

        score, ids, components = scorer.calculate_anomaly(df, [obs])
        assert components.onchain_component > 0

    def test_calculate_anomaly_with_funding_rate(self):
        """High funding rate affects anomaly score."""
        scorer = CryptoScorer()
        df = create_ohlcv_df(days=30)

        obs = create_observation(
            SourceType.CRYPTO,
            payload={'funding_rate': 0.02},  # 2% funding rate
        )

        score, ids, components = scorer.calculate_anomaly(df, [obs])
        assert components.funding_rate_component > 0
        assert len(ids) > 0

    def test_calculate_catalyst_with_polymarket(self):
        """Polymarket events increase catalyst for crypto."""
        scorer = CryptoScorer()

        obs = create_observation(SourceType.POLYMARKET)

        score, ids = scorer.calculate_catalyst([obs])
        assert score > 50.0  # Polymarket has weight 20 for crypto

    def test_calculate_flow_exchange_inflow(self):
        """Exchange inflow (negative = bullish) affects flow score."""
        scorer = CryptoScorer()

        obs = create_observation(
            SourceType.CRYPTO,
            payload={'exchange_netflow': -5000},  # Outflow is bullish
        )

        score, ids, components = scorer.calculate_flow([obs])
        assert score > 50.0  # Outflow increases score
        assert components.exchange_flow_component > 0

    def test_calculate_flow_whale_activity(self):
        """Whale activity affects flow score."""
        scorer = CryptoScorer()

        obs = create_observation(
            SourceType.CRYPTO,
            payload={'whale_transactions': 50},
        )

        score, ids, components = scorer.calculate_flow([obs])
        assert components.whale_activity_component > 0

    def test_calculate_confidence_lower_baseline(self):
        """Crypto has slightly lower confidence baseline."""
        scorer = CryptoScorer()
        df = pd.DataFrame()
        score, ids = scorer.calculate_confidence([], df)
        assert score == 10.0  # Very low with no data


# ============================================================================
# Test PolymarketScorer
# ============================================================================

class TestPolymarketScorer:
    """Tests for PolymarketScorer."""

    def test_asset_type_is_polymarket(self):
        """PolymarketScorer handles POLYMARKET assets."""
        scorer = PolymarketScorer()
        assert scorer.asset_type == AssetType.POLYMARKET

    def test_uses_polymarket_weights(self):
        """PolymarketScorer uses POLYMARKET_WEIGHTS by default."""
        scorer = PolymarketScorer()
        assert scorer.weights.catalyst == POLYMARKET_WEIGHTS.catalyst

    def test_calculate_anomaly_poll_divergence(self):
        """Poll divergence affects anomaly score."""
        scorer = PolymarketScorer()
        df = create_ohlcv_df(days=10)  # Polymarket may have less data

        obs = create_observation(
            SourceType.POLYMARKET,
            payload={'odds': 0.65, 'poll_average': 0.45},  # 20% divergence
        )

        score, ids, components = scorer.calculate_anomaly(df, [obs])
        assert components.poll_divergence_component > 0
        assert len(ids) > 0

    def test_calculate_catalyst_resolution(self):
        """Market resolution is a major catalyst."""
        scorer = PolymarketScorer()

        obs_normal = create_observation(SourceType.POLYMARKET)
        obs_resolution = create_observation(
            SourceType.POLYMARKET,
            payload={'is_resolution': True},
        )

        score_normal, _ = scorer.calculate_catalyst([obs_normal])
        score_resolution, _ = scorer.calculate_catalyst([obs_resolution])

        assert score_resolution > score_normal  # Resolution gets 2x boost

    def test_calculate_catalyst_poll_release(self):
        """New poll release increases catalyst."""
        scorer = PolymarketScorer()

        obs = create_observation(
            SourceType.POLYMARKET,
            payload={'new_poll_release': True},
        )

        score, ids = scorer.calculate_catalyst([obs])
        assert score > 50.0

    def test_calculate_flow_large_trades(self):
        """Large trades affect flow score."""
        scorer = PolymarketScorer()

        obs = create_observation(
            SourceType.POLYMARKET,
            payload={'trade_size': 50000},  # $50k trade
        )

        score, ids, components = scorer.calculate_flow([obs])
        assert components.large_trades_component > 0
        assert score > 50.0

    def test_calculate_flow_smart_money(self):
        """Smart money indicators affect flow score."""
        scorer = PolymarketScorer()

        obs = create_observation(
            SourceType.POLYMARKET,
            payload={'known_sharp_trader': True, 'trade_direction': 'yes'},
        )

        score, ids, components = scorer.calculate_flow([obs])
        assert components.smart_money_component > 0

    def test_calculate_confidence_liquidity(self):
        """High liquidity increases confidence."""
        scorer = PolymarketScorer()
        df = pd.DataFrame()

        obs = create_observation(
            SourceType.POLYMARKET,
            payload={'total_liquidity': 200000, 'volume_24h': 75000},
        )

        score, ids = scorer.calculate_confidence([obs], df)
        assert score > 60.0  # High liquidity should give good confidence


# ============================================================================
# Test UnifiedScorer
# ============================================================================

class TestUnifiedScorer:
    """Tests for UnifiedScorer unified interface."""

    def test_get_scorer_equity(self):
        """UnifiedScorer returns EquityScorer for EQUITY assets."""
        scorer = UnifiedScorer()
        equity_scorer = scorer.get_scorer(AssetType.EQUITY)
        assert isinstance(equity_scorer, EquityScorer)

    def test_get_scorer_crypto(self):
        """UnifiedScorer returns CryptoScorer for CRYPTO assets."""
        scorer = UnifiedScorer()
        crypto_scorer = scorer.get_scorer(AssetType.CRYPTO)
        assert isinstance(crypto_scorer, CryptoScorer)

    def test_get_scorer_polymarket(self):
        """UnifiedScorer returns PolymarketScorer for POLYMARKET assets."""
        scorer = UnifiedScorer()
        pm_scorer = scorer.get_scorer(AssetType.POLYMARKET)
        assert isinstance(pm_scorer, PolymarketScorer)

    def test_get_scorer_index_uses_equity(self):
        """INDEX assets use EquityScorer."""
        scorer = UnifiedScorer()
        index_scorer = scorer.get_scorer(AssetType.INDEX)
        assert isinstance(index_scorer, EquityScorer)

    def test_get_scorer_commodity_uses_equity(self):
        """COMMODITY assets use EquityScorer."""
        scorer = UnifiedScorer()
        commodity_scorer = scorer.get_scorer(AssetType.COMMODITY)
        assert isinstance(commodity_scorer, EquityScorer)

    def test_calculate_scores_routes_correctly(self):
        """calculate_scores routes to appropriate scorer."""
        scorer = UnifiedScorer()
        df = create_ohlcv_df(days=60)

        # Test equity
        equity_result = scorer.calculate_scores(AssetType.EQUITY, df, [])
        assert isinstance(equity_result, ScoringResult)

        # Test crypto
        crypto_result = scorer.calculate_scores(AssetType.CRYPTO, df, [])
        assert isinstance(crypto_result, ScoringResult)

        # Test polymarket
        pm_result = scorer.calculate_scores(AssetType.POLYMARKET, df, [])
        assert isinstance(pm_result, ScoringResult)

    def test_historical_scores_updated(self):
        """Historical scores are updated after each calculation."""
        scorer = UnifiedScorer()
        df = create_ohlcv_df(days=60)

        # Initial state: empty history
        assert len(scorer._historical_scores[AssetType.EQUITY]["anomaly"]) == 0

        # Calculate scores
        scorer.calculate_scores(AssetType.EQUITY, df, [])

        # History should be updated
        assert len(scorer._historical_scores[AssetType.EQUITY]["anomaly"]) == 1

    def test_percentile_ranking(self):
        """Percentile ranking works with historical data."""
        scorer = UnifiedScorer()
        df = create_ohlcv_df(days=60)

        # Calculate multiple scores to build history
        for _ in range(10):
            scorer.calculate_scores(AssetType.EQUITY, df, [])

        # Next score should have percentile ranking
        result = scorer.calculate_scores(AssetType.EQUITY, df, [], use_percentiles=True)

        # Percentiles should be calculated
        assert 0 <= result.anomaly_percentile <= 100

    def test_compare_cross_asset(self):
        """Cross-asset comparison sorts by normalized score."""
        scorer = UnifiedScorer()
        df = create_ohlcv_df(days=60)

        # Create results for different asset types
        equity_result = scorer.calculate_scores(AssetType.EQUITY, df, [])
        crypto_result = scorer.calculate_scores(AssetType.CRYPTO, df, [])
        pm_result = scorer.calculate_scores(AssetType.POLYMARKET, df, [])

        results = [
            (AssetType.EQUITY, equity_result),
            (AssetType.CRYPTO, crypto_result),
            (AssetType.POLYMARKET, pm_result),
        ]

        compared = scorer.compare_cross_asset(results)

        # Should be sorted by normalized score descending
        assert len(compared) == 3
        for i in range(len(compared) - 1):
            assert compared[i][2] >= compared[i + 1][2]

    def test_compare_cross_asset_empty(self):
        """Empty results list returns empty comparison."""
        scorer = UnifiedScorer()
        compared = scorer.compare_cross_asset([])
        assert compared == []

    def test_get_attention_score_weights(self):
        """Get attention score weights for each asset type."""
        scorer = UnifiedScorer()

        equity_weights = scorer.get_attention_score_weights(AssetType.EQUITY)
        assert equity_weights == EQUITY_WEIGHTS

        crypto_weights = scorer.get_attention_score_weights(AssetType.CRYPTO)
        assert crypto_weights == CRYPTO_WEIGHTS

        pm_weights = scorer.get_attention_score_weights(AssetType.POLYMARKET)
        assert pm_weights == POLYMARKET_WEIGHTS


# ============================================================================
# Test BaseScorer (via concrete implementations)
# ============================================================================

class TestBaseScorer:
    """Tests for BaseScorer abstract methods."""

    def test_invalid_weights_raises(self):
        """Invalid weights raise ValueError."""
        with pytest.raises(ValueError):
            invalid_weights = ScoringWeights(
                anomaly=0.5, catalyst=0.5, flow=0.5, confidence=0.5
            )
            EquityScorer(weights=invalid_weights)

    def test_z_to_score_mapping(self):
        """Z-score to 0-100 score mapping works correctly."""
        scorer = EquityScorer()

        # Z=0 -> 50
        assert scorer._z_to_score(0) == 50.0

        # Z=2 -> ~80
        assert 75 <= scorer._z_to_score(2) <= 85

        # Z=-2 -> ~20
        assert 15 <= scorer._z_to_score(-2) <= 25

        # Score clamped to 0-100
        assert scorer._z_to_score(10) == 100.0
        assert scorer._z_to_score(-10) == 0.0

    def test_calculate_percentile(self):
        """Percentile calculation works correctly."""
        scorer = EquityScorer()

        historical = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]

        # Score of 55 should be around 50th percentile
        percentile = scorer._calculate_percentile(55.0, historical)
        assert 40 <= percentile <= 60

        # Score of 100 should be around 90th percentile
        percentile = scorer._calculate_percentile(100.0, historical)
        assert percentile >= 90

    def test_calculate_percentile_empty_history(self):
        """Empty history returns raw score as percentile."""
        scorer = EquityScorer()

        percentile = scorer._calculate_percentile(75.0, [])
        assert percentile == 75.0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for the unified scoring system."""

    def test_full_equity_scoring_pipeline(self):
        """Full scoring pipeline for equity asset."""
        scorer = UnifiedScorer()
        df = create_ohlcv_df(days=60)

        observations = [
            create_observation(SourceType.SEC, payload={'form': '8-K'}),
            create_observation(SourceType.NEWS),
            create_observation(SourceType.CONGRESS, payload={'type': 'Purchase'}),
        ]

        result = scorer.calculate_scores(AssetType.EQUITY, df, observations)

        # All scores in valid range
        assert 0 <= result.anomaly_score <= 100
        assert 0 <= result.catalyst_score <= 100
        assert 0 <= result.flow_score <= 100
        assert 0 <= result.confidence_score <= 100
        assert 0 <= result.attention_score <= 100

        # Should have evidence from observations
        assert len(result.evidence_ids) > 0

        # Result can be serialized
        d = result.to_dict()
        assert "anomaly_score" in d
        assert "percentiles" in d

    def test_full_crypto_scoring_pipeline(self):
        """Full scoring pipeline for crypto asset."""
        scorer = UnifiedScorer()
        df = create_ohlcv_df(days=30)

        observations = [
            create_observation(
                SourceType.CRYPTO,
                payload={
                    'exchange_netflow': -10000,
                    'whale_transactions': 20,
                    'funding_rate': 0.015,
                },
            ),
            create_observation(SourceType.NEWS),
        ]

        result = scorer.calculate_scores(AssetType.CRYPTO, df, observations)

        # All scores in valid range
        assert 0 <= result.anomaly_score <= 100
        assert 0 <= result.attention_score <= 100

        # Should have flow components from crypto data
        assert result.flow_components.exchange_flow_component != 0 or \
               result.flow_components.whale_activity_component != 0

    def test_full_polymarket_scoring_pipeline(self):
        """Full scoring pipeline for polymarket asset."""
        scorer = UnifiedScorer()
        df = create_ohlcv_df(days=15)

        observations = [
            create_observation(
                SourceType.POLYMARKET,
                payload={
                    'odds': 0.70,
                    'poll_average': 0.50,
                    'trade_size': 25000,
                    'total_liquidity': 150000,
                },
            ),
        ]

        result = scorer.calculate_scores(AssetType.POLYMARKET, df, observations)

        # All scores in valid range
        assert 0 <= result.anomaly_score <= 100
        assert 0 <= result.attention_score <= 100

        # Should have anomaly from poll divergence
        assert result.anomaly_components.poll_divergence_component > 0

    def test_cross_asset_comparison_realistic(self):
        """Realistic cross-asset comparison scenario."""
        scorer = UnifiedScorer()

        # Create different scenarios for each asset type
        equity_df = create_ohlcv_df(days=60, volatility=0.02)
        crypto_df = create_ohlcv_df(days=30, volatility=0.05)  # Higher volatility
        pm_df = create_ohlcv_df(days=15, volatility=0.01)

        equity_obs = [
            create_observation(SourceType.SEC, payload={'form': '8-K'}),
            create_observation(SourceType.CONGRESS, payload={'type': 'Purchase'}),
        ]

        crypto_obs = [
            create_observation(SourceType.CRYPTO, payload={'whale_transactions': 30}),
        ]

        pm_obs = [
            create_observation(
                SourceType.POLYMARKET,
                payload={'is_resolution': True, 'trade_size': 100000},
            ),
        ]

        equity_result = scorer.calculate_scores(AssetType.EQUITY, equity_df, equity_obs)
        crypto_result = scorer.calculate_scores(AssetType.CRYPTO, crypto_df, crypto_obs)
        pm_result = scorer.calculate_scores(AssetType.POLYMARKET, pm_df, pm_obs)

        results = [
            (AssetType.EQUITY, equity_result),
            (AssetType.CRYPTO, crypto_result),
            (AssetType.POLYMARKET, pm_result),
        ]

        compared = scorer.compare_cross_asset(results)

        # All three should be compared
        assert len(compared) == 3

        # Each entry has asset_type, result, normalized_score
        for asset_type, result, normalized_score in compared:
            assert isinstance(asset_type, AssetType)
            assert isinstance(result, ScoringResult)
            assert 0 <= normalized_score <= 100
