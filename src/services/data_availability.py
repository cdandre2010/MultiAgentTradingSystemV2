"""
Data availability and integrity checking service.

This module provides services for checking data availability, identifying
missing data segments, and verifying data integrity.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple

from ..database.influxdb import InfluxDBClient
from ..models.market_data import DataAvailability, AdjustmentInfo, MarketDataRequest
from ..models.strategy import DataConfig, BacktestDataRange, DataSourceType

logger = logging.getLogger(__name__)


class DataAvailabilityService:
    """
    Service for checking data availability and integrity.
    
    This service provides methods for checking data availability, identifying
    missing data segments, and verifying data integrity.
    """
    
    def __init__(self, influxdb_client: InfluxDBClient):
        """
        Initialize the service.
        
        Args:
            influxdb_client: The InfluxDB client
        """
        self.influxdb = influxdb_client
    
    async def check_data_requirements(self, data_config: DataConfig) -> Dict[str, Any]:
        """
        Check if data is available for a strategy's data requirements.
        
        Args:
            data_config: The data configuration from the strategy
            
        Returns:
            Dict containing availability information for each required data source
        """
        results = {}
        
        if not data_config.backtest_range:
            logger.warning("Cannot check data requirements: backtest_range is not defined")
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
        
        # Check availability for each source
        for source in data_config.sources:
            source_type = source.type if isinstance(source.type, str) else source.type.value
            source_key = f"{source_type}_priority_{source.priority}"
            
            availability = self.influxdb.check_data_availability(
                instrument=data_config.instrument,
                timeframe=data_config.frequency,
                start_date=start_date,
                end_date=end_date,
                version="latest"
            )
            
            results[source_key] = availability
        
        # Add overall availability assessment
        results["overall"] = {
            "is_complete": any(src["is_complete"] for src in results.values() if isinstance(src, dict)),
            "highest_availability": max(
                (src.get("availability_pct", 0) for src in results.values() if isinstance(src, dict)),
                default=0
            ),
            "required_start_date": start_date,
            "required_end_date": end_date
        }
        
        return results
    
    async def get_missing_segments(self, request: MarketDataRequest) -> List[Dict[str, Any]]:
        """
        Identify missing data segments in a date range.
        
        Args:
            request: The market data request
            
        Returns:
            List of missing data segments with start and end dates
        """
        # Get the data to analyze gaps
        data = self.influxdb.query_ohlcv(
            instrument=request.instrument,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date,
            version=request.version
        )
        
        if not data:
            # If no data at all, return the entire range as missing
            return [{
                "start_date": request.start_date,
                "end_date": request.end_date,
                "expected_points": self._calculate_expected_points(
                    request.start_date, request.end_date, request.timeframe
                )
            }]
        
        # Convert data to sorted timestamp list
        timestamps = sorted([point["timestamp"] for point in data])
        
        # Calculate the expected interval based on timeframe
        interval_minutes = self._get_timeframe_duration_minutes(request.timeframe)
        interval = timedelta(minutes=interval_minutes)
        
        # Find gaps in the data
        missing_segments = []
        expected_time = timestamps[0]
        
        for current_time in timestamps[1:]:
            expected_time += interval
            
            # If there's a gap (allowing for small timestamp variations)
            if (current_time - expected_time) > (interval * 1.5):
                # Found a gap
                gap_start = expected_time
                gap_end = current_time - interval
                
                missing_segments.append({
                    "start_date": gap_start,
                    "end_date": gap_end,
                    "expected_points": self._calculate_expected_points(
                        gap_start, gap_end, request.timeframe
                    )
                })
                
                # Reset expected time to current time for next iteration
                expected_time = current_time
        
        # Check if there's a gap at the beginning
        start_date = request.start_date
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
            
        if (timestamps[0] - start_date) > (interval * 1.5):
            missing_segments.insert(0, {
                "start_date": start_date,
                "end_date": timestamps[0] - interval,
                "expected_points": self._calculate_expected_points(
                    start_date, timestamps[0] - interval, request.timeframe
                )
            })
        
        # Check if there's a gap at the end
        end_date = request.end_date
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
            
        if (end_date - timestamps[-1]) > (interval * 1.5):
            missing_segments.append({
                "start_date": timestamps[-1] + interval,
                "end_date": end_date,
                "expected_points": self._calculate_expected_points(
                    timestamps[-1] + interval, end_date, request.timeframe
                )
            })
        
        return missing_segments
    
    async def check_adjustments(self, instrument: str, timeframe: str, 
                             reference_date: Optional[Union[datetime, str]] = None) -> AdjustmentInfo:
        """
        Check for data adjustments since a reference date.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            reference_date: The reference date (default: 30 days ago)
            
        Returns:
            AdjustmentInfo object with adjustment information
        """
        result = self.influxdb.check_for_adjustments(
            instrument=instrument,
            timeframe=timeframe,
            reference_date=reference_date
        )
        
        return AdjustmentInfo(
            instrument=instrument,
            timeframe=timeframe,
            **result
        )
    
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
    
    def _get_timeframe_duration_minutes(self, timeframe: str) -> int:
        """
        Convert a timeframe string to minutes.
        
        Args:
            timeframe: The timeframe string (e.g., "1m", "1h", "1d")
            
        Returns:
            int: The duration in minutes
        """
        # Handle common timeframe formats
        if timeframe.endswith('m'):
            return int(timeframe[:-1])
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 60 * 24
        elif timeframe.endswith('w'):
            return int(timeframe[:-1]) * 60 * 24 * 7
        else:
            # Default to 1 minute if unknown format
            logger.warning(f"Unknown timeframe format: {timeframe}, defaulting to 1 minute")
            return 1
    
    def _calculate_expected_points(self, 
                                start_date: Union[datetime, str], 
                                end_date: Union[datetime, str], 
                                timeframe: str) -> int:
        """
        Calculate the expected number of data points for a time range.
        
        Args:
            start_date: The start date
            end_date: The end date
            timeframe: The timeframe string
            
        Returns:
            int: The expected number of data points
        """
        # Convert string dates to datetime for calculation
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
            
        # Get the timeframe duration in minutes
        timeframe_minutes = self._get_timeframe_duration_minutes(timeframe)
        
        # Calculate the total minutes in the range
        delta = end_date - start_date
        total_minutes = delta.total_seconds() / 60
        
        # Calculate expected points
        expected_points = int(total_minutes / timeframe_minutes) + 1
        
        return max(expected_points, 0)  # Ensure non-negative result