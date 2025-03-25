"""
Unit tests for DataRetrievalService.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.services.data_retrieval import DataRetrievalService
from src.services.indicators import IndicatorService
from src.models.market_data import OHLCV, OHLCVPoint, MarketDataRequest
from src.models.strategy import DataConfig, BacktestDataRange, DataSourceType, DataSource, DataPreprocessing


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing."""
    # Create sample data with 5 data points
    base_time = datetime(2023, 1, 1)
    data = []
    
    for i in range(5):
        timestamp = base_time + timedelta(hours=i)
        data.append(OHLCVPoint(
            timestamp=timestamp,
            open=100.0 + i,
            high=102.0 + i,
            low=99.0 + i,
            close=101.0 + i,
            volume=1000 + i * 100
        ))
    
    return OHLCV(
        instrument="BTCUSDT",
        timeframe="1h",
        source="test",
        data=data
    )


@pytest.fixture
def mock_influxdb_client():
    """Create a mock InfluxDB client for testing."""
    client = MagicMock()
    
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
    
    # Mock create_snapshot
    client.create_snapshot.return_value = "snapshot123"
    
    return client


@pytest.fixture
def mock_indicator_service():
    """Create a mock IndicatorService for testing."""
    service = MagicMock(spec=IndicatorService)
    
    # Mock calculate_indicator
    service.calculate_indicator.return_value = {
        "values": {"2023-01-01T00:00:00": 100.0, "2023-01-01T01:00:00": 101.0},
        "metadata": {"indicator_type": "sma", "parameters": {"period": 14}}
    }
    
    # Mock calculate_multiple_indicators
    service.calculate_multiple_indicators.return_value = {
        "SMA": {
            "values": {"2023-01-01T00:00:00": 100.0, "2023-01-01T01:00:00": 101.0},
            "metadata": {"indicator_type": "sma", "parameters": {"period": 14}}
        },
        "RSI": {
            "values": {"2023-01-01T00:00:00": 50.0, "2023-01-01T01:00:00": 60.0},
            "metadata": {"indicator_type": "rsi", "parameters": {"period": 14}}
        }
    }
    
    return service


