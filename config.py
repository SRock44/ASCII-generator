"""Configuration management for ASCII Generator."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Cache Configuration
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_DIR = Path(os.getenv("CACHE_DIR", ".cache"))
CACHE_DIR.mkdir(exist_ok=True)

# Rate Limiting
RATE_LIMIT_RPM = 15  # Gemini free tier limit
RATE_LIMIT_WINDOW = 60  # seconds

# Output Configuration
MAX_WIDTH = 80
DEFAULT_TIMEOUT = 30  # seconds

