"""
Fact extraction from observations for structured report generation.

Extracts deterministic FactTableEntry data from observations to prevent
LLM fabrication in reports. Each observation source type has its own
extraction logic.

Supported sources:
- Congress: politician, party, trade_type, amount_range, ticker, trade_date
- SEC: filing_type, filed_date, form_url, key_items
- News: headline, publisher, published_at, sentiment_score
- Market (Equities/Crypto): price, change_pct, volume, volume_vs_avg
- Polymarket: market_question, probability, probability_change
"""
import logging
from datetime import datetime
from typing import Dict, List
from uuid import UUID

from ..models import FactTableEntry, FactType, Observation, SourceType

logger = logging.getLogger(__name__)


def extract_facts(observation: Observation) -> List[FactTableEntry]:
    """
    Extract structured facts from an observation based on its source type.

    Args:
        observation: The observation to extract facts from

    Returns:
        List of FactTableEntry objects
    """
    source = observation.source

    if source == SourceType.CONGRESS:
        return extract_congress_facts(observation)
    elif source == SourceType.SEC:
        return extract_sec_facts(observation)
    elif source == SourceType.NEWS:
        return extract_news_facts(observation)
    elif source in (SourceType.EQUITIES, SourceType.CRYPTO):
        return extract_market_facts(observation)
    elif source == SourceType.POLYMARKET:
        return extract_polymarket_facts(observation)
    elif source == SourceType.HEDGEFUND:
        return extract_hedgefund_facts(observation)
    else:
        logger.debug(f"No fact extractor for source type: {source}")
        return []


