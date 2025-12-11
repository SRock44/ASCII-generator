"""Factory for creating AI clients based on provider selection."""
from typing import Optional
from .client import AIClient
import config


def create_ai_client(provider: Optional[str] = None, mode: str = "art") -> AIClient:
    """
    Create an AI client based on provider selection.

    Args:
        provider: Provider name ('gemini', 'groq', or None for auto-select)
        mode: Validation mode - "art", "chart", or "diagram" (defaults to "art")

    Returns:
        AIClient instance

    Raises:
        ValueError: If no provider is available or specified provider is invalid
    """
    if provider:
        provider = provider.lower()

        if provider == "gemini":
            from .gemini import GeminiClient
            if not config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is required but not set")
            return GeminiClient(mode=mode)

        elif provider == "groq":
            from .groq_client import GroqClient
            if not config.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is required but not set")
            return GroqClient(mode=mode)

        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'gemini' or 'groq'")

    # Auto-select: use first available provider in lexicographical order
    available_providers = []

    if config.GEMINI_API_KEY:
        available_providers.append(("gemini", "GeminiClient"))
    if config.GROQ_API_KEY:
        available_providers.append(("groq", "GroqClient"))

    if not available_providers:
        raise ValueError("No AI provider API keys found. Please set GEMINI_API_KEY or GROQ_API_KEY in your .env file")

    # Sort lexicographically and use first one
    available_providers.sort()
    provider_name, client_class = available_providers[0]

    if provider_name == "gemini":
        from .gemini import GeminiClient
        return GeminiClient(mode=mode)
    elif provider_name == "groq":
        from .groq_client import GroqClient
        return GroqClient(mode=mode)
    else:
        raise ValueError(f"Unexpected provider: {provider_name}")

