"""Chart generator for bar charts, line charts, etc."""
from typing import Optional
from ai.client import AIClient
from ai.prompts import CHART_PROMPT
from cache import Cache
from rate_limiter import RateLimiter
from renderer import Renderer
from validators import ASCIIValidator


class ChartGenerator:
    """Generator for terminal-based charts."""
    
    def __init__(self, ai_client: AIClient, cache: Optional[Cache] = None, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize chart generator.

        Args:
            ai_client: AI client instance
            cache: Optional cache instance
            rate_limiter: Optional rate limiter instance
        """
        self.ai_client = ai_client
        self.cache = cache or Cache()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.validator = ASCIIValidator(mode="chart")
        self.renderer = Renderer()
    
    def generate(self, prompt: str, use_cache: bool = True) -> str:
        """
        Generate chart from prompt.

        Args:
            prompt: User prompt describing the chart and data
            use_cache: Whether to use cache

        Returns:
            Generated chart
        """
        # Check cache first
        if use_cache:
            cached = self.cache.get(prompt, "chart")
            if cached:
                return cached

        # Wait for rate limit
        self.rate_limiter.wait_if_needed()

        # Generate using AI
        result = self.ai_client.generate(prompt, CHART_PROMPT)
        
        # Validate and clean the result (preserves color hints for colorizer)
        cleaned_result, validation = self.validator.validate_and_clean(result, strict=False)

        # Cache cleaned result
        if use_cache:
            self.cache.set(prompt, "chart", cleaned_result)

        return cleaned_result

    def generate_stream(self, prompt: str, use_cache: bool = True):
        """
        Generate chart from prompt with streaming (yields chunks as they arrive).

        Args:
            prompt: User prompt describing the chart and data
            use_cache: Whether to use cache

        Yields:
            Text chunks as they are generated
        """
        # Check cache first
        if use_cache:
            cached = self.cache.get(prompt, "chart")
            if cached:
                # Yield cached content in one chunk
                yield cached
                return

        # Wait for rate limit
        self.rate_limiter.wait_if_needed()

        # Generate using AI with streaming
        accumulated = ""
        generate_stream_method = getattr(self.ai_client, 'generate_stream', None)
        if generate_stream_method:
            for chunk in generate_stream_method(prompt, CHART_PROMPT):
                accumulated += chunk
                yield chunk

            # Validate and clean the final result (preserves color hints)
            cleaned_result, validation = self.validator.validate_and_clean(accumulated, strict=False)
            
            # Cache cleaned result
            if use_cache:
                self.cache.set(prompt, "chart", cleaned_result)
        else:
            # Fallback to non-streaming if not supported
            result = self.ai_client.generate(prompt, CHART_PROMPT)
            if use_cache:
                self.cache.set(prompt, "chart", result)
            yield result





