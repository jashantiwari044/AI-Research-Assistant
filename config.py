"""
config.py — Centralized Configuration
======================================
This module loads environment variables from a .env file and provides
them as simple Python variables to the rest of the application.

WHY THIS EXISTS:
- Single source of truth for all settings
- Keeps API keys out of your code (security!)
- Easy to change settings without modifying code

HOW IT WORKS:
1. python-dotenv reads your .env file
2. os.getenv() fetches each variable (with fallback defaults)
3. Other modules just do: from config import GEMINI_API_KEY
"""

import os
from dotenv import load_dotenv

# ── Load .env file ──────────────────────────────────────────────
# load_dotenv() searches for a .env file in the current directory
# and loads its key=value pairs into environment variables.
# If no .env file exists, this does nothing (no crash).
load_dotenv()

# ── Gemini LLM Settings ────────────────────────────────────────
# os.getenv("KEY", "default") fetches the env var, or uses the default
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ── Search Settings ────────────────────────────────────────────
# Maximum number of results to fetch from each search source
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "5"))

# Wikipedia language (default: English)
WIKIPEDIA_LANGUAGE = os.getenv("WIKIPEDIA_LANGUAGE", "en")

# ── Application Settings ───────────────────────────────────────
# Flask server settings
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
