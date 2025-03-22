"""
Knowledge Graph Integration for the Multi-Agent Trading System.

This module provides helper functions to integrate the Neo4j knowledge graph
with the agent system, enabling knowledge-driven strategy creation and validation.
"""

from typing import Dict, Any, List, Optional
import logging
import json

# Set up logging
logger = logging.getLogger(__name__)


def get_knowledge_recommendations(strategy_repository, strategy_type: str) -> Dict[str, Any]:
    """
    Get knowledge-driven recommendations for a strategy type.
    
    Args:
        strategy_repository: Repository for Neo4j operations
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


def enhance_validation_feedback(
    strategy_repository, 
    errors: List[str], 
    strategy_type: str
) -> List[str]:
    """
    Enhance validation feedback with knowledge-driven suggestions.
    
    Args:
        strategy_repository: Repository for Neo4j operations
        errors: List of validation errors
        strategy_type: Strategy type
        
    Returns:
        List of knowledge-driven suggestions
    """
    knowledge_suggestions = []
    
    try:
        # Generate suggestions based on error types
        for error in errors:
            if "lookback_period" in error:
                # Get parameter recommendations from knowledge graph
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
                
        # If no specific error-based suggestions, provide general recommendation
        if not knowledge_suggestions and strategy_type:
            template = strategy_repository.generate_strategy_template(
                strategy_type=strategy_type,
                instrument="generic",
                timeframe="daily"
            )
            if template:
                knowledge_suggestions.append(
                    f"Consider using our pre-defined template for {strategy_type} strategies, "
                    f"which includes recommended indicators ({', '.join(template.get('component_indicators', [])[:3])}) "
                    f"and position sizing methods ({template.get('component_position_sizing', 'percent')})."
                )
    except Exception as e:
        logger.error(f"Error enhancing validation feedback: {e}")
        
    return knowledge_suggestions


def enhance_llm_prompt_with_knowledge(
    prompt: str,
    strategy_repository,
    strategy_type: str
) -> str:
    """
    Enhance an LLM prompt with knowledge from the knowledge graph.
    
    Args:
        prompt: Original LLM prompt
        strategy_repository: Repository for Neo4j operations
        strategy_type: Strategy type
        
    Returns:
        Enhanced prompt with knowledge
    """
    try:
        # Get knowledge recommendations
        recommendations = get_knowledge_recommendations(strategy_repository, strategy_type)
        
        # Enhance prompt with knowledge
        knowledge_prompt = f"""
        {prompt}
        
        Use these knowledge-based recommendations from our trading knowledge graph:
        Recommended indicators for {strategy_type}: {', '.join(recommendations['indicators'])}
        Recommended position sizing: {recommendations['position_sizing']}
        Recommended risk management: {', '.join(recommendations['risk_management'])}
        
        Rationale: {recommendations['explanation']}
        
        Incorporate this knowledge into your response if relevant.
        """
        
        return knowledge_prompt
    except Exception as e:
        logger.error(f"Error enhancing prompt with knowledge: {e}")
        return prompt  # Return original prompt on error