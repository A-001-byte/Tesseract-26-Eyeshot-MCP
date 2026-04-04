from pathlib import Path
import os

from dotenv import load_dotenv


ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV_FILE)


def get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY") or ""


def get_allowed_origins() -> list[str]:
    configured_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if configured_origins.strip():
        return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]

    # Default to common local frontend origins instead of using a wildcard
    # when credentials are enabled.
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
