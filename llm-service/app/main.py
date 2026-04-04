import asyncio
import logging
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


ALLOWED_ACTIONS = {
    "load_model": {"file_path": str},
    "list_entities": {},
    "get_entity_properties": {"entity_id": str},
    "measure_distance": {"entity1": str, "entity2": str},
}


def _is_blank(value: str) -> bool:
    return not value or not value.strip()


def _llm_service_unavailable() -> JSONResponse:
    return JSONResponse(status_code=503, content={"error": "LLM service unavailable"})


def _invalid_input_error() -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": "Input must not be empty"})


def _failure_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"status": "failure", "error": message},
    )


def _validate_structured_command(structured_json: dict) -> str | None:
    if not isinstance(structured_json, dict):
        return "Structured command must be a JSON object"
    if "error" in structured_json:
        return structured_json.get("error", "Invalid LLM response")

    action = structured_json.get("action")
    if not isinstance(action, str):
        return 'Missing or invalid "action" field'
    if action not in ALLOWED_ACTIONS:
        return f'Unsupported action "{action}"'

    for field_name, expected_type in ALLOWED_ACTIONS[action].items():
        field_value = structured_json.get(field_name)
        if not isinstance(field_value, expected_type):
            return f'Invalid or missing "{field_name}" for action "{action}"'

    return None


async def _generate_and_parse_command(
    user_input: str, request_id: str
) -> tuple[str | None, dict | None]:
    prompt = build_command_prompt(user_input)
    logger.info("Prompt generated for request_id=%s", request_id)
    logger.debug("Prompt content for request_id=%s: %s", request_id, prompt)

    raw_llm_response = await asyncio.to_thread(generate_response, prompt)
    logger.info(
        "Model returned for request_id=%s response_length=%s",
        request_id,
        len(raw_llm_response),
    )
    logger.debug("Raw LLM response for request_id=%s: %s", request_id, raw_llm_response)

    parsed_output = parse_llm_output(raw_llm_response)
    logger.info("Parsed output ready for request_id=%s", request_id)
    logger.debug("Parsed output for request_id=%s: %s", request_id, parsed_output)

    validation_error = _validate_structured_command(parsed_output)
    return validation_error, parsed_output


@app.post("/api/v1/parse")
async def parse_instruction(request: ParseRequest):
    """
    Takes natural language, calls LLM, and enforces JSON schema.
    """
    request_id = str(uuid.uuid4())
    logger.info(
        "Parsing started for request_id=%s prompt_length=%s",
        request_id,
        len(request.prompt),
    )
    try:
        if _is_blank(request.prompt):
            logger.error(
                "Rejected empty prompt for request_id=%s route=/api/v1/parse",
                request_id,
            )
            return _invalid_input_error()

        validation_error, structured_json = await _generate_and_parse_command(
            request.prompt,
            request_id,
        )
        if validation_error:
            logger.error(
                "Validation failed for request_id=%s reason=%s",
                request_id,
                validation_error,
            )
            return _failure_response(validation_error, status_code=400)

        logger.info("Response sent for request_id=%s route=/api/v1/parse", request_id)
        return {"status": "success", "structured_command": structured_json}
    except RuntimeError as exc:
        logger.error(
            "LLM request failed for request_id=%s route=/api/v1/parse: %s",
            request_id,
            str(exc),
        )
        return _llm_service_unavailable()
    except Exception:
        logger.exception(
            "Unexpected error for request_id=%s route=/api/v1/parse", request_id
        )
        return _failure_response("Internal server error", status_code=500)


@app.post("/generate-command")
async def generate_command(request: GenerateCommandRequest):
    """
    Convert user input into a structured CAD command dictionary.
    """
    request_id = str(uuid.uuid4())
    logger.info(
        "Command generation started for request_id=%s input_length=%s",
        request_id,
        len(request.input),
    )
    try:
        if _is_blank(request.input):
            logger.error(
                "Rejected empty input for request_id=%s route=/generate-command",
                request_id,
            )
            return _invalid_input_error()

        validation_error, parsed_output = await _generate_and_parse_command(
            request.input,
            request_id,
        )
        if validation_error:
            logger.error(
                "Validation failed for request_id=%s reason=%s",
                request_id,
                validation_error,
            )
            return _failure_response(validation_error, status_code=400)

        logger.info("Response sent for request_id=%s route=/generate-command", request_id)
        return parsed_output
    except RuntimeError as exc:
        logger.error(
            "LLM request failed for request_id=%s route=/generate-command: %s",
            request_id,
            str(exc),
        )
        return _llm_service_unavailable()
    except Exception:
        logger.exception(
            "Unexpected error for request_id=%s route=/generate-command", request_id
        )
        return _failure_response("Internal server error", status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
