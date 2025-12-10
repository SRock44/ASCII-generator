"""Configuration management for ASCII Generator."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Default to gemini-2.5-pro for better availability and performance
# Can be overridden in .env file with GEMINI_MODEL
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "moonshotai/kimi-k2-instruct-0905")

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

