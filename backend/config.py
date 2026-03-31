"""Configuration for the Debate system."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Debate agent models
PRO_MODEL = "openai/gpt-5.1"
AGAINST_MODEL = "anthropic/claude-sonnet-4.5"
JUDGE_MODEL = "google/gemini-3-pro-preview"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for debate storage
DEBATES_DIR = "data/debates"
