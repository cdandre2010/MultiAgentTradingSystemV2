"""
LLM utilities for interfacing with Claude via Anthropic API.
"""
from typing import Optional, Dict, Any, List
from anthropic import Anthropic
from ..app.config import settings


def get_llm():
    """
    Get an instance of the Claude LLM client.
    
    Returns:
        LLM client instance
    """
    return ClaudeLLM(api_key=settings.ANTHROPIC_API_KEY)


class ClaudeLLM:
    """Claude LLM client wrapper."""
    
    def __init__(self, api_key: str):
        """
        Initialize Claude LLM client.
        
        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-7-sonnet-20250219"
        self.api_calls_made = 0
        self.last_api_call_time = None
        self.last_api_call_model = None
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"ClaudeLLM initialized with API key: {'*'*8 + api_key[-4:] if api_key else 'None'}")
        logger.info(f"Using model: {self.model}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from Claude.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt to guide the model's behavior
            
        Returns:
            Generated response text
        """
        if not system_prompt:
            system_prompt = (
                "You are an AI assistant specializing in trading strategy creation and analysis. "
                "Be precise, helpful, and explain financial concepts clearly."
            )
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Making API call to Anthropic with model: {self.model}")
        
        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Increment the API call counter
        self.api_calls_made += 1
        
        logger.info(f"API call #{self.api_calls_made} complete. Response received with {len(response.content[0].text)} characters.")
        
        if hasattr(response, 'usage') and hasattr(response.usage, 'request_time'):
            self.last_api_call_time = response.usage.request_time
        else:
            self.last_api_call_time = "Unknown"
            
        self.last_api_call_model = self.model
        
        return response.content[0].text
    
    def extract_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract structured data in JSON format from Claude's response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt to guide the model's behavior
            
        Returns:
            Parsed JSON data
        """
        if not system_prompt:
            system_prompt = (
                "You are an AI assistant specializing in trading strategy creation and analysis. "
                "When asked to extract information, respond ONLY with a valid JSON object without any explanation."
            )
        
        response = self.generate(prompt, system_prompt)
        
        # Use a JSON parser to handle the response
        try:
            import json
            import re
            
            # If the response includes a code block with JSON, extract it
            json_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response, re.IGNORECASE)
            if json_block_match:
                json_str = json_block_match.group(1).strip()
                return json.loads(json_str)
            else:
                # Try to parse the full response as JSON
                return json.loads(response)
                
        except json.JSONDecodeError:
            # If parsing fails, return a default structure
            return {"error": "Failed to parse response as JSON", "raw_response": response}
    
    def get_api_stats(self) -> Dict[str, Any]:
        """
        Get statistics about API calls made.
        
        Returns:
            Dictionary with API call statistics
        """
        return {
            "total_calls": self.api_calls_made,
            "last_call_time": self.last_api_call_time,
            "model": self.last_api_call_model
        }