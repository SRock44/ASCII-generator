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
                # If cached result exists but hasn't been validated, validate it now
                # This handles the case where streaming cached a raw result
                if cached and not cached.startswith("ERROR_CODE:"):
                    try:
                        cleaned_result, validation = self.validator.validate_and_clean(cached, strict=False)
                        # Update cache with cleaned version
                        self.cache.set(prompt, "chart", cleaned_result)
                        return cleaned_result
                    except Exception:
                        # If validation fails, return cached as-is
                        return cached
                return cached

        # Wait for rate limit
        self.rate_limiter.wait_if_needed()

        # Generate using AI
        result = self.ai_client.generate(prompt, CHART_PROMPT)
        
        # Check for errors before validation
        if result.startswith("ERROR_CODE:"):
            return result
        
        # Validate and clean the result (preserves color hints for colorizer)
        try:
            cleaned_result, validation = self.validator.validate_and_clean(result, strict=False)
        except Exception as e:
            # If validation fails, return raw result rather than blocking
            if use_cache:
                self.cache.set(prompt, "chart", result)
            return result

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
            try:
                # Stream chunks from AI
                stream_done = False
                for chunk in generate_stream_method(prompt, CHART_PROMPT):
                    # Check for errors in chunk
                    if chunk and chunk.startswith("ERROR_CODE:"):
                        # Error occurred, yield it and stop
                        yield chunk
                        return
                    accumulated += chunk
                    yield chunk
                    stream_done = True
                
                # Stream completed - generator exhausted, renderer's loop will exit
                # IMPORTANT: Do NOT do validation here - it blocks the CLI
                # Just cache the raw result immediately (validation happens on retrieval if needed)
                if stream_done and accumulated.strip() and not accumulated.startswith("ERROR_CODE:"):
                    if use_cache:
                        # Cache raw result immediately - no validation to avoid blocking
                        self.cache.set(prompt, "chart", accumulated)
                
                # Generator exhausted - exit immediately so renderer's loop exits
                return
            except StopIteration:
                # Generator exhausted normally - this is expected
                if accumulated.strip() and not accumulated.startswith("ERROR_CODE:"):
                    if use_cache:
                        self.cache.set(prompt, "chart", accumulated)
                return
            except Exception as e:
                # Handle any exceptions during streaming
                error_msg = f"ERROR_CODE: STREAM_ERROR\nERROR_MESSAGE: {str(e)}"
                yield error_msg
                return
        else:
            # Fallback to non-streaming if not supported
            try:
                result = self.ai_client.generate(prompt, CHART_PROMPT)
                if use_cache:
                    self.cache.set(prompt, "chart", result)
                yield result
                return
            except Exception as e:
                error_msg = f"ERROR_CODE: GENERATION_ERROR\nERROR_MESSAGE: {str(e)}"
                yield error_msg
                return





