"""
Unit tests for the data versioning service.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call

from src.services.data_versioning import DataVersioningService
from src.models.market_data import DataSnapshotMetadata


@pytest.fixture
def mock_influxdb_client():
    """Create a mock InfluxDB client."""
    mock_client = MagicMock()
    mock_client.bucket = "market_data"
    mock_client.audit_bucket = "data_audit"
    mock_client.org = "test_org"
    
    # Mock query_api
    mock_client.query_api = MagicMock()
    
    # Mock write_api
    mock_client.write_api = MagicMock()
    
    # Mock delete_api
    mock_client.delete_api = MagicMock()
    
    # Set up query_ohlcv to return test data
    sample_data = [
        {
            "timestamp": datetime.now(),
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 1000.0
        },
        {
            "timestamp": datetime.now() + timedelta(hours=1),
            "open": 103.0,
            "high": 107.0,
            "low": 102.0,
            "close": 106.0,
            "volume": 1200.0
        }
    ]
    mock_client.query_ohlcv = MagicMock(return_value=sample_data)
    
    # Set up write_ohlcv to return success
    mock_client.write_ohlcv = MagicMock(return_value=True)
    
    # Set up get_data_versions to return test versions
    mock_client.get_data_versions = MagicMock(
        return_value=["latest", "snapshot_123", "snapshot_456"]
    )
    
    return mock_client


@pytest.fixture
def versioning_service(mock_influxdb_client):
    """Create the data versioning service with the mock client."""
    return DataVersioningService(mock_influxdb_client)


class TestDataVersioningService:
    """Tests for the DataVersioningService class."""
    
    @pytest.mark.asyncio
    async def test_create_snapshot(self, versioning_service, mock_influxdb_client):
        """Test creating a data snapshot."""
        # Configure the test
        instrument = "BTCUSD"
        timeframe = "1h"
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        user_id = "test_user"
        strategy_id = "test_strategy"
        snapshot_id = "snapshot_test_123"
        
        # Execute the function
        result = await versioning_service.create_snapshot(
            instrument=instrument,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            strategy_id=strategy_id,
            snapshot_id=snapshot_id
        )
        
        # Verify the results
        assert result == snapshot_id
        
        # Verify that query_ohlcv was called
        mock_influxdb_client.query_ohlcv.assert_called_once_with(
            instrument=instrument,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            version="latest"
        )
        
        # Verify that write_ohlcv was called
        mock_influxdb_client.write_ohlcv.assert_called_once()
        write_args = mock_influxdb_client.write_ohlcv.call_args[1]
        assert write_args["instrument"] == instrument
        assert write_args["timeframe"] == timeframe
        assert write_args["source"] == "snapshot"
        assert write_args["version"] == snapshot_id
        
        # Verify that write_api.write was called for audit log
        mock_influxdb_client.write_api.write.assert_called()
    
    @pytest.mark.asyncio
    async def test_compare_versions(self, versioning_service, mock_influxdb_client):
        """Test comparing two data versions."""
        # Configure the test
        instrument = "BTCUSD"
        timeframe = "1h"
        version1 = "snapshot_123"
        version2 = "snapshot_456"
        
        # Configure mock to return different data for different versions
        data_v1 = [
            {
                "timestamp": datetime(2023, 1, 1, 12, 0),
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 103.0,
                "volume": 1000.0
            }
        ]
        
        data_v2 = [
            {
                "timestamp": datetime(2023, 1, 1, 12, 0),
                "open": 100.0,
                "high": 106.0,  # Different high
                "low": 98.0,    # Different low
                "close": 103.0,
                "volume": 1000.0
            }
        ]
        
        mock_influxdb_client.query_ohlcv.side_effect = lambda **kwargs: (
            data_v1 if kwargs.get("version") == version1 else data_v2
        )
        
        # Execute the function
        result = await versioning_service.compare_versions(
            instrument=instrument,
            timeframe=timeframe,
            version1=version1,
            version2=version2
        )
        
        # Verify the results
        assert result["instrument"] == instrument
        assert result["timeframe"] == timeframe
        assert result["version1"] == version1
        assert result["version2"] == version2
        assert "summary" in result
        assert "differences" in result
        
        # Verify that query_ohlcv was called twice
        assert mock_influxdb_client.query_ohlcv.call_count == 2
    
    @pytest.mark.asyncio
    async def test_list_versions(self, versioning_service, mock_influxdb_client):
        """Test listing data versions."""
        # Configure the test
        instrument = "BTCUSD"
        timeframe = "1h"
        
        # Execute the function
        result = await versioning_service.list_versions(
            instrument=instrument,
            timeframe=timeframe,
            include_metadata=False
        )
        
        # Verify the results
        assert len(result) == 3
        assert result[0]["version"] == "latest"
        assert result[1]["version"] == "snapshot_123"
        assert result[2]["version"] == "snapshot_456"
        
        # Verify that get_data_versions was called
        mock_influxdb_client.get_data_versions.assert_called_once_with(
            instrument=instrument,
            timeframe=timeframe
        )
    
    @pytest.mark.asyncio
    async def test_apply_retention_policy_dry_run(self, versioning_service, mock_influxdb_client):
        """Test applying retention policy in dry run mode."""
        # Configure the test
        mock_tables = MagicMock()
        mock_record = MagicMock()
        mock_record.values = {
            "snapshot_id": "snapshot_old",
            "purpose": "backtest"
        }
        mock_record.get_time.return_value = datetime.now() - timedelta(days=100)
        
        mock_tables.records = [mock_record]
        mock_influxdb_client.query_api.query.return_value = [mock_tables]
        
        # Execute the function
        result = await versioning_service.apply_retention_policy(
            max_snapshot_age_days=60,
            dry_run=True
        )
        
        # Verify the results
        assert result["dry_run"] is True
        assert len(result["candidates_for_deletion"]) == 1
        assert result["candidates_for_deletion"][0]["snapshot_id"] == "snapshot_old"
        
        # Verify that delete_api was not called
        mock_influxdb_client.delete_api.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_tag_version(self, versioning_service, mock_influxdb_client):
        """Test tagging a data version."""
        # Configure the test
        instrument = "BTCUSD"
        timeframe = "1h"
        version = "snapshot_123"
        tag_name = "compliance_approved"
        tag_value = "true"
        user_id = "test_user"
        
        mock_tables = MagicMock()
        mock_record = MagicMock()
        mock_record.values = {
            "tags": json.dumps({"existing_tag": "value"})
        }
        mock_record.get_time.return_value = datetime.now()
        
        mock_tables.records = [mock_record]
        mock_influxdb_client.query_api.query.return_value = [mock_tables]
        
        # Execute the function
        result = await versioning_service.tag_version(
            instrument=instrument,
            timeframe=timeframe,
            version=version,
            tag_name=tag_name,
            tag_value=tag_value,
            user_id=user_id
        )
        
        # Verify the results
        assert result is True
        
        # Verify that write_api.write was called for both the tag update and audit
        assert mock_influxdb_client.write_api.write.call_count >= 2