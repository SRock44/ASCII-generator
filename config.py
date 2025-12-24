"""Configuration management for ASCII Generator."""
import os
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
# Default to llama-3.3-70b-versatile for best performance
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Rate Limiting
RATE_LIMIT_RPM = 15  # Gemini free tier limit
RATE_LIMIT_WINDOW = 60  # seconds

# Output Configuration
MAX_WIDTH = 80
DEFAULT_TIMEOUT = 60  # seconds (increased for codebase analysis)

