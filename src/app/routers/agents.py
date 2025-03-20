"""
Agent router for the Multi-Agent Trading System.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
import uuid

from ..auth import get_current_user
from ...models.user import User
from ...agents.conversational_agent import ConversationalAgent
from ...agents.validation_agent import ValidationAgent
from ...agents.master_agent import MasterAgent

router = APIRouter()

# Initialize agents
conversational_agent = ConversationalAgent()
validation_agent = ValidationAgent()
master_agent = MasterAgent()

# Register the specialized agents with the master agent
master_agent.specialized_agents["conversation"] = conversational_agent
master_agent.specialized_agents["validation"] = validation_agent

class MessageRequest(BaseModel):
    """
    Message request model.
    """
    text: str = Field(..., description="The message text from the user")
    extract_params: bool = Field(False, description="Whether to extract strategy parameters from the message")
    session_id: Optional[str] = Field(None, description="Session ID to continue a conversation")

class MessageResponse(BaseModel):
    """
    Message response model.
    """
    text: str = Field(..., description="The response text")
    strategy_params: Optional[Dict[str, Any]] = Field(None, description="Extracted strategy parameters if requested")
    session_id: str = Field(..., description="Session ID for the conversation")

class StreamRequest(BaseModel):
    """
    Stream request model for streaming conversation.
    """
    text: str = Field(..., description="The message text from the user")
    session_id: Optional[str] = Field(None, description="Session ID to continue a conversation")
    
class ValidationRequest(BaseModel):
    """
    Request model for strategy validation.
    """
    strategy_params: Dict[str, Any] = Field(..., description="The strategy parameters to validate")
    session_id: Optional[str] = Field(None, description="Session ID to continue a conversation")

class ValidationResponse(BaseModel):
    """
    Response model for strategy validation.
    """
    is_valid: bool = Field(..., description="Whether the strategy is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors if any")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings if any")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    session_id: str = Field(..., description="Session ID for the conversation")

@router.post("/conversational", response_model=MessageResponse)
async def chat_with_agent(
    message: MessageRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Send a message to the conversational agent.
    """
    # Create session ID if not provided
    session_id = message.session_id or f"session_{current_user.id}_{uuid.uuid4().hex[:8]}"
    
    # Create agent message using the master agent format
    agent_message = {
        "message_id": f"msg_{uuid.uuid4().hex[:8]}",
        "timestamp": "",  # Will be filled by agent
        "sender": "user",
        "recipient": "master_agent",
        "message_type": "request",
        "content": message.text,
        "context": {
            "session_id": session_id,
            "extract_params": message.extract_params,
            "user_id": current_user.id
        }
    }
    
    # Process message through the master agent
    state = {"user_id": current_user.id, "session_id": session_id}
    response = master_agent.process(agent_message, state)
    
    # Check for errors
    if response["message_type"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response["content"]
        )
    
    # Return response
    return MessageResponse(
        text=response["content"].get("text", ""),
        strategy_params=response["content"].get("strategy_params"),
        session_id=session_id
    )

@router.post("/direct/conversational", response_model=MessageResponse)
async def direct_chat_with_conversational_agent(
    message: MessageRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Send a message directly to the conversational agent (bypassing the master agent).
    """
    # Create session ID if not provided
    session_id = message.session_id or f"session_{current_user.id}_{uuid.uuid4().hex[:8]}"
    
    # Create agent message
    agent_message = {
        "message_id": f"msg_{uuid.uuid4().hex[:8]}",
        "timestamp": "",  # Will be filled by agent
        "sender": "user",
        "recipient": "conversational_agent",
        "message_type": "request",
        "content": {"text": message.text},
        "context": {
            "session_id": session_id,
            "extract_params": message.extract_params,
            "user_id": current_user.id
        }
    }
    
    # Process message through the conversational agent directly
    response = conversational_agent.process_message(agent_message)
    
    # Return response
    return MessageResponse(
        text=response["content"]["text"],
        strategy_params=response["content"].get("strategy_params"),
        session_id=session_id
    )

@router.post("/validate", response_model=ValidationResponse)
async def validate_strategy(
    validation_request: ValidationRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Validate a strategy using the validation agent.
    """
    # Create session ID if not provided
    session_id = validation_request.session_id or f"session_{current_user.id}_{uuid.uuid4().hex[:8]}"
    
    # Create agent message
    agent_message = {
        "message_id": f"msg_{uuid.uuid4().hex[:8]}",
        "timestamp": "",  # Will be filled by agent
        "sender": "user",
        "recipient": "validation_agent",
        "message_type": "validation_request",
        "content": {"strategy_params": validation_request.strategy_params},
        "context": {
            "session_id": session_id,
            "user_id": current_user.id
        }
    }
    
    # Process message through the validation agent directly
    response = validation_agent.process(agent_message, {})
    
    # Return response
    return ValidationResponse(
        is_valid=response["content"]["is_valid"],
        errors=response["content"].get("errors", []),
        warnings=response["content"].get("warnings", []),
        suggestions=response["content"].get("suggestions", []),
        session_id=session_id
    )