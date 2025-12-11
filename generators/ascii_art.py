"""ASCII art generator."""
from typing import Optional
import re
from ai.client import AIClient
from ai.prompts import ASCII_ART_PROMPT, LOGO_PROMPT
from cache import Cache
from rate_limiter import RateLimiter
from renderer import Renderer
from validators import ASCIIValidator, ValidationResult


class ASCIIArtGenerator:
    """Generator for ASCII art."""

    # Keywords that suggest logo/branding generation
    LOGO_KEYWORDS = [
        r'\blogo\b', r'\bbranding\b', r'\bbrand\b', r'\bcompany\b', r'\bcorporate\b',
        r'\btext\b', r'\bletter\b', r'\bletters\b', r'\bword\b', r'\bwords\b',
        r'\bname\b', r'\btitle\b', r'\bheader\b', r'\bbanner\b', r'\bsign\b',
        r'\btypography\b', r'\bfont\b', r'\btypeface\b', r'\bmonogram\b',
        r'\bemblem\b', r'\binsignia\b', r'\bcrest\b', r'\bmark\b'
    ]

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

    def _detect_logo_request(self, prompt: str) -> bool:
        """
        Detect if the prompt is requesting a logo/branding generation.
        
        Args:
            prompt: User prompt text
            
        Returns:
            True if prompt suggests logo generation, False otherwise
        """
        prompt_lower = prompt.lower()
        
        # Check for logo-related keywords
        for keyword_pattern in self.LOGO_KEYWORDS:
            if re.search(keyword_pattern, prompt_lower, re.IGNORECASE):
                return True
        
        # Check if prompt is just text/words (likely a logo request)
        # If prompt is short (1-5 words) and contains mostly letters, it's likely a logo
        words = prompt.split()
        if len(words) <= 5:
            # Check if most words are short (likely text for a logo)
            short_words = sum(1 for w in words if len(w) <= 10)
            if short_words >= len(words) * 0.7:  # 70% of words are short
                # Check if it contains common logo phrases
                logo_phrases = ['for', 'called', 'named', 'logo for', 'text', 'letters']
                if any(phrase in prompt_lower for phrase in logo_phrases):
                    return True
                # If it's just a few words without "a" or "an" (not describing an object), likely logo
                if not any(word.lower() in ['a', 'an', 'the'] for word in words):
                    # Check if it looks like a company/product name (capitalized words)
                    capitalized = sum(1 for w in words if w and w[0].isupper())
                    if capitalized >= len(words) * 0.5:  # 50%+ capitalized
                        return True
        
        return False

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
        
        # Add specific guidance emphasizing ascii-art.de minimalist principles
        feedback_lines.extend([
            "PLEASE REGENERATE with these corrections (using ascii-art.de minimalist principles):",
            "1. Use STRATEGIC NEGATIVE SPACE: Leave empty areas to define form - quality ASCII art is 40-60% filled, NOT densely packed",
            "2. Focus on ICONIC FEATURES: Start with eyes, ears, nose - minimal, recognizable elements, not filling space",
            "3. SIMPLIFY: Choose fewer, more meaningful characters rather than complex variety - less is more",
            "4. Avoid repetition: Never repeat the same line pattern more than 4-5 times",
            "5. Create RECOGNIZABLE shapes: The output must INSTANTLY be recognizable as the requested subject",
            "6. BREATHING ROOM: Leave space around features to prevent visual clutter",
            "7. ENSURE SYMMETRY: For creatures, animals, and symmetrical objects, make sure both sides mirror each other perfectly",
            "8. Center your art: Count characters on left and right sides to ensure perfect balance",
            "9. Keep it MINIMAL: 4-12 lines is ideal - don't over-detail, stop when recognizable",
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
        quality_keywords = ["broken", "repetitive", "recognizable", "dense", "negative space"]
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
    
    def generate(self, prompt: str, use_cache: bool = True, is_logo: Optional[bool] = None) -> str:
        """
        Generate ASCII art from prompt with quality validation and retry on failure.

        Args:
            prompt: User prompt describing the art
            use_cache: Whether to use cache
            is_logo: Whether this is a logo/branding generation (uses larger size limits).
                    If None, automatically detects from prompt.

        Returns:
            Generated ASCII art (validated and cleaned)
        """
        # Auto-detect logo mode if not explicitly set
        if is_logo is None:
            is_logo = self._detect_logo_request(prompt)
        
        # Check cache first (include logo mode in cache key)
        cache_key = "logo" if is_logo else "ascii_art"
        if use_cache:
            cached = self.cache.get(prompt, cache_key)
            if cached:
                return cached

        # Use appropriate prompt based on mode
        system_prompt = LOGO_PROMPT if is_logo else ASCII_ART_PROMPT
        
        # Update validator mode if needed
        if is_logo and self.validator.mode != "logo":
            self.validator = ASCIIValidator(mode="logo")

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
                result = self.ai_client.generate(current_prompt, system_prompt)
            else:
                # Retry: use feedback prompt
                if last_validation and last_result:
                    feedback_prompt = self._build_feedback_prompt(prompt, last_validation, last_result)
                    # Combine feedback with original system prompt
                    enhanced_system_prompt = f"{system_prompt}\n\n--- REGENERATION REQUEST WITH FEEDBACK ---\n{feedback_prompt}"
                    result = self.ai_client.generate(prompt, enhanced_system_prompt)
                else:
                    # Fallback if we don't have previous validation/result
                    result = self.ai_client.generate(current_prompt, system_prompt)
            
            # Validate and clean the result
            cleaned_result, validation = self.validator.validate_and_clean(result, strict=False)
            
            # Check if result is valid and has no quality issues
            if validation.is_valid and not self._has_quality_issues(validation):
                # Success! Cache and return
                if use_cache:
                    self.cache.set(prompt, cache_key, cleaned_result)
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
            self.cache.set(prompt, cache_key, final_result)
        
        return final_result

    def generate_stream(self, prompt: str, use_cache: bool = True, is_logo: Optional[bool] = None):
        """
        Generate ASCII art from prompt with streaming (yields chunks as they arrive).
        If validation fails after streaming, automatically retries using non-streaming method.

        Args:
            prompt: User prompt describing the art
            use_cache: Whether to use cache
            is_logo: Whether this is a logo/branding generation (uses larger size limits).
                    If None, automatically detects from prompt.

        Yields:
            Text chunks as they are generated
        """
        # Auto-detect logo mode if not explicitly set
        if is_logo is None:
            is_logo = self._detect_logo_request(prompt)
        
        # Check cache first (include logo mode in cache key)
        cache_key = "logo" if is_logo else "ascii_art"
        if use_cache:
            cached = self.cache.get(prompt, cache_key)
            if cached:
                # Yield cached content in one chunk
                yield cached
                return

        # Use appropriate prompt based on mode
        system_prompt = LOGO_PROMPT if is_logo else ASCII_ART_PROMPT
        
        # Update validator mode if needed
        if is_logo and self.validator.mode != "logo":
            self.validator = ASCIIValidator(mode="logo")

        # Wait for rate limit
        self.rate_limiter.wait_if_needed()

        # Generate using AI with streaming
        accumulated = ""
        # Check if client supports streaming (using getattr to avoid type errors)
        generate_stream_method = getattr(self.ai_client, 'generate_stream', None)
        if generate_stream_method:
            for chunk in generate_stream_method(prompt, system_prompt):
                accumulated += chunk
                yield chunk

            # Validate and clean the final result
            cleaned_result, validation = self.validator.validate_and_clean(accumulated, strict=False)
            
            # Check if validation failed or quality issues detected
            if not validation.is_valid or self._has_quality_issues(validation):
                # Validation failed - the streamed result is broken/incomplete
                # Retry with streaming so it gets drawn live
                
                # Yield a marker to signal retry, then stream the retry result live
                # The renderer will detect "[RETRY]" and clear previous output
                yield "\n[RETRY]"
                
                # Retry with feedback - use streaming for live rendering
                last_result = cleaned_result
                last_validation = validation
                
                for attempt in range(self.max_retries + 1):
                    # Build feedback prompt
                    if last_validation and last_result:
                        feedback_prompt = self._build_feedback_prompt(prompt, last_validation, last_result)
                        enhanced_system_prompt = f"{system_prompt}\n\n--- REGENERATION REQUEST WITH FEEDBACK ---\n{feedback_prompt}"
                        retry_prompt = prompt
                    else:
                        enhanced_system_prompt = system_prompt
                        retry_prompt = prompt
                    
                    # Wait for rate limit
                    self.rate_limiter.wait_if_needed()
                    
                    # Stream the retry attempt
                    retry_accumulated = ""
                    for chunk in generate_stream_method(retry_prompt, enhanced_system_prompt):
                        retry_accumulated += chunk
                        yield chunk
                    
                    # Validate the retry result
                    retry_cleaned, retry_validation = self.validator.validate_and_clean(retry_accumulated, strict=False)
                    
                    # Check if retry succeeded
                    if retry_validation.is_valid and not self._has_quality_issues(retry_validation):
                        # Success! Cache and we're done
                        if use_cache:
                            self.cache.set(prompt, cache_key, retry_cleaned)
                        return
                    
                    # Store for next retry attempt
                    last_result = retry_cleaned
                    last_validation = retry_validation
                    
                    # If this was the last attempt, we're done
                    if attempt >= self.max_retries:
                        # Cache the best we got
                        if use_cache:
                            self.cache.set(prompt, cache_key, retry_cleaned)
                        return
            else:
                # Validation passed - cache the cleaned result
                if use_cache:
                    self.cache.set(prompt, cache_key, cleaned_result)
        else:
            # Fallback to non-streaming if not supported
            # Use the generate() method which has retry logic
            result = self.generate(prompt, use_cache=use_cache, is_logo=is_logo)
            yield result

