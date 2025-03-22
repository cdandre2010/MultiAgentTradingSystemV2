"""
API routes for market data operations.

This module provides FastAPI routes for retrieving and managing market data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...database.connection import get_db_manager
from ...models.market_data import MarketDataRequest, OHLCV
from ...services.data_availability import DataAvailabilityService
from ...services.data_retrieval import DataRetrievalService
from ...services.indicators import IndicatorService
from ...database.influxdb import InfluxDBClient

router = APIRouter(
    prefix="/data",
    tags=["data"],
    responses={404: {"description": "Not found"}},
)


@router.get("/health")
async def check_data_health(db=Depends(get_db_manager)):
    """Check the health of the data services."""
    
    if db.influxdb_client is None:
        raise HTTPException(status_code=503, detail="InfluxDB client not available")
    
    health_status = db.influxdb_client.health_check()
    
    if not health_status:
        raise HTTPException(status_code=503, detail="InfluxDB health check failed")
    
    return {"status": "healthy", "message": "Data services are operational"}


@router.get("/availability")
async def check_data_availability(
    instrument: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    version: str = "latest",
    db=Depends(get_db_manager)
):
    """Check if data is available for the specified parameters."""
    
    if db.influxdb_client is None:
        raise HTTPException(status_code=503, detail="InfluxDB client not available")
    
    # Create availability service
    availability_service = DataAvailabilityService(influxdb_client=db.influxdb_client)
    
    # Create request
    request = MarketDataRequest(
        instrument=instrument,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        version=version
    )
    
    # Get missing segments
    missing_segments = await availability_service.get_missing_segments(request)
    
    # Check availability
    availability = db.influxdb_client.check_data_availability(
        instrument=instrument,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        version=version
    )
    
    return {
        "availability": availability,
        "missing_segments": missing_segments
    }


@router.post("/snapshot")
async def create_data_snapshot(
    instrument: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    strategy_id: Optional[str] = None,
    db=Depends(get_db_manager)
):
    """Create a data snapshot for backtesting audit purposes."""
    
    if db.influxdb_client is None:
        raise HTTPException(status_code=503, detail="InfluxDB client not available")
    
    # Create a snapshot
    snapshot_id = db.influxdb_client.create_snapshot(
        instrument=instrument,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        snapshot_id=None,
        strategy_id=strategy_id,
        purpose="manual"
    )
    
    if not snapshot_id:
        raise HTTPException(
            status_code=500, 
            detail="Failed to create snapshot"
        )
    
    return {
        "snapshot_id": snapshot_id,
        "instrument": instrument,
        "timeframe": timeframe,
        "start_date": start_date,
        "end_date": end_date,
        "strategy_id": strategy_id
    }


@router.get("/versions")
async def get_data_versions(
    instrument: str,
    timeframe: str,
    db=Depends(get_db_manager)
):
    """Get available data versions for an instrument/timeframe."""
    
    if db.influxdb_client is None:
        raise HTTPException(status_code=503, detail="InfluxDB client not available")
    
    versions = db.influxdb_client.get_data_versions(
        instrument=instrument,
        timeframe=timeframe
    )
    
    return {
        "instrument": instrument,
        "timeframe": timeframe,
        "versions": versions
    }


@router.post("/indicators")
async def calculate_indicators(
    ohlcv_data: OHLCV,
    indicators: List[Dict[str, Any]],
    db=Depends(get_db_manager)
):
    """Calculate indicators for OHLCV data."""
    
    # Create indicator service
    indicator_service = IndicatorService()
    
    # Calculate indicators
    result = indicator_service.calculate_multiple_indicators(
        ohlcv_data=ohlcv_data,
        indicators_config=indicators
    )
    
    return result