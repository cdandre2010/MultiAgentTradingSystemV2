"""
Unit tests for the Strategy Repository module.
"""

import pytest
from src.database.strategy_repository import StrategyRepository, ComponentType, ComponentFilter
from src.database.connection import db_manager
from src.database.init import init_neo4j
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def setup_neo4j():
    """Set up Neo4j test database."""
    logger.info("Setting up Neo4j test database...")
    try:
        # Try connecting to Neo4j first
        if db_manager.neo4j_driver is None:
            logger.info("No Neo4j driver, connecting...")
            db_manager.connect_neo4j()
        
        if db_manager.neo4j_driver is None:
            logger.error("Failed to connect to Neo4j database")
            pytest.skip("Failed to connect to Neo4j database, skipping tests")
            return False
            
        # Test the connection
        try:
            with db_manager.neo4j_driver.session() as session:
                # Check if we have nodes
                result = session.run("MATCH (n) RETURN count(n) as count")
                count = result.single()["count"]
                logger.info(f"Connected to Neo4j database, found {count} nodes")
                
                # If we have nodes, we can skip initialization
                if count > 0:
                    logger.info("Neo4j database already has data, skipping initialization")
                    return True
        except Exception as e:
            logger.error(f"Error testing Neo4j connection: {e}")
            pytest.skip(f"Neo4j connection test failed: {e}, skipping tests")
            return False
        
        # Initialize only if we need to
        logger.info("Initializing Neo4j with enhanced schema...")
        success = init_neo4j(enhanced=True)
        
        if not success:
            logger.error("Neo4j initialization failed")
            pytest.skip("Neo4j initialization failed, skipping tests")
            return False
            
        logger.info("Neo4j setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Exception during Neo4j setup: {e}")
        pytest.skip(f"Neo4j setup exception: {e}, skipping tests")
        return False


@pytest.fixture
def repo(setup_neo4j):
    """Create a strategy repository instance."""
    return StrategyRepository()


class TestStrategyRepository:
    """Test class for StrategyRepository."""
    
    def test_get_components(self, repo):
        """Test retrieving components by type."""
        # Get strategy types
        strategies = repo.get_components(ComponentType.STRATEGY_TYPE)
        assert len(strategies) > 0
        assert "name" in strategies[0]
        assert "description" in strategies[0]
        
        # Get indicators
        indicators = repo.get_components(ComponentType.INDICATOR)
        assert len(indicators) > 0
        assert "name" in indicators[0]
        assert "description" in indicators[0]
        
        # Test with filters
        filters = ComponentFilter(category="trend", limit=2)
        trend_indicators = repo.get_components(ComponentType.INDICATOR, filters)
        
        # Check that we got at most 2 results
        assert len(trend_indicators) <= 2
        
        # Check that all returned indicators are trend indicators
        if trend_indicators:
            assert all(i.get("category") == "trend" for i in trend_indicators)
    
    def test_get_component_by_name(self, repo):
        """Test retrieving a specific component by name."""
        # Get RSI indicator
        rsi = repo.get_component_by_name(ComponentType.INDICATOR, "RSI")
        assert rsi is not None
        assert rsi["name"] == "RSI"
        assert "description" in rsi
        
        # Test with non-existent component
        non_existent = repo.get_component_by_name(ComponentType.INDICATOR, "NonExistentIndicator")
        assert non_existent is None
    
    def test_get_indicators_for_strategy_type(self, repo):
        """Test retrieving indicators for a strategy type."""
        # Get indicators for momentum strategy
        indicators = repo.get_indicators_for_strategy_type("momentum")
        assert len(indicators) > 0
        
        # Check that we have compatibility scores
        assert "compatibility_score" in indicators[0] or "strength" in indicators[0]
        
        # Test with min_strength filter
        high_strength_indicators = repo.get_indicators_for_strategy_type("momentum", min_strength=0.9)
        for indicator in high_strength_indicators:
            score = indicator.get("compatibility_score", 0)
            assert score >= 0.9
    
    def test_get_position_sizing_for_strategy_type(self, repo):
        """Test retrieving position sizing methods for a strategy type."""
        # Get position sizing for trend_following strategy
        position_sizing = repo.get_position_sizing_for_strategy_type("trend_following")
        assert len(position_sizing) > 0
        
        # Check that we have compatibility scores
        assert "compatibility_score" in position_sizing[0] or "strength" in position_sizing[0]
    
    def test_get_risk_management_for_strategy_type(self, repo):
        """Test retrieving risk management techniques for a strategy type."""
        # Get risk management for breakout strategy
        risk_management = repo.get_risk_management_for_strategy_type("breakout")
        assert len(risk_management) > 0
        
        # Check that we have compatibility scores
        assert "compatibility_score" in risk_management[0] or "strength" in risk_management[0]
    
    def test_get_parameters_for_indicator(self, repo):
        """Test retrieving parameters for an indicator."""
        # Get parameters for RSI
        parameters = repo.get_parameters_for_indicator("RSI")
        assert len(parameters) > 0
        
        # Check that we have parameter details
        assert "name" in parameters[0]
        assert "default_value" in parameters[0]
        assert "is_required" in parameters[0]
    
    def test_get_compatible_frequencies_for_instrument(self, repo):
        """Test retrieving compatible frequencies for an instrument."""
        # Get frequencies for BTCUSDT
        frequencies = repo.get_compatible_frequencies_for_instrument("BTCUSDT")
        assert len(frequencies) > 0
        
        # Check that we have compatibility scores
        assert "compatibility_score" in frequencies[0] or "strength" in frequencies[0]
    
    def test_get_available_data_sources_for_instrument(self, repo):
        """Test retrieving available data sources for an instrument."""
        # Get data sources for BTCUSDT
        sources = repo.get_available_data_sources_for_instrument("BTCUSDT")
        assert len(sources) > 0
        
        # Check that we have data quality information
        assert "data_quality" in sources[0]
        assert "name" in sources[0]
    
    def test_calculate_strategy_compatibility_score(self, repo):
        """Test calculating strategy compatibility score."""
        # Calculate score for a strategy configuration
        score, details = repo.calculate_strategy_compatibility_score(
            strategy_type="trend_following",
            indicators=["EMA", "ATR"],
            position_sizing="volatility",
            risk_management=["trailing_stop"],
            trade_management=["partial_exits"]
        )
        
        # Check that we have a score
        assert 0 <= score <= 1
        
        # Check that we have detailed scores
        assert "overall" in details
        assert "component_scores" in details
        assert "explanations" in details
    
    def test_get_strategy_recommendations(self, repo):
        """Test getting strategy recommendations."""
        # Get recommendations for crypto on 1h timeframe
        recommendations = repo.get_strategy_recommendations(
            instrument_type="crypto",
            timeframe="medium_term",
            experience_level="intermediate",
            risk_profile="moderate"
        )
        assert len(recommendations) > 0
        
        # Check that we have recommendation details
        assert "strategy_type" in recommendations[0]
        assert "compatibility_score" in recommendations[0]
        assert "recommended_indicators" in recommendations[0]
    
    def test_generate_strategy_template(self, repo):
        """Test generating a strategy template."""
        # Generate template for trend_following on BTCUSDT at 1h
        template = repo.generate_strategy_template(
            strategy_type="trend_following",
            instrument="BTCUSDT",
            timeframe="1h"
        )
        
        # Check that we have template details
        assert "name" in template
        assert "strategy_type" in template
        assert "instrument" in template
        assert "component_indicators" in template
        assert "component_position_sizing" in template
        assert "component_risk_management" in template