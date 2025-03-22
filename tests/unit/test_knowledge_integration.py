"""
Test the knowledge graph integration with agents.
"""
import unittest
import logging
import os
import sys
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.agents.knowledge_integration import (
    get_knowledge_recommendations,
    enhance_validation_feedback,
    enhance_strategy_with_knowledge
)


class TestKnowledgeIntegration(unittest.TestCase):
    """Test the knowledge integration with Neo4j."""
    
    def setUp(self):
        """Set up the test case."""
        # Create a mock strategy repository
        self.mock_repository = MagicMock()
        
        # Setup mock repository responses
        self.mock_repository.get_indicators_for_strategy_type.return_value = [
            {"name": "RSI", "explanation": "RSI is ideal for momentum strategies."},
            {"name": "MACD", "explanation": "MACD helps identify trend direction and strength."},
            {"name": "Bollinger Bands", "explanation": "Bollinger Bands help identify volatility."}
        ]
        
        self.mock_repository.get_position_sizing_for_strategy_type.return_value = [
            {"name": "percent_of_equity", "explanation": "Common position sizing method."}
        ]
        
        self.mock_repository.get_risk_management_for_strategy_type.return_value = [
            {"name": "stop_loss", "explanation": "Essential risk management technique."},
            {"name": "trailing_stop", "explanation": "Follows price movement to lock in profits."}
        ]
        
        self.mock_repository.get_parameters_for_indicator.return_value = [
            {"name": "period", "default_value": 14}
        ]
    
    def test_get_knowledge_recommendations(self):
        """Test getting knowledge recommendations."""
        # Test with valid strategy type
        recommendations = get_knowledge_recommendations(self.mock_repository, "momentum")
        
        # Verify results
        self.assertEqual(len(recommendations["indicators"]), 3)
        self.assertEqual(recommendations["indicators"][0], "RSI")
        self.assertEqual(recommendations["position_sizing"], "percent_of_equity")
        self.assertEqual(len(recommendations["risk_management"]), 2)
        self.assertEqual(recommendations["risk_management"][0], "stop_loss")
        self.assertIn("RSI is ideal", recommendations["explanation"])
        
        # Test with error handling
        self.mock_repository.get_indicators_for_strategy_type.side_effect = Exception("Test error")
        recommendations = get_knowledge_recommendations(self.mock_repository, "momentum")
        self.assertIn("Error", recommendations["explanation"])
    
    def test_enhance_validation_feedback(self):
        """Test enhancing validation feedback."""
        # Test with validation errors
        errors = ["Parameter 'lookback_period' value 2 is below minimum 5"]
        suggestions = enhance_validation_feedback(self.mock_repository, errors, "momentum")
        
        # Verify results
        self.assertTrue(len(suggestions) > 0)
        self.assertIn("Based on our trading knowledge", suggestions[0])
        
        # Test with different error type
        errors = ["Parameter 'threshold' value 0.001 is below minimum 0.01"]
        suggestions = enhance_validation_feedback(self.mock_repository, errors, "momentum")
        self.assertTrue(len(suggestions) > 0)
        self.assertIn("default parameters", suggestions[0])
    
    def test_enhance_strategy_with_knowledge(self):
        """Test enhancing strategy with knowledge."""
        # Test with basic strategy params
        strategy_params = {"strategy_type": "momentum", "parameters": {"lookback_period": 10}}
        enhanced = enhance_strategy_with_knowledge(self.mock_repository, strategy_params)
        
        # Verify results
        self.assertIn("indicators", enhanced)
        self.assertIn("position_sizing", enhanced)
        self.assertIn("risk_management", enhanced)
        self.assertEqual(enhanced["strategy_type"], "momentum")
        self.assertEqual(enhanced.get("parameters"), {"lookback_period": 10})


if __name__ == "__main__":
    unittest.main()