def extract_congress_facts(observation: Observation) -> List[FactTableEntry]:
    """
    Extract facts from a Congress trading observation.

    Extracts: politician, party, trade_type, amount_range, ticker, trade_date

    Args:
        observation: Congress observation with trade data in payload

    Returns:
        List of FactTableEntry objects
    """
    payload = observation.payload or {}
    facts: List[FactTableEntry] = []
    obs_id = observation.id
    base_timestamp = observation.effective_at or observation.observed_at
    source_name = payload.get("source", "Congress Trades")

    # Generate unique fact IDs
    def make_fact_id(fact_type: str) -> str:
        return f"{str(obs_id)[:8]}_{fact_type}"

    # Extract politician name
    politician = payload.get("member") or payload.get("politician")
    if politician:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("politician"),
            fact_type=FactType.POLITICIAN.value,
            label="Politician",
            value=politician,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract party
    party = payload.get("party")
    if party:
        party_full = {"D": "Democrat", "R": "Republican", "I": "Independent"}.get(party, party)
        facts.append(FactTableEntry(
            fact_id=make_fact_id("party"),
            fact_type=FactType.PARTY.value,
            label="Party",
            value=party_full,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract trade type (purchase/sale)
    trade_type = payload.get("type") or payload.get("trade_type")
    if trade_type:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("trade_type"),
            fact_type=FactType.TRADE_TYPE.value,
            label="Trade Type",
            value=trade_type.capitalize() if isinstance(trade_type, str) else str(trade_type),
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract amount range
    amount_str = payload.get("amount_str") or payload.get("amount_range")
    amount_min = payload.get("amount_min")
    if amount_str or amount_min:
        amount_display = amount_str or f"${amount_min:,}+"
        facts.append(FactTableEntry(
            fact_id=make_fact_id("amount"),
            fact_type=FactType.AMOUNT_RANGE.value,
            label="Trade Amount",
            value=amount_display,
            unit="$",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract ticker
    ticker = payload.get("ticker") or observation.entity_ticker
    if ticker:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("ticker"),
            fact_type=FactType.TICKER.value,
            label="Ticker",
            value=ticker.upper() if isinstance(ticker, str) else ticker,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract trade date
    trade_date = payload.get("transaction_date") or payload.get("trade_date")
    if trade_date:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("trade_date"),
            fact_type=FactType.TRADE_DATE.value,
            label="Trade Date",
            value=trade_date,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    return facts


def extract_sec_facts(observation: Observation) -> List[FactTableEntry]:
    """
    Extract facts from an SEC filing observation.

    Extracts: filing_type, filed_date, form_url, key_items

    Args:
        observation: SEC observation with filing data in payload

    Returns:
        List of FactTableEntry objects
    """
    payload = observation.payload or {}
    facts: List[FactTableEntry] = []
    obs_id = observation.id
    base_timestamp = observation.effective_at or observation.observed_at
    source_name = "SEC EDGAR"

    def make_fact_id(fact_type: str) -> str:
        return f"{str(obs_id)[:8]}_{fact_type}"

    # Extract filing type (10-K, 10-Q, 8-K, etc.)
    filing_type = payload.get("form") or payload.get("filing_type")
    if filing_type:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("filing_type"),
            fact_type=FactType.FILING_TYPE.value,
            label="Filing Type",
            value=filing_type,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract filed date
    filed_date = payload.get("filing_date") or payload.get("filed_date")
    if filed_date:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("filed_date"),
            fact_type=FactType.FILED_DATE.value,
            label="Filed Date",
            value=filed_date,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract form URL
    form_url = observation.source_url or payload.get("url") or payload.get("form_url")
    if form_url:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("form_url"),
            fact_type=FactType.FORM_URL.value,
            label="Filing URL",
            value=form_url,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
            source_url=form_url,
        ))

    # Extract ticker
    ticker = payload.get("ticker") or observation.entity_ticker
    if ticker:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("ticker"),
            fact_type=FactType.TICKER.value,
            label="Ticker",
            value=ticker.upper() if isinstance(ticker, str) else ticker,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract key items (for 8-K filings)
    key_items = payload.get("key_items") or payload.get("items")
    if key_items:
        if isinstance(key_items, list):
            for i, item in enumerate(key_items):
                facts.append(FactTableEntry(
                    fact_id=make_fact_id(f"key_item_{i}"),
                    fact_type=FactType.KEY_ITEM.value,
                    label=f"Key Item {i+1}",
                    value=item,
                    source=source_name,
                    timestamp=base_timestamp,
                    observation_id=obs_id,
                ))
        else:
            facts.append(FactTableEntry(
                fact_id=make_fact_id("key_items"),
                fact_type=FactType.KEY_ITEM.value,
                label="Key Items",
                value=key_items,
                source=source_name,
                timestamp=base_timestamp,
                observation_id=obs_id,
            ))

    # Extract company name
    company_name = payload.get("company_name")
    if company_name:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("company"),
            fact_type=FactType.OTHER.value,
            label="Company",
            value=company_name,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    return facts


def extract_news_facts(observation: Observation) -> List[FactTableEntry]:
    """
    Extract facts from a news observation.

    Extracts: headline, publisher, published_at, sentiment_score

    Args:
        observation: News observation with article data in payload

    Returns:
        List of FactTableEntry objects
    """
    payload = observation.payload or {}
    facts: List[FactTableEntry] = []
    obs_id = observation.id
    base_timestamp = observation.effective_at or observation.observed_at
    source_api = payload.get("source_api", "news")

    def make_fact_id(fact_type: str) -> str:
        return f"{str(obs_id)[:8]}_{fact_type}"

    # Extract headline/title
    headline = observation.title or payload.get("title") or payload.get("headline")
    if headline:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("headline"),
            fact_type=FactType.HEADLINE.value,
            label="Headline",
            value=headline,
            source=payload.get("source", source_api),
            timestamp=base_timestamp,
            observation_id=obs_id,
            source_url=observation.source_url or payload.get("url"),
        ))

    # Extract publisher/source
    publisher = payload.get("source") or payload.get("publisher")
    if publisher:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("publisher"),
            fact_type=FactType.PUBLISHER.value,
            label="Publisher",
            value=publisher,
            source=source_api,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract published_at
    published_at = payload.get("published_at") or payload.get("pubDate")
    if published_at:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("published_at"),
            fact_type=FactType.PUBLISHED_AT.value,
            label="Published At",
            value=published_at,
            source=payload.get("source", source_api),
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract sentiment score (if available)
    sentiment = payload.get("sentiment_score") or payload.get("sentiment")
    if sentiment is not None:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("sentiment"),
            fact_type=FactType.SENTIMENT_SCORE.value,
            label="Sentiment Score",
            value=sentiment,
            unit="score",
            source=payload.get("source", source_api),
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract ticker if present
    ticker = payload.get("ticker") or observation.entity_ticker
    if ticker:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("ticker"),
            fact_type=FactType.TICKER.value,
            label="Related Ticker",
            value=ticker.upper() if isinstance(ticker, str) else ticker,
            source=payload.get("source", source_api),
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    return facts


