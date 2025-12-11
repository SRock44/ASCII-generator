"""Groq AI client implementation."""
from groq import Groq
from typing import Optional
from .client import AIClient
import config
import signal
from contextlib import contextmanager
from validators import ASCIIValidator, StreamingValidator


class TimeoutError(Exception):
    """Custom timeout exception."""
    def __init__(self, message: str, timeout_seconds: int):
        self.message = message
        self.timeout_seconds = timeout_seconds
        self.error_code = "TIMEOUT"
        super().__init__(self.message)


@contextmanager
def timeout_context(seconds):
    """Context manager for timeout handling."""
    def timeout_handler(signum, frame):
        raise TimeoutError(
            f"Request timed out after {seconds} seconds. The API may be slow or unavailable.",
            timeout_seconds=seconds
        )
    
    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Restore the old handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class GroqClient(AIClient):
    """Groq AI client using Kimi K2 model."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: Optional[int] = None, mode: str = "art"):
        """
        Initialize Groq client.

        Args:
            api_key: Groq API key (defaults to config)
            model: Model name (defaults to kimi-k2)
            timeout: Request timeout in seconds (defaults to config.DEFAULT_TIMEOUT)
            mode: Validation mode - "art", "chart", or "diagram" (defaults to "art")
        """
        self.api_key = api_key or config.GROQ_API_KEY
        self.model_name = model or config.GROQ_MODEL
        self.timeout = timeout or config.DEFAULT_TIMEOUT
        self.mode = mode

        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required")

        self.client = Groq(api_key=self.api_key)
        self.validator = ASCIIValidator(mode=mode)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text response using Groq.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated text response or error string with code
        """
        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Use timeout to prevent hanging
            try:
                with timeout_context(self.timeout):
                    # Adjust max tokens based on mode - logos need more tokens
                    max_tokens = 2048 if self.mode == "logo" else 1024
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=0.6,
                        max_completion_tokens=max_tokens,  # Limit output to prevent excessive generation
                        top_p=1,
                        stream=False,  # Get full response at once
                        stop=None
                    )
            except TimeoutError as e:
                # Format error with code and message
                error_msg = f"ERROR_CODE: {e.error_code}\nERROR_MESSAGE: {e.message}"
                return error_msg
            
            # Extract text from response
            if completion.choices and len(completion.choices) > 0:
                content = completion.choices[0].message.content
                if content:
                    # Use validator to clean and validate the output
                    cleaned_text, validation_result = self.validator.validate_and_clean(content, strict=False)

                    # Log validation warnings/errors if any (for debugging)
                    # Only show if DEBUG environment variable is set
                    import os
                    if os.getenv("DEBUG"):
                        if validation_result.warnings:
                            import sys
                            print(f"[Validation Warnings]: {', '.join(validation_result.warnings)}", file=sys.stderr)
                        if validation_result.errors:
                            import sys
                            print(f"[Validation Errors]: {', '.join(validation_result.errors)}", file=sys.stderr)

                    return cleaned_text
                else:
                    return "ERROR_CODE: NO_RESPONSE\nERROR_MESSAGE: No response generated from the API"
            else:
                return "ERROR_CODE: NO_RESPONSE\nERROR_MESSAGE: No response generated from the API"
                
        except Exception as e:
            # Handle exceptions
            error_type = type(e).__name__
            error_str = str(e).lower()
            
            # Check for quota/rate limit errors
            if "429" in str(e) or "quota" in error_str or "rate limit" in error_str or "exceeded" in error_str:
                error_code = "QUOTA_EXCEEDED"
                error_msg = str(e) or "API quota exceeded. Please check your plan and billing details."
                return f"ERROR_CODE: {error_code}\nERROR_MESSAGE: {error_msg}"
            else:
                # Handle other exceptions
                error_code = getattr(e, 'code', 'UNKNOWN_ERROR')
                error_message = str(e) or "An unknown error occurred"
                
                # Check error message for status codes
                if "429" in str(e):
                    error_code = "QUOTA_EXCEEDED"
                    error_message = f"{error_message}\n\nTip: API quota exceeded. Wait a few minutes and try again."
                
                return f"ERROR_CODE: {error_code}\nERROR_MESSAGE: {error_message}"
    
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None):
        """
        Generate text response using Groq with streaming (yields chunks as they arrive).
        STRICT MODE: Validates chunks in real-time, only yields validated content.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context

        Yields:
            Validated text chunks as they are generated

        Raises:
            Exception: If there's an error during generation
        """
        try:
            # Initialize streaming validator for real-time validation
            stream_validator = StreamingValidator(mode=self.mode)

            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Use timeout to prevent hanging
            try:
                with timeout_context(self.timeout):
                    # Adjust max tokens based on mode - logos need more tokens
                    max_tokens = 2048 if self.mode == "logo" else 1024
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=0.6,
                        max_completion_tokens=max_tokens,
                        top_p=1,
                        stream=True,  # Enable streaming
                        stop=None
                    )

                    # Stream chunks with REAL-TIME validation
                    for chunk in completion:
                        if chunk.choices and len(chunk.choices) > 0:
                            delta = chunk.choices[0].delta
                            if delta.content:
                                # VALIDATE CHUNK BEFORE YIELDING - extremely fast character filtering
                                validated_chunk = stream_validator.process_chunk(delta.content)
                                # Only yield if there's validated content (invalid chars are stripped)
                                if validated_chunk:
                                    yield validated_chunk
                    
                    # Stream completed - ensure generator exits cleanly
                    return

            except TimeoutError as e:
                # Format error with code and message
                error_msg = f"ERROR_CODE: {e.error_code}\nERROR_MESSAGE: {e.message}"
                yield error_msg
                return

        except Exception as e:
            # Handle exceptions
            error_type = type(e).__name__
            error_str = str(e).lower()

            # Check for quota/rate limit errors
            if "429" in str(e) or "quota" in error_str or "rate limit" in error_str or "exceeded" in error_str:
                error_code = "QUOTA_EXCEEDED"
                error_msg = str(e) or "API quota exceeded. Please check your plan and billing details."
                yield f"ERROR_CODE: {error_code}\nERROR_MESSAGE: {error_msg}"
            else:
                # Handle other exceptions
                error_code = getattr(e, 'code', 'UNKNOWN_ERROR')
                error_message = str(e) or "An unknown error occurred"

                # Check error message for status codes
                if "429" in str(e):
                    error_code = "QUOTA_EXCEEDED"
                    error_message = f"{error_message}\n\nTip: API quota exceeded. Wait a few minutes and try again."

                yield f"ERROR_CODE: {error_code}\nERROR_MESSAGE: {error_message}"

    def is_available(self) -> bool:
        """Check if Groq client is available."""
        return bool(self.api_key and self.client)

