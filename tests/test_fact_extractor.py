"""
Unit tests for fact extraction from observations.

Tests fact extraction for each source type:
- Congress: politician, party, trade_type, amount_range, ticker, trade_date
- SEC: filing_type, filed_date, form_url, key_items
- News: headline, publisher, published_at, sentiment_score
- Market: price, change_pct, volume, volume_vs_avg
- Polymarket: market_question, probability, probability_change
- HedgeFund: fund_name, position_change, shares, value
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.tradz.events.fact_extractor import (
    batch_extract_facts,
    extract_congress_facts,
    extract_facts,
    extract_hedgefund_facts,
    extract_market_facts,
    extract_news_facts,
    extract_polymarket_facts,
    extract_sec_facts,
    update_observation_with_facts,
)
from src.tradz.models import FactTableEntry, FactType, Observation, SourceType


class TestExtractCongressFacts:
    """Tests for Congress fact extraction."""

    def test_extract_full_congress_trade(self):
        """Test extraction from complete Congress trade observation."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.CONGRESS,
            entity_ticker="AAPL",
            observed_at=datetime.now(timezone.utc),
            payload={
                "ticker": "AAPL",
                "member": "Nancy Pelosi",
                "party": "D",
                "type": "purchase",
                "amount_str": "$15K-$50K",
                "amount_min": 15000,
                "transaction_date": "2024-01-15",
                "source": "Capitol Trades",
            },
        )

        facts = extract_congress_facts(obs)

        assert len(facts) >= 5
        fact_types = {f.fact_type for f in facts}

        # Verify all expected fact types are present
        assert FactType.POLITICIAN.value in fact_types
        assert FactType.PARTY.value in fact_types
        assert FactType.TRADE_TYPE.value in fact_types
        assert FactType.AMOUNT_RANGE.value in fact_types
        assert FactType.TICKER.value in fact_types
        assert FactType.TRADE_DATE.value in fact_types

    def test_extract_politician_name(self):
        """Test politician name extraction."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.CONGRESS,
            observed_at=datetime.now(timezone.utc),
            payload={"member": "Dan Crenshaw"},
        )

        facts = extract_congress_facts(obs)
        politician_facts = [f for f in facts if f.fact_type == FactType.POLITICIAN.value]

        assert len(politician_facts) == 1
        assert politician_facts[0].value == "Dan Crenshaw"
        assert politician_facts[0].label == "Politician"

    def test_extract_party_democrat(self):
        """Test party extraction - Democrat."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.CONGRESS,
            observed_at=datetime.now(timezone.utc),
            payload={"party": "D"},
        )

        facts = extract_congress_facts(obs)
        party_facts = [f for f in facts if f.fact_type == FactType.PARTY.value]

        assert len(party_facts) == 1
        assert party_facts[0].value == "Democrat"

    def test_extract_party_republican(self):
        """Test party extraction - Republican."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.CONGRESS,
            observed_at=datetime.now(timezone.utc),
            payload={"party": "R"},
        )

        facts = extract_congress_facts(obs)
        party_facts = [f for f in facts if f.fact_type == FactType.PARTY.value]

        assert len(party_facts) == 1
        assert party_facts[0].value == "Republican"

    def test_extract_trade_type_purchase(self):
        """Test trade type extraction - purchase."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.CONGRESS,
            observed_at=datetime.now(timezone.utc),
            payload={"type": "purchase"},
        )

        facts = extract_congress_facts(obs)
        type_facts = [f for f in facts if f.fact_type == FactType.TRADE_TYPE.value]

        assert len(type_facts) == 1
        assert type_facts[0].value == "Purchase"

    def test_extract_amount_from_string(self):
        """Test amount extraction from string format."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.CONGRESS,
            observed_at=datetime.now(timezone.utc),
            payload={"amount_str": "$100K-$250K"},
        )

        facts = extract_congress_facts(obs)
        amount_facts = [f for f in facts if f.fact_type == FactType.AMOUNT_RANGE.value]

        assert len(amount_facts) == 1
        assert amount_facts[0].value == "$100K-$250K"
        assert amount_facts[0].unit == "$"

    def test_extract_empty_congress_payload(self):
        """Test extraction with empty payload."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.CONGRESS,
            observed_at=datetime.now(timezone.utc),
            payload={},
        )

        facts = extract_congress_facts(obs)
        assert len(facts) == 0


