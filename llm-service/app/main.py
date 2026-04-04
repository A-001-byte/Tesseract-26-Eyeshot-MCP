import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import ROOT_ENV_FILE
from app.services.llm_client import generate_response
from app.services.parser import parse_llm_output
from app.services.prompt_templates import build_command_prompt
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Loaded environment variables from %s", ROOT_ENV_FILE)

app = FastAPI(title="LLM Parsing Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ParseRequest(BaseModel):
    prompt: str


class GenerateCommandRequest(BaseModel):
    input: str


def _is_blank(value: str) -> bool:
    return not value or not value.strip()


def _llm_service_unavailable() -> dict:
    return {"error": "LLM service unavailable"}


def _invalid_input_error() -> dict:
    return {"error": "Input must not be empty"}


@app.post("/api/v1/parse")
async def parse_instruction(request: ParseRequest):
    """
    Takes natural language, calls LLM, and enforces JSON schema.
    """
    logger.info(f"Parsing instruction: {request.prompt}")
    try:
        if _is_blank(request.prompt):
            logger.error("Rejected empty prompt for /api/v1/parse")
            return _invalid_input_error()

        # Call LLM
        raw_llm_response = generate_response(request.prompt)
        # Enforce JSON
        structured_json = parse_llm_output(raw_llm_response)
        
        return {"status": "success", "structured_command": structured_json}
    except RuntimeError as exc:
        logger.error("LLM request failed for /api/v1/parse: %s", str(exc))
        return _llm_service_unavailable()
    except Exception as e:
        logger.exception("Unexpected error while parsing instruction")
        return {"error": "Failed to parse instruction", "details": str(e)}


@app.post("/generate-command")
async def generate_command(request: GenerateCommandRequest):
    """
    Convert user input into a structured CAD command dictionary.
    """
    try:
        if _is_blank(request.input):
            logger.error("Rejected empty input for /generate-command")
            return _invalid_input_error()

        logger.info("Input received: %s", request.input)

        prompt = build_command_prompt(request.input)
        logger.info("Prompt generated")

        raw_llm_response = generate_response(prompt)
        logger.info("Raw LLM response: %s", raw_llm_response)

        parsed_output = parse_llm_output(raw_llm_response)
        logger.info("Parsed output: %s", parsed_output)
        return parsed_output
    except RuntimeError as exc:
        logger.error("LLM request failed for /generate-command: %s", str(exc))
        return _llm_service_unavailable()
    except Exception as exc:
        logger.exception("Failed to generate command")
        return {
            "error": "Failed to generate command",
            "details": str(exc),
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
