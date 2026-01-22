"""
Entity Resolver module for aligning data across sources.

Responsibilities:
- Resolve tickers/CIKs/names to unique Entity IDs
- Maintain the 'entities' table in the database
- Extract entities from unstructured text (news, tweets)
- Detect asset types (equity, crypto, polymarket) and handle identifier conflicts
"""
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import httpx

from .database import Database, get_database
from .models import Entity, EntityType, AssetType

logger = logging.getLogger(__name__)


# Well-known crypto symbols that could conflict with equity tickers
KNOWN_CRYPTO_SYMBOLS: Set[str] = {
    "BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOGE", "AVAX", "DOT", "MATIC",
    "LINK", "UNI", "ATOM", "LTC", "XLM", "ALGO", "NEAR", "FTM", "SAND", "MANA",
    "AXS", "FIL", "AAVE", "CRV", "MKR", "SNX", "COMP", "YFI", "SUSHI", "BAL",
    "ENJ", "CHZ", "GRT", "1INCH", "LRC", "REN", "OCEAN", "BAND", "ZRX", "KNC",
    "OMG", "BAT", "ZIL", "ICX", "ONT", "VET", "NEO", "QTUM", "EOS", "TRX",
    "XTZ", "THETA", "EGLD", "HBAR", "ICP", "FLOW", "ROSE", "ONE", "AR", "HNT",
    "APE", "GMT", "SHIB", "PEPE", "WLD", "SEI", "SUI", "APT", "ARB", "OP",
}

# Symbols that are definitely equities even if they look like crypto
KNOWN_EQUITY_SYMBOLS: Set[str] = {
    "COIN",  # Coinbase stock, not a crypto
    "MSTR",  # MicroStrategy
    "RIOT",  # Riot Platforms
    "MARA",  # Marathon Digital
    "HUT",   # Hut 8 Mining
    "BITF",  # Bitfarms
    "CLSK",  # CleanSpark
}

# Symbols that could be both equity and crypto (conflict list)
AMBIGUOUS_SYMBOLS: Set[str] = {
    "LINK",  # Chainlink (crypto) vs LKQ Corporation was NYSE:LINK in past
    "ATOM",  # Cosmos (crypto) vs Atomera (ATOM on NASDAQ)
    "SAND",  # The Sandbox (crypto) vs Sandstorm Gold (SAND on NYSE)
    "MANA",  # Decentraland (crypto)
    "ONE",   # Harmony (crypto) vs OneSmart (ONE on NYSE)
    "FLOW",  # Flow (crypto) vs SPX FLOW (FLOW on NYSE)
    "ICX",   # ICON (crypto)
    "NEO",   # NEO (crypto) vs NeoGenomics (NEO on NASDAQ)
    "ROSE",  # Oasis Network (crypto) vs Rosehill Resources (ROSE)
    "AR",    # Arweave (crypto) vs Antero Resources (AR on NYSE)
}

# Common crypto trading pair suffixes
CRYPTO_PAIR_SUFFIXES: Set[str] = {
    "USDT", "USDC", "USD", "BUSD", "DAI", "EUR", "GBP", "BTC", "ETH", "BNB",
}


