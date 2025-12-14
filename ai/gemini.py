"""Google Gemini AI client implementation."""
import google.generativeai as genai
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


class GeminiClient(AIClient):
    """Google Gemini AI client."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: Optional[int] = None, mode: str = "art"):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to config)
            model: Model name (defaults to config)
            timeout: Request timeout in seconds (defaults to config.DEFAULT_TIMEOUT)
            mode: Validation mode - "art", "chart", "diagram", or "logo" (defaults to "art")
        """
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model_name = model or config.GEMINI_MODEL
        self.timeout = timeout or config.DEFAULT_TIMEOUT
        self.mode = mode
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        genai.configure(api_key=self.api_key)
        if not self.model_name:
            raise ValueError("Model name is required")
        
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text response using Gemini.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated text response or error string with code
        """
        try:
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser request: {prompt}"
            
            # Use timeout to prevent hanging
            try:
                with timeout_context(self.timeout):
                    # Quality-focused: Allow plenty of tokens for detailed, complete art
                    max_tokens = 8192 if self.mode == "logo" else 6144  # Generous limits for quality art
                    response = self.model.generate_content(
                        full_prompt,
                        generation_config={
                            "temperature": 0.5,  # Lower temperature for more accurate, consistent output
                            "max_output_tokens": max_tokens,
                        }
                    )
            except TimeoutError as e:
                # Format error with code and message
                error_msg = f"ERROR_CODE: {e.error_code}\nERROR_MESSAGE: {e.message}"
                return error_msg
            
            # Check for finish reasons (safety blocks, etc.)
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason
                    # Finish reason 1 = STOP (normal), 2 = MAX_TOKENS, 3 = SAFETY, 4 = RECITATION
                    if finish_reason == 3:  # SAFETY
                        error_msg = "Response was blocked by safety filters. Try rephrasing your prompt."
                        if hasattr(candidate, 'safety_ratings'):
                            safety_issues = []
                            for rating in candidate.safety_ratings:
                                if rating.probability.name in ['HIGH', 'MEDIUM']:
                                    safety_issues.append(f"{rating.category.name}: {rating.probability.name}")
                            if safety_issues:
                                error_msg += f" Safety concerns: {', '.join(safety_issues)}"
                        return f"ERROR_CODE: SAFETY_BLOCKED\nERROR_MESSAGE: {error_msg}"
                    elif finish_reason == 2:  # MAX_TOKENS
                        # Response was cut off, but we can still return what we have
                        pass
                    elif finish_reason == 4:  # RECITATION
                        return "ERROR_CODE: RECITATION_BLOCKED\nERROR_MESSAGE: Response was blocked due to potential recitation of copyrighted content."
            
            # Extract text from response
            try:
                if response.text:
                    # Clean up any markdown code blocks that might wrap the output
                    text = response.text.strip()
                    if text.startswith("```"):
                        # Remove markdown code blocks
                        lines = text.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines[-1].strip() == "```":
                            lines = lines[:-1]
                        text = "\n".join(lines).strip()
                    return text
                else:
                    # Check if we have candidates but no text
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'finish_reason'):
                            finish_reason = candidate.finish_reason
                            if finish_reason == 3:
                                return "ERROR_CODE: SAFETY_BLOCKED\nERROR_MESSAGE: Response was blocked by safety filters. The prompt may have triggered content safety checks."
                    return "ERROR_CODE: NO_RESPONSE\nERROR_MESSAGE: No response generated from the API"
            except Exception as text_error:
                # Handle the specific error about response.text requiring valid Part
                error_str = str(text_error)
                if "response.text" in error_str and "finish_reason" in error_str:
                    # Extract finish reason if available
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'finish_reason'):
                            finish_reason = candidate.finish_reason
                            if finish_reason == 3:
                                return "ERROR_CODE: SAFETY_BLOCKED\nERROR_MESSAGE: Response was blocked by safety filters. Try rephrasing your prompt or using different wording."
                            elif finish_reason == 2:
                                return "ERROR_CODE: MAX_TOKENS\nERROR_MESSAGE: Response exceeded maximum token limit. Try a shorter or simpler prompt."
                            elif finish_reason == 4:
                                return "ERROR_CODE: RECITATION_BLOCKED\nERROR_MESSAGE: Response was blocked due to potential recitation of copyrighted content."
                    return f"ERROR_CODE: INVALID_RESPONSE\nERROR_MESSAGE: {error_str}"
                raise
        except Exception as e:
            # Check for specific Google API exceptions
            error_type = type(e).__name__
            error_str = str(e).lower()
            
            # Check for quota/rate limit errors
            if "429" in str(e) or "quota" in error_str or "rate limit" in error_str or "exceeded" in error_str:
                error_code = "QUOTA_EXCEEDED"
                error_msg = str(e) or "API quota exceeded. Please check your plan and billing details."
                if "429" in str(e):
                    error_msg += "\n\nTip: The free tier has rate limits. Wait a few minutes and try again, or check your usage at https://ai.dev/usage?tab=rate-limit"
                return f"ERROR_CODE: {error_code}\nERROR_MESSAGE: {error_msg}"
            elif "BlockedPrompt" in error_type or "blocked" in error_str:
                error_code = "BLOCKED_PROMPT"
                error_msg = str(e) or "The prompt was blocked by the safety filters"
                return f"ERROR_CODE: {error_code}\nERROR_MESSAGE: {error_msg}"
            elif "StopCandidate" in error_type or "stopped" in error_str:
                error_code = "STOP_CANDIDATE"
                error_msg = str(e) or "Generation was stopped"
                return f"ERROR_CODE: {error_code}\nERROR_MESSAGE: {error_msg}"
            else:
                # Handle other exceptions - try to extract error code if available
                error_code = getattr(e, 'code', 'UNKNOWN_ERROR')
                error_message = str(e) or "An unknown error occurred"
                
                # Check if it's a Google API error with more details
                status_code = getattr(e, 'status_code', None)
                reason = getattr(e, 'reason', None)
                
                # Check error message for status codes
                if "429" in str(e):
                    error_code = "QUOTA_EXCEEDED"
                    error_message = f"{error_message}\n\nTip: API quota exceeded. Wait a few minutes and try again."
                elif status_code:
                    error_code = f"HTTP_{status_code}"
                    if status_code == 429:
                        error_code = "QUOTA_EXCEEDED"
                        error_message = f"{error_message}\n\nTip: Rate limit exceeded. Wait a few minutes and try again."
                if reason:
                    error_message = f"{error_message} (Reason: {reason})"
                
                return f"ERROR_CODE: {error_code}\nERROR_MESSAGE: {error_message}"
    
    def is_available(self) -> bool:
        """Check if Gemini client is available."""
        return bool(self.api_key and self.model)

