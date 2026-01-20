"""
Entity Resolver module for aligning data across sources.

Responsibilities:
- Resolve tickers/CIKs/names to unique Entity IDs
- Maintain the 'entities' table in the database
- Extract entities from unstructured text (news, tweets)
"""
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import httpx

from .database import Database, get_database
from .models import Entity, EntityType

logger = logging.getLogger(__name__)


class EntityResolver:
    """
    Resolves data points to canonical Entities.
    
    Acts as the source of truth for Ticker <-> CIK <-> Company Name mappings.
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
        self._ticker_cache: Dict[str, Entity] = {}
        self._cik_cache: Dict[str, Entity] = {}
        self._name_cache: Dict[str, Entity] = {}
        
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
                    
                # Create entity definition
                entity = Entity(
                    entity_type=EntityType.TICKER,
                    ticker=ticker,
                    cik=cik,
                    name=company_name,
                    aliases=[company_name]
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
            
    def resolve_ticker(self, ticker: str) -> Optional[Entity]:
        """Resolve a ticker symbol to an Entity."""
        ticker = ticker.upper()
        
        # 1. Check memory cache
        if ticker in self._ticker_cache:
            return self._ticker_cache[ticker]
            
        # 2. Check database
        entity = self.db.get_entity_by_ticker(ticker)
        if entity:
            self._update_cache(entity)
            return entity
            
        # 3. If not found, create a temporary/placeholder entity? 
        # For now, return None to indicate unknown
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

    def get_or_create_entity(self, ticker: str, name: Optional[str] = None) -> Entity:
        """
        Get existing entity or update/create one.
        
        Useful for when we encounter a ticker from a source that isn't in SEC list
        (e.g., Crypto, International).
        """
        ticker = ticker.upper()
        entity = self.resolve_ticker(ticker)
        
        if entity:
            return entity
            
        # Create new
        new_entity = Entity(
            entity_type=EntityType.TICKER, # Could be CRYPTO if logic added
            ticker=ticker,
            name=name,
            aliases=[name] if name else []
        )
        self.db.insert_entity(new_entity)
        self._update_cache(new_entity)
        return new_entity
