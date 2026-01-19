"""
Signals router for trading signal endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.schemas.signals import Signal, SignalsResponse, TopSignalsResponse
from api.services.signal_service import signal_service

router = APIRouter()


@router.get("", response_model=SignalsResponse)
async def get_signals(
    refresh: bool = Query(False, description="Force refresh from data sources")
) -> SignalsResponse:
    """
    Get all trading signals.

    Returns signals for all tracked assets, sorted by score.
    """
    try:
        data = signal_service.get_signals(force_refresh=refresh)
        return SignalsResponse(
            top_equities=[Signal(**s) for s in data["top_equities"]],
            top_crypto=[Signal(**s) for s in data["top_crypto"]],
            all_signals=[Signal(**s) for s in data["all_signals"]],
            generated_at=data["generated_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top", response_model=TopSignalsResponse)
async def get_top_signals(
    refresh: bool = Query(False, description="Force refresh from data sources")
) -> TopSignalsResponse:
    """
    Get top trading signals only.

    Returns top 5 equity and top 5 crypto signals.
    """
    try:
        data = signal_service.get_top_signals(force_refresh=refresh)
        return TopSignalsResponse(
            top_equities=[Signal(**s) for s in data["top_equities"]],
            top_crypto=[Signal(**s) for s in data["top_crypto"]],
            generated_at=data["generated_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}", response_model=Signal)
async def get_signal_by_symbol(
    symbol: str,
    refresh: bool = Query(False, description="Force refresh from data sources")
) -> Signal:
    """
    Get signal for a specific symbol.

    Args:
        symbol: Asset symbol (e.g., AAPL, BTC/USDT)
    """
    try:
        data = signal_service.get_signal_by_symbol(symbol, force_refresh=refresh)
        if data is None:
            raise HTTPException(status_code=404, detail=f"Signal for {symbol} not found")
        return Signal(**data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