class TestExtractSECFacts:
    """Tests for SEC filing fact extraction."""

    def test_extract_full_sec_filing(self):
        """Test extraction from complete SEC filing observation."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.SEC,
            entity_ticker="MSFT",
            source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany",
            observed_at=datetime.now(timezone.utc),
            payload={
                "ticker": "MSFT",
                "form": "10-K",
                "filing_date": "2024-01-30",
                "company_name": "Microsoft Corporation",
            },
        )

        facts = extract_sec_facts(obs)

        assert len(facts) >= 3
        fact_types = {f.fact_type for f in facts}

        assert FactType.FILING_TYPE.value in fact_types
        assert FactType.FILED_DATE.value in fact_types
        assert FactType.TICKER.value in fact_types

    def test_extract_filing_type(self):
        """Test filing type extraction."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.SEC,
            observed_at=datetime.now(timezone.utc),
            payload={"form": "8-K"},
        )

        facts = extract_sec_facts(obs)
        type_facts = [f for f in facts if f.fact_type == FactType.FILING_TYPE.value]

        assert len(type_facts) == 1
        assert type_facts[0].value == "8-K"
        assert type_facts[0].source == "SEC EDGAR"

    def test_extract_key_items_list(self):
        """Test key items extraction from list."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.SEC,
            observed_at=datetime.now(timezone.utc),
            payload={
                "form": "8-K",
                "key_items": ["Item 2.02", "Item 9.01"],
            },
        )

        facts = extract_sec_facts(obs)
        key_item_facts = [f for f in facts if f.fact_type == FactType.KEY_ITEM.value]

        assert len(key_item_facts) == 2

    def test_extract_form_url(self):
        """Test form URL extraction."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.SEC,
            source_url="https://sec.gov/filing/12345",
            observed_at=datetime.now(timezone.utc),
            payload={"form": "10-Q"},
        )

        facts = extract_sec_facts(obs)
        url_facts = [f for f in facts if f.fact_type == FactType.FORM_URL.value]

        assert len(url_facts) == 1
        assert url_facts[0].value == "https://sec.gov/filing/12345"
        assert url_facts[0].source_url == "https://sec.gov/filing/12345"


class TestExtractNewsFacts:
    """Tests for News fact extraction."""

    def test_extract_full_news_article(self):
        """Test extraction from complete news observation."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.NEWS,
            entity_ticker="TSLA",
            title="Tesla Announces Record Deliveries",
            source_url="https://example.com/news/tesla",
            observed_at=datetime.now(timezone.utc),
            payload={
                "title": "Tesla Announces Record Deliveries",
                "source": "Reuters",
                "published_at": "2024-01-15T10:30:00Z",
                "ticker": "TSLA",
                "source_api": "yahoo",
            },
        )

        facts = extract_news_facts(obs)

        assert len(facts) >= 3
        fact_types = {f.fact_type for f in facts}

        assert FactType.HEADLINE.value in fact_types
        assert FactType.PUBLISHER.value in fact_types
        assert FactType.PUBLISHED_AT.value in fact_types

    def test_extract_headline(self):
        """Test headline extraction."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.NEWS,
            title="Apple Reaches New All-Time High",
            observed_at=datetime.now(timezone.utc),
            payload={},
        )

        facts = extract_news_facts(obs)
        headline_facts = [f for f in facts if f.fact_type == FactType.HEADLINE.value]

        assert len(headline_facts) == 1
        assert headline_facts[0].value == "Apple Reaches New All-Time High"

    def test_extract_publisher(self):
        """Test publisher extraction."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.NEWS,
            observed_at=datetime.now(timezone.utc),
            payload={"source": "Bloomberg"},
        )

        facts = extract_news_facts(obs)
        publisher_facts = [f for f in facts if f.fact_type == FactType.PUBLISHER.value]

        assert len(publisher_facts) == 1
        assert publisher_facts[0].value == "Bloomberg"

    def test_extract_sentiment_score(self):
        """Test sentiment score extraction."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.NEWS,
            observed_at=datetime.now(timezone.utc),
            payload={"sentiment_score": 0.75},
        )

        facts = extract_news_facts(obs)
        sentiment_facts = [f for f in facts if f.fact_type == FactType.SENTIMENT_SCORE.value]

        assert len(sentiment_facts) == 1
        assert sentiment_facts[0].value == 0.75
        assert sentiment_facts[0].unit == "score"


