"""Abstract AI client interface."""
from abc import ABC, abstractmethod
from typing import Optional


class AIClient(ABC):
    """Abstract base class for AI clients."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text response from AI model.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI client is available and configured."""
        pass






