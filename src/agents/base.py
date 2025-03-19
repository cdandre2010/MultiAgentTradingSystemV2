from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import uuid
from datetime import datetime

class Agent(ABC):
    """
    Base class for all agents in the trading strategy system.
    
    Provides common functionality for message handling, state management,
    and inter-agent communication.
    """
    
    def __init__(self, name: str):
        """
        Initialize the agent.
        
        Args:
            name: Unique identifier for the agent
        """
        self.name = name
    
    def create_message(
        self, 
        recipient: str, 
        message_type: str, 
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized message to send to another agent.
        
        Args:
            recipient: Name of the target agent
            message_type: Type of message (request, response, error, etc.)
            content: Message content as a dictionary
            context: Optional context information

        Returns:
            Dictionary containing the formatted message
        """
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        return {
            "message_id": message_id,
            "timestamp": timestamp,
            "sender": self.name,
            "recipient": recipient,
            "message_type": message_type,
            "content": content,
            "context": context or {},
        }
    
    @abstractmethod
    def process(self, message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message.
        
        Args:
            message: The message to process
            state: Current conversation state

        Returns:
            Response message
        """
        pass
    
    def validate_message(self, message: Dict[str, Any]) -> bool:
        """
        Validate that a message has the required structure.
        
        Args:
            message: Message to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["message_id", "timestamp", "sender", "recipient", "message_type", "content"]
        return all(field in message for field in required_fields)
    
    def log_message(self, message: Dict[str, Any], direction: str = "received") -> None:
        """
        Log a message for debugging purposes.
        
        Args:
            message: Message to log
            direction: "received" or "sent"
        """
        # In a real implementation, this would use a proper logger
        print(f"[{self.name}] {direction.upper()} from {message['sender']}: {message['message_type']}")
        # Don't log entire content in production to avoid exposing sensitive data
        # print(json.dumps(message, indent=2))