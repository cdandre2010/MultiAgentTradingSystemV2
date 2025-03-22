"""
Market data models for storing, retrieving, and managing financial market data.

This module provides Pydantic models for market data with support for OHLCV data,
metadata, and audit information.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, List, Optional, Union, Any, Set
from datetime import datetime
from enum import Enum


class DataPointSource(str, Enum):
    """Enumeration of possible data point sources."""
    INFLUXDB = "influxdb"
    BINANCE = "binance"
    YAHOO = "yahoo"
    ALPHA_VANTAGE = "alpha_vantage"
    CSV = "csv"
    CUSTOM = "custom"
    SNAPSHOT = "snapshot"


class OHLCVPoint(BaseModel):
    """
    Model for an individual OHLCV data point.
    
    This represents a single candlestick or price point with open, high, low, close, and volume values.
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    adjustment_factor: Optional[float] = None
    source_id: Optional[str] = None
    
    @field_validator('high')
    @classmethod
    def validate_high(cls, v, info):
        """Validate that high is not less than open, low, or close."""
        values = info.data
        if 'open' in values and v < values['open']:
            raise ValueError("High cannot be less than open")
        if 'low' in values and v < values['low']:
            raise ValueError("High cannot be less than low")
        if 'close' in values and v < values['close']:
            raise ValueError("High cannot be less than close")
        return v
    
    @field_validator('low')
    @classmethod
    def validate_low(cls, v, info):
        """Validate that low is not greater than open, high, or close."""
        values = info.data
        if 'open' in values and v > values['open']:
            raise ValueError("Low cannot be greater than open")
        if 'high' in values and v > values['high']:
            raise ValueError("Low cannot be greater than high")
        if 'close' in values and v > values['close']:
            raise ValueError("Low cannot be greater than close")
        return v
    
    @model_validator(mode='after')
    def validate_values(self):
        """Validate that all values are non-negative."""
        if self.open < 0:
            raise ValueError("Open cannot be negative")
        if self.high < 0:
            raise ValueError("High cannot be negative")
        if self.low < 0:
            raise ValueError("Low cannot be negative")
        if self.close < 0:
            raise ValueError("Close cannot be negative")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
        return self


class OHLCV(BaseModel):
    """
    Model for a collection of OHLCV data points with metadata.
    
    This represents a series of price data for a specific instrument and timeframe,
    along with metadata about the source and version.
    """
    instrument: str
    timeframe: str
    source: Union[str, DataPointSource]
    version: str = "latest"
    is_adjusted: bool = False
    data: List[OHLCVPoint]
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def start_date(self) -> Optional[datetime]:
        """Get the start date of the data series."""
        if not self.data:
            return None
        return min(point.timestamp for point in self.data)
    
    @property
    def end_date(self) -> Optional[datetime]:
        """Get the end date of the data series."""
        if not self.data:
            return None
        return max(point.timestamp for point in self.data)
    
    @property
    def count(self) -> int:
        """Get the number of data points."""
        return len(self.data)


class DataSnapshotMetadata(BaseModel):
    """
    Model for data snapshot metadata.
    
    This represents metadata about a data snapshot, including its purpose,
    source versions, and integrity information.
    """
    snapshot_id: str
    instrument: str
    timeframe: str
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = "system"
    strategy_id: Optional[str] = None
    purpose: str = "backtest"
    source_versions: Dict[str, Any]
    data_hash: str
    data_points: int
    start_date: Union[str, datetime]
    end_date: Union[str, datetime]


class DataAvailability(BaseModel):
    """
    Model for data availability information.
    
    This represents the availability of data for a specific instrument, timeframe,
    and date range, including completeness metrics.
    """
    instrument: str
    timeframe: str
    start_date: Union[str, datetime]
    end_date: Union[str, datetime]
    expected_points: int
    actual_points: int
    missing_points: int
    availability_pct: float
    is_complete: bool
    version: str = "latest"
    error: Optional[str] = None


class AdjustmentInfo(BaseModel):
    """
    Model for adjustment information.
    
    This represents information about price adjustments, such as those
    due to corporate actions like splits and dividends.
    """
    instrument: str
    timeframe: str
    has_adjustments: bool
    adjustment_count: int
    adjustment_details: List[Dict[str, Any]] = []
    error: Optional[str] = None


class MarketDataRequest(BaseModel):
    """
    Model for market data requests.
    
    This represents a request for market data, including the instrument,
    timeframe, date range, and version.
    """
    instrument: str
    timeframe: str
    start_date: Union[str, datetime]
    end_date: Union[str, datetime]
    version: str = "latest"
    include_metadata: bool = False
    
    @model_validator(mode='after')
    def validate_dates(self):
        """Validate that end_date is after start_date."""
        # Convert string dates to datetime for comparison
        start = self.start_date
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
            
        end = self.end_date
        if isinstance(end, str):
            end = datetime.fromisoformat(end)
            
        if end <= start:
            raise ValueError("End date must be after start date")
        
        return self