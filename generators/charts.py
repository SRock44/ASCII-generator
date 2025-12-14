"""Chart generator for bar charts, line charts, etc."""
from typing import Optional
from ai.client import AIClient
from ai.prompts import CHART_PROMPT
from session_context import SessionContext
from rate_limiter import RateLimiter
from renderer import Renderer
from validators import ASCIIValidator


class ChartGenerator:
    """Generator for terminal-based charts."""

    def __init__(self, ai_client: AIClient, session_context: Optional[SessionContext] = None, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize chart generator.

        Args:
            ai_client: AI client instance
            session_context: Optional session context for conversation history
            rate_limiter: Optional rate limiter instance
        """
        self.ai_client = ai_client
        self.session_context = session_context
        self.rate_limiter = rate_limiter or RateLimiter()
        self.validator = ASCIIValidator(mode="chart")
        self.renderer = Renderer()
    
    def generate(self, prompt: str) -> str:
        """
        Generate chart from prompt.

        Args:
            prompt: User prompt describing the chart and data

        Returns:
            Generated chart
        """
        # Wait for rate limit
        self.rate_limiter.wait_if_needed()

        # Generate using AI
        result = self.ai_client.generate(prompt, CHART_PROMPT)

        # Check for errors before validation
        if result.startswith("ERROR_CODE:"):
            return result

        # Validate and clean the result
        try:
            cleaned_result, validation = self.validator.validate_and_clean(result, strict=False)
        except Exception:
            # If validation fails, return raw result
            if self.session_context:
                self.session_context.add_interaction(prompt, result, "chart", success=False)
            return result

        # Record in session context
        if self.session_context:
            self.session_context.add_interaction(prompt, cleaned_result, "chart", success=True)

        return cleaned_result

    def generate_stream(self, prompt: str):
        """
        Generate chart from prompt with streaming (yields chunks as they arrive).

        Args:
            prompt: User prompt describing the chart and data

        Yields:
            Text chunks as they are generated
        """
        # Wait for rate limit
        self.rate_limiter.wait_if_needed()

        # Generate using AI with streaming
        accumulated = ""
        generate_stream_method = getattr(self.ai_client, 'generate_stream', None)
        if generate_stream_method:
            try:
                # Stream chunks from AI
                for chunk in generate_stream_method(prompt, CHART_PROMPT):
                    # Check for errors in chunk
                    if chunk and chunk.startswith("ERROR_CODE:"):
                        yield chunk
                        return
                    accumulated += chunk
                    yield chunk

                # Record in session context
                if accumulated.strip() and not accumulated.startswith("ERROR_CODE:"):
                    if self.session_context:
                        self.session_context.add_interaction(prompt, accumulated, "chart", success=True)
                return
            except Exception as e:
                error_msg = f"ERROR_CODE: STREAM_ERROR\nERROR_MESSAGE: {str(e)}"
                yield error_msg
                return
        else:
            # Fallback to non-streaming if not supported
            try:
                result = self.ai_client.generate(prompt, CHART_PROMPT)
                if self.session_context:
                    self.session_context.add_interaction(prompt, result, "chart", success=True)
                yield result
                return
            except Exception as e:
                error_msg = f"ERROR_CODE: GENERATION_ERROR\nERROR_MESSAGE: {str(e)}"
                yield error_msg
                return





