"""ASCII art generator."""
from typing import Optional
from ai.client import AIClient
from ai.prompts import ASCII_ART_PROMPT
from cache import Cache
from rate_limiter import RateLimiter
from renderer import Renderer
from validators import ASCIIValidator, ValidationResult


class ASCIIArtGenerator:
    """Generator for ASCII art."""

    def __init__(self, ai_client: AIClient, cache: Optional[Cache] = None, rate_limiter: Optional[RateLimiter] = None, max_retries: int = 2):
        """
        Initialize ASCII art generator.

        Args:
            ai_client: AI client instance
            cache: Optional cache instance
            rate_limiter: Optional rate limiter instance
            max_retries: Maximum number of retries with feedback (default: 2)
        """
        self.ai_client = ai_client
        self.cache = cache or Cache()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.validator = ASCIIValidator(mode="art")
        self.max_retries = max_retries
        # Don't create renderer here - create it with prompt context when needed

    def _build_feedback_prompt(self, original_prompt: str, validation: ValidationResult, previous_output: str) -> str:
        """
        Build a feedback prompt that includes validation errors for regeneration.
        
        Args:
            original_prompt: Original user prompt
            validation: Validation result with errors/warnings
            previous_output: The previous output that failed validation
            
        Returns:
            Enhanced prompt with feedback
        """
        feedback_lines = [
            f"Your previous attempt to generate ASCII art for '{original_prompt}' had quality issues:",
            ""
        ]
        
        # Add errors
        if validation.errors:
            feedback_lines.append("CRITICAL ISSUES FOUND:")
            for error in validation.errors:
                feedback_lines.append(f"- {error}")
            feedback_lines.append("")
        
        # Add warnings
        if validation.warnings:
            feedback_lines.append("WARNINGS:")
            for warning in validation.warnings:
                feedback_lines.append(f"- {warning}")
            feedback_lines.append("")
        
        # Add specific guidance
        feedback_lines.extend([
            "PLEASE REGENERATE with these corrections:",
            "1. Ensure VARIETY: Use different characters, patterns, and line structures",
            "2. Avoid repetition: Never repeat the same line pattern more than 4-5 times",
            "3. Add character diversity: Use a mix of letters, symbols, and structural elements",
            "4. Create RECOGNIZABLE shapes: The output must INSTANTLY be recognizable as the requested subject",
            "5. Include ICONIC ELEMENTS: Add distinctive features that make the subject clearly identifiable",
            "6. Vary line lengths: Don't make all lines the same length",
            "7. ENSURE SYMMETRY: For creatures, animals, and symmetrical objects, make sure both sides mirror each other perfectly",
            "8. Center your art: Count characters on left and right sides to ensure perfect balance",
            "9. AVOID ABSTRACT SHAPES: Create concrete, recognizable representations, not abstract patterns",
            "",
            f"Original request: {original_prompt}",
            "",
            "Generate NEW, IMPROVED ASCII art that is INSTANTLY RECOGNIZABLE as '{original_prompt}' and addresses all the issues above."
        ])
        
        # Add symmetry-specific feedback if asymmetry was detected
        symmetry_warnings = [w for w in validation.warnings if "symmetry" in w.lower() or "balanced" in w.lower()]
        if symmetry_warnings:
            feedback_lines.insert(-3, "")
            feedback_lines.insert(-3, "SYMMETRY ISSUE DETECTED:")
            feedback_lines.insert(-3, "- Your art is not symmetrical - both left and right sides should mirror each other")
            feedback_lines.insert(-3, "- Count characters on each side of the center to ensure perfect balance")
            feedback_lines.insert(-3, "- Center your art properly - equal spacing and characters on both sides")
            feedback_lines.insert(-3, "")
        
        return "\n".join(feedback_lines)

    def _has_quality_issues(self, validation: ValidationResult) -> bool:
        """
        Check if validation result indicates quality issues that warrant retry.
        
        Args:
            validation: Validation result
            
        Returns:
            True if quality issues detected, False otherwise
        """
        # Check for critical quality errors
        quality_keywords = ["broken", "repetitive", "diversity", "recognizable", "variety"]
        for error in validation.errors:
            if any(keyword in error.lower() for keyword in quality_keywords):
                return True
        
        # Check for quality-related warnings if there are many lines
        if validation.warnings:
            quality_warnings = [w for w in validation.warnings 
                              if any(keyword in w.lower() for keyword in quality_keywords)]
            if quality_warnings:
                return True
        
        return False
    
    def generate(self, prompt: str, use_cache: bool = True) -> str:
        """
        Generate ASCII art from prompt with quality validation and retry on failure.

        Args:
            prompt: User prompt describing the art
            use_cache: Whether to use cache

        Returns:
            Generated ASCII art (validated and cleaned)
        """
        # Check cache first
        if use_cache:
            cached = self.cache.get(prompt, "ascii_art")
            if cached:
                return cached

        # Try generation with retries
        current_prompt = prompt
        last_result = None
        last_validation = None
        cleaned_result = ""  # Initialize to avoid unbound variable
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            # Wait for rate limit
            self.rate_limiter.wait_if_needed()

            # Generate using AI
            if attempt == 0:
                # First attempt: use original prompt
                result = self.ai_client.generate(current_prompt, ASCII_ART_PROMPT)
            else:
                # Retry: use feedback prompt
                if last_validation and last_result:
                    feedback_prompt = self._build_feedback_prompt(prompt, last_validation, last_result)
                    # Combine feedback with original system prompt
                    enhanced_system_prompt = f"{ASCII_ART_PROMPT}\n\n--- REGENERATION REQUEST WITH FEEDBACK ---\n{feedback_prompt}"
                    result = self.ai_client.generate(prompt, enhanced_system_prompt)
                else:
                    # Fallback if we don't have previous validation/result
                    result = self.ai_client.generate(current_prompt, ASCII_ART_PROMPT)
            
            # Validate and clean the result
            cleaned_result, validation = self.validator.validate_and_clean(result, strict=False)
            
            # Check if result is valid and has no quality issues
            if validation.is_valid and not self._has_quality_issues(validation):
                # Success! Cache and return
                if use_cache:
                    self.cache.set(prompt, "ascii_art", cleaned_result)
                return cleaned_result
            
            # Store for potential retry
            last_result = cleaned_result
            last_validation = validation
            
            # If this was the last attempt, return what we have (even if not perfect)
            if attempt >= self.max_retries:
                break

        # After all retries, return the best result we got (even if it has issues)
        # The validator has already cleaned it as much as possible
        final_result = last_result if last_result else cleaned_result
        if use_cache:
            self.cache.set(prompt, "ascii_art", final_result)
        
        return final_result

    def generate_stream(self, prompt: str, use_cache: bool = True):
        """
        Generate ASCII art from prompt with streaming (yields chunks as they arrive).
        Note: Streaming doesn't support retry with feedback (would break the stream).
        Quality validation happens after streaming completes.

        Args:
            prompt: User prompt describing the art
            use_cache: Whether to use cache

        Yields:
            Text chunks as they are generated
        """
        # Check cache first
        if use_cache:
            cached = self.cache.get(prompt, "ascii_art")
            if cached:
                # Yield cached content in one chunk
                yield cached
                return

        # Wait for rate limit
        self.rate_limiter.wait_if_needed()

        # Generate using AI with streaming
        accumulated = ""
        # Check if client supports streaming (using getattr to avoid type errors)
        generate_stream_method = getattr(self.ai_client, 'generate_stream', None)
        if generate_stream_method:
            for chunk in generate_stream_method(prompt, ASCII_ART_PROMPT):
                accumulated += chunk
                yield chunk

            # Validate and clean the final result
            cleaned_result, validation = self.validator.validate_and_clean(accumulated, strict=False)
            
            # Note: We can't retry during streaming, but we've cleaned the result
            # If quality is really poor, the user will see it, but at least it's cleaned
            
            # Cache cleaned result
            if use_cache:
                self.cache.set(prompt, "ascii_art", cleaned_result)
        else:
            # Fallback to non-streaming if not supported
            # Use the generate() method which has retry logic
            result = self.generate(prompt, use_cache=use_cache)
            yield result

