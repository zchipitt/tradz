"""
Tests for multi-asset entity support (US-026).

Tests Entity model, EntityResolver, and Database operations for:
- AssetType enum
- Entity identifiers and metadata
- Asset type detection (_looks_like_crypto, _looks_like_polymarket)
- Identifier conflict handling
- Cross-asset relationships
"""
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from src.tradz.database import Database
from src.tradz.entity_resolver import (
    AMBIGUOUS_SYMBOLS,
    KNOWN_CRYPTO_SYMBOLS,
    KNOWN_EQUITY_SYMBOLS,
    EntityResolver,
)
from src.tradz.models import AssetType, Entity


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create a temp directory and use a file path inside it
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_multi_asset.duckdb"
    db = Database(db_path)
    db.init_schema()
    yield db
    db.close()
    # Clean up
    db_path.unlink(missing_ok=True)
    Path(temp_dir).rmdir()


@pytest.fixture
def resolver(temp_db):
    """Create an EntityResolver with temp database."""
    return EntityResolver(db=temp_db)


# =============================================================================
# AssetType Enum Tests
# =============================================================================


class TestAssetTypeEnum:
    """Test AssetType enum values."""

    def test_asset_type_values(self):
        """Test that all expected asset types exist."""
        assert AssetType.EQUITY.value == "equity"
        assert AssetType.CRYPTO.value == "crypto"
        assert AssetType.POLYMARKET.value == "polymarket"
        assert AssetType.INDEX.value == "index"
        assert AssetType.COMMODITY.value == "commodity"

    def test_asset_type_from_string(self):
        """Test creating AssetType from string."""
        assert AssetType("equity") == AssetType.EQUITY
        assert AssetType("crypto") == AssetType.CRYPTO
        assert AssetType("polymarket") == AssetType.POLYMARKET

    def test_asset_type_iteration(self):
        """Test that we can iterate over AssetType."""
        types = list(AssetType)
        assert len(types) == 5
        assert AssetType.EQUITY in types
        assert AssetType.CRYPTO in types


# =============================================================================
# Entity Model Tests
# =============================================================================


class TestEntityModel:
    """Test Entity dataclass with multi-asset fields."""

    def test_entity_default_values(self):
        """Test Entity default values for new fields."""
        entity = Entity(ticker="AAPL")
        assert entity.asset_type == AssetType.EQUITY
        assert entity.identifiers == {}
        assert entity.metadata == {}
        assert entity.related_entities == []

    def test_entity_with_identifiers(self):
        """Test Entity with asset-specific identifiers."""
        entity = Entity(
            ticker="BTC",
            asset_type=AssetType.CRYPTO,
            identifiers={"coingecko_id": "bitcoin", "ticker": "BTC"},
        )
        assert entity.identifiers["coingecko_id"] == "bitcoin"
        assert entity.identifiers["ticker"] == "BTC"

    def test_entity_with_metadata(self):
        """Test Entity with asset-specific metadata."""
        entity = Entity(
            ticker="ETH",
            asset_type=AssetType.CRYPTO,
            metadata={"rank": "2", "category": "layer-1"},
        )
        assert entity.metadata["rank"] == "2"
        assert entity.metadata["category"] == "layer-1"

    def test_entity_with_related_entities(self):
        """Test Entity with cross-asset relationships."""
        related_id = uuid4()
        entity = Entity(
            ticker="BITO",  # Bitcoin ETF
            asset_type=AssetType.EQUITY,
            related_entities=[related_id],
        )
        assert len(entity.related_entities) == 1
        assert entity.related_entities[0] == related_id

    def test_entity_to_dict_includes_new_fields(self):
        """Test that to_dict() includes all multi-asset fields."""
        related_id = uuid4()
        entity = Entity(
            ticker="SOL",
            asset_type=AssetType.CRYPTO,
            identifiers={"coingecko_id": "solana"},
            metadata={"rank": "5"},
            related_entities=[related_id],
        )
        d = entity.to_dict()
        assert d["asset_type"] == "crypto"
        assert d["identifiers"] == {"coingecko_id": "solana"}
        assert d["metadata"] == {"rank": "5"}
        assert d["related_entities"] == [str(related_id)]

    def test_equity_entity_with_cik(self):
        """Test equity entity with CIK identifier."""
        entity = Entity(
            ticker="AAPL",
            cik="0000320193",
            name="Apple Inc.",
            asset_type=AssetType.EQUITY,
            identifiers={"ticker": "AAPL", "cik": "0000320193"},
            metadata={"sector": "Technology"},
        )
        assert entity.cik == "0000320193"
        assert entity.identifiers["cik"] == "0000320193"
        assert entity.metadata["sector"] == "Technology"

    def test_polymarket_entity(self):
        """Test Polymarket entity with market_id."""
        entity = Entity(
            ticker="WILL_TRUMP",
            asset_type=AssetType.POLYMARKET,
            identifiers={"market_id": "abc123def456"},
            metadata={
                "question": "Will Trump win 2024?",
                "category": "Politics",
                "end_date": "2024-11-05",
            },
        )
        assert entity.asset_type == AssetType.POLYMARKET
        assert entity.identifiers["market_id"] == "abc123def456"
        assert entity.metadata["end_date"] == "2024-11-05"


