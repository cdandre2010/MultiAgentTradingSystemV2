import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

from src.agents.conversational_agent import ConversationalAgent
from src.agents.data_feature_agent import DataFeatureAgent
from src.services.indicators import IndicatorService
from src.services.data_availability import DataAvailabilityService
from src.services.data_retrieval import DataRetrievalService
from src.models.market_data import OHLCV, OHLCVPoint


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    mock = MagicMock()
    mock.generate.return_value = "I'll help you create a chart for Apple stock."
    mock.extract_json.return_value = {
        "indicator": "sma",
        "parameters": {
            "window": 20
        },
        "instrument": "AAPL",
        "timeframe": "1d"
    }
    return mock


@pytest.fixture
def mock_indicator_service():
    """Create a mock IndicatorService for testing."""
    mock = MagicMock(spec=IndicatorService)
    mock.calculate_indicator.return_value = {
        "type": "sma",
        "values": {
            "2023-01-01T00:00:00": 150.0,
            "2023-01-02T00:00:00": 151.0,
            "2023-01-03T00:00:00": 152.0
        },
        "metadata": {
            "params": {"window": 20}
        }
    }
    return mock


@pytest.fixture
def mock_data_availability_service():
    """Create a mock DataAvailabilityService for testing."""
    mock = MagicMock(spec=DataAvailabilityService)
    
    async def mock_check_data_requirements(*args, **kwargs):
        return {
            "overall": {
                "is_complete": True,
                "highest_availability": 98.5,
                "source": "influxdb"
            },
            "sources": {
                "influxdb": {
                    "availability": 98.5,
                    "status": "complete"
                }
            }
        }
    
    mock.check_data_requirements = mock_check_data_requirements
    return mock


@pytest.fixture
def mock_data_retrieval_service():
    """Create a mock DataRetrievalService for testing."""
    mock = MagicMock(spec=DataRetrievalService)
    
    # Sample OHLCV data for testing
    ohlcv_data = OHLCV(
        instrument="AAPL",
        timeframe="1d",
        source="influxdb",
        data=[
            OHLCVPoint(
                timestamp=datetime.fromisoformat("2023-01-01T00:00:00"),
                open=150.0,
                high=155.0,
                low=149.0,
                close=153.0,
                volume=1000000
            ),
            OHLCVPoint(
                timestamp=datetime.fromisoformat("2023-01-02T00:00:00"),
                open=153.0,
                high=158.0,
                low=152.0,
                close=157.0,
                volume=1200000
            ),
            OHLCVPoint(
                timestamp=datetime.fromisoformat("2023-01-03T00:00:00"),
                open=157.0,
                high=160.0,
                low=156.0,
                close=159.0,
                volume=1100000
            )
        ]
    )
    
    async def mock_get_ohlcv(*args, **kwargs):
        return ohlcv_data
        
    mock.get_ohlcv = mock_get_ohlcv
    return mock


@pytest.fixture
def data_feature_agent(mock_indicator_service, mock_data_availability_service, mock_data_retrieval_service):
    """Create a DataFeatureAgent instance with mocked services."""
    return DataFeatureAgent(
        indicator_service=mock_indicator_service,
        data_availability_service=mock_data_availability_service,
        data_retrieval_service=mock_data_retrieval_service
    )


@pytest.fixture
def conversational_agent(mock_llm):
    """Create a ConversationalAgent instance with a mock LLM."""
    with patch('src.agents.conversational_agent.get_llm', return_value=mock_llm):
        agent = ConversationalAgent()
        # Mock the strategy repository to avoid DB connections
        agent.strategy_repository = MagicMock()
        return agent


