"""Chart generator for bar charts, line charts, etc."""
from ai.client import AIClient
from ai.prompts import CHART_PROMPT
from cache import Cache
from rate_limiter import RateLimiter
from renderer import Renderer


class ChartGenerator:
    """Generator for terminal-based charts."""
    
    def __init__(self, ai_client: AIClient, cache: Cache = None, rate_limiter: RateLimiter = None):
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
        
        # Cache result
        if use_cache:
            self.cache.set(prompt, "chart", result)
        
        return result



