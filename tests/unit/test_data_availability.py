"""
Unit tests for DataAvailabilityService.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.services.data_availability import DataAvailabilityService
from src.models.market_data import DataAvailability, MarketDataRequest, AdjustmentInfo
from src.models.strategy import DataConfig, BacktestDataRange, DataSourceType, DataSource


@pytest.fixture
def mock_influxdb_client():
    """Create a mock InfluxDB client for testing."""
    client = MagicMock()
    
    # Mock check_data_availability
    client.check_data_availability.return_value = {
        "is_complete": True,
        "availability_pct": 100.0,
        "expected_points": 24,
        "actual_points": 24,
        "missing_points": 0
    }
    
    # Mock query_ohlcv
    mock_data = [
        {
            "timestamp": datetime(2023, 1, 1, 0, 0),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000
        },
        {
            "timestamp": datetime(2023, 1, 1, 1, 0),
            "open": 100.5,
            "high": 102.0,
            "low": 100.0,
            "close": 101.5,
            "volume": 1200
        }
    ]
    client.query_ohlcv.return_value = mock_data
    
    # Mock check_for_adjustments
    client.check_for_adjustments.return_value = {
        "has_adjustments": False,
        "adjustment_count": 0,
        "adjustment_details": []
    }
    
    return client


class TestDataAvailabilityService:
    """Tests for the DataAvailabilityService class."""
    
    def test_initialization(self, mock_influxdb_client):
        """Test service initialization."""
        service = DataAvailabilityService(mock_influxdb_client)
        assert service.influxdb == mock_influxdb_client
    
    @pytest.mark.asyncio
    async def test_check_data_requirements(self, mock_influxdb_client):
        """Test checking data requirements for a strategy."""
        service = DataAvailabilityService(mock_influxdb_client)
        
        # Create a data config
        data_config = DataConfig(
            instrument="BTCUSDT",
            frequency="1h",
            sources=[
                DataSource(type=DataSourceType.INFLUXDB, priority=1),
                DataSource(type=DataSourceType.BINANCE, priority=2)
            ],
            backtest_range=BacktestDataRange(
                start_date="2023-01-01",
                end_date="2023-01-02"
            )
        )
        
        # Test the check_data_requirements method
        result = await service.check_data_requirements(data_config)
        
        # Check that the result contains the expected keys
        assert "influxdb_priority_1" in result
        assert "binance_priority_2" in result
        assert "overall" in result
        
        # Check that the overall result contains the expected keys
        assert "is_complete" in result["overall"]
        assert "highest_availability" in result["overall"]
        assert "required_start_date" in result["overall"]
        assert "required_end_date" in result["overall"]
        
        # Check that the InfluxDB client was called with the correct parameters
        mock_influxdb_client.check_data_availability.assert_called_with(
            instrument="BTCUSDT",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-01-02",
            version="latest"
        )
    
    @pytest.mark.asyncio
    async def test_get_missing_segments(self, mock_influxdb_client):
        """Test identifying missing data segments."""
        service = DataAvailabilityService(mock_influxdb_client)
        
        # Create a request
        request = MarketDataRequest(
            instrument="BTCUSDT",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-01-02"
        )
        
        # Test the get_missing_segments method
        result = await service.get_missing_segments(request)
        
        # Since our mock returns two consecutive data points, there should be only
        # a gap between the end of the data and the requested end date
        assert len(result) == 1
        
        # Check that the gap has the expected structure
        gap = result[0]
        assert "start_date" in gap
        assert "end_date" in gap
        assert "expected_points" in gap
        
        # Check that the InfluxDB client was called with the correct parameters
        mock_influxdb_client.query_ohlcv.assert_called_with(
            instrument="BTCUSDT",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-01-02",
            version="latest"
        )
    
    @pytest.mark.asyncio
    async def test_get_missing_segments_no_data(self, mock_influxdb_client):
        """Test identifying missing segments when no data is available."""
        service = DataAvailabilityService(mock_influxdb_client)
        
        # Mock query_ohlcv to return empty data
        mock_influxdb_client.query_ohlcv.return_value = []
        
        # Create a request
        request = MarketDataRequest(
            instrument="BTCUSDT",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-01-02"
        )
        
        # Test the get_missing_segments method
        result = await service.get_missing_segments(request)
        
        # Since there's no data, there should be one gap for the entire range
        assert len(result) == 1
        gap = result[0]
        assert gap["start_date"] == "2023-01-01"
        assert gap["end_date"] == "2023-01-02"
    
    @pytest.mark.asyncio
    async def test_check_adjustments(self, mock_influxdb_client):
        """Test checking for data adjustments."""
        service = DataAvailabilityService(mock_influxdb_client)
        
        # Test the check_adjustments method
        result = await service.check_adjustments("BTCUSDT", "1h")
        
        # Check that the result has the expected structure
        assert isinstance(result, AdjustmentInfo)
        assert result.instrument == "BTCUSDT"
        assert result.timeframe == "1h"
        assert result.has_adjustments is False
        assert result.adjustment_count == 0
        
        # Check that the InfluxDB client was called with the correct parameters
        mock_influxdb_client.check_for_adjustments.assert_called_with(
            instrument="BTCUSDT",
            timeframe="1h",
            reference_date=None
        )
    
    def test_timeframe_duration(self, mock_influxdb_client):
        """Test conversion of timeframe strings to minutes."""
        service = DataAvailabilityService(mock_influxdb_client)
        
        # Test various timeframe formats
        assert service._get_timeframe_duration_minutes("1m") == 1
        assert service._get_timeframe_duration_minutes("5m") == 5
        assert service._get_timeframe_duration_minutes("1h") == 60
        assert service._get_timeframe_duration_minutes("4h") == 240
        assert service._get_timeframe_duration_minutes("1d") == 1440
        assert service._get_timeframe_duration_minutes("1w") == 10080
        
        # Test unknown format
        assert service._get_timeframe_duration_minutes("unknown") == 1  # Default to 1 minute
    
    def test_calculate_expected_points(self, mock_influxdb_client):
        """Test calculation of expected data points for a time range."""
        service = DataAvailabilityService(mock_influxdb_client)
        
        # Test with datetime objects
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 2)
        assert service._calculate_expected_points(start, end, "1h") == 25  # 24 hours + 1
        
        # Test with string dates
        assert service._calculate_expected_points("2023-01-01", "2023-01-02", "1h") == 25
        
        # Test with different timeframes
        assert service._calculate_expected_points(start, end, "15m") == 97  # 96 quarters + 1
        assert service._calculate_expected_points(start, end, "4h") == 7    # 6 periods + 1
        
        # Test with zero duration
        same_time = datetime(2023, 1, 1)
        assert service._calculate_expected_points(same_time, same_time, "1h") == 1
    
    def test_adjust_for_lookback(self, mock_influxdb_client):
        """Test adjustment of start date for lookback period."""
        service = DataAvailabilityService(mock_influxdb_client)
        
        # Test with datetime objects
        start = datetime(2023, 2, 1)
        
        # Test days
        adjusted = service._adjust_for_lookback(start, "30D")
        assert adjusted == datetime(2023, 1, 2)
        
        # Test weeks
        adjusted = service._adjust_for_lookback(start, "2W")
        assert adjusted == datetime(2023, 1, 18)
        
        # Test months (approximate as 30 days)
        adjusted = service._adjust_for_lookback(start, "1M")
        assert adjusted == datetime(2023, 1, 2)
        
        # Test years (approximate as 365 days)
        adjusted = service._adjust_for_lookback(start, "1Y")
        expected = datetime(2022, 2, 1)
        assert abs((adjusted - expected).days) <= 1  # Allow off-by-one for leap years
        
        # Test with string dates
        adjusted = service._adjust_for_lookback("2023-02-01", "30D")
        assert adjusted == "2023-01-02T00:00:00"
        
        # Test invalid lookback format
        assert service._adjust_for_lookback(start, "invalid") is None