def extract_market_facts(observation: Observation) -> List[FactTableEntry]:
    """
    Extract facts from market (equities/crypto) observation.

    Extracts: price, change_pct, volume, volume_vs_avg

    Args:
        observation: Market observation with price/volume data in payload

    Returns:
        List of FactTableEntry objects
    """
    payload = observation.payload or {}
    facts: List[FactTableEntry] = []
    obs_id = observation.id
    base_timestamp = observation.effective_at or observation.observed_at
    source_name = "Yahoo Finance" if observation.source == SourceType.EQUITIES else "Exchange"

    def make_fact_id(fact_type: str) -> str:
        return f"{str(obs_id)[:8]}_{fact_type}"

    # Extract ticker
    ticker = payload.get("ticker") or payload.get("symbol") or observation.entity_ticker
    if ticker:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("ticker"),
            fact_type=FactType.TICKER.value,
            label="Ticker",
            value=ticker.upper() if isinstance(ticker, str) else ticker,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract price
    price = payload.get("close") or payload.get("price") or payload.get("Close")
    if price is not None:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("price"),
            fact_type=FactType.PRICE.value,
            label="Price",
            value=price,
            unit="$" if observation.source == SourceType.EQUITIES else "USDT",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract price change percentage
    change_pct = (
        payload.get("change_pct") or
        payload.get("day_return") or
        payload.get("return_pct") or
        payload.get("pct_change")
    )
    if change_pct is not None:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("change_pct"),
            fact_type=FactType.PRICE_CHANGE.value,
            label="Price Change",
            value=change_pct,
            unit="%",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract volume
    volume = payload.get("volume") or payload.get("Volume")
    if volume is not None:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("volume"),
            fact_type=FactType.VOLUME.value,
            label="Volume",
            value=volume,
            unit="shares" if observation.source == SourceType.EQUITIES else "units",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract volume vs average
    vol_vs_avg = (
        payload.get("volume_vs_avg") or
        payload.get("vol_ratio") or
        payload.get("relative_volume")
    )
    if vol_vs_avg is not None:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("vol_vs_avg"),
            fact_type=FactType.VOLUME_VS_AVG.value,
            label="Volume vs Avg",
            value=vol_vs_avg,
            unit="x",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract volatility if available
    volatility = payload.get("volatility") or payload.get("atr_pct")
    if volatility is not None:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("volatility"),
            fact_type=FactType.VOLATILITY.value,
            label="Volatility",
            value=volatility,
            unit="%",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    return facts


