import logging

from google import genai
from google.genai import types

from app.config import get_gemini_api_key

logger = logging.getLogger(__name__)
MODEL_NAME = "gemini-2.5-flash"


def _get_client() -> genai.Client:
    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError("Gemini API key is not configured.")

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=120000,
            retryOptions=types.HttpRetryOptions(attempts=5),
        ),
    )


def generate_response(prompt: str) -> str:
    """
    Send a prompt to Gemini and return the raw text response.
    """
    logger.info("Sending request to Gemini")
    logger.debug("Using Gemini model: %s", MODEL_NAME)

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        response_text = getattr(response, "text", None)
        if not response_text:
            logger.error("Received empty response text from Gemini model %s", MODEL_NAME)
            raise RuntimeError(f"Empty response from Gemini model {MODEL_NAME}.")

        logger.info("Received response from Gemini")
        logger.debug("Gemini response length=%s", len(response_text))
        return response_text
    except RuntimeError:
        raise
    except Exception as exc:
        logger.exception("Gemini API request failed")
        raise RuntimeError("Gemini API request failed.") from exc
