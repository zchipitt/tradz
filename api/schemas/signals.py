"""
Pydantic schemas for trading signals.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class AssetType(str, Enum):
    """Asset type enumeration."""
    EQUITY = "equity"
    CRYPTO = "crypto"


class SignalMetrics(BaseModel):
    """Metrics for a trading signal."""
    day_return: float = Field(..., description="1-day return in %")
    week_return: float = Field(..., description="7-day return in %")
    volatility_7d: float = Field(..., description="7-day annualized volatility in %")
    volatility_30d: float = Field(..., description="30-day annualized volatility in %")
    volatility_change: float = Field(..., description="Volatility change vs baseline in %")
    volume_ratio: float = Field(..., description="Current volume / 30-day avg volume")
    last_price: float = Field(..., description="Most recent price")


class Signal(BaseModel):
    """Trading signal for an asset."""
    symbol: str = Field(..., description="Asset symbol (e.g., AAPL, BTC/USDT)")
    score: int = Field(..., ge=0, le=100, description="Signal score (0-100)")
    asset_type: AssetType = Field(..., description="Type of asset")
    metrics: SignalMetrics = Field(..., description="Signal metrics")
    why: List[str] = Field(default_factory=list, description="Rationale for the signal")
    caveats: List[str] = Field(default_factory=list, description="Data quality caveats")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "NVDA",
                "score": 85,
                "asset_type": "equity",
                "metrics": {
                    "day_return": 5.2,
                    "week_return": 12.3,
                    "volatility_7d": 35.5,
                    "volatility_30d": 28.2,
                    "volatility_change": 25.9,
                    "volume_ratio": 2.1,
                    "last_price": 875.50
                },
                "why": [
                    "Strong 1-day move: up 5.2%",
                    "7-day momentum: gained 12.3%",
                    "High volume: 2.1x average"
                ],
                "caveats": [
                    "Data from free sources (yfinance/ccxt), may have delays or gaps"
                ]
            }
        }


class SignalsResponse(BaseModel):
    """Response containing all signals."""
    top_equities: List[Signal] = Field(..., description="Top 5 equity signals")
    top_crypto: List[Signal] = Field(..., description="Top 5 crypto signals")
    all_signals: List[Signal] = Field(..., description="All signals sorted by score")
    generated_at: str = Field(..., description="Timestamp when signals were generated")

    class Config:
        json_schema_extra = {
            "example": {
                "top_equities": [],
                "top_crypto": [],
                "all_signals": [],
                "generated_at": "2024-01-17T10:30:00"
            }
        }


class TopSignalsResponse(BaseModel):
    """Response containing only top signals."""
    top_equities: List[Signal] = Field(..., description="Top 5 equity signals")
    top_crypto: List[Signal] = Field(..., description="Top 5 crypto signals")
    generated_at: str = Field(..., description="Timestamp when signals were generated")
