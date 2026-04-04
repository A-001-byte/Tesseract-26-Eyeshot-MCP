import logging

from google import genai
from google.genai import types

from app.config import get_gemini_api_key

logger = logging.getLogger(__name__)
MODEL_NAME = "gemini-2.5-flash"


def _get_client() -> genai.Client:
    api_key = get_gemini_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")

    return genai.Client(api_key=api_key)


def generate_response(prompt: str) -> str:
    """
    Send a prompt to Gemini and return the raw text response.
    """
    logger.info("Sending request to Gemini model %s", MODEL_NAME)
    logger.debug("Using Gemini model: gemini-2.5-flash")

    try:
        client = _get_client()

        # Send the prompt as plain text and read back the top-level text field.
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        response_text = getattr(response, "text", "") or ""
        if not response_text:
            logger.error("Received empty response text from Gemini model %s", MODEL_NAME)
            return '{"error": "Empty response from LLM"}'

        logger.info("Received response from Gemini model %s", MODEL_NAME)
        return response_text
    except ValueError:
        logger.exception("Gemini configuration error")
        raise
    except Exception as exc:
        logger.exception("Gemini API request failed")
        raise RuntimeError("Gemini API request failed.") from exc
