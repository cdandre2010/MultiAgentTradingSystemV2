"""
Data retrieval service for accessing market data with version awareness.

This module provides services for retrieving market data from InfluxDB
with version awareness, intelligent source selection, and fallback mechanisms.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple
import asyncio

from ..database.influxdb import InfluxDBClient
from ..models.market_data import OHLCV, OHLCVPoint, MarketDataRequest, DataPointSource
from ..models.strategy import DataConfig, BacktestDataRange, DataSourceType
from .indicators import IndicatorService

logger = logging.getLogger(__name__)


class DataRetrievalService:
    """
    Service for retrieving market data from InfluxDB with version awareness.
    
    This service provides methods for retrieving market data from InfluxDB
    with version awareness, intelligent source selection, and fallback mechanisms.
    """
    
    def __init__(self, 
                influxdb_client: InfluxDBClient, 
                indicator_service: IndicatorService):
        """
        Initialize the service.
        
        Args:
            influxdb_client: The InfluxDB client
            indicator_service: The indicator calculation service
        """
        self.influxdb = influxdb_client
        self.indicators = indicator_service
    
    async def get_data_for_strategy(self, 
                                  data_config: DataConfig, 
                                  version: str = "latest") -> Dict[str, Any]:
        """
        Get all required data for a strategy.
        
        Args:
            data_config: The data configuration from the strategy
            version: The version tag (default: "latest")
            
        Returns:
            Dict containing the retrieved data with metadata
        """
        if not data_config.backtest_range:
            logger.warning("Cannot retrieve data: backtest_range is not defined")
            return {"error": "Backtest range not defined in data configuration"}
        
        # Extract dates from backtest range
        start_date = data_config.backtest_range.start_date
        end_date = data_config.backtest_range.end_date
        
        # If lookback period is specified, adjust start date
        if data_config.backtest_range.lookback_period:
            adjusted_start = self._adjust_for_lookback(
                start_date, data_config.backtest_range.lookback_period
            )
            if adjusted_start:
                start_date = adjusted_start
        
        # Retrieve data using priority-based source selection
        ohlcv_data = await self.get_ohlcv(
            data_sources=data_config.sources,
            instrument=data_config.instrument,
            timeframe=data_config.frequency,
            start_date=start_date,
            end_date=end_date,
            version=version
        )
        
        if not ohlcv_data or not ohlcv_data.data:
            logger.warning(f"No data found for {data_config.instrument}/{data_config.frequency}")
            return {"error": "No data found for the specified parameters"}
        
        # Apply preprocessing if specified
        if data_config.preprocessing:
            ohlcv_data = self._apply_preprocessing(ohlcv_data, data_config.preprocessing)
        
        # Create metadata
        metadata = {
            "instrument": data_config.instrument,
            "timeframe": data_config.frequency,
            "start_date": ohlcv_data.start_date.isoformat() if ohlcv_data.start_date else None,
            "end_date": ohlcv_data.end_date.isoformat() if ohlcv_data.end_date else None,
            "data_points": ohlcv_data.count,
            "source": ohlcv_data.source,
            "version": ohlcv_data.version,
            "is_adjusted": ohlcv_data.is_adjusted,
            "lookback_applied": data_config.backtest_range.lookback_period is not None,
            "preprocessing_applied": data_config.preprocessing is not None
        }
        
        return {
            "data": ohlcv_data,
            "metadata": metadata
        }
    
    async def get_ohlcv(self, 
                      data_sources: List, 
                      instrument: str, 
                      timeframe: str, 
                      start_date: Union[datetime, str], 
                      end_date: Union[datetime, str], 
                      version: str = "latest") -> Optional[OHLCV]:
        """
        Get OHLCV data using priority-based source selection.
        
        Args:
            data_sources: List of data sources with priorities
            instrument: The instrument symbol
            timeframe: The timeframe
            start_date: The start date
            end_date: The end date
            version: The version tag (default: "latest")
            
        Returns:
            OHLCV object with the retrieved data, or None if not found
        """
        # Sort sources by priority (lower number = higher priority)
        sorted_sources = sorted(data_sources, key=lambda s: s.priority)
        
        # Try each source in priority order
        for source in sorted_sources:
            source_type = source.type if isinstance(source.type, str) else source.type.value
            
            # For InfluxDB source, query directly
            if source_type.lower() == DataSourceType.INFLUXDB.value.lower():
                data = self.influxdb.query_ohlcv(
                    instrument=instrument,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date,
                    version=version
                )
                
                if data:
                    logger.info(f"Retrieved {len(data)} data points from InfluxDB for {instrument}/{timeframe}")
                    return OHLCV(
                        instrument=instrument,
                        timeframe=timeframe,
                        source=source_type,
                        version=version,
                        is_adjusted=any("adjustment_factor" in point for point in data),
                        data=[
                            OHLCVPoint(**point) for point in data
                        ]
                    )
            
            # For external data sources, use the appropriate connector
            elif source_type.lower() == DataSourceType.BINANCE.value.lower():
                return await self._get_from_connector("binance", source, instrument, timeframe, start_date, end_date)
            
            elif source_type.lower() == DataSourceType.YAHOO.value.lower():
                return await self._get_from_connector("yfinance", source, instrument, timeframe, start_date, end_date)
                
            elif source_type.lower() == DataSourceType.ALPHA_VANTAGE.value.lower():
                return await self._get_from_connector("alpha_vantage", source, instrument, timeframe, start_date, end_date)
                
            elif source_type.lower() == DataSourceType.CSV.value.lower():
                return await self._get_from_connector("csv", source, instrument, timeframe, start_date, end_date)
                
        # If we get here, data was not found in any source
        logger.warning(f"No data found for {instrument}/{timeframe} in any configured source")
        return None
        
    async def _get_from_connector(self,
                               connector_type: str,
                               source: Any,
                               instrument: str,
                               timeframe: str,
                               start_date: Union[datetime, str],
                               end_date: Union[datetime, str]) -> Optional[OHLCV]:
        """
        Get data from a specific data source connector.
        
        Args:
            connector_type: Type of connector to use ("binance", "yfinance", etc.)
            source: The data source configuration
            instrument: The instrument symbol
            timeframe: The timeframe
            start_date: The start date
            end_date: The end date
            
        Returns:
            OHLCV data or None if retrieval failed
        """
        try:
            # Import the appropriate connector class
            connector_class = None
            if connector_type == "binance":
                from ..data_sources.binance import BinanceConnector
                connector_class = BinanceConnector
            elif connector_type == "yfinance":
                from ..data_sources.yfinance import YFinanceConnector
                connector_class = YFinanceConnector
            elif connector_type == "alpha_vantage":
                from ..data_sources.alpha_vantage import AlphaVantageConnector
                connector_class = AlphaVantageConnector
            elif connector_type == "csv":
                from ..data_sources.csv import CSVConnector
                connector_class = CSVConnector
            else:
                logger.error(f"Unknown connector type: {connector_type}")
                return None
            
            # Extract configuration from source's custom_parameters if available
            config = {}
            if hasattr(source, 'custom_parameters') and source.custom_parameters:
                config = source.custom_parameters
                
            # For Alpha Vantage, try to get API key from reference
            if connector_type == "alpha_vantage" and not config.get('api_key') and hasattr(source, 'api_key_reference'):
                from ..app.config import settings
                api_key_ref = source.api_key_reference
                if hasattr(settings, api_key_ref):
                    config['api_key'] = getattr(settings, api_key_ref)
            
            # Create connector instance
            connector = connector_class(
                config=config,
                cache_to_influxdb=True,
                influxdb_client=self.influxdb
            )
            
            # Fetch data
            data = await connector.fetch_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info(f"Retrieved {len(data.data) if data and data.data else 0} data points from {connector_type} for {instrument}/{timeframe}")
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving data from {connector_type}: {e}")
            return None
    
    def get_data_with_indicators(self, 
                               ohlcv_data: OHLCV, 
                               indicators_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get OHLCV data and calculate required indicators.
        
        Args:
            ohlcv_data: The OHLCV data
            indicators_config: List of indicator configurations
            
        Returns:
            Dict containing the data and calculated indicators
        """
        if not ohlcv_data or not ohlcv_data.data:
            logger.warning("Cannot calculate indicators: no data provided")
            return {"error": "No data provided for indicator calculation"}
        
        # Calculate indicators
        indicators = self.indicators.calculate_multiple_indicators(
            ohlcv_data=ohlcv_data,
            indicators_config=indicators_config
        )
        
        return {
            "data": ohlcv_data,
            "indicators": indicators
        }
    
    async def create_backtest_snapshot(self, 
                                    data_config: DataConfig, 
                                    snapshot_id: Optional[str] = None,
                                    strategy_id: Optional[str] = None) -> str:
        """
        Create a data snapshot for backtest audit purposes.
        
        Args:
            data_config: The data configuration
            snapshot_id: Optional snapshot ID (generated if None)
            strategy_id: Optional strategy ID for tracking
            
        Returns:
            The snapshot ID
        """
        if not data_config.backtest_range:
            logger.warning("Cannot create snapshot: backtest_range is not defined")
            return ""
        
        # Create snapshot
        snapshot_id = self.influxdb.create_snapshot(
            instrument=data_config.instrument,
            timeframe=data_config.frequency,
            start_date=data_config.backtest_range.start_date,
            end_date=data_config.backtest_range.end_date,
            snapshot_id=snapshot_id,
            strategy_id=strategy_id,
            purpose="backtest"
        )
        
        if not snapshot_id:
            logger.error(f"Failed to create snapshot for {data_config.instrument}/{data_config.frequency}")
            return ""
        
        logger.info(f"Created snapshot {snapshot_id} for {data_config.instrument}/{data_config.frequency}")
        return snapshot_id
    
    def _adjust_for_lookback(self, start_date: Union[datetime, str], 
                          lookback_period: str) -> Optional[Union[datetime, str]]:
        """
        Adjust start date for lookback period.
        
        Args:
            start_date: The original start date
            lookback_period: The lookback period (e.g., "30D", "6M")
            
        Returns:
            Adjusted start date or None if invalid lookback format
        """
        # Convert string date to datetime for adjustment
        if isinstance(start_date, str):
            try:
                dt_start = datetime.fromisoformat(start_date)
            except ValueError:
                logger.error(f"Invalid start date format: {start_date}")
                return None
        else:
            dt_start = start_date
        
        # Parse the lookback period
        if lookback_period.endswith('D'):
            days = int(lookback_period[:-1])
            adjusted = dt_start - timedelta(days=days)
        elif lookback_period.endswith('W'):
            weeks = int(lookback_period[:-1])
            adjusted = dt_start - timedelta(weeks=weeks)
        elif lookback_period.endswith('M'):
            months = int(lookback_period[:-1])
            # Approximate months as 30 days
            adjusted = dt_start - timedelta(days=30 * months)
        elif lookback_period.endswith('Y'):
            years = int(lookback_period[:-1])
            # Approximate years as 365 days
            adjusted = dt_start - timedelta(days=365 * years)
        else:
            logger.warning(f"Invalid lookback period format: {lookback_period}")
            return None
        
        # Return in the same format as input
        if isinstance(start_date, str):
            return adjusted.isoformat()
        return adjusted
    
    def _apply_preprocessing(self, ohlcv_data: OHLCV, preprocessing_config) -> OHLCV:
        """
        Apply preprocessing to OHLCV data.
        
        Args:
            ohlcv_data: The OHLCV data
            preprocessing_config: The preprocessing configuration
            
        Returns:
            Preprocessed OHLCV data
        """
        # This is a placeholder for preprocessing implementation
        # We would implement various preprocessing techniques here
        logger.info(f"Preprocessing data for {ohlcv_data.instrument}/{ohlcv_data.timeframe}")
        
        # For now, just return the original data
        return ohlcv_data