class TestConversationalDataIntegration:
    """Test the integration between ConversationalAgent and DataFeatureAgent."""
    
    def test_conversational_agent_recognizes_data_requests(self, conversational_agent, mock_llm):
        """Test that the agent can recognize data-related requests."""
        # Setup the test
        message = {
            "message_id": "test_id",
            "timestamp": datetime.utcnow().isoformat(),
            "sender": "user",
            "recipient": "conversational_agent",
            "message_type": "request",
            "content": {"text": "Can you show me a chart of Apple stock?"},
            "context": {"session_id": "test_session"}
        }
        
        # Configure the mock to extract data request parameters
        mock_llm.extract_json.return_value = {
            "data_request": True,
            "chart_type": "candlestick",
            "instrument": "AAPL",
            "timeframe": "1d"
        }
        
        # Process the message
        response = conversational_agent.process_message(message)
        
        # Assertions to check that the agent recognized a data request
        assert response["message_id"] != message["message_id"]
        assert response["sender"] == "conversational_agent"
        assert response["recipient"] == "user"
        assert "I'll help you create a chart for Apple stock." in response["content"]["text"]
    
    def test_create_data_request_message(self, conversational_agent):
        """Test that the agent can create a properly formatted data request message."""
        # This will test the new method to create messages for the DataFeatureAgent
        
        data_params = {
            "instrument": "AAPL",
            "timeframe": "1d",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "indicators": [{"type": "sma", "parameters": {"window": 20}}]
        }
        
        # Call the method (to be implemented)
        data_request = conversational_agent.create_data_feature_request(
            "create_visualization", 
            data_params, 
            "test_session"
        )
        
        # Check that the message is formatted correctly
        assert data_request["sender"] == "conversational_agent"
        assert data_request["recipient"] == "data_feature"
        assert data_request["message_type"] == "request"
        assert data_request["context"]["session_id"] == "test_session"
        assert data_request["content"]["type"] == "create_visualization"
        assert data_request["content"]["data"] == data_params
    
    def test_conversational_agent_can_format_data_response(self, conversational_agent):
        """Test that the agent can format data responses into natural language."""
        # Mock a response from the DataFeatureAgent
        data_response = {
            "message_id": "data_response_id",
            "timestamp": datetime.utcnow().isoformat(),
            "sender": "data_feature",
            "recipient": "conversational_agent",
            "message_type": "response",
            "content": {
                "type": "data_availability_result",
                "data": {
                    "availability": {
                        "overall": {
                            "is_complete": True,
                            "highest_availability": 98.5,
                            "source": "influxdb"
                        }
                    },
                    "instrument": "AAPL",
                    "timeframe": "1d",
                    "start_date": "2023-01-01",
                    "end_date": "2023-01-31"
                }
            },
            "context": {"session_id": "test_session"}
        }
        
        # Mock LLM to return a natural language explanation
        conversational_agent.llm.generate.return_value = (
            "Great news! We have complete data for Apple stock (AAPL) on a daily timeframe "
            "from January 1, 2023 to January 31, 2023. The data is 98.5% complete from our primary source."
        )
        
        # Call the method (to be implemented)
        user_response = conversational_agent.format_data_response(data_response)
        
        # Check the response
        assert user_response["sender"] == "conversational_agent"
        assert user_response["recipient"] == "user"
        assert "Great news!" in user_response["content"]["text"]
        assert user_response["context"]["session_id"] == "test_session"
    
    def test_data_agent_visualization_integration(self, conversational_agent, data_feature_agent, mock_llm):
        """Test the full integration flow for visualization requests."""
        # Mock conversational agent to extract visualization parameters
        mock_llm.extract_json.return_value = {
            "data_request_type": "visualization",
            "visualization_type": "candlestick",
            "instrument": "AAPL",
            "timeframe": "1d",
            "start_date": "2023-01-01",
            "end_date": "2023-01-03",
            "indicators": [{"type": "sma", "parameters": {"window": 20}}]
        }
        
        # Create a user message requesting a chart
        user_message = {
            "message_id": "user_msg_id",
            "timestamp": datetime.utcnow().isoformat(),
            "sender": "user",
            "recipient": "conversational_agent",
            "message_type": "request",
            "content": {"text": "Show me a chart for Apple with a 20-day moving average"},
            "context": {"session_id": "test_session"}
        }
        
        # Process the user message to detect data request and extract parameters
        with patch.object(conversational_agent, 'create_data_feature_request') as mock_create_request:
            # Set up the mock to return a properly formatted request
            mock_create_request.return_value = {
                "message_id": "data_req_id",
                "timestamp": datetime.utcnow().isoformat(),
                "sender": "conversational_agent",
                "recipient": "data_feature",
                "message_type": "request",
                "content": {
                    "type": "create_visualization",
                    "data": {
                        "visualization_type": "candlestick",
                        "instrument": "AAPL",
                        "timeframe": "1d",
                        "start_date": "2023-01-01",
                        "end_date": "2023-01-03",
                        "indicators": [{"type": "sma", "parameters": {"window": 20}}]
                    }
                },
                "context": {"session_id": "test_session"}
            }
            
            with patch.object(conversational_agent, 'format_data_response') as mock_format_response:
                # Set up the mock to return a user-friendly response
                mock_format_response.return_value = {
                    "message_id": "response_id",
                    "timestamp": datetime.utcnow().isoformat(),
                    "sender": "conversational_agent",
                    "recipient": "user",
                    "message_type": "response",
                    "content": {
                        "text": "Here's the chart for Apple stock with a 20-day moving average.",
                        "visualization_url": "/api/visualizations/12345"
                    },
                    "context": {"session_id": "test_session"}
                }
                
                # Call the method that needs to be implemented
                response = conversational_agent.handle_data_visualization_request(user_message)
                
                # Verify the method generated the proper request and formatted the response
                mock_create_request.assert_called_once()
                request_args = mock_create_request.call_args[0]
                assert request_args[0] == "create_visualization"
                assert request_args[1]["instrument"] == "AAPL"
                
                # Verify the data feature agent would have been called
                # (this is a unit test, so we're not actually calling it)
                
                # Verify the response was formatted
                assert response["content"]["text"] == "Here's the chart for Apple stock with a 20-day moving average."
                assert "visualization_url" in response["content"]
    
    def test_data_agent_availability_integration(self, conversational_agent, data_feature_agent, mock_llm):
        """Test the full integration flow for data availability requests."""
        # Mock conversational agent to extract data availability parameters
        mock_llm.extract_json.return_value = {
            "data_request_type": "availability",
            "instrument": "AAPL",
            "timeframe": "1d",
            "start_date": "2023-01-01", 
            "end_date": "2023-01-31"
        }
        
        # Create a user message asking about data availability
        user_message = {
            "message_id": "user_msg_id",
            "timestamp": datetime.utcnow().isoformat(),
            "sender": "user",
            "recipient": "conversational_agent",
            "message_type": "request",
            "content": {"text": "Do we have data for Apple stock for January 2023?"},
            "context": {"session_id": "test_session"}
        }
        
        # Process the user message to detect data request and extract parameters
        with patch.object(conversational_agent, 'create_data_feature_request') as mock_create_request:
            # Set up the mock to return a properly formatted request
            mock_create_request.return_value = {
                "message_id": "data_req_id",
                "timestamp": datetime.utcnow().isoformat(),
                "sender": "conversational_agent",
                "recipient": "data_feature",
                "message_type": "request",
                "content": {
                    "type": "check_data_availability",
                    "data": {
                        "instrument": "AAPL",
                        "timeframe": "1d",
                        "start_date": "2023-01-01",
                        "end_date": "2023-01-31"
                    }
                },
                "context": {"session_id": "test_session"}
            }
            
            with patch.object(conversational_agent, 'format_data_response') as mock_format_response:
                # Set up the mock to return a user-friendly response
                mock_format_response.return_value = {
                    "message_id": "response_id",
                    "timestamp": datetime.utcnow().isoformat(),
                    "sender": "conversational_agent",
                    "recipient": "user",
                    "message_type": "response",
                    "content": {
                        "text": "Yes, we have complete data for Apple stock for January 2023. The data is 98.5% complete from our primary source."
                    },
                    "context": {"session_id": "test_session"}
                }
                
                # Call the method that needs to be implemented
                response = conversational_agent.handle_data_availability_request(user_message)
                
                # Verify the method generated the proper request and formatted the response
                mock_create_request.assert_called_once()
                request_args = mock_create_request.call_args[0]
                assert request_args[0] == "check_data_availability"
                assert request_args[1]["instrument"] == "AAPL"
                
                # Verify the response was formatted
                assert "Yes, we have complete data" in response["content"]["text"]
    
    def test_indicator_explanation_request(self, conversational_agent, mock_llm):
        """Test that the agent can provide natural language explanations of indicators."""
        # Mock the LLM to return an explanation
        mock_llm.generate.return_value = (
            "A Simple Moving Average (SMA) is calculated by adding the closing prices "
            "of a security over a specific period and dividing by the number of periods. "
            "The 20-day SMA is often used to identify trend direction and support/resistance levels."
        )
        
        # Create a user message asking about an indicator
        user_message = {
            "message_id": "user_msg_id",
            "timestamp": datetime.utcnow().isoformat(),
            "sender": "user",
            "recipient": "conversational_agent",
            "message_type": "request",
            "content": {"text": "What is a 20-day simple moving average?"},
            "context": {"session_id": "test_session"}
        }
        
        # Call the method that needs to be implemented
        response = conversational_agent.handle_indicator_explanation_request(user_message, "sma", {"window": 20})
        
        # Verify the response contains the explanation
        assert "Simple Moving Average (SMA)" in response["content"]["text"]
        assert "20-day SMA" in response["content"]["text"]