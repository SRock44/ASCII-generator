"""ASCII art generator."""
from typing import Optional
import re
from ai.client import AIClient
from ai.prompts import ASCII_ART_PROMPT, LOGO_PROMPT
from rate_limiter import RateLimiter
from renderer import Renderer
from validators import ASCIIValidator, ValidationResult
from prompt_builder import PromptBuilder
from session_context import SessionContext


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

    def __init__(self, ai_client: AIClient, session_context: Optional[SessionContext] = None, rate_limiter: Optional[RateLimiter] = None, max_retries: int = 2):
        """
        Initialize ASCII art generator.

        Args:
            ai_client: AI client instance
            session_context: Optional session context for maintaining conversation history
            rate_limiter: Optional rate limiter instance
            max_retries: Maximum number of retries with feedback (default: 2)
        """
        self.ai_client = ai_client
        self.session_context = session_context
        self.rate_limiter = rate_limiter or RateLimiter()
        self.validator = ASCIIValidator(mode="art")
        self.max_retries = max_retries
        self.prompt_builder = PromptBuilder()  # Lazy-loaded example cache
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
        Build a concise feedback prompt with specific fixes for regeneration.

        Args:
            original_prompt: Original user prompt
            validation: Validation result with errors/warnings
            previous_output: The previous output that failed validation

        Returns:
            Enhanced prompt with feedback
        """
        # Count lines in previous output for specific feedback
        prev_lines = len([l for l in previous_output.split('\n') if l.strip()])

        feedback_lines = [f"RETRY for '{original_prompt}' - previous attempt had issues:", ""]

        # Add specific, actionable fixes based on errors
        fixes = []
        for error in validation.errors:
            if "incomplete" in error.lower() or "cut off" in error.lower():
                fixes.append("COMPLETE: Finish the entire drawing. Complete all lines, close all brackets/parentheses, finish the bottom.")
            elif "lines" in error.lower() or "too many" in error.lower():
                fixes.append(f"REDUCE: Cut from {prev_lines} lines to 4-10 lines. Show only 2-3 iconic features.")
            elif "dense" in error.lower():
                fixes.append("SPARSE: Use 40-60% filled space. Add more whitespace between elements.")
            elif "repetitive" in error.lower() or "consecutive" in error.lower():
                fixes.append("VARY: No more than 3 identical consecutive lines. Each line should differ.")
            elif "pattern" in error.lower():
                fixes.append("DIVERSIFY: Use different characters/structures throughout.")
            else:
                fixes.append(f"FIX: {error}")

        for warning in validation.warnings:
            if "symmetr" in warning.lower():
                fixes.append("MIRROR: Left side must mirror right side. Use ( ) / \\ pairs correctly.")
            elif "feature" in warning.lower():
                fixes.append("FEATURES: Add iconic chars like o O for eyes, /\\ for ears, ( ) for curves.")
            elif "variety" in warning.lower() or "length" in warning.lower():
                fixes.append("SHAPE: Vary line lengths to create natural silhouette.")

        if fixes:
            feedback_lines.append("SPECIFIC FIXES NEEDED:")
            for fix in fixes[:5]:  # Max 5 fixes to keep it focused
                feedback_lines.append(f"- {fix}")
            feedback_lines.append("")

        # Add concise reminder of good art
        feedback_lines.extend([
            "REFERENCE - Good ascii-art.de style:",
            "  /\\_/\\     <- 4-8 lines",
            " ( o.o )    <- 50% whitespace",
            "  > ^ <     <- iconic features clear",
            " /|   |\\    <- symmetric",
            "",
            f"NOW: Regenerate '{original_prompt}' following these fixes."
        ])

        return "\n".join(feedback_lines)

    def _has_quality_issues(self, validation: ValidationResult) -> bool:
        """
        Check if validation result indicates critical issues that warrant retry.
        Very lenient - only retries on truly broken output.
        
        Args:
            validation: Validation result
            
        Returns:
            True only if output is truly broken, False otherwise
        """
        # Only retry on critical errors that indicate broken output
        # Removed "repetitive", "dense", "recognizable", "negative space" - these are not critical
        critical_keywords = ["broken", "markdown", "disallowed characters", "exceeds maximum", "incomplete", "cut off"]
        
        for error in validation.errors:
            if any(keyword in error.lower() for keyword in critical_keywords):
                return True
        
        # Don't retry based on warnings - they're just suggestions
        return False

    def _is_ladder_failure(self, validation: Optional[ValidationResult]) -> bool:
        """Detect the degenerate 'ladder/template' failure mode for art."""
        # ValidationResult defines __bool__ as is_valid; we must not treat invalid results as "no object".
        if validation is None:
            return False
        ladder_keywords = [
            "degenerate template/ladder",
            "extreme pattern repetition",
            "extreme repetition detected",
            "consecutive identical lines",
        ]
        combined = " ".join((validation.errors or []) + (validation.warnings or [])).lower()
        return any(k in combined for k in ladder_keywords)

    def _build_hard_reprompt(self, original_prompt: str) -> str:
        """
        Build a hard reset prompt specifically to avoid ladder/template outputs.
        This intentionally overwrites prior behavior with strict, concrete constraints.
        """
        return "\n".join([
            f"HARD RESET: Generate ASCII art for: {original_prompt}",
            "",
            "ABSOLUTE RULES:",
            "- Output ONLY the ASCII drawing (no prose, no labels).",
            "- DO NOT produce a repeated 'ladder/template' made of similar lines.",
            "- No more than 2 similar consecutive lines; every line must add a new shape/detail.",
            "- Use 6–14 lines total. Max width 60.",
            "- Make it clearly recognizable with 3+ iconic features (e.g., head, eyes, wings, tail).",
            "",
            "NEGATIVE EXAMPLE (DO NOT DO THIS): repeated scaffolding like '/ /| |\\ \\' many times.",
            "",
            "POSITIVE SHAPE GUIDANCE:",
            "- Vary line lengths to form a silhouette.",
            "- Use whitespace and curves; avoid vertical repetition.",
            "",
            "NOW OUTPUT THE DRAWING:",
        ])
    
    def generate(self, prompt: str, is_logo: Optional[bool] = None) -> str:
        """
        Generate ASCII art from prompt with quality validation and retry on failure.

        Args:
            prompt: User prompt describing the art
            is_logo: Whether this is a logo/branding generation (uses larger size limits).
                    If None, automatically detects from prompt.

        Returns:
            Generated ASCII art (validated and cleaned)
        """
        # Auto-detect logo mode if not explicitly set
        if is_logo is None:
            is_logo = self._detect_logo_request(prompt)
        
        generator_type = "logo" if is_logo else "art"

        # Build enhanced prompt with relevant examples (lazy-loaded)
        # Add session context if available
        base_prompt = self.prompt_builder.build(prompt, is_logo=is_logo, max_examples=3)
        
        # Add session context for continuity
        if self.session_context:
            context_summary = self.session_context.get_context_summary(generator_type)
            if context_summary:
                system_prompt = f"{base_prompt}\n\n{context_summary}"
            else:
                system_prompt = base_prompt
        else:
            system_prompt = base_prompt
        
        # Update validator mode if needed
        if is_logo and self.validator.mode != "logo":
            self.validator = ASCIIValidator(mode="logo")

        # Try generation with retries
        current_prompt = prompt
        last_result = None
        last_validation = None
        cleaned_result = ""  # Initialize to avoid unbound variable
        validation = None  # For type checkers; last_validation is the authoritative final value.
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            # Wait for rate limit
            self.rate_limiter.wait_if_needed()

            # Generate using AI
            if attempt == 0:
                # First attempt: use original prompt
                result = self.ai_client.generate(current_prompt, system_prompt)
            else:
                # Retry: use feedback prompt
                if last_validation is not None and last_result:
                    feedback_prompt = self._build_feedback_prompt(prompt, last_validation, last_result)
                    # Combine feedback with original system prompt
                    enhanced_system_prompt = f"{system_prompt}\n\n--- REGENERATION REQUEST WITH FEEDBACK ---\n{feedback_prompt}"
                    result = self.ai_client.generate(prompt, enhanced_system_prompt)
                else:
                    # Fallback if we don't have previous validation/result
                    result = self.ai_client.generate(current_prompt, system_prompt)
            
            # Validate and clean the result (minimal cleaning for art mode)
            cleaned_result, validation = self.validator.validate_and_clean(result, strict=False, minimal_clean=True)
            
            # Check if result is valid and has no quality issues
            if validation.is_valid and not self._has_quality_issues(validation):
                # Success! Record in session context and return
                if self.session_context:
                    self.session_context.add_interaction(prompt, cleaned_result, generator_type, success=True)
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
        
        # Record in session context (even if not perfect)
        if self.session_context:
            success = last_validation.is_valid if last_validation is not None else False
            self.session_context.add_interaction(prompt, final_result, generator_type, success=success)
        
        return final_result

    def generate_stream(self, prompt: str, is_logo: Optional[bool] = None):
        """
        Generate ASCII art from prompt with streaming (yields chunks as they arrive).
        If validation fails after streaming, automatically retries using non-streaming method.

        Args:
            prompt: User prompt describing the art
            is_logo: Whether this is a logo/branding generation (uses larger size limits).
                    If None, automatically detects from prompt.

        Yields:
            Text chunks as they are generated
        """
        # Auto-detect logo mode if not explicitly set
        if is_logo is None:
            is_logo = self._detect_logo_request(prompt)
        
        generator_type = "logo" if is_logo else "art"

        # Build enhanced prompt with relevant examples (lazy-loaded)
        # Add session context if available
        base_prompt = self.prompt_builder.build(prompt, is_logo=is_logo, max_examples=3)
        
        # Add session context for continuity
        if self.session_context:
            context_summary = self.session_context.get_context_summary(generator_type)
            if context_summary:
                system_prompt = f"{base_prompt}\n\n{context_summary}"
            else:
                system_prompt = base_prompt
        else:
            system_prompt = base_prompt
        
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

            # Validate and clean the final result (minimal cleaning for art mode)
            cleaned_result, validation = self.validator.validate_and_clean(accumulated, strict=False, minimal_clean=True)

            # If cleaning materially changes output (e.g., fixes indentation or strips fences),
            # re-render the cleaned result so the user sees the best final art.
            # This is cheap (local) and improves UX for streaming output.
            try:
                raw_norm = accumulated.replace("\r\n", "\n").replace("\r", "\n").rstrip()
                cleaned_norm = cleaned_result.replace("\r\n", "\n").replace("\r", "\n").rstrip()
                if cleaned_norm and cleaned_norm != raw_norm:
                    yield "\n[FINAL]"
                    yield cleaned_norm + "\n"
            except Exception:
                # Never let final re-render fail the stream.
                pass
            
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
                ladder_failures = 1 if self._is_ladder_failure(validation) else 0
                hard_reprompt_used = False
                
                for attempt in range(self.max_retries + 1):
                    # Clear previous attempt output before starting a new attempt
                    # (prevents stacking multiple failed ladders on screen).
                    if attempt > 0:
                        yield "\n[RETRY]"

                    # Escalate if we hit the ladder failure again: hard re-prompt ONCE.
                    ladder_again = self._is_ladder_failure(last_validation)
                    if ladder_again:
                        ladder_failures += 1

                    if ladder_failures >= 2 and not hard_reprompt_used:
                        # Complete reset: ignore prior output and demand non-ladder drawing.
                        hard_reprompt_used = True
                        enhanced_system_prompt = system_prompt
                        retry_prompt = self._build_hard_reprompt(prompt)
                    else:
                        # Standard feedback prompt
                        if last_validation is not None and last_result:
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
                    
                    # Validate the retry result (minimal cleaning for art mode)
                    retry_cleaned, retry_validation = self.validator.validate_and_clean(retry_accumulated, strict=False, minimal_clean=True)
                    
                    # Check if retry succeeded
                    if retry_validation.is_valid and not self._has_quality_issues(retry_validation):
                        # Success! Record in session context and we're done
                        if self.session_context:
                            self.session_context.add_interaction(prompt, retry_cleaned, generator_type, success=True)
                        return
                    
                    # Store for next retry attempt
                    last_result = retry_cleaned
                    last_validation = retry_validation

                    # If we already escalated and still got ladder output, stop cleanly.
                    if hard_reprompt_used and self._is_ladder_failure(retry_validation):
                        yield "ERROR_CODE: VALIDATION_FAILED\nERROR_MESSAGE: Model produced repeated ladder/template output multiple times. Try a more specific prompt (e.g., 'dragon head with wings, 10 lines')."
                        return
                    
                    # If this was the last attempt, we're done
                    if attempt >= self.max_retries:
                        # Record in session context (even if not perfect)
                        if self.session_context:
                            success = retry_validation.is_valid if retry_validation else False
                            self.session_context.add_interaction(prompt, retry_cleaned, generator_type, success=success)
                        # Avoid leaving the user with an obviously broken ladder output.
                        if self._is_ladder_failure(retry_validation):
                            yield "ERROR_CODE: VALIDATION_FAILED\nERROR_MESSAGE: Could not generate a non-ladder drawing after multiple retries. Please try again with a more specific prompt."
                            return
                        return
            else:
                # Validation passed - record in session context
                if self.session_context:
                    self.session_context.add_interaction(prompt, cleaned_result, generator_type, success=True)
        else:
            # Fallback to non-streaming if not supported
            # Use the generate() method which has retry logic
            result = self.generate(prompt, is_logo=is_logo)
            yield result