class TestDataRetrievalService:
    """Tests for the DataRetrievalService class."""
    
    def test_initialization(self, mock_influxdb_client, mock_indicator_service):
        """Test service initialization."""
        service = DataRetrievalService(mock_influxdb_client, mock_indicator_service)
        assert service.influxdb == mock_influxdb_client
        assert service.indicators == mock_indicator_service
    
    @pytest.mark.asyncio
    async def test_get_data_for_strategy(self, mock_influxdb_client, mock_indicator_service, sample_ohlcv_data):
        """Test retrieving data for a strategy."""
        service = DataRetrievalService(mock_influxdb_client, mock_indicator_service)
        
        # Mock get_ohlcv to return sample data
        with patch.object(service, 'get_ohlcv', return_value=sample_ohlcv_data):
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
            
            # Test the get_data_for_strategy method
            result = await service.get_data_for_strategy(data_config)
            
            # Check that the result has the expected structure
            assert "data" in result
            assert "metadata" in result
            assert result["data"] == sample_ohlcv_data
            
            # Check that the metadata contains the expected keys
            metadata = result["metadata"]
            assert metadata["instrument"] == "BTCUSDT"
            assert metadata["timeframe"] == "1h"
            assert metadata["data_points"] == 5
            assert metadata["source"] == "test"
    
    @pytest.mark.asyncio
    async def test_get_data_for_strategy_no_backtest_range(self, mock_influxdb_client, mock_indicator_service):
        """Test retrieving data for a strategy with no backtest range."""
        service = DataRetrievalService(mock_influxdb_client, mock_indicator_service)
        
        # Create a data config with no backtest range
        data_config = DataConfig(
            instrument="BTCUSDT",
            frequency="1h",
            sources=[
                DataSource(type=DataSourceType.INFLUXDB, priority=1)
            ]
        )
        
        # Test the get_data_for_strategy method
        result = await service.get_data_for_strategy(data_config)
        
        # Check that an error is returned
        assert "error" in result
        assert "Backtest range not defined" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_data_for_strategy_with_lookback(self, mock_influxdb_client, mock_indicator_service, sample_ohlcv_data):
        """Test retrieving data with lookback period."""
        service = DataRetrievalService(mock_influxdb_client, mock_indicator_service)
        
        # Mock get_ohlcv to return sample data
        with patch.object(service, 'get_ohlcv', return_value=sample_ohlcv_data):
            # Create a data config with lookback period
            data_config = DataConfig(
                instrument="BTCUSDT",
                frequency="1h",
                sources=[
                    DataSource(type=DataSourceType.INFLUXDB, priority=1)
                ],
                backtest_range=BacktestDataRange(
                    start_date="2023-01-01",
                    end_date="2023-01-02",
                    lookback_period="30D"
                )
            )
            
            # Test the get_data_for_strategy method
            result = await service.get_data_for_strategy(data_config)
            
            # Check that the result has the expected structure
            assert "data" in result
            assert "metadata" in result
            
            # Check that the lookback was applied
            metadata = result["metadata"]
            assert metadata["lookback_applied"] is True
    
    @pytest.mark.asyncio
    async def test_get_ohlcv(self, mock_influxdb_client, mock_indicator_service):
        """Test retrieving OHLCV data with priority-based source selection."""
        service = DataRetrievalService(mock_influxdb_client, mock_indicator_service)
        
        # Create a list of data sources
        data_sources = [
            DataSource(type=DataSourceType.INFLUXDB, priority=1),
            DataSource(type=DataSourceType.BINANCE, priority=2)
        ]
        
        # Test the get_ohlcv method
        result = await service.get_ohlcv(
            data_sources=data_sources,
            instrument="BTCUSDT",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-01-02"
        )
        
        # Check that the result has the expected structure
        assert isinstance(result, OHLCV)
        assert result.instrument == "BTCUSDT"
        assert result.timeframe == "1h"
        assert result.source == "influxdb"
        assert len(result.data) == 2
        
        # Check that the InfluxDB client was called with the correct parameters
        mock_influxdb_client.query_ohlcv.assert_called_with(
            instrument="BTCUSDT",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-01-02",
            version="latest"
        )
    
    def test_get_data_with_indicators(self, mock_influxdb_client, mock_indicator_service, sample_ohlcv_data):
        """Test retrieving data with indicators."""
        service = DataRetrievalService(mock_influxdb_client, mock_indicator_service)
        
        # Create a list of indicator configurations
        indicators_config = [
            {"type": "sma", "parameters": {"period": 14}, "name": "SMA"},
            {"type": "rsi", "parameters": {"period": 14}, "name": "RSI"}
        ]
        
        # Test the get_data_with_indicators method
        result = service.get_data_with_indicators(sample_ohlcv_data, indicators_config)
        
        # Check that the result has the expected structure
        assert "data" in result
        assert "indicators" in result
        assert result["data"] == sample_ohlcv_data
        
        # Check that indicators were calculated
        assert "SMA" in result["indicators"]
        assert "RSI" in result["indicators"]
        
        # Check that the indicator service was called with the correct parameters
        mock_indicator_service.calculate_multiple_indicators.assert_called_with(
            ohlcv_data=sample_ohlcv_data,
            indicators_config=indicators_config
        )
    
    def test_get_data_with_indicators_no_data(self, mock_influxdb_client, mock_indicator_service):
        """Test handling of empty data when calculating indicators."""
        service = DataRetrievalService(mock_influxdb_client, mock_indicator_service)
        
        # Create empty OHLCV data
        empty_data = OHLCV(
            instrument="BTCUSDT",
            timeframe="1h",
            source="test",
            data=[]
        )
        
        # Create a list of indicator configurations
        indicators_config = [
            {"type": "sma", "parameters": {"period": 14}}
        ]
        
        # Test the get_data_with_indicators method
        result = service.get_data_with_indicators(empty_data, indicators_config)
        
        # Check that an error is returned
        assert "error" in result
        assert "No data provided" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_backtest_snapshot(self, mock_influxdb_client, mock_indicator_service):
        """Test creating a backtest snapshot."""
        service = DataRetrievalService(mock_influxdb_client, mock_indicator_service)
        
        # Create a data config
        data_config = DataConfig(
            instrument="BTCUSDT",
            frequency="1h",
            sources=[
                DataSource(type=DataSourceType.INFLUXDB, priority=1)
            ],
            backtest_range=BacktestDataRange(
                start_date="2023-01-01",
                end_date="2023-01-02"
            )
        )
        
        # Test the create_backtest_snapshot method
        snapshot_id = await service.create_backtest_snapshot(data_config, strategy_id="strategy123")
        
        # Check that the snapshot ID was returned
        assert snapshot_id == "snapshot123"
        
        # Check that the InfluxDB client was called with the correct parameters
        mock_influxdb_client.create_snapshot.assert_called_with(
            instrument="BTCUSDT",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-01-02",
            snapshot_id=None,
            strategy_id="strategy123",
            purpose="backtest"
        )
    
    @pytest.mark.asyncio
    async def test_create_backtest_snapshot_no_range(self, mock_influxdb_client, mock_indicator_service):
        """Test handling of missing backtest range when creating snapshots."""
        service = DataRetrievalService(mock_influxdb_client, mock_indicator_service)
        
        # Create a data config with no backtest range
        data_config = DataConfig(
            instrument="BTCUSDT",
            frequency="1h",
            sources=[
                DataSource(type=DataSourceType.INFLUXDB, priority=1)
            ]
        )
        
        # Test the create_backtest_snapshot method
        snapshot_id = await service.create_backtest_snapshot(data_config)
        
        # Check that an empty string is returned
        assert snapshot_id == ""
    
    def test_adjust_for_lookback(self, mock_influxdb_client, mock_indicator_service):
        """Test adjustment of start date for lookback period."""
        service = DataRetrievalService(mock_influxdb_client, mock_indicator_service)
        
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
    
    def test_apply_preprocessing(self, mock_influxdb_client, mock_indicator_service, sample_ohlcv_data):
        """Test application of preprocessing to OHLCV data."""
        service = DataRetrievalService(mock_influxdb_client, mock_indicator_service)
        
        # Create a preprocessing configuration
        preprocessing = DataPreprocessing(
            fill_missing="forward_fill",
            normalization="min-max"
        )
        
        # Currently preprocessing is a placeholder
        result = service._apply_preprocessing(sample_ohlcv_data, preprocessing)
        
        # Check that the original data is returned
        assert result == sample_ohlcv_data