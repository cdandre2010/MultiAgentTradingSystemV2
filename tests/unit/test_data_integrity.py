"""
Unit tests for the DataIntegrityService.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.services.data_integrity import DataIntegrityService, AdjustmentType, DataDiscrepancyType
from src.models.market_data import OHLCVPoint, OHLCV


@pytest.fixture
def mock_influxdb_client():
    """Create a mock InfluxDB client for testing."""
    mock_client = MagicMock()
    
    # Mock query_api
    mock_client.query_api = MagicMock()
    mock_client.write_api = MagicMock()
    
    # Mock organization
    mock_client.org = "test_org"
    mock_client.audit_bucket = "audit"
    
    return mock_client


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing."""
    # Create sample data with 30 data points
    base_time = datetime(2023, 1, 1)
    data = []
    
    for i in range(30):
        timestamp = base_time + timedelta(hours=i)
        data.append({
            "timestamp": timestamp,
            "open": 100 + i * 0.1,
            "high": 101 + i * 0.1,
            "low": 99 + i * 0.1,
            "close": 100.5 + i * 0.1,
            "volume": 1000 + i * 10
        })
    
    return data


@pytest.fixture
def sample_ohlcv_data_with_anomalies(sample_ohlcv_data):
    """Generate sample OHLCV data with injected anomalies for testing."""
    # Create a copy of the sample data
    data = sample_ohlcv_data.copy()
    
    # Inject price anomaly (outlier)
    data[5]["close"] = 150  # Significant price spike
    
    # Inject volume anomaly
    data[10]["volume"] = 10000  # Volume spike
    
    # Inject gap
    data[15]["close"] = 105
    data[16]["open"] = 115  # Large gap between close and next open
    
    # Inject potential split
    data[20]["close"] = 100
    data[21]["open"] = 50  # 50% drop overnight
    data[21]["volume"] = 2000  # Increased volume
    
    return data