class TestExtractMarketFacts:
    """Tests for Market (Equities/Crypto) fact extraction."""

    def test_extract_full_equity_data(self):
        """Test extraction from complete equity observation."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.EQUITIES,
            entity_ticker="NVDA",
            observed_at=datetime.now(timezone.utc),
            payload={
                "ticker": "NVDA",
                "close": 875.25,
                "change_pct": 5.2,
                "volume": 45000000,
                "volume_vs_avg": 2.3,
            },
        )

        facts = extract_market_facts(obs)

        assert len(facts) >= 4
        fact_types = {f.fact_type for f in facts}

        assert FactType.TICKER.value in fact_types
        assert FactType.PRICE.value in fact_types
        assert FactType.PRICE_CHANGE.value in fact_types
        assert FactType.VOLUME.value in fact_types
        assert FactType.VOLUME_VS_AVG.value in fact_types

    def test_extract_price(self):
        """Test price extraction."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.EQUITIES,
            observed_at=datetime.now(timezone.utc),
            payload={"close": 150.50},
        )

        facts = extract_market_facts(obs)
        price_facts = [f for f in facts if f.fact_type == FactType.PRICE.value]

        assert len(price_facts) == 1
        assert price_facts[0].value == 150.50
        assert price_facts[0].unit == "$"

    def test_extract_crypto_price(self):
        """Test crypto price extraction with correct unit."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.CRYPTO,
            entity_ticker="BTC/USDT",
            observed_at=datetime.now(timezone.utc),
            payload={"price": 45000.00},
        )

        facts = extract_market_facts(obs)
        price_facts = [f for f in facts if f.fact_type == FactType.PRICE.value]

        assert len(price_facts) == 1
        assert price_facts[0].value == 45000.00
        assert price_facts[0].unit == "USDT"

    def test_extract_volume_vs_avg(self):
        """Test volume vs average extraction."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.EQUITIES,
            observed_at=datetime.now(timezone.utc),
            payload={"volume_vs_avg": 3.5},
        )

        facts = extract_market_facts(obs)
        vol_avg_facts = [f for f in facts if f.fact_type == FactType.VOLUME_VS_AVG.value]

        assert len(vol_avg_facts) == 1
        assert vol_avg_facts[0].value == 3.5
        assert vol_avg_facts[0].unit == "x"

    def test_extract_volatility(self):
        """Test volatility extraction."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.EQUITIES,
            observed_at=datetime.now(timezone.utc),
            payload={"volatility": 25.5},
        )

        facts = extract_market_facts(obs)
        vol_facts = [f for f in facts if f.fact_type == FactType.VOLATILITY.value]

        assert len(vol_facts) == 1
        assert vol_facts[0].value == 25.5
        assert vol_facts[0].unit == "%"


class TestExtractPolymarketFacts:
    """Tests for Polymarket fact extraction."""

    def test_extract_full_polymarket_data(self):
        """Test extraction from complete Polymarket observation."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.POLYMARKET,
            title="Will Bitcoin reach $100k in 2024?",
            source_url="https://polymarket.com/market/btc-100k",
            observed_at=datetime.now(timezone.utc),
            payload={
                "question": "Will Bitcoin reach $100k in 2024?",
                "probability": 0.65,
                "probability_change": 0.05,
                "volume": 1500000,
                "category": "Crypto",
            },
        )

        facts = extract_polymarket_facts(obs)

        assert len(facts) >= 3
        fact_types = {f.fact_type for f in facts}

        assert FactType.MARKET_QUESTION.value in fact_types
        assert FactType.PROBABILITY.value in fact_types
        assert FactType.PROBABILITY_CHANGE.value in fact_types

    def test_extract_probability_converts_decimal(self):
        """Test probability extraction converts decimal to percentage."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.POLYMARKET,
            observed_at=datetime.now(timezone.utc),
            payload={"probability": 0.75},
        )

        facts = extract_polymarket_facts(obs)
        prob_facts = [f for f in facts if f.fact_type == FactType.PROBABILITY.value]

        assert len(prob_facts) == 1
        assert prob_facts[0].value == 75.0
        assert prob_facts[0].unit == "%"

    def test_extract_probability_change(self):
        """Test probability change extraction."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.POLYMARKET,
            observed_at=datetime.now(timezone.utc),
            payload={"probability_change": -0.10},
        )

        facts = extract_polymarket_facts(obs)
        change_facts = [f for f in facts if f.fact_type == FactType.PROBABILITY_CHANGE.value]

        assert len(change_facts) == 1
        assert change_facts[0].value == -10.0
        assert change_facts[0].unit == "%"


