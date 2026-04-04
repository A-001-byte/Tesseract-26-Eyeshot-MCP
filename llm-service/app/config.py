from pathlib import Path
import os

from dotenv import load_dotenv


ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV_FILE)


def get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY") or ""
