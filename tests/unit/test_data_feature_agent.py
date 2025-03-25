"""
Unit tests for the DataFeatureAgent.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from src.agents.base import Agent
from src.services.indicators import IndicatorService
from src.services.data_availability import DataAvailabilityService
from src.services.data_retrieval import DataRetrievalService
from src.models.market_data import OHLCV, OHLCVPoint


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
    """Create a mock InfluxDBClient for testing."""
    client = MagicMock()
    client.check_data_availability.return_value = {
        "is_complete": True,
        "availability_pct": 100.0,
        "expected_points": 24,
        "actual_points": 24,
        "missing_points": 0
    }
    client.query_ohlcv.return_value = []
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


@pytest.fixture
def mock_data_availability_service():
    """Create a mock DataAvailabilityService for testing."""
    service = MagicMock(spec=DataAvailabilityService)
    
    # Mock check_data_requirements
    service.check_data_requirements.return_value = {
        "influxdb_priority_1": {
            "is_complete": True,
            "availability_pct": 100.0,
            "expected_points": 24,
            "actual_points": 24,
            "missing_points": 0
        },
        "overall": {
            "is_complete": True,
            "highest_availability": 100.0,
            "required_start_date": "2023-01-01",
            "required_end_date": "2023-01-02"
        }
    }
    
    # Mock get_missing_segments
    service.get_missing_segments.return_value = []
    
    return service


@pytest.fixture
def mock_data_retrieval_service(sample_ohlcv_data):
    """Create a mock DataRetrievalService for testing."""
    service = MagicMock(spec=DataRetrievalService)
    
    # Mock get_data_for_strategy
    service.get_data_for_strategy.return_value = {
        "data": sample_ohlcv_data,
        "metadata": {
            "instrument": "BTCUSDT",
            "timeframe": "1h",
            "data_points": 5,
            "source": "test"
        }
    }
    
    # Mock get_ohlcv
    service.get_ohlcv.return_value = sample_ohlcv_data
    
    # Mock get_data_with_indicators
    service.get_data_with_indicators.return_value = {
        "data": sample_ohlcv_data,
        "indicators": {
            "SMA": {
                "values": {"2023-01-01T00:00:00": 100.0},
                "metadata": {"indicator_type": "sma", "parameters": {"period": 14}}
            },
            "RSI": {
                "values": {"2023-01-01T00:00:00": 50.0},
                "metadata": {"indicator_type": "rsi", "parameters": {"period": 14}}
            }
        }
    }
    
    # Mock create_backtest_snapshot
    service.create_backtest_snapshot.return_value = "snapshot123"
    
    return service


class TestDataFeatureAgent:
    """Tests for the DataFeatureAgent class."""
    
    def test_initialization(self, mock_influxdb_client, mock_indicator_service, 
                            mock_data_availability_service, mock_data_retrieval_service):
        """Test agent initialization."""
        # Import inside the test to avoid import errors before implementation
        from src.agents.data_feature_agent import DataFeatureAgent
        
        # Disable actual InfluxDB client initialization in the agent constructor
        with patch('src.agents.data_feature_agent.InfluxDBClient', return_value=mock_influxdb_client):
            # Create the agent with mock services
            agent = DataFeatureAgent(
                indicator_service=mock_indicator_service,
                data_availability_service=mock_data_availability_service,
                data_retrieval_service=mock_data_retrieval_service
            )
            
            # Verify initialization
            assert agent.name == "data_feature"
            assert agent.indicator_service == mock_indicator_service
            assert agent.data_availability_service == mock_data_availability_service
            assert agent.data_retrieval_service == mock_data_retrieval_service
            
    def test_process_invalid_message(self, mock_influxdb_client, mock_indicator_service, 
                                  mock_data_availability_service, mock_data_retrieval_service):
        """Test processing an invalid message."""
        from src.agents.data_feature_agent import DataFeatureAgent
        
        # Create the agent with mock services
        with patch('src.agents.data_feature_agent.InfluxDBClient', return_value=mock_influxdb_client):
            agent = DataFeatureAgent(
                indicator_service=mock_indicator_service,
                data_availability_service=mock_data_availability_service,
                data_retrieval_service=mock_data_retrieval_service
            )
            
            # Create an invalid message (missing required fields)
            invalid_message = {
                "sender": "test_sender"
            }
            
            # Process the message
            response = agent.process(invalid_message, {})
            
            # Verify response
            assert response["message_type"] == "error"
            assert "Invalid message format" in response["content"]["error"]
            
    def test_async_wrapper(self, mock_influxdb_client, mock_indicator_service, 
                          mock_data_availability_service, mock_data_retrieval_service):
        """Test that the async wrapper correctly handles async functions."""
        from src.agents.data_feature_agent import DataFeatureAgent
        import asyncio
        
        # Create the agent with mock services
        with patch('src.agents.data_feature_agent.InfluxDBClient', return_value=mock_influxdb_client):
            agent = DataFeatureAgent(
                indicator_service=mock_indicator_service,
                data_availability_service=mock_data_availability_service,
                data_retrieval_service=mock_data_retrieval_service
            )
            
            # Create a test async function
            async def test_async_function():
                await asyncio.sleep(0.01)  # Very small sleep to simulate async work
                return {"status": "success", "data": "test_data"}
            
            # Run the async function through our wrapper
            result = agent.run_async(test_async_function())
            
            # Verify the result
            assert result == {"status": "success", "data": "test_data"}
            
    def test_handle_check_data_availability(self, mock_influxdb_client, mock_indicator_service, 
                                      mock_data_availability_service, mock_data_retrieval_service):
        """Test handling a check_data_availability message with async methods."""
        from src.agents.data_feature_agent import DataFeatureAgent
        import asyncio
        
        # Configure mock data availability service to return a mock for the async method
        async def mock_check_data_requirements(*args, **kwargs):
            return {
                "influxdb_priority_1": {
                    "is_complete": True,
                    "availability_pct": 100.0,
                    "expected_points": 24,
                    "actual_points": 24,
                    "missing_points": 0
                },
                "overall": {
                    "is_complete": True,
                    "highest_availability": 100.0,
                    "required_start_date": "2023-01-01",
                    "required_end_date": "2023-01-02"
                }
            }
        
        # Override the mock's check_data_requirements method to be async
        mock_data_availability_service.check_data_requirements = mock_check_data_requirements
        
        # Create the agent with mock services
        with patch('src.agents.data_feature_agent.InfluxDBClient', return_value=mock_influxdb_client):
            agent = DataFeatureAgent(
                indicator_service=mock_indicator_service,
                data_availability_service=mock_data_availability_service,
                data_retrieval_service=mock_data_retrieval_service
            )
            
            # Create a valid message for checking data availability
            message = {
                "message_id": "test_msg_1",
                "timestamp": "2023-01-01T00:00:00Z",
                "sender": "test_sender",
                "recipient": "data_feature",
                "message_type": "request",
                "content": {
                    "type": "check_data_availability",
                    "data": {
                        "instrument": "BTCUSDT",
                        "timeframe": "1h",
                        "start_date": "2023-01-01",
                        "end_date": "2023-02-01"  # At least 30 days to satisfy validation
                    }
                },
                "context": {}
            }
            
            # Process the message
            response = agent.process(message, {})
            
            # Verify the response
            assert response["message_type"] == "response"
            assert response["content"]["type"] == "data_availability_result"
            assert "data" in response["content"]
            assert "availability" in response["content"]["data"]