class EntityResolver:
    """
    Resolves data points to canonical Entities.

    Acts as the source of truth for Ticker <-> CIK <-> Company Name mappings.
    Supports multi-asset types: equity, crypto, polymarket, index, commodity.
    Handles identifier conflicts (e.g., LINK could be equity or crypto).
    """

    SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

    def __init__(self, db: Optional[Database] = None):
        """
        Initialize EntityResolver.

        Args:
            db: Database instance (uses singleton if not provided)
        """
        self.db = db or get_database()
        # SEC requires User-Agent: AppName/Version (email)
        self._user_agent = "Tradz/1.0 (contact@tradz.app)"

        # In-memory caches for fast lookup
        # Key format: (ticker, asset_type) for disambiguation
        self._ticker_cache: Dict[str, Entity] = {}
        self._cik_cache: Dict[str, Entity] = {}
        self._name_cache: Dict[str, Entity] = {}
        self._identifier_cache: Dict[Tuple[str, str], Entity] = {}  # (key, value) -> Entity
        
    def initialize_reference_data(self):
        """
        Initialize reference data (SEC tickers) into the database.
        
        Should be called periodically (e.g., once a week).
        """
        logger.info("Initializing entity reference data...")
        self._sync_sec_tickers()
        
    def _sync_sec_tickers(self):
        """Fetch SEC company tickers and update database."""
        try:
            logger.info(f"Fetching SEC ticker map from {self.SEC_TICKERS_URL}...")
            
            with httpx.Client(headers={"User-Agent": self._user_agent}, timeout=30.0) as client:
                resp = client.get(self.SEC_TICKERS_URL)
                resp.raise_for_status()
                data = resp.json()
            
            logger.info(f"Received {len(data)} entries from SEC. Updating database...")
            
            count = 0
            for entry in data.values():
                ticker = entry.get('ticker', '').upper()
                cik = str(entry.get('cik_str', '')).zfill(10)
                company_name = entry.get('title', '')
                
                if not ticker or not cik:
                    continue
                    
                # Create entity definition with asset_type and identifiers
                entity = Entity(
                    entity_type=EntityType.TICKER,
                    ticker=ticker,
                    cik=cik,
                    name=company_name,
                    aliases=[company_name],
                    asset_type=AssetType.EQUITY,  # SEC tickers are always equities
                    identifiers={"ticker": ticker, "cik": cik},
                )
                
                # Insert/Update in DB
                # Note: We use ticker as a unique key for lookup, but DB ID will be mostly stable 
                # if we lookup before insert?
                # For Phase 2, we rely on DB UPSERT based on ID. 
                # But wait, we don't have a stable ID from SEC.
                # We should check if it exists first to keep ID stable.
                
                existing = self.db.get_entity_by_ticker(ticker)
                if existing:
                    entity.id = existing.id
                    # Merge aliases
                    if company_name not in existing.aliases:
                        entity.aliases = existing.aliases + [company_name]
                    else:
                        entity.aliases = existing.aliases
                
                self.db.insert_entity(entity)
                
                # Update cache
                self._update_cache(entity)
                count += 1
                
                if count % 1000 == 0:
                    logger.debug(f"Processed {count} entities...")
            
            logger.info(f"Successfully synced {count} entities from SEC.")
            
        except Exception as e:
            logger.error(f"Failed to sync SEC tickers: {e}")

    def _update_cache(self, entity: Entity):
        """Update in-memory caches."""
        if entity.ticker:
            self._ticker_cache[entity.ticker] = entity
        if entity.cik:
            self._cik_cache[entity.cik] = entity
        if entity.name:
            self._name_cache[entity.name.lower()] = entity
            
    def resolve_ticker(
        self,
        ticker: str,
        asset_type: Optional[AssetType] = None,
    ) -> Optional[Entity]:
        """
        Resolve a ticker symbol to an Entity.

        Args:
            ticker: Ticker symbol to resolve
            asset_type: Optional filter by asset type for disambiguation

        Returns:
            Entity if found, None otherwise
        """
        ticker = ticker.upper()

        # 1. Check memory cache (with asset type if provided)
        cache_key = f"{ticker}:{asset_type.value}" if asset_type else ticker
        if cache_key in self._ticker_cache:
            return self._ticker_cache[cache_key]

        # Also check without asset type as fallback
        if ticker in self._ticker_cache:
            cached = self._ticker_cache[ticker]
            if asset_type is None or cached.asset_type == asset_type:
                return cached

        # 2. Check database
        entity = self.db.get_entity_by_ticker(ticker)
        if entity:
            # Filter by asset type if specified
            if asset_type is not None and entity.asset_type != asset_type:
                return None
            self._update_cache(entity)
            return entity

        # 3. If not found, return None
        return None

    def resolve_cik(self, cik: str) -> Optional[Entity]:
        """Resolve a CIK to an Entity."""
        cik = str(cik).zfill(10)
        
        if cik in self._cik_cache:
            return self._cik_cache[cik]
            
        entity = self.db.get_entity_by_cik(cik)
        if entity:
            self._update_cache(entity)
            return entity
            
        return None

    def extract_entities_from_text(self, text: str) -> List[Entity]:
        """
        Extract entities from unstructured text.
        
        Strategies:
        1. Cashtag regex ($AAPL)
        2. Ticker regex (AAPL) - careful with common words
        3. Company name fuzzy match (exact match for now)
        """
        found_entities: Dict[str, Entity] = {}
        
        # 1. Cashtags (High confidence)
        cashtags = re.findall(r'\$([A-Z]{1,6})', text)
        for ticker in cashtags:
            entity = self.resolve_ticker(ticker)
            if entity:
                found_entities[str(entity.id)] = entity
                
        # 2. Known company names (Mid confidence)
        # This is expensive if we check all names. 
        # For MVP, we skip this or only check a watchlist if provided.
        # Let's keep it simple for Phase 2: Cashtags only + Explicit Tickers in structure
        
        return list(found_entities.values())

    def get_or_create_entity(
        self,
        ticker: str,
        name: Optional[str] = None,
        asset_type: Optional[AssetType] = None,
        identifiers: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Entity:
        """
        Get existing entity or update/create one.

        Useful for when we encounter a ticker from a source that isn't in SEC list
        (e.g., Crypto, International).

        Args:
            ticker: Ticker symbol
            name: Human-readable name
            asset_type: Asset type (auto-detected if not provided)
            identifiers: Asset-specific identifiers
            metadata: Asset-specific metadata

        Returns:
            Existing or newly created Entity
        """
        ticker = ticker.upper()

        # Auto-detect asset type if not provided
        if asset_type is None:
            asset_type = self._detect_asset_type(ticker)

        # Try to resolve existing entity with the same asset type
        entity = self.resolve_ticker(ticker, asset_type=asset_type)

        if entity:
            return entity

        # Create new entity
        new_entity = Entity(
            entity_type=EntityType.TICKER,
            ticker=ticker,
            name=name,
            aliases=[name] if name else [],
            asset_type=asset_type,
            identifiers=identifiers or {"ticker": ticker},
            metadata=metadata or {},
        )
        self.db.insert_entity(new_entity)
        self._update_cache(new_entity)
        return new_entity

    def _detect_asset_type(self, symbol: str) -> AssetType:
        """
        Detect the most likely asset type for a symbol.

        This uses heuristics based on known crypto symbols, equity symbols,
        and symbol patterns.

        Args:
            symbol: The symbol to classify

        Returns:
            Detected AssetType
        """
        symbol = symbol.upper()

        # Check for crypto pair format (e.g., BTC/USDT, ETH-USD)
        if self._looks_like_crypto(symbol):
            return AssetType.CRYPTO

        # Check for Polymarket format (usually longer IDs or specific patterns)
        if self._looks_like_polymarket(symbol):
            return AssetType.POLYMARKET

        # Check known equity symbols first (override crypto)
        if symbol in KNOWN_EQUITY_SYMBOLS:
            return AssetType.EQUITY

        # Check known crypto symbols
        if symbol in KNOWN_CRYPTO_SYMBOLS:
            return AssetType.CRYPTO

        # Default to equity for unknown symbols
        return AssetType.EQUITY

    def _looks_like_crypto(self, symbol: str) -> bool:
        """
        Check if a symbol looks like a crypto trading pair or crypto asset.

        Args:
            symbol: Symbol to check

        Returns:
            True if it looks like crypto
        """
        symbol = symbol.upper()

        # Check for trading pair format: BTC/USDT, ETH-USD, BTCUSDT
        if "/" in symbol or "-" in symbol:
            parts = re.split(r"[/-]", symbol)
            if len(parts) == 2:
                base, quote = parts
                if quote in CRYPTO_PAIR_SUFFIXES:
                    return True
                if base in KNOWN_CRYPTO_SYMBOLS:
                    return True

        # Check for concatenated pair format: BTCUSDT
        for suffix in CRYPTO_PAIR_SUFFIXES:
            if symbol.endswith(suffix) and len(symbol) > len(suffix):
                base = symbol[:-len(suffix)]
                if base in KNOWN_CRYPTO_SYMBOLS:
                    return True

        # Check if it's a known crypto symbol
        if symbol in KNOWN_CRYPTO_SYMBOLS:
            return True

        return False

    def _looks_like_polymarket(self, symbol: str) -> bool:
        """
        Check if an identifier looks like a Polymarket market.

        Polymarket markets typically have:
        - Long alphanumeric IDs (32+ chars)
        - Specific question formats

        Args:
            symbol: Symbol or ID to check

        Returns:
            True if it looks like a Polymarket market
        """
        # Polymarket IDs are typically long hex strings or URLs
        if len(symbol) >= 32 and re.match(r"^[a-f0-9-]+$", symbol.lower()):
            return True

        # Check for question-like format often used in Polymarket
        if "?" in symbol or symbol.startswith("Will "):
            return True

        return False

    def resolve_symbol_with_context(
        self,
        symbol: str,
        source_type: Optional[str] = None,
        hint_asset_type: Optional[AssetType] = None,
    ) -> Tuple[Optional[Entity], AssetType]:
        """
        Resolve a symbol to an entity with context-aware disambiguation.

        This handles identifier conflicts by using source context.

        Args:
            symbol: Symbol to resolve
            source_type: Source that provided the symbol (e.g., 'crypto', 'equities')
            hint_asset_type: Optional hint about expected asset type

        Returns:
            Tuple of (Entity or None, detected AssetType)
        """
        symbol = symbol.upper()

        # Determine asset type based on context
        if hint_asset_type:
            asset_type = hint_asset_type
        elif source_type:
            asset_type = self._asset_type_from_source(source_type)
        else:
            asset_type = self._detect_asset_type(symbol)

        # Try to resolve with the determined asset type
        entity = self.resolve_ticker(symbol, asset_type=asset_type)

        return entity, asset_type

    def _asset_type_from_source(self, source_type: str) -> AssetType:
        """
        Map source type to asset type.

        Args:
            source_type: Data source type string

        Returns:
            Corresponding AssetType
        """
        source_mapping = {
            "equities": AssetType.EQUITY,
            "equity": AssetType.EQUITY,
            "crypto": AssetType.CRYPTO,
            "polymarket": AssetType.POLYMARKET,
            "sec": AssetType.EQUITY,
            "congress": AssetType.EQUITY,
            "hedgefund": AssetType.EQUITY,
            "news": AssetType.EQUITY,  # Default for news
        }
        return source_mapping.get(source_type.lower(), AssetType.EQUITY)

    def is_ambiguous_symbol(self, symbol: str) -> bool:
        """
        Check if a symbol is known to be ambiguous (could be multiple asset types).

        Args:
            symbol: Symbol to check

        Returns:
            True if the symbol is in the ambiguous list
        """
        return symbol.upper() in AMBIGUOUS_SYMBOLS

    def resolve_all_asset_types(self, symbol: str) -> List[Entity]:
        """
        Resolve a symbol to all possible entities across asset types.

        Useful for ambiguous symbols that could match multiple assets.

        Args:
            symbol: Symbol to resolve

        Returns:
            List of all matching entities
        """
        symbol = symbol.upper()
        entities: List[Entity] = []

        # Check cache first
        if symbol in self._ticker_cache:
            entities.append(self._ticker_cache[symbol])

        # Check database for all asset types
        for asset_type in AssetType:
            entity = self.db.get_entity_by_ticker(symbol)
            if entity and entity.asset_type == asset_type:
                if entity not in entities:
                    entities.append(entity)

        return entities

    def get_or_create_crypto_entity(
        self,
        symbol: str,
        name: Optional[str] = None,
        coingecko_id: Optional[str] = None,
        rank: Optional[int] = None,
        category: Optional[str] = None,
    ) -> Entity:
        """
        Get or create a crypto-specific entity.

        Args:
            symbol: Crypto symbol (e.g., BTC, ETH)
            name: Full name (e.g., Bitcoin, Ethereum)
            coingecko_id: CoinGecko identifier
            rank: Market cap rank
            category: Category (e.g., "layer-1", "defi")

        Returns:
            Entity with crypto-specific metadata
        """
        identifiers: Dict[str, str] = {"ticker": symbol.upper()}
        if coingecko_id:
            identifiers["coingecko_id"] = coingecko_id

        metadata: Dict[str, str] = {}
        if rank:
            metadata["rank"] = str(rank)
        if category:
            metadata["category"] = category

        return self.get_or_create_entity(
            ticker=symbol,
            name=name,
            asset_type=AssetType.CRYPTO,
            identifiers=identifiers,
            metadata=metadata,
        )

    def get_or_create_polymarket_entity(
        self,
        market_id: str,
        question: str,
        category: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Entity:
        """
        Get or create a Polymarket-specific entity.

        Args:
            market_id: Polymarket market ID
            question: Market question
            category: Market category
            end_date: When the market resolves

        Returns:
            Entity with polymarket-specific metadata
        """
        # Use first few words of question as ticker for display
        ticker = self._generate_polymarket_ticker(question, market_id)

        identifiers = {"market_id": market_id, "ticker": ticker}

        metadata: Dict[str, str] = {"question": question}
        if category:
            metadata["category"] = category
        if end_date:
            metadata["end_date"] = end_date

        # Check if exists by market_id first
        existing = self.db.get_entity_by_identifier("market_id", market_id)
        if existing:
            return existing

        return self.get_or_create_entity(
            ticker=ticker,
            name=question,
            asset_type=AssetType.POLYMARKET,
            identifiers=identifiers,
            metadata=metadata,
        )

    def _generate_polymarket_ticker(self, question: str, market_id: str) -> str:
        """
        Generate a short ticker-like identifier for a Polymarket question.

        Args:
            question: Market question
            market_id: Fallback to use part of market ID

        Returns:
            Short identifier string
        """
        # Take first 3 words, uppercase, join with underscore
        words = re.sub(r"[^a-zA-Z0-9\s]", "", question).split()[:3]
        if words:
            ticker = "_".join(w.upper() for w in words)
            # Limit to 20 chars
            return ticker[:20]

        # Fallback to first 8 chars of market_id
        return market_id[:8].upper()
