"""
Test real LLM API integration with the ConversationalAgent.
"""
import pytest
from datetime import datetime
import os
from unittest.mock import patch

from src.agents.conversational_agent import ConversationalAgent
from src.agents.data_feature_agent import DataFeatureAgent
from src.utils.llm import ClaudeLLM, get_llm
from src.services.indicators import IndicatorService
from src.services.data_availability import DataAvailabilityService
from src.services.data_retrieval import DataRetrievalService


@pytest.fixture
def llm():
    """Create a real LLM client for testing."""
    # This will use the real API key from environment variables
    return get_llm()


@pytest.fixture
def conversational_agent_with_real_llm():
    """Create a ConversationalAgent with a real LLM."""
    # Get real LLM instead of mock
    agent = ConversationalAgent()
    # Mock the strategy repository to avoid DB connections
    agent.strategy_repository = None
    return agent


@pytest.fixture
def data_feature_agent():
    """Create a DataFeatureAgent with mocked services."""
    indicator_service = IndicatorService()
    
    # Create mock services with minimal functionality
    with patch.object(DataAvailabilityService, "__init__", return_value=None):
        with patch.object(DataRetrievalService, "__init__", return_value=None):
            data_availability_service = DataAvailabilityService()
            data_retrieval_service = DataRetrievalService()
            
            # Add the check_data_requirements method
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
            data_availability_service.check_data_requirements = mock_check_data_requirements
            
            # Create the agent with these services
            return DataFeatureAgent(
                indicator_service=indicator_service,
                data_availability_service=data_availability_service,
                data_retrieval_service=data_retrieval_service
            )


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), 
                    reason="Skip if no API key is provided")
class TestLiveLLMIntegration:
    """Test integration with a live LLM API."""
    
    def test_llm_generation_and_verify_api_call(self, llm, caplog):
        """Test that the LLM can generate responses and verify API calls are made."""
        # Set up logging to capture API calls
        import logging
        caplog.set_level(logging.INFO)
        
        # Get initial stats
        initial_stats = llm.get_api_stats()
        initial_calls = initial_stats["total_calls"]
        
        # Make the API call
        response = llm.generate("What is a trading strategy?")
        
        # Get updated stats
        updated_stats = llm.get_api_stats()
        
        # Verify response
        assert len(response) > 0
        assert isinstance(response, str)
        
        # Verify API call was made
        assert updated_stats["total_calls"] > initial_calls
        
        # Print verification info
        print(f"\n\nAPI VERIFICATION: Response received length: {len(response)} characters")
        print(f"API VERIFICATION: Total API calls made: {updated_stats['total_calls']}")
        print(f"API VERIFICATION: Using model: {updated_stats['model']}")
        
        # Verify that logs contain API call info
        assert any("API call #" in record.message for record in caplog.records)
        
        # Return success if we made it here
        return True
    
    def test_llm_extraction(self, llm):
        """Test that the LLM can extract structured data."""
        response = llm.extract_json(
            "Extract parameters for a moving average strategy with a 20-day period and 2% threshold.",
            "Extract the trading parameters as JSON with fields: strategy_type, parameters (containing lookback_period and threshold)."
        )
        assert isinstance(response, dict)
        assert "strategy_type" in response or "parameters" in response
    
    def test_conversational_agent_interpret_data_request(self, conversational_agent_with_real_llm):
        """Test that the agent can interpret a data-related request using a real LLM."""
        message = {
            "message_id": "test_id",
            "timestamp": datetime.now().isoformat(),
            "sender": "user",
            "recipient": "conversational_agent",
            "message_type": "request",
            "content": {"text": "Can you show me a chart of Apple stock with a 20-day moving average?"},
            "context": {"session_id": "test_session"}
        }
        
        # Process the message - this should use the real LLM to interpret the request
        with patch.object(conversational_agent_with_real_llm, 'handle_data_visualization_request') as mock_handler:
            # Configure mock to return a simple response
            mock_handler.return_value = {
                "message_id": "response_id",
                "timestamp": datetime.now().isoformat(),
                "sender": "conversational_agent",
                "recipient": "user",
                "message_type": "response",
                "content": {"text": "Here's the Apple stock chart with a 20-day MA."}
            }
            
            # Process the message
            response = conversational_agent_with_real_llm.process_message(message)
            
            # Verify the data visualization handler was called
            mock_handler.assert_called_once()
            
            # Basic response structure checks
            assert response["sender"] == "conversational_agent"
            assert response["recipient"] == "user"
    
    def test_indicator_explanation_with_real_llm(self, conversational_agent_with_real_llm):
        """Test that the agent can provide a real LLM-generated explanation of an indicator."""
        message = {
            "message_id": "test_id",
            "timestamp": datetime.now().isoformat(),
            "sender": "user",
            "recipient": "conversational_agent",
            "message_type": "request",
            "content": {"text": "What is a 20-day moving average?"},
            "context": {"session_id": "test_session"}
        }
        
        # Call the indicator explanation method directly with real LLM
        response = conversational_agent_with_real_llm.handle_indicator_explanation_request(
            message, "sma", {"window": 20}
        )
        
        # Check that we got a substantive response
        assert response["sender"] == "conversational_agent"
        assert response["recipient"] == "user"
        assert len(response["content"]["text"]) > 100  # Expect a detailed explanation
        assert "moving average" in response["content"]["text"].lower()