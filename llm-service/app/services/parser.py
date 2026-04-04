import json
import re


def parse_llm_output(response: str) -> dict:
    """
    Decode the first JSON object found in an LLM response.
    """
    decoder = json.JSONDecoder()

    try:
        # Scan forward until we find a position where a JSON object decodes
        # cleanly, which is more resilient than slicing between braces.
        for start_index, char in enumerate(response):
            if char != "{":
                continue

            parsed_response, end_index = decoder.raw_decode(response[start_index:])
            if not isinstance(parsed_response, dict):
                raise json.JSONDecodeError("Parsed JSON is not an object", response, start_index)

            json_payload = response[start_index : start_index + end_index]
            return json.loads(json_payload)

        raise json.JSONDecodeError("No JSON object found", response, 0)
    except (json.JSONDecodeError, TypeError):
        return {
            "error": "Invalid LLM response",
            "raw": response,
        }


from app.models.command_schema import StructuredCommand

def enforce_json_output(llm_response: str) -> dict:
    parsed = None

    try:
        parsed = json.loads(llm_response)
    except json.JSONDecodeError:
        parsed = None

    if parsed is None:
        match = re.search(r"```(?:json)?(.*?)```", llm_response, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                parsed = None

    if parsed is None:
        parsed = parse_llm_output(llm_response)

    if not isinstance(parsed, dict) or parsed.get("error"):
        raise ValueError(f"Could not extract valid JSON from LLM output: {llm_response}")

    # Accept legacy snake_case from some prompts and normalize to camelCase.
    if "file_path" in parsed and "filePath" not in parsed:
        parsed["filePath"] = parsed.pop("file_path")

    validated = StructuredCommand.model_validate(parsed)
    return validated.model_dump(exclude_none=True)
