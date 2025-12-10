"""Groq AI client implementation."""
from groq import Groq
from typing import Optional
from .client import AIClient
import config
import signal
from contextlib import contextmanager


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
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: Optional[int] = None):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key (defaults to config)
            model: Model name (defaults to kimi-k2)
            timeout: Request timeout in seconds (defaults to config.DEFAULT_TIMEOUT)
        """
        self.api_key = api_key or config.GROQ_API_KEY
        self.model_name = model or config.GROQ_MODEL
        self.timeout = timeout or config.DEFAULT_TIMEOUT
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required")
        
        self.client = Groq(api_key=self.api_key)
    
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
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=0.6,
                        max_completion_tokens=1024,  # Limit output to prevent excessive generation
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
                    # Clean up any markdown code blocks that might wrap the output
                    text = content.strip()
                    if text.startswith("```"):
                        # Remove markdown code blocks
                        lines = text.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines[-1].strip() == "```":
                            lines = lines[:-1]
                        text = "\n".join(lines).strip()
                    
                    # Remove trailing repetitive patterns (like extra rectangles)
                    lines = text.split("\n")
                    cleaned_lines = []
                    last_line = None
                    repeat_count = 0
                    trailing_simple_patterns = 0
                    
                    for line in lines:
                        line_stripped = line.strip()
                        
                        # Skip empty lines at the end
                        if not line_stripped:
                            if cleaned_lines:  # Only skip if we have content
                                trailing_simple_patterns += 1
                                if trailing_simple_patterns > 2:  # Stop after 2 empty lines
                                    break
                                continue
                            continue
                        
                        trailing_simple_patterns = 0  # Reset if we see content
                        
                        # Detect repetitive patterns (same line repeated many times)
                        if last_line and line_stripped == last_line:
                            repeat_count += 1
                            if repeat_count > 2:  # If same line repeats more than 2 times, stop
                                break
                        else:
                            repeat_count = 0
                            last_line = line_stripped
                        
                        # Detect simple repetitive patterns (like |   | repeated)
                        line_no_spaces = line_stripped.replace(' ', '')
                        if len(line_no_spaces) > 0:
                            # Check if line is mostly repetitive characters (like | | | or - - -)
                            unique_chars = set(line_no_spaces)
                            if len(unique_chars) <= 2:  # Only 1-2 unique characters
                                # Check if it's a simple pattern (like |   | or - - -)
                                if len(line_no_spaces) > 3:
                                    # Count how many similar simple patterns we've seen recently
                                    recent_simple = sum(1 for l in cleaned_lines[-10:] 
                                                       if len(set(l.strip().replace(' ', ''))) <= 2 
                                                       and len(l.strip().replace(' ', '')) > 3)
                                    if recent_simple > 5:  # Too many simple patterns in a row
                                        break
                                    cleaned_lines.append(line)
                                else:
                                    cleaned_lines.append(line)
                            else:
                                cleaned_lines.append(line)
                    
                    text = "\n".join(cleaned_lines).strip()
                    
                    # Remove trailing empty lines
                    while text.endswith("\n\n"):
                        text = text.rstrip("\n")
                    
                    # Final safety: limit to 60 lines max for ASCII art
                    lines = text.split("\n")
                    if len(lines) > 60:
                        # Try to find a natural stopping point
                        for i in range(40, min(60, len(lines))):
                            if not lines[i].strip():
                                text = "\n".join(lines[:i]).strip()
                                break
                        else:
                            text = "\n".join(lines[:60]).strip()
                    
                    return text
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
    
    def is_available(self) -> bool:
        """Check if Groq client is available."""
        return bool(self.api_key and self.client)

