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
        
        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
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
            return json.loads(response)
        except json.JSONDecodeError:
            # If parsing fails, return a default structure
            return {"error": "Failed to parse response as JSON", "raw_response": response}