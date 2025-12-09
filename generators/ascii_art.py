"""ASCII art generator."""
from ai.client import AIClient
from ai.prompts import ASCII_ART_PROMPT
from cache import Cache
from rate_limiter import RateLimiter
from renderer import Renderer


class ASCIIArtGenerator:
    """Generator for ASCII art."""
    
    def __init__(self, ai_client: AIClient, cache: Cache = None, rate_limiter: RateLimiter = None):
        """
        Initialize ASCII art generator.
        
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
        Generate ASCII art from prompt.
        
        Args:
            prompt: User prompt describing the art
            use_cache: Whether to use cache
            
        Returns:
            Generated ASCII art
        """
        # Check cache first
        if use_cache:
            cached = self.cache.get(prompt, "ascii_art")
            if cached:
                return cached
        
        # Wait for rate limit
        self.rate_limiter.wait_if_needed()
        
        # Generate using AI
        result = self.ai_client.generate(prompt, ASCII_ART_PROMPT)
        
        # Cache result
        if use_cache:
            self.cache.set(prompt, "ascii_art", result)
        
        return result