class TestExtractHedgeFundFacts:
    """Tests for Hedge Fund (13F) fact extraction."""

    def test_extract_full_13f_data(self):
        """Test extraction from complete 13F observation."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.HEDGEFUND,
            entity_ticker="META",
            observed_at=datetime.now(timezone.utc),
            payload={
                "ticker": "META",
                "fund_name": "Berkshire Hathaway",
                "change_type": "increased",
                "change_pct": 50.0,
                "shares": 5000000,
                "value": 2500000000,
            },
        )

        facts = extract_hedgefund_facts(obs)

        assert len(facts) >= 4
        fact_types = {f.fact_type for f in facts}

        assert FactType.TICKER.value in fact_types
        # Fund name is stored as OTHER type
        other_facts = [f for f in facts if f.label == "Fund Name"]
        assert len(other_facts) == 1

    def test_extract_position_change(self):
        """Test position change extraction."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.HEDGEFUND,
            observed_at=datetime.now(timezone.utc),
            payload={"change_pct": 75.5},
        )

        facts = extract_hedgefund_facts(obs)
        change_facts = [f for f in facts if f.fact_type == FactType.PRICE_CHANGE.value]

        assert len(change_facts) == 1
        assert change_facts[0].value == 75.5
        assert change_facts[0].unit == "%"


class TestExtractFactsDispatch:
    """Tests for the main extract_facts dispatch function."""

    def test_dispatch_to_congress(self):
        """Test dispatch to Congress extractor."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.CONGRESS,
            observed_at=datetime.now(timezone.utc),
            payload={"member": "Test Member"},
        )

        facts = extract_facts(obs)
        assert len(facts) > 0
        assert any(f.fact_type == FactType.POLITICIAN.value for f in facts)

    def test_dispatch_to_sec(self):
        """Test dispatch to SEC extractor."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.SEC,
            observed_at=datetime.now(timezone.utc),
            payload={"form": "10-K"},
        )

        facts = extract_facts(obs)
        assert len(facts) > 0
        assert any(f.fact_type == FactType.FILING_TYPE.value for f in facts)

    def test_dispatch_to_news(self):
        """Test dispatch to News extractor."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.NEWS,
            title="Test Headline",
            observed_at=datetime.now(timezone.utc),
            payload={},
        )

        facts = extract_facts(obs)
        assert len(facts) > 0
        assert any(f.fact_type == FactType.HEADLINE.value for f in facts)

    def test_dispatch_to_equities(self):
        """Test dispatch to Equities extractor."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.EQUITIES,
            observed_at=datetime.now(timezone.utc),
            payload={"close": 100.0},
        )

        facts = extract_facts(obs)
        assert len(facts) > 0
        assert any(f.fact_type == FactType.PRICE.value for f in facts)

    def test_dispatch_to_crypto(self):
        """Test dispatch to Crypto extractor (uses market facts)."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.CRYPTO,
            observed_at=datetime.now(timezone.utc),
            payload={"price": 50000.0},
        )

        facts = extract_facts(obs)
        assert len(facts) > 0
        assert any(f.fact_type == FactType.PRICE.value for f in facts)

    def test_dispatch_to_polymarket(self):
        """Test dispatch to Polymarket extractor."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.POLYMARKET,
            observed_at=datetime.now(timezone.utc),
            payload={"probability": 0.5},
        )

        facts = extract_facts(obs)
        assert len(facts) > 0
        assert any(f.fact_type == FactType.PROBABILITY.value for f in facts)

    def test_dispatch_to_hedgefund(self):
        """Test dispatch to HedgeFund extractor."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.HEDGEFUND,
            observed_at=datetime.now(timezone.utc),
            payload={"fund_name": "Test Fund"},
        )

        facts = extract_facts(obs)
        assert len(facts) > 0

    def test_unknown_source_returns_empty(self):
        """Test unknown source returns empty list."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.BROKER,  # No extractor for BROKER yet
            observed_at=datetime.now(timezone.utc),
            payload={"test": "data"},
        )

        facts = extract_facts(obs)
        assert facts == []


