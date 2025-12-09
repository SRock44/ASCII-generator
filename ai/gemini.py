"""Google Gemini AI client implementation."""
import google.generativeai as genai
from typing import Optional
from .client import AIClient
import config


class GeminiClient(AIClient):
    """Google Gemini AI client."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to config)
            model: Model name (defaults to config)
        """
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model_name = model or config.GEMINI_MODEL
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text response using Gemini.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated text response
        """
        try:
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser request: {prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                }
            )
            
            # Extract text from response
            if response.text:
                # Clean up any markdown code blocks that might wrap the output
                text = response.text.strip()
                if text.startswith("```"):
                    # Remove markdown code blocks
                    lines = text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].strip() == "```":
                        lines = lines[:-1]
                    text = "\n".join(lines).strip()
                return text
            else:
                return "Error: No response generated"
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if Gemini client is available."""
        return bool(self.api_key and self.model)