# =============================================================================
# Database Tests
# =============================================================================


class TestDatabaseMultiAsset:
    """Test Database operations with multi-asset entities."""

    def test_insert_entity_with_asset_type(self, temp_db):
        """Test inserting entity with asset_type."""
        entity = Entity(
            ticker="BTC",
            name="Bitcoin",
            asset_type=AssetType.CRYPTO,
            identifiers={"coingecko_id": "bitcoin"},
        )
        entity_id = temp_db.insert_entity(entity)
        assert entity_id == str(entity.id)

    def test_get_entity_by_ticker_returns_asset_type(self, temp_db):
        """Test that get_entity_by_ticker returns asset_type."""
        entity = Entity(
            ticker="ETH",
            asset_type=AssetType.CRYPTO,
            identifiers={"coingecko_id": "ethereum"},
            metadata={"rank": "2"},
        )
        temp_db.insert_entity(entity)

        retrieved = temp_db.get_entity_by_ticker("ETH")
        assert retrieved is not None
        assert retrieved.asset_type == AssetType.CRYPTO
        assert retrieved.identifiers.get("coingecko_id") == "ethereum"
        assert retrieved.metadata.get("rank") == "2"

    def test_get_entities_by_asset_type(self, temp_db):
        """Test filtering entities by asset type."""
        # Insert some equity entities
        for ticker in ["AAPL", "MSFT", "GOOGL"]:
            temp_db.insert_entity(
                Entity(ticker=ticker, asset_type=AssetType.EQUITY)
            )

        # Insert some crypto entities
        for ticker in ["BTC", "ETH"]:
            temp_db.insert_entity(
                Entity(ticker=ticker, asset_type=AssetType.CRYPTO)
            )

        equities = temp_db.get_entities_by_asset_type(AssetType.EQUITY)
        assert len(equities) == 3

        cryptos = temp_db.get_entities_by_asset_type(AssetType.CRYPTO)
        assert len(cryptos) == 2

    def test_get_entity_by_identifier(self, temp_db):
        """Test getting entity by identifier key-value."""
        entity = Entity(
            ticker="BTC",
            asset_type=AssetType.CRYPTO,
            identifiers={"coingecko_id": "bitcoin", "ticker": "BTC"},
        )
        temp_db.insert_entity(entity)

        retrieved = temp_db.get_entity_by_identifier("coingecko_id", "bitcoin")
        assert retrieved is not None
        assert retrieved.ticker == "BTC"

    def test_update_entity_preserves_multi_asset_fields(self, temp_db):
        """Test that updating entity preserves new fields."""
        entity = Entity(
            ticker="LINK",
            asset_type=AssetType.CRYPTO,
            identifiers={"coingecko_id": "chainlink"},
            metadata={"rank": "15"},
        )
        temp_db.insert_entity(entity)

        # Update with new metadata
        entity.metadata["rank"] = "12"
        temp_db.insert_entity(entity)

        retrieved = temp_db.get_entity_by_ticker("LINK")
        assert retrieved is not None
        assert retrieved.metadata.get("rank") == "12"

    def test_entity_with_related_entities(self, temp_db):
        """Test storing and retrieving related_entities."""
        # Create a crypto entity
        btc = Entity(
            ticker="BTC",
            asset_type=AssetType.CRYPTO,
        )
        temp_db.insert_entity(btc)

        # Create an equity that references the crypto
        bito = Entity(
            ticker="BITO",
            asset_type=AssetType.EQUITY,
            related_entities=[btc.id],
        )
        temp_db.insert_entity(bito)

        retrieved = temp_db.get_entity_by_ticker("BITO")
        assert retrieved is not None
        assert len(retrieved.related_entities) == 1
        assert retrieved.related_entities[0] == btc.id

    def test_migration_adds_new_columns(self, temp_db):
        """Test that migration adds new columns to existing table."""
        # This is implicitly tested - if the schema was created with
        # old code and then migrated, the new columns should exist
        result = temp_db.conn.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'entities'
        """).fetchall()
        columns = [r[0] for r in result]
        assert "asset_type" in columns
        assert "identifiers" in columns
        assert "metadata" in columns
        assert "related_entities" in columns


# =============================================================================
# EntityResolver Tests
# =============================================================================


class TestEntityResolverAssetTypeDetection:
    """Test EntityResolver asset type detection methods."""

    def test_looks_like_crypto_with_known_symbols(self, resolver):
        """Test _looks_like_crypto with known crypto symbols."""
        assert resolver._looks_like_crypto("BTC") is True
        assert resolver._looks_like_crypto("ETH") is True
        assert resolver._looks_like_crypto("SOL") is True

    def test_looks_like_crypto_with_trading_pairs(self, resolver):
        """Test _looks_like_crypto with trading pair format."""
        assert resolver._looks_like_crypto("BTC/USDT") is True
        assert resolver._looks_like_crypto("ETH-USD") is True
        assert resolver._looks_like_crypto("SOL/USDC") is True

    def test_looks_like_crypto_with_concatenated_pairs(self, resolver):
        """Test _looks_like_crypto with concatenated pair format."""
        assert resolver._looks_like_crypto("BTCUSDT") is True
        assert resolver._looks_like_crypto("ETHUSDC") is True

    def test_looks_like_crypto_false_for_equities(self, resolver):
        """Test _looks_like_crypto returns false for equity symbols."""
        assert resolver._looks_like_crypto("AAPL") is False
        assert resolver._looks_like_crypto("MSFT") is False
        assert resolver._looks_like_crypto("GOOGL") is False

    def test_looks_like_polymarket_with_long_id(self, resolver):
        """Test _looks_like_polymarket with long hex ID."""
        long_id = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
        assert resolver._looks_like_polymarket(long_id) is True

    def test_looks_like_polymarket_with_question(self, resolver):
        """Test _looks_like_polymarket with question format."""
        assert resolver._looks_like_polymarket("Will Trump win?") is True
        assert resolver._looks_like_polymarket("Will Bitcoin reach 100k?") is True

    def test_looks_like_polymarket_false_for_short_symbols(self, resolver):
        """Test _looks_like_polymarket returns false for regular symbols."""
        assert resolver._looks_like_polymarket("BTC") is False
        assert resolver._looks_like_polymarket("AAPL") is False

    def test_detect_asset_type_equity(self, resolver):
        """Test _detect_asset_type for equity symbols."""
        assert resolver._detect_asset_type("AAPL") == AssetType.EQUITY
        assert resolver._detect_asset_type("MSFT") == AssetType.EQUITY
        assert resolver._detect_asset_type("COIN") == AssetType.EQUITY  # Known equity

    def test_detect_asset_type_crypto(self, resolver):
        """Test _detect_asset_type for crypto symbols."""
        assert resolver._detect_asset_type("BTC") == AssetType.CRYPTO
        assert resolver._detect_asset_type("ETH") == AssetType.CRYPTO
        assert resolver._detect_asset_type("SOL") == AssetType.CRYPTO

    def test_detect_asset_type_polymarket(self, resolver):
        """Test _detect_asset_type for Polymarket identifiers."""
        long_id = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
        assert resolver._detect_asset_type(long_id) == AssetType.POLYMARKET

    def test_detect_asset_type_crypto_pair(self, resolver):
        """Test _detect_asset_type for crypto trading pairs."""
        assert resolver._detect_asset_type("BTC/USDT") == AssetType.CRYPTO
        assert resolver._detect_asset_type("ETHUSDC") == AssetType.CRYPTO


class TestEntityResolverIdentifierConflicts:
    """Test EntityResolver handling of identifier conflicts."""

    def test_known_equity_symbols_list(self):
        """Test that known equity symbols are defined."""
        assert "COIN" in KNOWN_EQUITY_SYMBOLS
        assert "MSTR" in KNOWN_EQUITY_SYMBOLS

    def test_known_crypto_symbols_list(self):
        """Test that known crypto symbols are defined."""
        assert "BTC" in KNOWN_CRYPTO_SYMBOLS
        assert "ETH" in KNOWN_CRYPTO_SYMBOLS
        assert "LINK" in KNOWN_CRYPTO_SYMBOLS

    def test_ambiguous_symbols_list(self):
        """Test that ambiguous symbols are defined."""
        assert "LINK" in AMBIGUOUS_SYMBOLS
        assert "ATOM" in AMBIGUOUS_SYMBOLS
        assert "SAND" in AMBIGUOUS_SYMBOLS

    def test_is_ambiguous_symbol(self, resolver):
        """Test is_ambiguous_symbol method."""
        assert resolver.is_ambiguous_symbol("LINK") is True
        assert resolver.is_ambiguous_symbol("ATOM") is True
        assert resolver.is_ambiguous_symbol("BTC") is False
        assert resolver.is_ambiguous_symbol("AAPL") is False

    def test_coin_is_equity_not_crypto(self, resolver):
        """Test that COIN (Coinbase) is detected as equity."""
        assert resolver._detect_asset_type("COIN") == AssetType.EQUITY

    def test_resolve_symbol_with_context_uses_source(self, resolver, temp_db):
        """Test that resolve_symbol_with_context uses source for disambiguation."""
        # Create a crypto entity for LINK
        crypto_link = Entity(
            ticker="LINK",
            name="Chainlink",
            asset_type=AssetType.CRYPTO,
        )
        temp_db.insert_entity(crypto_link)

        # Resolve with crypto context
        _entity, asset_type = resolver.resolve_symbol_with_context(
            "LINK", source_type="crypto"
        )
        assert asset_type == AssetType.CRYPTO

        # Resolve with equity context
        _entity, asset_type = resolver.resolve_symbol_with_context(
            "LINK", source_type="equities"
        )
        assert asset_type == AssetType.EQUITY

    def test_asset_type_from_source(self, resolver):
        """Test _asset_type_from_source mapping."""
        assert resolver._asset_type_from_source("equities") == AssetType.EQUITY
        assert resolver._asset_type_from_source("crypto") == AssetType.CRYPTO
        assert resolver._asset_type_from_source("polymarket") == AssetType.POLYMARKET
        assert resolver._asset_type_from_source("sec") == AssetType.EQUITY
        assert resolver._asset_type_from_source("unknown") == AssetType.EQUITY


class TestEntityResolverCRUD:
    """Test EntityResolver CRUD operations with multi-asset support."""

    def test_get_or_create_entity_auto_detects_asset_type(self, resolver):
        """Test that get_or_create_entity auto-detects asset type."""
        btc = resolver.get_or_create_entity("BTC", name="Bitcoin")
        assert btc.asset_type == AssetType.CRYPTO

        aapl = resolver.get_or_create_entity("AAPL", name="Apple Inc.")
        assert aapl.asset_type == AssetType.EQUITY

    def test_get_or_create_entity_with_explicit_asset_type(self, resolver):
        """Test get_or_create_entity with explicit asset type."""
        # Force LINK to be equity even though it's in crypto list
        link = resolver.get_or_create_entity(
            "LINK",
            name="Link Stock",
            asset_type=AssetType.EQUITY,
        )
        assert link.asset_type == AssetType.EQUITY

    def test_get_or_create_entity_with_identifiers(self, resolver):
        """Test get_or_create_entity with identifiers."""
        eth = resolver.get_or_create_entity(
            "ETH",
            name="Ethereum",
            identifiers={"coingecko_id": "ethereum"},
        )
        assert eth.identifiers.get("coingecko_id") == "ethereum"

    def test_get_or_create_entity_with_metadata(self, resolver):
        """Test get_or_create_entity with metadata."""
        eth = resolver.get_or_create_entity(
            "ETH",
            name="Ethereum",
            metadata={"rank": "2", "category": "smart-contracts"},
        )
        assert eth.metadata.get("rank") == "2"

    def test_get_or_create_crypto_entity(self, resolver):
        """Test get_or_create_crypto_entity convenience method."""
        btc = resolver.get_or_create_crypto_entity(
            symbol="BTC",
            name="Bitcoin",
            coingecko_id="bitcoin",
            rank=1,
            category="currency",
        )
        assert btc.asset_type == AssetType.CRYPTO
        assert btc.identifiers.get("coingecko_id") == "bitcoin"
        assert btc.metadata.get("rank") == "1"
        assert btc.metadata.get("category") == "currency"

    def test_get_or_create_polymarket_entity(self, resolver):
        """Test get_or_create_polymarket_entity convenience method."""
        market = resolver.get_or_create_polymarket_entity(
            market_id="abc123def456789",
            question="Will Bitcoin reach 100k in 2024?",
            category="Crypto",
            end_date="2024-12-31",
        )
        assert market.asset_type == AssetType.POLYMARKET
        assert market.identifiers.get("market_id") == "abc123def456789"
        assert market.metadata.get("question") == "Will Bitcoin reach 100k in 2024?"
        assert market.metadata.get("category") == "Crypto"
        assert market.metadata.get("end_date") == "2024-12-31"

    def test_polymarket_ticker_generation(self, resolver):
        """Test _generate_polymarket_ticker generates readable tickers."""
        ticker = resolver._generate_polymarket_ticker(
            "Will Bitcoin reach 100k?", "abc123"
        )
        assert ticker == "WILL_BITCOIN_REACH"

        # Test with short question
        ticker = resolver._generate_polymarket_ticker("Yes?", "abc123")
        assert ticker == "YES"

        # Test with empty question
        ticker = resolver._generate_polymarket_ticker("", "abc123def")
        assert ticker == "ABC123DE"

    def test_resolve_ticker_with_asset_type_filter(self, resolver, temp_db):
        """Test resolve_ticker with asset_type filter."""
        # Create crypto LINK
        temp_db.insert_entity(
            Entity(ticker="LINK", asset_type=AssetType.CRYPTO, name="Chainlink")
        )

        # Resolve without filter - should find it
        entity = resolver.resolve_ticker("LINK")
        assert entity is not None

        # Resolve with crypto filter - should find it
        entity = resolver.resolve_ticker("LINK", asset_type=AssetType.CRYPTO)
        assert entity is not None

        # Resolve with equity filter - should not find it
        entity = resolver.resolve_ticker("LINK", asset_type=AssetType.EQUITY)
        assert entity is None

    def test_resolve_all_asset_types(self, resolver, temp_db):
        """Test resolve_all_asset_types returns all matching entities."""
        # Create an entity
        temp_db.insert_entity(
            Entity(ticker="BTC", asset_type=AssetType.CRYPTO, name="Bitcoin")
        )

        entities = resolver.resolve_all_asset_types("BTC")
        assert len(entities) >= 1
        assert any(e.ticker == "BTC" for e in entities)


class TestEntityResolverCaching:
    """Test EntityResolver caching behavior with multi-asset support."""

    def test_cache_key_includes_asset_type(self, resolver, temp_db):
        """Test that cache keys include asset type for disambiguation."""
        entity = Entity(
            ticker="LINK",
            asset_type=AssetType.CRYPTO,
            name="Chainlink",
        )
        temp_db.insert_entity(entity)

        # First call should hit database
        result1 = resolver.resolve_ticker("LINK", asset_type=AssetType.CRYPTO)
        assert result1 is not None

        # Second call should hit cache
        result2 = resolver.resolve_ticker("LINK", asset_type=AssetType.CRYPTO)
        assert result2 is not None
        assert result1.id == result2.id


# =============================================================================
# Integration Tests
# =============================================================================


class TestMultiAssetIntegration:
    """Integration tests for multi-asset entity support."""

    def test_full_crypto_workflow(self, resolver):
        """Test complete workflow for crypto entity."""
        # Create
        btc = resolver.get_or_create_crypto_entity(
            symbol="BTC",
            name="Bitcoin",
            coingecko_id="bitcoin",
            rank=1,
        )

        # Verify
        assert btc.asset_type == AssetType.CRYPTO
        assert btc.identifiers.get("coingecko_id") == "bitcoin"

        # Resolve by ticker
        resolved = resolver.resolve_ticker("BTC")
        assert resolved is not None
        assert resolved.id == btc.id

        # Resolve with context
        entity, asset_type = resolver.resolve_symbol_with_context(
            "BTC", source_type="crypto"
        )
        assert asset_type == AssetType.CRYPTO
        assert entity is not None

    def test_full_polymarket_workflow(self, resolver, temp_db):
        """Test complete workflow for Polymarket entity."""
        # Create
        market = resolver.get_or_create_polymarket_entity(
            market_id="pm-123456789",
            question="Will ETH flip BTC?",
            category="Crypto",
        )

        # Verify
        assert market.asset_type == AssetType.POLYMARKET
        assert market.identifiers.get("market_id") == "pm-123456789"

        # Find by identifier
        found = temp_db.get_entity_by_identifier("market_id", "pm-123456789")
        assert found is not None
        assert found.id == market.id

    def test_cross_asset_relationships(self, resolver, temp_db):
        """Test entities with cross-asset relationships."""
        # Create underlying crypto
        btc = resolver.get_or_create_crypto_entity(
            symbol="BTC",
            name="Bitcoin",
        )

        # Create ETF that references the crypto
        bito = resolver.get_or_create_entity(
            ticker="BITO",
            name="ProShares Bitcoin ETF",
            asset_type=AssetType.EQUITY,
        )

        # Update BITO with relationship
        bito.related_entities = [btc.id]
        temp_db.insert_entity(bito)

        # Verify relationship
        retrieved = temp_db.get_entity_by_ticker("BITO")
        assert retrieved is not None
        assert btc.id in retrieved.related_entities

    def test_ambiguous_symbol_handling(self, resolver, temp_db):  # noqa: ARG002
        """Test handling of ambiguous symbols like LINK."""
        # LINK is in AMBIGUOUS_SYMBOLS - could be crypto or equity
        assert resolver.is_ambiguous_symbol("LINK")

        # Create as crypto (default detection)
        link = resolver.get_or_create_entity("LINK", name="Chainlink")
        assert link.asset_type == AssetType.CRYPTO  # Detected as crypto

        # Resolve with different contexts
        _entity, asset_type = resolver.resolve_symbol_with_context(
            "LINK", source_type="crypto"
        )
        assert asset_type == AssetType.CRYPTO

        _entity, asset_type = resolver.resolve_symbol_with_context(
            "LINK", source_type="equities"
        )
        assert asset_type == AssetType.EQUITY
