"""
API routes for market data operations.

This module provides FastAPI routes for retrieving and managing market data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...database.connection import get_db_manager
from ...models.market_data import MarketDataRequest, OHLCV
from ...services.data_availability import DataAvailabilityService
from ...services.data_retrieval import DataRetrievalService
from ...services.data_versioning import DataVersioningService
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
    purpose: str = "manual",
    description: Optional[str] = None,
    user_id: str = "system",
    strategy_id: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    db=Depends(get_db_manager)
):
    """Create a data snapshot for audit and versioning purposes."""
    
    if db.influxdb_client is None:
        raise HTTPException(status_code=503, detail="InfluxDB client not available")
    
    # Create versioning service
    versioning_service = DataVersioningService(influxdb_client=db.influxdb_client)
    
    # Create a snapshot with enhanced metadata
    snapshot_id = await versioning_service.create_snapshot(
        instrument=instrument,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        strategy_id=strategy_id,
        purpose=purpose,
        description=description,
        tags=tags
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
        "purpose": purpose,
        "user_id": user_id,
        "strategy_id": strategy_id,
        "tags": tags
    }


@router.get("/versions")
async def get_data_versions(
    instrument: str,
    timeframe: str,
    include_snapshots: bool = True,
    include_latest: bool = True,
    include_metadata: bool = False,
    db=Depends(get_db_manager)
):
    """Get available data versions for an instrument/timeframe with optional metadata."""
    
    if db.influxdb_client is None:
        raise HTTPException(status_code=503, detail="InfluxDB client not available")
    
    # Create versioning service
    versioning_service = DataVersioningService(influxdb_client=db.influxdb_client)
    
    # Get versions with enhanced filtering and metadata
    versions = await versioning_service.list_versions(
        instrument=instrument,
        timeframe=timeframe,
        include_snapshots=include_snapshots,
        include_latest=include_latest,
        include_metadata=include_metadata
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


@router.get("/version/compare")
async def compare_versions(
    instrument: str,
    timeframe: str,
    version1: str,
    version2: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db=Depends(get_db_manager)
):
    """Compare two data versions and identify differences."""
    
    if db.influxdb_client is None:
        raise HTTPException(status_code=503, detail="InfluxDB client not available")
    
    # Create versioning service
    versioning_service = DataVersioningService(influxdb_client=db.influxdb_client)
    
    # Compare versions
    comparison = await versioning_service.compare_versions(
        instrument=instrument,
        timeframe=timeframe,
        version1=version1,
        version2=version2,
        start_date=start_date,
        end_date=end_date
    )
    
    return comparison


@router.get("/version/lineage/{version}")
async def get_version_lineage(
    version: str,
    instrument: str,
    timeframe: str,
    db=Depends(get_db_manager)
):
    """Get the lineage information for a data version."""
    
    if db.influxdb_client is None:
        raise HTTPException(status_code=503, detail="InfluxDB client not available")
    
    # Create versioning service
    versioning_service = DataVersioningService(influxdb_client=db.influxdb_client)
    
    # Get lineage
    lineage = await versioning_service.get_version_lineage(
        instrument=instrument,
        timeframe=timeframe,
        version=version
    )
    
    if "error" in lineage:
        raise HTTPException(
            status_code=404,
            detail=f"Failed to retrieve lineage: {lineage['error']}"
        )
    
    return lineage


@router.post("/version/tag")
async def tag_version(
    instrument: str,
    timeframe: str,
    version: str,
    tag_name: str,
    tag_value: str,
    user_id: str = "system",
    db=Depends(get_db_manager)
):
    """Add a tag to a data version for categorization."""
    
    if db.influxdb_client is None:
        raise HTTPException(status_code=503, detail="InfluxDB client not available")
    
    # Create versioning service
    versioning_service = DataVersioningService(influxdb_client=db.influxdb_client)
    
    # Tag version
    success = await versioning_service.tag_version(
        instrument=instrument,
        timeframe=timeframe,
        version=version,
        tag_name=tag_name,
        tag_value=tag_value,
        user_id=user_id
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Failed to tag version: Version {version} not found"
        )
    
    return {
        "instrument": instrument,
        "timeframe": timeframe,
        "version": version,
        "tag": {
            "name": tag_name,
            "value": tag_value
        },
        "user_id": user_id,
        "success": success
    }


@router.post("/version/retention")
async def apply_retention_policy(
    max_snapshot_age_days: int = 90,
    exempt_purposes: List[str] = Body(default=["approval", "compliance"]),
    exempt_tags: Optional[Dict[str, str]] = None,
    instrument: Optional[str] = None,
    timeframe: Optional[str] = None,
    dry_run: bool = True,
    db=Depends(get_db_manager)
):
    """Apply data retention policy to snapshots."""
    
    if db.influxdb_client is None:
        raise HTTPException(status_code=503, detail="InfluxDB client not available")
    
    # Create versioning service
    versioning_service = DataVersioningService(influxdb_client=db.influxdb_client)
    
    # Apply retention policy
    result = await versioning_service.apply_retention_policy(
        instrument=instrument,
        timeframe=timeframe,
        max_snapshot_age_days=max_snapshot_age_days,
        exempt_purposes=exempt_purposes,
        exempt_tags=exempt_tags,
        dry_run=dry_run
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply retention policy: {result['error']}"
        )
    
    return result