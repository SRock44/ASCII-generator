"""Session-based context system for maintaining conversation history."""
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Interaction:
    """Represents a single user interaction."""
    prompt: str
    result: str
    timestamp: datetime
    generator_type: str  # "art", "chart", "diagram", "logo"
    success: bool = True


class SessionContext:
    """
    Maintains session-based context from recent user interactions.
    This provides continuity and learning from previous inputs without
    the complexity and issues of file-based caching.
    """
    
    def __init__(self, max_interactions: int = 10, max_age_minutes: int = 60):
        """
        Initialize session context.
        
        Args:
            max_interactions: Maximum number of interactions to keep in memory
            max_age_minutes: Maximum age of interactions before they expire
        """
        self.max_interactions = max_interactions
        self.max_age_minutes = max_age_minutes
        self.interactions: List[Interaction] = []
    
    def add_interaction(self, prompt: str, result: str, generator_type: str, success: bool = True):
        """
        Add a new interaction to the session context.
        
        Args:
            prompt: User prompt
            result: Generated result
            generator_type: Type of generator used
            success: Whether the generation was successful
        """
        interaction = Interaction(
            prompt=prompt,
            result=result,
            timestamp=datetime.now(),
            generator_type=generator_type,
            success=success
        )
        
        self.interactions.append(interaction)
        self._cleanup_old_interactions()
    
    def get_recent_context(self, generator_type: Optional[str] = None, limit: int = 3) -> List[Interaction]:
        """
        Get recent interactions for context.
        
        Args:
            generator_type: Filter by generator type (None for all types)
            limit: Maximum number of interactions to return
            
        Returns:
            List of recent interactions, most recent first
        """
        self._cleanup_old_interactions()
        
        # Filter by generator type if specified
        filtered = self.interactions
        if generator_type:
            filtered = [i for i in self.interactions if i.generator_type == generator_type]
        
        # Return most recent interactions
        return filtered[-limit:] if len(filtered) > limit else filtered
    
    def get_context_summary(self, generator_type: Optional[str] = None) -> str:
        """
        Get a text summary of recent context for use in prompts.
        
        Args:
            generator_type: Filter by generator type (None for all types)
            
        Returns:
            Formatted context summary string
        """
        recent = self.get_recent_context(generator_type, limit=3)
        
        if not recent:
            return ""
        
        summary_parts = ["Recent context from this session:"]
        for interaction in recent:
            summary_parts.append(f"- User requested: {interaction.prompt[:50]}...")
            if interaction.success:
                summary_parts.append(f"  Generated: {len(interaction.result)} chars")
            else:
                summary_parts.append(f"  Result: Failed")
        
        return "\n".join(summary_parts)
    
    def clear(self):
        """Clear all interactions."""
        self.interactions.clear()
    
    def _cleanup_old_interactions(self):
        """Remove interactions that are too old or exceed the limit."""
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=self.max_age_minutes)
        
        # Remove expired interactions
        self.interactions = [
            i for i in self.interactions 
            if i.timestamp > cutoff_time
        ]
        
        # Limit to max_interactions (keep most recent)
        if len(self.interactions) > self.max_interactions:
            self.interactions = self.interactions[-self.max_interactions:]


