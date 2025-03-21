import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

from src.agents.base import Agent
from src.agents.conversational_agent import ConversationalAgent


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    mock = MagicMock()
    mock.generate.return_value = "I'll help you create a trading strategy."
    mock.extract_json.return_value = {
        "strategy_type": "momentum",
        "parameters": {
            "lookback_period": 14,
            "threshold": 0.05
        }
    }
    return mock


@pytest.fixture
def conversational_agent(mock_llm):
    """Create a ConversationalAgent instance with a mock LLM."""
    with patch('src.agents.conversational_agent.get_llm', return_value=mock_llm):
        return ConversationalAgent()


def test_agent_initialization(conversational_agent):
    """Test that the agent initializes correctly."""
    assert conversational_agent.name == "conversational_agent"
    assert conversational_agent.llm is not None


def test_agent_processes_user_message(conversational_agent, mock_llm):
    """Test that the agent can process a user message."""
    message = {
        "message_id": "test_id",
        "timestamp": datetime.utcnow().isoformat(),
        "sender": "user",
        "recipient": "conversational_agent",
        "message_type": "request",
        "content": {"text": "I want to create a momentum strategy"},
        "context": {"session_id": "test_session"}
    }
    
    response = conversational_agent.process_message(message)
    
    # Check that LLM was called with appropriate prompt
    mock_llm.generate.assert_called_once()
    call_args = mock_llm.generate.call_args[0][0]
    assert "momentum strategy" in call_args
    
    # Verify response structure
    assert response["message_id"] != message["message_id"]  # Should be a new ID
    assert response["sender"] == "conversational_agent"
    assert response["recipient"] == "user"
    assert response["message_type"] == "response"
    assert "text" in response["content"]
    assert response["context"]["session_id"] == "test_session"


def test_agent_extracts_strategy_parameters(conversational_agent, mock_llm):
    """Test that the agent can extract strategy parameters from a conversation."""
    # Mock is already set up in the fixture to return strategy parameters
    
    message = {
        "message_id": "test_id",
        "timestamp": datetime.utcnow().isoformat(),
        "sender": "user",
        "recipient": "conversational_agent",
        "message_type": "request",
        "content": {"text": "I want a momentum strategy that looks back 14 days with a 5% threshold"},
        "context": {"session_id": "test_session", "extract_params": True}
    }
    
    response = conversational_agent.process_message(message)
    
    # Verify the response contains strategy parameters
    assert "strategy_params" in response["content"]
    assert response["content"]["strategy_params"] is not None


def test_agent_handles_validation_feedback(conversational_agent, mock_llm):
    """Test that the agent can process validation feedback."""
    # First we need to set the agent state to have an ongoing strategy creation
    conversational_agent.session_state = {
        "test_session": {
            "conversation_history": [
                {"role": "user", "content": "I want to create a momentum strategy"},
                {"role": "assistant", "content": "What parameters would you like to use?"},
                {"role": "user", "content": "5 day lookback with 5% threshold"}
            ],
            "current_strategy": {
                "strategy_type": "momentum",
                "parameters": {
                    "lookback_period": 5,  # Invalid - too short
                    "threshold": 0.05
                }
            }
        }
    }
    
    # Mock the validation feedback message
    message = {
        "message_id": "test_id",
        "timestamp": datetime.utcnow().isoformat(),
        "sender": "validation_agent",
        "recipient": "conversational_agent",
        "message_type": "feedback",
        "content": {
            "is_valid": False,
            "errors": [
                {"parameter": "lookback_period", "error": "Lookback period should be at least 10 days"}
            ],
            "suggestions": [
                {"parameter": "lookback_period", "suggestion": "Consider using 14 days which is standard"}
            ]
        },
        "context": {"session_id": "test_session"}
    }
    
    # Mock the LLM to return a response addressing the validation issues
    mock_llm.generate.return_value = "I see there's an issue with your lookback period. It should be at least 10 days."
    
    # Process the feedback message
    response = conversational_agent.process_message(message)
    
    # Verify response addresses validation issues and correct recipient
    assert response["content"]["text"] == "I see there's an issue with your lookback period. It should be at least 10 days."
    assert response["recipient"] == "user"
    assert response["message_type"] == "response"
    
    # Verify the conversation history was updated
    assert len(conversational_agent.session_state["test_session"]["conversation_history"]) == 4
    assert conversational_agent.session_state["test_session"]["conversation_history"][-1]["role"] == "assistant"