"""
Base class for all data source connectors.

This module provides the abstract base class for all data source connectors
to ensure a consistent interface for data retrieval.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

from ..models.market_data import OHLCV, OHLCVPoint, DataPointSource
from ..database.influxdb import InfluxDBClient

logger = logging.getLogger(__name__)


class DataSourceConnector(ABC):
    """
    Abstract base class for all data source connectors.

    This class defines the interface that all data source connectors must implement
    to provide a consistent way of retrieving market data.
    """

    def __init__(self, 
                 config: Dict[str, Any],
                 cache_to_influxdb: bool = True,
                 influxdb_client: Optional[InfluxDBClient] = None):
        """
        Initialize the data source connector.

        Args:
            config: Configuration parameters for the connector
            cache_to_influxdb: Whether to cache retrieved data to InfluxDB
            influxdb_client: InfluxDB client for caching data (required if cache_to_influxdb is True)
        """
        self.config = config
        self.cache_to_influxdb = cache_to_influxdb
        self.influxdb_client = influxdb_client
        
        # If caching is enabled, ensure influxdb_client is provided
        if self.cache_to_influxdb and self.influxdb_client is None:
            raise ValueError("InfluxDB client must be provided if cache_to_influxdb is True")
        
        # Initialize the connector
        self._initialize()
        
    def _initialize(self):
        """
        Initialize the connector with additional setup if needed.
        
        Override this method in derived classes for custom initialization logic.
        """
        pass
        
    @abstractmethod
    async def fetch_ohlcv(self, 
                        instrument: str,
                        timeframe: str,
                        start_date: Union[datetime, str],
                        end_date: Union[datetime, str]) -> OHLCV:
        """
        Fetch OHLCV data from the data source.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            start_date: The start date
            end_date: The end date
            
        Returns:
            OHLCV object with the retrieved data
        """
        pass
    
    @abstractmethod
    async def check_availability(self,
                              instrument: str,
                              timeframe: str) -> Dict[str, Any]:
        """
        Check if data is available for the specified instrument and timeframe.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            
        Returns:
            Dict containing availability information
        """
        pass
    
    @abstractmethod
    def get_supported_timeframes(self) -> List[str]:
        """
        Get the list of timeframes supported by this data source.
        
        Returns:
            List of supported timeframe strings
        """
        pass
    
    @abstractmethod
    def get_supported_instruments(self) -> List[str]:
        """
        Get the list of instruments supported by this data source.
        
        Returns:
            List of supported instrument symbols
        """
        pass
    
    def get_source_type(self) -> DataPointSource:
        """
        Get the source type enumeration value for this connector.
        
        Returns:
            DataPointSource enum value
        """
        # Override in derived classes to return the appropriate enum value
        return DataPointSource.CUSTOM
    
    async def _cache_to_influxdb(self, 
                               instrument: str, 
                               timeframe: str, 
                               data: List[Dict[str, Any]],
                               is_adjusted: bool = False) -> bool:
        """
        Cache the retrieved data to InfluxDB.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            data: List of OHLCV data points
            is_adjusted: Whether the data is adjusted for corporate actions
            
        Returns:
            bool: True if caching was successful, False otherwise
        """
        if not self.cache_to_influxdb or self.influxdb_client is None:
            return False
            
        try:
            source_type = self.get_source_type().value
            
            success = self.influxdb_client.write_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                data=data,
                source=source_type,
                version="latest",
                is_adjusted=is_adjusted
            )
            
            if success:
                logger.info(f"Cached {len(data)} data points for {instrument}/{timeframe} from {source_type}")
            else:
                logger.warning(f"Failed to cache data for {instrument}/{timeframe} from {source_type}")
                
            return success
        except Exception as e:
            logger.error(f"Error caching data to InfluxDB: {e}")
            return False