class TestDataIntegrityService:
    """Tests for the DataIntegrityService class."""
    
    def test_init(self, mock_influxdb_client):
        """Test service initialization."""
        service = DataIntegrityService(influxdb_client=mock_influxdb_client)
        
        assert service.influxdb == mock_influxdb_client
        assert service.versioning_service is not None
        assert service.config is not None
        assert "z_score_threshold" in service.config
    
    @patch.object(DataIntegrityService, "_detect_price_anomalies")
    @patch.object(DataIntegrityService, "_detect_volume_anomalies")
    @patch.object(DataIntegrityService, "_detect_price_gaps")
    @patch.object(DataIntegrityService, "_detect_potential_corporate_actions")
    @patch.object(DataIntegrityService, "_detect_timestamp_irregularities")
    async def test_detect_anomalies(
        self, 
        mock_timestamp, 
        mock_corporate, 
        mock_gaps, 
        mock_volume, 
        mock_price, 
        mock_influxdb_client, 
        sample_ohlcv_data
    ):
        """Test anomaly detection."""
        # Setup mocks
        mock_influxdb_client.query_ohlcv.return_value = sample_ohlcv_data
        
        mock_price.return_value = [{"timestamp": datetime(2023, 1, 1, 5), "type": "price_outlier", "confidence": 0.8}]
        mock_volume.return_value = [{"timestamp": datetime(2023, 1, 1, 10), "type": "volume_outlier", "confidence": 0.7}]
        mock_gaps.return_value = [{"timestamp": datetime(2023, 1, 1, 15), "type": "gap", "confidence": 0.9}]
        mock_corporate.return_value = [{"timestamp": datetime(2023, 1, 1, 20), "type": "split", "confidence": 0.85}]
        mock_timestamp.return_value = []
        
        # Create service and call detect_anomalies
        service = DataIntegrityService(influxdb_client=mock_influxdb_client)
        result = await service.detect_anomalies(
            instrument="AAPL",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-01-02",
            version="latest"
        )
        
        # Check the result
        assert result["instrument"] == "AAPL"
        assert result["timeframe"] == "1h"
        assert len(result["anomalies"]) == 4
        assert result["summary"]["total_anomalies"] == 4
        assert result["summary"]["high_confidence_anomalies"] == 3
        
        # Verify that all mock methods were called
        mock_influxdb_client.query_ohlcv.assert_called_once()
        mock_price.assert_called_once()
        mock_volume.assert_called_once()
        mock_gaps.assert_called_once()
        mock_corporate.assert_called_once()
        mock_timestamp.assert_called_once()
    
    def test_detect_price_anomalies(self, mock_influxdb_client, sample_ohlcv_data_with_anomalies):
        """Test price anomaly detection."""
        # Convert to DataFrame
        df = pd.DataFrame(sample_ohlcv_data_with_anomalies)
        
        service = DataIntegrityService(influxdb_client=mock_influxdb_client)
        anomalies = service._detect_price_anomalies(df)
        
        # Should detect the price spike
        assert len(anomalies) > 0
        assert any(a["type"] == DataDiscrepancyType.PRICE_OUTLIER.value for a in anomalies)
    
    def test_detect_volume_anomalies(self, mock_influxdb_client, sample_ohlcv_data_with_anomalies):
        """Test volume anomaly detection."""
        # Convert to DataFrame
        df = pd.DataFrame(sample_ohlcv_data_with_anomalies)
        
        service = DataIntegrityService(influxdb_client=mock_influxdb_client)
        anomalies = service._detect_volume_anomalies(df)
        
        # Should detect the volume spike
        assert len(anomalies) > 0
        assert any(a["type"] == DataDiscrepancyType.VOLUME_OUTLIER.value for a in anomalies)
    
    def test_detect_price_gaps(self, mock_influxdb_client, sample_ohlcv_data_with_anomalies):
        """Test price gap detection."""
        # Convert to DataFrame
        df = pd.DataFrame(sample_ohlcv_data_with_anomalies)
        
        service = DataIntegrityService(influxdb_client=mock_influxdb_client)
        anomalies = service._detect_price_gaps(df)
        
        # Should detect the gap between close and next open
        assert len(anomalies) > 0
        assert any(a["type"] == DataDiscrepancyType.GAP.value for a in anomalies)
    
    def test_detect_stock_splits(self, mock_influxdb_client, sample_ohlcv_data_with_anomalies):
        """Test stock split detection."""
        # Convert to DataFrame
        df = pd.DataFrame(sample_ohlcv_data_with_anomalies)
        
        service = DataIntegrityService(influxdb_client=mock_influxdb_client)
        anomalies = service._detect_stock_splits(df)
        
        # Should detect the potential split
        assert len(anomalies) > 0
        assert any(a["type"] == AdjustmentType.SPLIT.value for a in anomalies)
    
    @patch("src.data_sources.yfinance.YFinanceConnector.fetch_ohlcv")
    async def test_reconcile_with_source(self, mock_fetch, mock_influxdb_client, sample_ohlcv_data):
        """Test data reconciliation with external source."""
        # Setup mock for cached data
        mock_influxdb_client.query_ohlcv.return_value = sample_ohlcv_data
        
        # Create slightly different source data
        source_data = OHLCV(
            instrument="AAPL",
            timeframe="1h",
            data=[
                OHLCVPoint(
                    timestamp=data["timestamp"],
                    open=data["open"] * 1.01,  # 1% difference
                    high=data["high"] * 1.01,
                    low=data["low"] * 1.01,
                    close=data["close"] * 1.01,
                    volume=data["volume"]
                )
                for data in sample_ohlcv_data
            ]
        )
        
        # Setup mock for source data
        mock_fetch.return_value = source_data
        
        # Create service and call reconcile_with_source
        service = DataIntegrityService(influxdb_client=mock_influxdb_client)
        result = await service.reconcile_with_source(
            instrument="AAPL",
            timeframe="1h",
            source="yfinance",
            start_date="2023-01-01",
            end_date="2023-01-02",
            create_adjustment=False
        )
        
        # Check the result
        assert result["status"] == "success"
        assert result["instrument"] == "AAPL"
        assert result["timeframe"] == "1h"
        assert result["source"] == "yfinance"
        assert len(result["discrepancies"]) > 0
        assert result["total_discrepancies"] > 0
        assert "adjustment_recommendation" in result
    
    @patch.object(DataIntegrityService, "_detect_stock_splits")
    @patch.object(DataIntegrityService, "_detect_dividends")
    @patch.object(DataIntegrityService, "_detect_mergers")
    async def test_detect_corporate_actions(
        self,
        mock_mergers,
        mock_dividends,
        mock_splits,
        mock_influxdb_client,
        sample_ohlcv_data
    ):
        """Test corporate action detection."""
        # Setup mocks
        mock_influxdb_client.query_ohlcv.return_value = sample_ohlcv_data
        
        mock_splits.return_value = [{"timestamp": datetime(2023, 1, 1, 20), "type": "split", "confidence": 0.9}]
        mock_dividends.return_value = [{"timestamp": datetime(2023, 1, 1, 15), "type": "dividend", "confidence": 0.8}]
        mock_mergers.return_value = []
        
        # Create service and call detect_corporate_actions
        service = DataIntegrityService(influxdb_client=mock_influxdb_client)
        result = await service.detect_corporate_actions(
            instrument="AAPL",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-01-02",
            version="latest"
        )
        
        # Check the result
        assert result["instrument"] == "AAPL"
        assert result["timeframe"] == "1h"
        assert len(result["corporate_actions"]) == 2
        assert result["high_confidence_actions"] == 2
        
        # Verify that mock methods were called
        mock_influxdb_client.query_ohlcv.assert_called_once()
        mock_splits.assert_called_once()
        mock_dividends.assert_called_once()
        mock_mergers.assert_called_once()
    
    @patch.object(DataIntegrityService, "_record_version_audit")
    async def test_create_adjustment(
        self,
        mock_record_audit,
        mock_influxdb_client,
        sample_ohlcv_data
    ):
        """Test creating a data adjustment."""
        # Setup mocks
        mock_influxdb_client.query_ohlcv.return_value = sample_ohlcv_data
        mock_influxdb_client.write_ohlcv.return_value = True
        
        # Create service
        service = DataIntegrityService(influxdb_client=mock_influxdb_client)
        
        # Mock the versioning service
        service.versioning_service = MagicMock()
        service.versioning_service.create_snapshot.return_value = "snapshot_123"
        
        # Call create_adjustment
        result = await service.create_adjustment(
            instrument="AAPL",
            timeframe="1h",
            adjustment_type="split",
            adjustment_factor=2.0,
            reference_date="2023-01-01T12:00:00",
            description="Test split adjustment",
            affected_fields=["open", "high", "low", "close", "volume"],
            source="test",
            user_id="test_user"
        )
        
        # Check the result
        assert result["status"] == "success"
        assert result["instrument"] == "AAPL"
        assert result["timeframe"] == "1h"
        assert result["adjustment_type"] == "split"
        assert result["adjustment_factor"] == 2.0
        assert result["affected_points"] == len(sample_ohlcv_data)
        
        # Verify mock calls
        mock_influxdb_client.query_ohlcv.assert_called_once()
        mock_influxdb_client.write_ohlcv.assert_called_once()
        service.versioning_service.create_snapshot.assert_called_once()
        service.versioning_service.tag_version.assert_called_once()
    
    @patch("pandas.DataFrame")
    async def test_verify_data_quality(
        self,
        mock_df,
        mock_influxdb_client,
        sample_ohlcv_data
    ):
        """Test data quality verification."""
        # Setup mocks
        mock_influxdb_client.query_ohlcv.return_value = sample_ohlcv_data
        
        # Configure mock DataFrame
        df_instance = MagicMock()
        mock_df.return_value = df_instance
        df_instance.sort_values.return_value = df_instance
        df_instance.__len__.return_value = len(sample_ohlcv_data)
        df_instance.isnull.return_value.sum.return_value.to_dict.return_value = {}
        df_instance.duplicated.return_value.sum.return_value = 0
        df_instance.iterrows.return_value = []
        
        # Create service and call verify_data_quality
        service = DataIntegrityService(influxdb_client=mock_influxdb_client)
        
        # Mock helper methods
        service._get_timeframe_duration_minutes = MagicMock(return_value=60)
        service._calculate_expected_points = MagicMock(return_value=30)
        service._get_quality_level = MagicMock(return_value="Good")
        
        result = await service.verify_data_quality(
            instrument="AAPL",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-01-02",
            version="latest"
        )
        
        # Check the result
        assert result["instrument"] == "AAPL"
        assert result["timeframe"] == "1h"
        assert result["status"] == "success"
        assert "quality_level" in result
        assert "scores" in result
    
    def test_helper_methods(self, mock_influxdb_client):
        """Test various helper methods."""
        service = DataIntegrityService(influxdb_client=mock_influxdb_client)
        
        # Test _timestamp_to_str
        dt = datetime(2023, 1, 1)
        assert service._timestamp_to_str(dt) == dt.isoformat()
        assert service._timestamp_to_str("2023-01-01") == "2023-01-01"
        
        # Test _get_timeframe_duration_minutes
        assert service._get_timeframe_duration_minutes("1m") == 1
        assert service._get_timeframe_duration_minutes("5m") == 5
        assert service._get_timeframe_duration_minutes("1h") == 60
        assert service._get_timeframe_duration_minutes("1d") == 1440
        
        # Test _calculate_expected_points
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 2)
        assert service._calculate_expected_points(start, end, 60) == 25  # 24 hours + 1
        
        # Test _get_quality_level
        assert service._get_quality_level(95) == "Excellent"
        assert service._get_quality_level(85) == "Good"
        assert service._get_quality_level(65) == "Moderate"