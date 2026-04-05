import json

from app.models.command_schema import StructuredCommand


def parse_llm_output(response: str) -> dict:
    """
    Decode the first valid JSON object found in an LLM response.
    """
    decoder = json.JSONDecoder()

    # Scan forward until we find a position where a JSON object decodes
    # cleanly, which is more resilient than slicing between braces.
    for start_index, char in enumerate(response):
        if char != "{":
            continue

        try:
            parsed_response, end_index = decoder.raw_decode(response[start_index:])
            if not isinstance(parsed_response, dict):
                continue

            json_payload = response[start_index : start_index + end_index]
            return json.loads(json_payload)
        except json.JSONDecodeError:
            continue

    raise ValueError("Invalid LLM response")

def enforce_json_output(llm_response: str) -> dict:
    try:
        parsed = parse_llm_output(llm_response)
    except ValueError as exc:
        raise ValueError("Invalid LLM response") from exc

    validated = StructuredCommand.model_validate(parsed)
    return validated.model_dump(exclude_none=True)
