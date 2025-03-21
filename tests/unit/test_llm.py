"""
Test module for LLM utilities.
"""
import pytest
from unittest.mock import patch, MagicMock
import json

from src.utils.llm import ClaudeLLM, get_llm


@pytest.fixture
def mock_anthropic():
    """Create a mock Anthropic client."""
    mock = MagicMock()
    
    # Mock messages response
    message_response = MagicMock()
    message_response.content = [MagicMock()]
    message_response.content[0].text = "This is a test response from Claude"
    
    mock.messages.create.return_value = message_response
    return mock


@pytest.fixture
def claude_llm(mock_anthropic):
    """Create a ClaudeLLM instance with a mock Anthropic client."""
    with patch('anthropic.Anthropic', return_value=mock_anthropic):
        llm = ClaudeLLM(api_key="dummy-api-key")
        llm.client = mock_anthropic
        return llm


def test_get_llm():
    """Test that get_llm returns a ClaudeLLM instance."""
    with patch('src.utils.llm.ClaudeLLM') as mock_claude:
        mock_claude.return_value = "mock_llm_instance"
        llm = get_llm()
        assert llm == "mock_llm_instance"


def test_generate(claude_llm, mock_anthropic):
    """Test generating text with Claude."""
    response = claude_llm.generate("Tell me about trading strategies")
    
    # Verify the response
    assert response == "This is a test response from Claude"
    
    # Verify the API was called with correct parameters
    mock_anthropic.messages.create.assert_called_once()
    call_args = mock_anthropic.messages.create.call_args[1]
    assert call_args["model"] == claude_llm.model
    assert "Tell me about trading strategies" in call_args["messages"][0]["content"]


def test_extract_json(claude_llm, mock_anthropic):
    """Test extracting JSON from Claude's response."""
    # Set up the mock to return valid JSON
    test_json = {"strategy_type": "momentum", "parameters": {"lookback_period": 14}}
    mock_anthropic.messages.create.return_value.content[0].text = json.dumps(test_json)
    
    # Test extraction
    result = claude_llm.extract_json("Extract params from: RSI strategy with 14 day lookback")
    
    # Verify the result
    assert result == test_json


def test_extract_json_invalid(claude_llm, mock_anthropic):
    """Test handling invalid JSON in Claude's response."""
    # Set up the mock to return invalid JSON
    mock_anthropic.messages.create.return_value.content[0].text = "This is not valid JSON"
    
    # Test extraction with invalid JSON
    result = claude_llm.extract_json("Extract params from: RSI strategy with 14 day lookback")
    
    # Verify it handles the error gracefully
    assert "error" in result
    assert "raw_response" in result
    assert result["raw_response"] == "This is not valid JSON"