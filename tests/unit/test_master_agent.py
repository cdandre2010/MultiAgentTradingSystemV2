import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json
from datetime import datetime

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agents.master_agent import MasterAgent
from src.agents.base import Agent


class TestMasterAgent(unittest.TestCase):
    """Test cases for the Master Agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.master_agent = MasterAgent()
    
    def test_create_message(self):
        """Test message creation with proper format."""
        message = self.master_agent.create_message(
            recipient="test_agent",
            message_type="request",
            content={"action": "test"},
            context={"user_id": "user_123"}
        )
        
        # Check required fields
        self.assertIn("message_id", message)
        self.assertIn("timestamp", message)
        self.assertIn("sender", message)
        self.assertIn("recipient", message)
        self.assertIn("message_type", message)
        self.assertIn("content", message)
        self.assertIn("context", message)
        
        # Check values
        self.assertEqual(message["sender"], "master_agent")
        self.assertEqual(message["recipient"], "test_agent")
        self.assertEqual(message["message_type"], "request")
        self.assertEqual(message["content"], {"action": "test"})
        self.assertEqual(message["context"], {"user_id": "user_123"})
    
    def test_validate_message(self):
        """Test message validation."""
        # Valid message
        valid_message = {
            "message_id": "msg_12345",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sender": "test_agent",
            "recipient": "master_agent",
            "message_type": "request",
            "content": {"action": "test"}
        }
        
        # Invalid message (missing required fields)
        invalid_message = {
            "sender": "test_agent",
            "content": {"action": "test"}
        }
        
        self.assertTrue(self.master_agent.validate_message(valid_message))
        self.assertFalse(self.master_agent.validate_message(invalid_message))
    
    def test_route_message(self):
        """Test message routing to appropriate agent."""
        # For now our implementation always routes to conversation agent
        # This is a placeholder test
        state = {}
        
        # Test message about strategy creation
        result = self.master_agent.route_message(
            "I want to create a momentum strategy", 
            state
        )
        self.assertEqual(result, "conversation")
        
        # In a more complete implementation, we would test different routing
        # scenarios, but for now our implementation has a fixed return value


if __name__ == '__main__':
    unittest.main()