def extract_polymarket_facts(observation: Observation) -> List[FactTableEntry]:
    """
    Extract facts from a Polymarket prediction observation.

    Extracts: market_question, probability, probability_change

    Args:
        observation: Polymarket observation with prediction data in payload

    Returns:
        List of FactTableEntry objects
    """
    payload = observation.payload or {}
    facts: List[FactTableEntry] = []
    obs_id = observation.id
    base_timestamp = observation.effective_at or observation.observed_at
    source_name = "Polymarket"

    def make_fact_id(fact_type: str) -> str:
        return f"{str(obs_id)[:8]}_{fact_type}"

    # Extract market question
    question = (
        payload.get("question") or
        payload.get("title") or
        payload.get("market_question") or
        observation.title
    )
    if question:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("question"),
            fact_type=FactType.MARKET_QUESTION.value,
            label="Market Question",
            value=question,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
            source_url=observation.source_url or payload.get("url"),
        ))

    # Extract current probability
    probability = (
        payload.get("probability") or
        payload.get("yes_price") or
        payload.get("price")
    )
    if probability is not None:
        # Convert to percentage if in decimal form
        if isinstance(probability, (int, float)) and probability <= 1:
            probability = probability * 100
        facts.append(FactTableEntry(
            fact_id=make_fact_id("probability"),
            fact_type=FactType.PROBABILITY.value,
            label="Probability",
            value=probability,
            unit="%",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract probability change
    prob_change = (
        payload.get("probability_change") or
        payload.get("price_change") or
        payload.get("change_24h")
    )
    if prob_change is not None:
        # Convert to percentage if in decimal form
        if isinstance(prob_change, (int, float)) and -1 <= prob_change <= 1:
            prob_change = prob_change * 100
        facts.append(FactTableEntry(
            fact_id=make_fact_id("prob_change"),
            fact_type=FactType.PROBABILITY_CHANGE.value,
            label="24h Change",
            value=prob_change,
            unit="%",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract volume if available
    volume = payload.get("volume") or payload.get("volume_24h")
    if volume is not None:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("volume"),
            fact_type=FactType.VOLUME.value,
            label="Trading Volume",
            value=volume,
            unit="$",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract category if available
    category = payload.get("category")
    if category:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("category"),
            fact_type=FactType.OTHER.value,
            label="Category",
            value=category,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    return facts


def extract_hedgefund_facts(observation: Observation) -> List[FactTableEntry]:
    """
    Extract facts from a hedge fund 13F filing observation.

    Extracts: fund_name, position_change, shares, value

    Args:
        observation: 13F observation with position data in payload

    Returns:
        List of FactTableEntry objects
    """
    payload = observation.payload or {}
    facts: List[FactTableEntry] = []
    obs_id = observation.id
    base_timestamp = observation.effective_at or observation.observed_at
    source_name = "SEC 13F"

    def make_fact_id(fact_type: str) -> str:
        return f"{str(obs_id)[:8]}_{fact_type}"

    # Extract fund name
    fund_name = payload.get("fund_name") or payload.get("fund") or payload.get("manager")
    if fund_name:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("fund"),
            fact_type=FactType.OTHER.value,
            label="Fund Name",
            value=fund_name,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract ticker
    ticker = payload.get("ticker") or observation.entity_ticker
    if ticker:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("ticker"),
            fact_type=FactType.TICKER.value,
            label="Ticker",
            value=ticker.upper() if isinstance(ticker, str) else ticker,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract position change
    change_type = payload.get("change_type") or payload.get("action")
    if change_type:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("change_type"),
            fact_type=FactType.TRADE_TYPE.value,
            label="Position Change",
            value=change_type,
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract position change percentage
    change_pct = payload.get("change_pct") or payload.get("position_change_pct")
    if change_pct is not None:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("change_pct"),
            fact_type=FactType.PRICE_CHANGE.value,
            label="Position Change",
            value=change_pct,
            unit="%",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract shares
    shares = payload.get("shares") or payload.get("position_shares")
    if shares is not None:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("shares"),
            fact_type=FactType.VOLUME.value,
            label="Shares Held",
            value=shares,
            unit="shares",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    # Extract value
    value = payload.get("value") or payload.get("market_value")
    if value is not None:
        facts.append(FactTableEntry(
            fact_id=make_fact_id("value"),
            fact_type=FactType.PRICE.value,
            label="Position Value",
            value=value,
            unit="$",
            source=source_name,
            timestamp=base_timestamp,
            observation_id=obs_id,
        ))

    return facts


def update_observation_with_facts(observation: Observation) -> Observation:
    """
    Extract facts and update the observation's fact_entries field.

    Args:
        observation: The observation to update

    Returns:
        The updated observation with fact_entries populated
    """
    facts = extract_facts(observation)
    observation.fact_entries = [f.to_dict() for f in facts]
    return observation


def batch_extract_facts(observations: List[Observation]) -> Dict[UUID, List[FactTableEntry]]:
    """
    Extract facts from multiple observations.

    Args:
        observations: List of observations to process

    Returns:
        Dict mapping observation ID to list of extracted facts
    """
    results: Dict[UUID, List[FactTableEntry]] = {}

    for obs in observations:
        try:
            facts = extract_facts(obs)
            results[obs.id] = facts
        except Exception as e:
            logger.error(f"Failed to extract facts from observation {obs.id}: {e}")
            results[obs.id] = []

    return results
