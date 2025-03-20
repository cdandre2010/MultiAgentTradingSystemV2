import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

from src.agents.base import Agent
from src.agents.validation_agent import ValidationAgent


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    mock = MagicMock()
    mock.generate.return_value = "The strategy parameters have been validated."
    
    # Create a side effect function that returns different values based on inputs
    def extract_json_side_effect(prompt):
        if "lookback_period\": 14" in prompt:
            # Valid parameters should return no errors
            return {
                "errors": [],
                "suggestions": ["Consider using a threshold of 0.03 for more balanced results"]
            }
        else:
            # Invalid parameters should return errors
            return {
                "errors": ["Lookback period should be at least 10 days"],
                "suggestions": ["Consider using 14 days which is standard"]
            }
    
    mock.extract_json.side_effect = extract_json_side_effect
    return mock


@pytest.fixture
def validation_agent(mock_llm):
    """Create a ValidationAgent instance with a mock LLM."""
    with patch('src.agents.validation_agent.get_llm', return_value=mock_llm):
        return ValidationAgent()


def test_agent_initialization(validation_agent):
    """Test that the agent initializes correctly."""
    assert validation_agent.name == "validation_agent"
    assert validation_agent.llm is not None
    assert validation_agent.validation_rules is not None


def test_parameter_validation(validation_agent):
    """Test parameter validation with valid and invalid parameters."""
    # Test invalid parameter (lookback_period too small)
    message = {
        "message_id": "test_id",
        "timestamp": datetime.utcnow().isoformat(),
        "sender": "conversational_agent",
        "recipient": "validation_agent",
        "message_type": "validation_request",
        "content": {
            "strategy_params": {
                "strategy_type": "momentum",
                "parameters": {
                    "lookback_period": 3,  # Below minimum of 10
                    "threshold": 0.05
                }
            }
        },
        "context": {"session_id": "test_session"}
    }
    
    response = validation_agent.process(message, {})
    
    # Check that validation results are correct
    assert response["message_type"] == "validation_result"
    assert response["recipient"] == "conversational_agent"
    assert response["content"]["is_valid"] is False
    assert len(response["content"]["errors"]) > 0
    # Modified to handle case-insensitive "lookback period" instead of "lookback_period"
    assert "lookback" in response["content"]["errors"][0].lower()
    
    # Test valid parameters
    message["content"]["strategy_params"]["parameters"]["lookback_period"] = 14
    response = validation_agent.process(message, {})
    
    # Check that validation passes
    assert response["message_type"] == "validation_result"
    assert response["content"]["is_valid"] is True


def test_strategy_completeness_validation(validation_agent):
    """Test validation of a complete vs. incomplete strategy."""
    # Test incomplete strategy (missing required parameter)
    message = {
        "message_id": "test_id",
        "timestamp": datetime.utcnow().isoformat(),
        "sender": "conversational_agent",
        "recipient": "validation_agent",
        "message_type": "validation_request",
        "content": {
            "strategy_params": {
                "strategy_type": "momentum",
                "parameters": {
                    # Missing lookback_period
                    "threshold": 0.05
                }
            }
        },
        "context": {"session_id": "test_session"}
    }
    
    response = validation_agent.process(message, {})
    
    # Check that validation detects missing parameter
    assert response["message_type"] == "validation_result"
    assert response["content"]["is_valid"] is False
    assert len(response["content"]["errors"]) > 0
    assert "required parameter" in response["content"]["errors"][0].lower() or \
           "lookback_period" in response["content"]["errors"][0].lower()
    
    # Test complete strategy with all required parameters
    message["content"]["strategy_params"]["parameters"]["lookback_period"] = 14
    response = validation_agent.process(message, {})
    
    # Check that validation passes for complete strategy
    assert response["message_type"] == "validation_result"
    assert response["content"]["is_valid"] is True


def test_validation_with_llm_consistency_check(validation_agent, mock_llm):
    """Test that the agent uses the LLM for logical consistency checking."""
    # Override the side_effect with a direct return value for this test
    mock_llm.extract_json.side_effect = None
    mock_llm.extract_json.return_value = {
        "errors": ["RSI threshold of 90 is too extreme for entry conditions"],
        "suggestions": ["Consider using a more moderate threshold like 70"]
    }
    
    # Test strategy with logical inconsistency
    message = {
        "message_id": "test_id",
        "timestamp": datetime.utcnow().isoformat(),
        "sender": "conversational_agent",
        "recipient": "validation_agent",
        "message_type": "validation_request",
        "content": {
            "strategy_params": {
                "strategy_type": "rsi",
                "parameters": {
                    "period": 14,
                    "overbought": 90,  # This is very extreme
                    "oversold": 10
                }
            }
        },
        "context": {"session_id": "test_session"}
    }
    
    response = validation_agent.process(message, {})
    
    # Check that LLM was called with appropriate prompt
    mock_llm.extract_json.assert_called_once()
    call_args = mock_llm.extract_json.call_args[0][0]
    assert "evaluate" in call_args.lower()
    assert "consistency" in call_args.lower()
    assert "rsi" in call_args.lower()
    
    # Verify response contains LLM's suggestions
    assert response["content"]["is_valid"] is False
    assert "threshold" in str(response["content"]["errors"]).lower() or \
           "90" in str(response["content"]["errors"]).lower()
    assert "moderate" in str(response["content"]["suggestions"]).lower() or \
           "70" in str(response["content"]["suggestions"]).lower()


def test_state_based_validation(validation_agent):
    """Test validation using strategy parameters from state."""
    # Test that the agent can retrieve strategy parameters from state
    # when they're not in the message
    message = {
        "message_id": "test_id",
        "timestamp": datetime.utcnow().isoformat(),
        "sender": "conversational_agent",
        "recipient": "validation_agent",
        "message_type": "validation_request",
        "content": {},  # No strategy_params in content
        "context": {"session_id": "test_session"}
    }
    
    # Create state with strategy parameters
    state = {
        "current_strategy": {
            "strategy_type": "moving_average_crossover",
            "parameters": {
                "fast_period": 5,
                "slow_period": 10  # Below recommended minimum of 20
            }
        }
    }
    
    response = validation_agent.process(message, state)
    
    # Verify validation was performed using state data
    assert response["message_type"] == "validation_result"
    assert "slow_period" in str(response["content"]).lower() or \
           "10" in str(response["content"]).lower()


def test_error_handling(validation_agent):
    """Test handling of invalid message types and formats."""
    # Test unsupported message type
    message = {
        "message_id": "test_id",
        "timestamp": datetime.utcnow().isoformat(),
        "sender": "conversational_agent",
        "recipient": "validation_agent",
        "message_type": "unknown_type",
        "content": {},
        "context": {"session_id": "test_session"}
    }
    
    response = validation_agent.process(message, {})
    
    # Verify error response
    assert response["message_type"] == "error"
    assert "unsupported message type" in response["content"]["text"].lower()
    
    # Test with no strategy parameters
    message = {
        "message_id": "test_id",
        "timestamp": datetime.utcnow().isoformat(),
        "sender": "conversational_agent",
        "recipient": "validation_agent",
        "message_type": "validation_request",
        "content": {},  # No strategy_params
        "context": {"session_id": "test_session"}
    }
    
    response = validation_agent.process(message, {})  # Empty state
    
    # Verify appropriate error response
    assert response["message_type"] == "error"
    assert "no strategy parameters" in response["content"]["text"].lower()