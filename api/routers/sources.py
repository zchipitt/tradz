"""
Sources router for data source endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict

from api.services.aggregator_service import aggregator_service

router = APIRouter()


@router.get("")
async def get_all_sources(
    refresh: bool = Query(False, description="Force refresh from data sources")
) -> Dict[str, Any]:
    """
    Get data from all sources.

    Returns combined data from equities, crypto, congress, hedge funds,
    polymarket, news, and SEC filings.
    """
    try:
        return aggregator_service.get_all_sources(force_refresh=refresh)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equities")
async def get_equities(
    refresh: bool = Query(False, description="Force refresh from data source")
) -> Dict[str, Any]:
    """
    Get equities data.

    Returns price and volume data for tracked equity tickers.
    """
    try:
        return aggregator_service.get_equities(force_refresh=refresh)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crypto")
async def get_crypto(
    refresh: bool = Query(False, description="Force refresh from data source")
) -> Dict[str, Any]:
    """
    Get cryptocurrency data.

    Returns price and volume data for tracked crypto pairs.
    """
    try:
        return aggregator_service.get_crypto(force_refresh=refresh)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/congress")
async def get_congress(
    refresh: bool = Query(False, description="Force refresh from data source")
) -> Dict[str, Any]:
    """
    Get congress trading data.

    Returns recent trades by House and Senate members,
    including watchlist overlaps.
    """
    try:
        data = aggregator_service.get_congress(force_refresh=refresh)
        if "error" in data and data["error"].startswith("Congress data source is disabled"):
            raise HTTPException(status_code=503, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hedgefunds")
async def get_hedgefunds(
    refresh: bool = Query(False, description="Force refresh from data source")
) -> Dict[str, Any]:
    """
    Get hedge fund 13F filing data.

    Returns recent 13F filings from notable hedge funds.
    """
    try:
        data = aggregator_service.get_hedgefunds(force_refresh=refresh)
        if "error" in data and data["error"].startswith("Hedge fund data source is disabled"):
            raise HTTPException(status_code=503, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/polymarket")
async def get_polymarket(
    refresh: bool = Query(False, description="Force refresh from data source")
) -> Dict[str, Any]:
    """
    Get Polymarket prediction market data.

    Returns market predictions for economics, crypto, business, and politics.
    """
    try:
        data = aggregator_service.get_polymarket(force_refresh=refresh)
        if "error" in data and data["error"].startswith("Polymarket data source is disabled"):
            raise HTTPException(status_code=503, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news")
async def get_news(
    refresh: bool = Query(False, description="Force refresh from data source")
) -> Dict[str, Any]:
    """
    Get news data.

    Returns news articles grouped by ticker and market headlines.
    """
    try:
        data = aggregator_service.get_news(force_refresh=refresh)
        if "error" in data and data["error"].startswith("News data source is disabled"):
            raise HTTPException(status_code=503, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sec")
async def get_sec_filings(
    refresh: bool = Query(False, description="Force refresh from data source")
) -> Dict[str, Any]:
    """
    Get SEC filings data.

    Returns recent 10-K, 10-Q, and 8-K filings for watchlist tickers.
    """
    try:
        data = aggregator_service.get_sec_filings(force_refresh=refresh)
        if "error" in data and data["error"].startswith("SEC filings data source is disabled"):
            raise HTTPException(status_code=503, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