class TestUpdateObservationWithFacts:
    """Tests for updating observations with extracted facts."""

    def test_update_observation_populates_fact_entries(self):
        """Test that update_observation_with_facts populates fact_entries."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.EQUITIES,
            entity_ticker="AAPL",
            observed_at=datetime.now(timezone.utc),
            payload={"close": 175.50, "volume": 50000000},
        )

        assert obs.fact_entries == []

        updated = update_observation_with_facts(obs)

        assert len(updated.fact_entries) > 0
        assert all(isinstance(f, dict) for f in updated.fact_entries)
        # Verify the observation is the same object
        assert updated is obs


class TestBatchExtractFacts:
    """Tests for batch fact extraction."""

    def test_batch_extract_multiple_observations(self):
        """Test batch extraction from multiple observations."""
        obs1 = Observation(
            id=uuid4(),
            source=SourceType.EQUITIES,
            observed_at=datetime.now(timezone.utc),
            payload={"close": 100.0},
        )
        obs2 = Observation(
            id=uuid4(),
            source=SourceType.NEWS,
            title="Test News",
            observed_at=datetime.now(timezone.utc),
            payload={},
        )
        obs3 = Observation(
            id=uuid4(),
            source=SourceType.CONGRESS,
            observed_at=datetime.now(timezone.utc),
            payload={"member": "Test Member"},
        )

        results = batch_extract_facts([obs1, obs2, obs3])

        assert len(results) == 3
        assert obs1.id in results
        assert obs2.id in results
        assert obs3.id in results

        # Each should have extracted facts
        assert len(results[obs1.id]) > 0
        assert len(results[obs2.id]) > 0
        assert len(results[obs3.id]) > 0


class TestFactTableEntryMethods:
    """Tests for FactTableEntry class methods."""

    def test_to_dict(self):
        """Test FactTableEntry.to_dict() method."""
        obs_id = uuid4()
        fact = FactTableEntry(
            fact_id="test_fact_1",
            fact_type=FactType.PRICE.value,
            label="Price",
            value=150.50,
            unit="$",
            source="Yahoo Finance",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            observation_id=obs_id,
        )

        result = fact.to_dict()

        assert result["fact_id"] == "test_fact_1"
        assert result["fact_type"] == "price"
        assert result["label"] == "Price"
        assert result["value"] == 150.50
        assert result["unit"] == "$"
        assert result["source"] == "Yahoo Finance"
        assert result["observation_id"] == str(obs_id)

    def test_from_dict(self):
        """Test FactTableEntry.from_dict() class method."""
        obs_id = uuid4()
        data = {
            "fact_id": "test_fact_2",
            "fact_type": "volume",
            "label": "Volume",
            "value": 5000000,
            "unit": "shares",
            "source": "Exchange",
            "timestamp": "2024-01-15T10:30:00",
            "observation_id": str(obs_id),
        }

        fact = FactTableEntry.from_dict(data)

        assert fact.fact_id == "test_fact_2"
        assert fact.fact_type == "volume"
        assert fact.label == "Volume"
        assert fact.value == 5000000
        assert fact.unit == "shares"
        assert fact.observation_id == obs_id

    def test_backward_compatibility_category_field(self):
        """Test that category field is set from fact_type for backward compatibility."""
        fact = FactTableEntry(
            fact_id="test",
            fact_type=FactType.PRICE.value,
            label="Test",
        )

        assert fact.category == FactType.PRICE.value


class TestFactIdUniqueness:
    """Tests for fact ID uniqueness."""

    def test_fact_ids_are_unique_per_observation(self):
        """Test that fact IDs are unique within an observation."""
        obs = Observation(
            id=uuid4(),
            source=SourceType.CONGRESS,
            observed_at=datetime.now(timezone.utc),
            payload={
                "member": "Test Member",
                "party": "D",
                "type": "purchase",
                "amount_str": "$15K-$50K",
                "ticker": "AAPL",
                "transaction_date": "2024-01-15",
            },
        )

        facts = extract_congress_facts(obs)
        fact_ids = [f.fact_id for f in facts]

        # All fact IDs should be unique
        assert len(fact_ids) == len(set(fact_ids))

    def test_fact_ids_contain_observation_id_prefix(self):
        """Test that fact IDs contain observation ID prefix."""
        obs_id = uuid4()
        obs = Observation(
            id=obs_id,
            source=SourceType.EQUITIES,
            observed_at=datetime.now(timezone.utc),
            payload={"close": 100.0},
        )

        facts = extract_market_facts(obs)
        obs_id_prefix = str(obs_id)[:8]

        for fact in facts:
            assert fact.fact_id.startswith(obs_id_prefix)
