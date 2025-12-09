"""Caching system for generated ASCII art."""
import hashlib
import json
from pathlib import Path
from typing import Optional
import config


class Cache:
    """Simple file-based cache for generated content."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize cache.
        
        Args:
            cache_dir: Cache directory path (defaults to config)
        """
        self.cache_dir = cache_dir or config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.enabled = config.CACHE_ENABLED
    
    def _get_cache_key(self, prompt: str, generator_type: str) -> str:
        """
        Generate cache key from prompt and generator type.
        
        Args:
            prompt: User prompt
            generator_type: Type of generator (ascii_art, chart, diagram)
            
        Returns:
            Cache key (filename)
        """
        key_string = f"{generator_type}:{prompt}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, prompt: str, generator_type: str) -> Optional[str]:
        """
        Get cached content.
        
        Args:
            prompt: User prompt
            generator_type: Type of generator
            
        Returns:
            Cached content or None if not found
        """
        if not self.enabled:
            return None
        
        cache_file = self.cache_dir / f"{self._get_cache_key(prompt, generator_type)}.txt"
        
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding="utf-8")
            except Exception:
                return None
        
        return None
    
    def set(self, prompt: str, generator_type: str, content: str):
        """
        Cache content.
        
        Args:
            prompt: User prompt
            generator_type: Type of generator
            content: Content to cache
        """
        if not self.enabled:
            return
        
        cache_file = self.cache_dir / f"{self._get_cache_key(prompt, generator_type)}.txt"
        
        try:
            cache_file.write_text(content, encoding="utf-8")
        except Exception:
            pass  # Silently fail if cache write fails
    
    def clear(self):
        """Clear all cached content."""
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.txt"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass

