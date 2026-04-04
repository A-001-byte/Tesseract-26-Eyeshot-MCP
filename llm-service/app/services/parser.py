import json
import re

from app.models.command_schema import StructuredCommand

def enforce_json_output(llm_response: str) -> dict:
    """
    Extracts JSON from LLM text output in case it wrapped it in markdown.
    """
    parsed = None

    try:
        parsed = json.loads(llm_response)
    except json.JSONDecodeError:
        parsed = None

    # Try extracting markdown blocks
    if parsed is None:
        match = re.search(r'```(?:json)?(.*?)```', llm_response, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                parsed = None

    if parsed is None:
        raise ValueError(f"Could not extract valid JSON from LLM output: {llm_response}")

    validated = StructuredCommand.model_validate(parsed)
    return validated.model_dump(exclude_none=True)
