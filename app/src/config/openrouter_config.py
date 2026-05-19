import os
from dotenv import load_dotenv
from pathlib import Path

# Load env variables from root .env
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Use model from environment or fallback to gemini-3-flash-preview
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "google/gemini-3-flash-preview")
