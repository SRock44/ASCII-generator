"""Rate limiter for API calls."""
import time
from collections import deque
from threading import Lock
import config


class RateLimiter:
    """Thread-safe rate limiter."""
    
    def __init__(self, max_requests: int = None, window_seconds: int = None):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window (defaults to config)
            window_seconds: Time window in seconds (defaults to config)
        """
        self.max_requests = max_requests or config.RATE_LIMIT_RPM
        self.window_seconds = window_seconds or config.RATE_LIMIT_WINDOW
        self.requests = deque()
        self.lock = Lock()
    
    def acquire(self) -> bool:
        """
        Try to acquire a request slot.
        
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        with self.lock:
            now = time.time()
            
            # Remove requests outside the time window
            while self.requests and self.requests[0] < now - self.window_seconds:
                self.requests.popleft()
            
            # Check if we can make a new request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            else:
                return False
    
    def wait_if_needed(self):
        """Wait until a request slot is available."""
        while not self.acquire():
            # Calculate wait time
            if self.requests:
                oldest_request = self.requests[0]
                wait_time = self.window_seconds - (time.time() - oldest_request)
                if wait_time > 0:
                    time.sleep(min(wait_time, 1))  # Sleep in 1-second increments
                else:
                    # Clean up stale requests
                    with self.lock:
                        now = time.time()
                        while self.requests and self.requests[0] < now - self.window_seconds:
                            self.requests.popleft()
            else:
                break





