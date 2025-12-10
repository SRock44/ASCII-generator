"""Diagram generator for flowcharts and architecture diagrams."""
from ai.client import AIClient
from ai.prompts import DIAGRAM_PROMPT, CODEBASE_ANALYSIS_PROMPT
from cache import Cache
from rate_limiter import RateLimiter
from renderer import Renderer


class DiagramGenerator:
    """Generator for flowcharts and architecture diagrams."""
    
    def __init__(self, ai_client: AIClient, cache: Cache = None, rate_limiter: RateLimiter = None):
        """
        Initialize diagram generator.
        
        Args:
            ai_client: AI client instance
            cache: Optional cache instance
            rate_limiter: Optional rate limiter instance
        """
        self.ai_client = ai_client
        self.cache = cache or Cache()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.renderer = Renderer()
    
    def generate(self, prompt: str, use_cache: bool = True, is_codebase: bool = False, orientation: str = "top-to-bottom") -> str:
        """
        Generate diagram from prompt.

        Args:
            prompt: User prompt describing the diagram
            use_cache: Whether to use cache
            is_codebase: Whether this is a codebase analysis diagram
            orientation: Diagram orientation - "top-to-bottom" or "left-to-right"

        Returns:
            Generated diagram
        """
        # Check cache first (include orientation in cache key)
        cache_key = f"{'diagram_codebase' if is_codebase else 'diagram'}_{orientation}"
        if use_cache:
            cached = self.cache.get(prompt, cache_key)
            if cached:
                return cached

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

        # Cache result
        if use_cache:
            self.cache.set(prompt, cache_key, result)

        return result

    def generate_stream(self, prompt: str, use_cache: bool = True, is_codebase: bool = False, orientation: str = "top-to-bottom"):
        """
        Generate diagram from prompt with streaming (yields chunks as they arrive).

        Args:
            prompt: User prompt describing the diagram
            use_cache: Whether to use cache
            is_codebase: Whether this is a codebase analysis diagram
            orientation: Diagram orientation - "top-to-bottom" or "left-to-right"

        Yields:
            Text chunks as they are generated
        """
        # Check cache first (include orientation in cache key)
        cache_key = f"{'diagram_codebase' if is_codebase else 'diagram'}_{orientation}"
        if use_cache:
            cached = self.cache.get(prompt, cache_key)
            if cached:
                # Yield cached content in one chunk
                yield cached
                return

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
        if hasattr(self.ai_client, 'generate_stream'):
            for chunk in self.ai_client.generate_stream(prompt, system_prompt):
                accumulated += chunk
                yield chunk

            # Cache result
            if use_cache:
                self.cache.set(prompt, cache_key, accumulated)
        else:
            # Fallback to non-streaming if not supported
            result = self.ai_client.generate(prompt, system_prompt)
            if use_cache:
                self.cache.set(prompt, cache_key, result)
            yield result


