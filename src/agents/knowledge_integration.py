"""
Knowledge integration for agents with Neo4j knowledge graph.

This module contains helper functions for integrating the Neo4j knowledge graph
with the agent system to provide knowledge-driven recommendations and validations.
"""

import logging
from typing import Dict, Any, List, Optional

# Set up logging
logger = logging.getLogger(__name__)


def get_knowledge_recommendations(strategy_repository, strategy_type: str) -> Dict[str, Any]:
    """
    Get knowledge-driven recommendations for a strategy type.
    
    Args:
        strategy_repository: Neo4j strategy repository instance
        strategy_type: Type of trading strategy
        
    Returns:
        Dictionary with recommendations
    """
    recommendations = {
        "indicators": [],
        "position_sizing": "",
        "risk_management": [],
        "explanation": ""
    }
    
    if not strategy_repository:
        return recommendations
    
    try:
        # Get recommended indicators
        indicators = strategy_repository.get_indicators_for_strategy_type(
            strategy_type=strategy_type, 
            min_strength=0.7,
            limit=3
        )
        if indicators:
            recommendations["indicators"] = [i["name"] for i in indicators]
            
            # Get explanation for first indicator
            if indicators[0].get("explanation"):
                recommendations["explanation"] += f"Indicator rationale: {indicators[0]['explanation']} "
        
        # Get position sizing
        position_sizing = strategy_repository.get_position_sizing_for_strategy_type(
            strategy_type=strategy_type,
            min_compatibility=0.7,
            limit=1
        )
        if position_sizing and len(position_sizing) > 0:
            recommendations["position_sizing"] = position_sizing[0]["name"]
            
            # Get explanation
            if position_sizing[0].get("explanation"):
                recommendations["explanation"] += f"Position sizing rationale: {position_sizing[0]['explanation']} "
        
        # Get risk management
        risk_management = strategy_repository.get_risk_management_for_strategy_type(
            strategy_type=strategy_type,
            min_compatibility=0.7,
            limit=2
        )
        if risk_management:
            recommendations["risk_management"] = [rm["name"] for rm in risk_management]
            
            # Get explanation
            if risk_management[0].get("explanation"):
                recommendations["explanation"] += f"Risk management rationale: {risk_management[0]['explanation']}"
                
    except Exception as e:
        logger.error(f"Error getting knowledge recommendations: {e}")
        recommendations["explanation"] = f"Error retrieving recommendations: {str(e)}"
        
    return recommendations


def enhance_validation_feedback(strategy_repository, errors: List[str], strategy_type: str) -> List[str]:
    """
    Generate knowledge-driven suggestions based on validation errors.
    
    Args:
        strategy_repository: Neo4j strategy repository instance
        errors: List of validation errors
        strategy_type: Strategy type
        
    Returns:
        List of knowledge-driven suggestions
    """
    if not strategy_repository:
        return []
        
    knowledge_suggestions = []
    
    try:
        for error in errors:
            if "lookback_period" in error or "period" in error:
                # Get indicator recommendations
                indicators = strategy_repository.get_indicators_for_strategy_type(strategy_type)
                if indicators:
                    knowledge_suggestions.append(
                        f"Based on our trading knowledge, the {strategy_type} strategy typically works best with these indicators: "
                        f"{', '.join([i['name'] for i in indicators[:3]])}"
                    )
            
            if "threshold" in error or "deviation" in error:
                # Add strategy-specific suggestions
                knowledge_suggestions.append(
                    f"For {strategy_type} strategies, consider using default parameters from our knowledge base. "
                    f"These parameters have been optimized based on historical performance."
                )
    except Exception as e:
        logger.error(f"Error enhancing validation feedback: {e}")
        
    return knowledge_suggestions


def enhance_strategy_with_knowledge(
    strategy_repository, 
    strategy_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enhance a strategy with knowledge-driven recommendations.
    
    Args:
        strategy_repository: Neo4j strategy repository instance
        strategy_params: Basic strategy parameters
        
    Returns:
        Enhanced strategy parameters
    """
    if not strategy_repository:
        return strategy_params
        
    strategy_type = strategy_params.get("strategy_type")
    if not strategy_type:
        return strategy_params
        
    try:
        # Get strategy recommendations
        recommendations = get_knowledge_recommendations(strategy_repository, strategy_type)
        
        # Add indicators with parameters
        indicators = []
        for indicator_name in recommendations["indicators"]:
            params = strategy_repository.get_parameters_for_indicator(indicator_name)
            indicator = {
                "name": indicator_name,
                "parameters": {p["name"]: p.get("default_value", 14) for p in params}
            }
            indicators.append(indicator)
            
        # Build enhanced strategy
        enhanced_strategy = {
            "strategy_type": strategy_type,
            "indicators": indicators,
            "position_sizing": recommendations["position_sizing"],
            "risk_management": recommendations["risk_management"],
            "explanation": recommendations["explanation"]
        }
        
        # Copy original parameters
        for key, value in strategy_params.items():
            if key not in enhanced_strategy:
                enhanced_strategy[key] = value
                
        return enhanced_strategy
    except Exception as e:
        logger.error(f"Error enhancing strategy with knowledge: {e}")
        return strategy_params