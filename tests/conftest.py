import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.main import app


@pytest.fixture
def test_client():
    """
    Create a test client for FastAPI application.
    
    This fixture allows tests to make requests to the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
def mock_master_agent():
    """Create a mock master agent for testing."""
    from unittest.mock import MagicMock
    
    mock_agent = MagicMock()
    mock_agent.name = "master_agent"
    mock_agent.process.return_value = {
        "message_id": "msg_test",
        "timestamp": "2023-06-01T12:00:00Z",
        "sender": "master_agent",
        "recipient": "user",
        "message_type": "response",
        "content": {"message": "This is a test response"},
        "context": {}
    }
    
    return mock_agent


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user_test123",
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "created_at": "2023-06-01T12:00:00Z"
    }


@pytest.fixture
def sample_strategy_data():
    """Sample strategy data for testing."""
    return {
        "id": "strat_test123",
        "name": "Test Momentum Strategy",
        "user_id": "user_test123",
        "strategy_type": "momentum",
        "instrument": "BTCUSDT",
        "frequency": "1h",
        "indicators": [
            {
                "name": "RSI",
                "parameters": {"period": 14}
            }
        ],
        "conditions": [
            {
                "type": "entry",
                "logic": "RSI < 30"
            },
            {
                "type": "exit",
                "logic": "RSI > 70"
            }
        ],
        "created_at": "2023-06-01T12:00:00Z",
        "updated_at": "2023-06-01T12:00:00Z"
    }