"""
Conversational Agent for the Multi-Agent Trading System.
This agent handles natural language interactions with users.
"""
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Set up logging
logger = logging.getLogger(__name__)

from .base import Agent
from ..utils.llm import get_llm
from ..database.strategy_repository import get_strategy_repository
from .knowledge_integration import (
    get_knowledge_recommendations,
    enhance_validation_feedback,
    enhance_strategy_with_knowledge
)


class ConversationalAgent(Agent):
    """
    Agent responsible for natural language conversations with users.
    Interprets user intent, extracts strategy parameters, and explains concepts.
    Uses Neo4j knowledge graph to provide knowledge-driven recommendations.
    """
    
    def __init__(self):
        """Initialize the Conversational Agent."""
        super().__init__(name="conversational_agent")
        self.llm = get_llm()
        self.session_state = {}  # Track conversation state by session
        self.strategy_repository = get_strategy_repository()  # Get Neo4j repository
    
    def process(self, message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message according to the Agent interface.
        
        Args:
            message: The message to process
            state: Current conversation state
            
        Returns:
            Response message
        """
        # Forward to internal process_message method
        return self.process_message(message)
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message and generate a response.
        
        Args:
            message: The incoming message to process
            
        Returns:
            Response message
        """
        message_type = message["message_type"]
        sender = message["sender"]
        content = message["content"]
        context = message.get("context", {})
        session_id = context.get("session_id", "default")
        
        # Initialize session state if it doesn't exist
        if session_id not in self.session_state:
            self.session_state[session_id] = {
                "conversation_history": [],
                "current_strategy": None
            }
            
        # Add message to conversation history
        self.session_state[session_id]["conversation_history"].append({
            "role": "user" if sender == "user" else "system",
            "content": content.get("text", str(content))
        })
        
        # Process based on message type and sender
        if message_type == "request" and sender == "user":
            return self._handle_user_request(message, session_id)
        elif message_type == "feedback" and sender == "validation_agent":
            return self._handle_validation_feedback(message, session_id)
        else:
            # Default response for unhandled message types
            return self.create_message(
                recipient=sender,
                message_type="error",
                content={"text": f"Unsupported message type: {message_type} from {sender}"},
                context=context
            )
    
    def _handle_user_request(self, message: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Handle a user request message.
        
        Args:
            message: The user request message
            session_id: The session ID
            
        Returns:
            Response message
        """
        content = message["content"]
        context = message.get("context", {})
        extract_params = context.get("extract_params", False)
        use_knowledge_graph = context.get("use_knowledge_graph", True)  # Default to using knowledge graph
        
        user_text = content.get("text", "")
        
        # Prepare prompt based on conversation history
        history = self.session_state[session_id]["conversation_history"]
        prompt = self._build_prompt(user_text, history)
        
        if extract_params:
            # Generate structured parameters from user input
            system_prompt = """
            Extract the trading strategy parameters from the user's request.
            Respond with ONLY a JSON object containing the strategy type and parameters.
            For example:
            {
                "strategy_type": "momentum",
                "parameters": {
                    "lookback_period": 14,
                    "threshold": 0.05
                }
            }
            """
            try:
                # Extract basic parameters from user request
                strategy_params = self.llm.extract_json(prompt, system_prompt)
                
                # Enhance with knowledge if configured
                if use_knowledge_graph and self.strategy_repository:
                    try:
                        # Enhance strategy with knowledge-driven recommendations
                        enhanced_strategy = enhance_strategy_with_knowledge(
                            self.strategy_repository,
                            strategy_params
                        )
                        
                        # Get recommendations for explanation
                        recommendations = get_knowledge_recommendations(
                            self.strategy_repository,
                            enhanced_strategy.get("strategy_type", "")
                        )
                        
                        # Create enhanced response
                        knowledge_enhanced_response = {
                            "text": "I've extracted your strategy parameters and enhanced them with recommendations from our trading knowledge graph.",
                            "strategy_params": enhanced_strategy,
                            "knowledge_recommendations": recommendations,
                            "knowledge_driven": True
                        }
                        
                        # Store enhanced parameters in session state
                        self.session_state[session_id]["current_strategy"] = enhanced_strategy
                        self.session_state[session_id]["knowledge_recommendations"] = recommendations
                        
                        return self.create_message(
                            recipient="user",
                            message_type="response",
                            content=knowledge_enhanced_response,
                            context={"session_id": session_id}
                        )
                    except Exception as e:
                        logger.error(f"Error enhancing strategy with knowledge: {e}")
                        # Fall back to basic response on error
                
                # Store standard parameters in session state
                self.session_state[session_id]["current_strategy"] = strategy_params
                
                # Return standard response if no knowledge enhancement
                return self.create_message(
                    recipient="user",
                    message_type="response",
                    content={
                        "text": "I've extracted the parameters for your strategy.",
                        "strategy_params": strategy_params
                    },
                    context={"session_id": session_id}
                )
            except Exception as e:
                return self.create_message(
                    recipient="user",
                    message_type="error",
                    content={"text": f"Error extracting strategy parameters: {str(e)}"},
                    context={"session_id": session_id}
                )
        else:
            # For conversational responses, try to enhance with knowledge when appropriate
            if use_knowledge_graph and self.strategy_repository and "strategy" in user_text.lower():
                try:
                    # Extract strategy type from text if possible
                    extract_prompt = """
                    Extract just the trading strategy type from the user's message.
                    Respond with ONLY a JSON object containing the strategy_type.
                    For example: {"strategy_type": "momentum"}
                    If no specific strategy type is mentioned, return {"strategy_type": ""}
                    """
                    strategy_info = self.llm.extract_json(user_text, extract_prompt)
                    strategy_type = strategy_info.get("strategy_type", "")
                    
                    if strategy_type:
                        # Get knowledge recommendations
                        recommendations = get_knowledge_recommendations(
                            self.strategy_repository,
                            strategy_type
                        )
                        
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
                        
                        # Generate knowledge-enhanced response
                        response_text = self.llm.generate(knowledge_prompt)
                    else:
                        # Generate standard response if no strategy type detected
                        response_text = self.llm.generate(prompt)
                except Exception as e:
                    logger.error(f"Error generating knowledge-enhanced response: {e}")
                    # Fall back to standard response on error
                    response_text = self.llm.generate(prompt)
            else:
                # Generate standard conversational response
                response_text = self.llm.generate(prompt)
            
            return self.create_message(
                recipient="user",
                message_type="response",
                content={"text": response_text},
                context={"session_id": session_id}
            )
    
    def _handle_validation_feedback(self, message: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Handle validation feedback from the validation agent.
        
        Args:
            message: The validation feedback message
            session_id: The session ID
            
        Returns:
            Response message to the user explaining validation issues
        """
        content = message["content"]
        is_valid = content.get("is_valid", False)
        errors = content.get("errors", [])
        suggestions = content.get("suggestions", [])
        
        # Get current strategy from session state
        current_strategy = self.session_state[session_id].get("current_strategy", {})
        
        # If validation failed and we have Neo4j integration, use knowledge-driven suggestions
        knowledge_suggestions = []
        if not is_valid and self.strategy_repository:
            try:
                # Get strategy type
                strategy_type = current_strategy.get("strategy_type")
                if strategy_type:
                    # Get knowledge-driven suggestions using the integration module
                    knowledge_suggestions = enhance_validation_feedback(
                        self.strategy_repository, 
                        errors, 
                        strategy_type
                    )
                    
                    # Store suggestions in session state for future reference
                    self.session_state[session_id]["knowledge_suggestions"] = knowledge_suggestions
            except Exception as e:
                logger.error(f"Error getting knowledge graph suggestions: {e}")
        
        # Build prompt for LLM to generate a response to the user
        prompt = f"""
        I'm helping a user create a trading strategy with these parameters:
        {json.dumps(current_strategy, indent=2)}
        
        The validation system found these issues:
        Errors: {json.dumps(errors, indent=2)}
        Suggestions: {json.dumps(suggestions, indent=2)}
        
        Knowledge-based suggestions:
        {json.dumps(knowledge_suggestions, indent=2)}
        
        Please create a helpful response that explains the validation issues to the user
        in a friendly way. Suggest corrections based on the validation feedback.
        If there are knowledge-based suggestions, incorporate them into your response.
        """
        
        # Generate response addressing validation issues
        response_text = self.llm.generate(prompt)
        
        # Add response to conversation history
        self.session_state[session_id]["conversation_history"].append({
            "role": "assistant",
            "content": response_text
        })
        
        return self.create_message(
            recipient="user",
            message_type="response",
            content={"text": response_text},
            context={"session_id": session_id}
        )
    
    def _build_prompt(self, user_text: str, history: list) -> str:
        """
        Build a prompt for the LLM based on conversation history.
        
        Args:
            user_text: The latest user message
            history: The conversation history
            
        Returns:
            Formatted prompt for LLM
        """
        # Convert history to formatted string if needed
        conversation_context = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in history[-5:] if msg['role'] != 'system'  # Only include last 5 messages
        ])
        
        return f"""
        Previous conversation:
        {conversation_context}
        
        User's latest message: {user_text}
        
        Please respond to the user's latest message, considering the conversation context.
        Focus on helping them create a trading strategy.
        """
        
    def _get_knowledge_recommendations(self, strategy_type: str) -> Dict[str, Any]:
        """
        Get knowledge-driven recommendations for a strategy type.
        
        Args:
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
            indicators = self.strategy_repository.get_indicators_for_strategy_type(
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
            position_sizing = self.strategy_repository.get_position_sizing_for_strategy_type(
                strategy_type=strategy_type,
                min_compatibility=0.7,
                limit=1
            )
            if position_sizing and position_sizing[0]["name"]:
                recommendations["position_sizing"] = position_sizing[0]["name"]
                
                # Get explanation
                if position_sizing[0].get("explanation"):
                    recommendations["explanation"] += f"Position sizing rationale: {position_sizing[0]['explanation']} "
            
            # Get risk management
            risk_management = self.strategy_repository.get_risk_management_for_strategy_type(
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
            print(f"Error getting knowledge recommendations: {e}")
            recommendations["explanation"] = f"Error retrieving recommendations: {str(e)}"
            
        return recommendations