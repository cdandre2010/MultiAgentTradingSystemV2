"""
Conversational Agent for the Multi-Agent Trading System.
This agent handles natural language interactions with users.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from .base import Agent
from ..utils.llm import get_llm


class ConversationalAgent(Agent):
    """
    Agent responsible for natural language conversations with users.
    Interprets user intent, extracts strategy parameters, and explains concepts.
    """
    
    def __init__(self):
        """Initialize the Conversational Agent."""
        super().__init__(name="conversational_agent")
        self.llm = get_llm()
        self.session_state = {}  # Track conversation state by session
    
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
                strategy_params = self.llm.extract_json(prompt, system_prompt)
                
                # Store extracted parameters in session state
                self.session_state[session_id]["current_strategy"] = strategy_params
                
                # Create response with extracted parameters
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
            # Generate conversational response
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
        
        # Build prompt for LLM to generate a response to the user
        prompt = f"""
        I'm helping a user create a trading strategy with these parameters:
        {json.dumps(current_strategy, indent=2)}
        
        The validation system found these issues:
        Errors: {json.dumps(errors, indent=2)}
        Suggestions: {json.dumps(suggestions, indent=2)}
        
        Please create a helpful response that explains the validation issues to the user
        in a friendly way. Suggest corrections based on the validation feedback.
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