"""Diagram generator for flowcharts and architecture diagrams."""
from typing import Optional
from ai.client import AIClient
from ai.prompts import DIAGRAM_PROMPT, CODEBASE_ANALYSIS_PROMPT
from session_context import SessionContext
from rate_limiter import RateLimiter
from renderer import Renderer


class DiagramGenerator:
    """Generator for flowcharts and architecture diagrams."""

    def __init__(self, ai_client: AIClient, session_context: Optional[SessionContext] = None, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize diagram generator.

        Args:
            ai_client: AI client instance
            session_context: Optional session context for conversation history
            rate_limiter: Optional rate limiter instance
        """
        self.ai_client = ai_client
        self.session_context = session_context
        self.rate_limiter = rate_limiter or RateLimiter()
        self.renderer = Renderer()
    
    def generate(self, prompt: str, is_codebase: bool = False, orientation: str = "top-to-bottom") -> str:
        """
        Generate diagram from prompt.

        Args:
            prompt: User prompt describing the diagram
            is_codebase: Whether this is a codebase analysis diagram
            orientation: Diagram orientation - "top-to-bottom" or "left-to-right"

        Returns:
            Generated diagram
        """
        # Wait for rate limit
        self.rate_limiter.wait_if_needed()

        # Choose appropriate prompt
        if is_codebase:
            system_prompt = CODEBASE_ANALYSIS_PROMPT
        else:
            from ai.prompts import get_diagram_prompt
            system_prompt = get_diagram_prompt(orientation)

        # Generate using AI
        result = self.ai_client.generate(prompt, system_prompt)

        # Record in session context
        generator_type = "diagram_codebase" if is_codebase else "diagram"
        if self.session_context:
            self.session_context.add_interaction(prompt, result, generator_type, success=not result.startswith("ERROR_CODE:"))

        return result

    def generate_stream(self, prompt: str, is_codebase: bool = False, orientation: str = "top-to-bottom"):
        """
        Generate diagram from prompt with streaming (yields chunks as they arrive).

        Args:
            prompt: User prompt describing the diagram
            is_codebase: Whether this is a codebase analysis diagram
            orientation: Diagram orientation - "top-to-bottom" or "left-to-right"

        Yields:
            Text chunks as they are generated
        """
        # Wait for rate limit
        self.rate_limiter.wait_if_needed()

        # Choose appropriate prompt
        if is_codebase:
            system_prompt = CODEBASE_ANALYSIS_PROMPT
        else:
            from ai.prompts import get_diagram_prompt
            system_prompt = get_diagram_prompt(orientation)

        # Generate using AI with streaming
        accumulated = ""
        generator_type = "diagram_codebase" if is_codebase else "diagram"

        if hasattr(self.ai_client, 'generate_stream'):
            for chunk in self.ai_client.generate_stream(prompt, system_prompt):
                accumulated += chunk
                yield chunk

            # Record in session context
            if self.session_context and accumulated.strip():
                self.session_context.add_interaction(prompt, accumulated, generator_type, success=not accumulated.startswith("ERROR_CODE:"))
        else:
            # Fallback to non-streaming if not supported
            result = self.ai_client.generate(prompt, system_prompt)
            if self.session_context:
                self.session_context.add_interaction(prompt, result, generator_type, success=not result.startswith("ERROR_CODE:"))
            yield result


