import json


def parse_llm_output(response: str) -> dict:
    """
    Extract the first JSON object from an LLM response and parse it.
    """
    try:
        # Pull out the outermost JSON object by slicing from the first
        # opening brace to the last closing brace in the response text.
        start_index = response.find("{")
        end_index = response.rfind("}")

        if start_index == -1 or end_index == -1 or start_index > end_index:
            raise json.JSONDecodeError("No JSON object found", response, 0)

        json_payload = response[start_index : end_index + 1]

        # Decode the extracted JSON substring into a Python dictionary.
        parsed_response = json.loads(json_payload)
        if isinstance(parsed_response, dict):
            return parsed_response

        raise json.JSONDecodeError("Parsed JSON is not an object", json_payload, 0)
    except (json.JSONDecodeError, TypeError):
        return {
            "error": "Invalid LLM response",
            "raw": response,
        }


def enforce_json_output(llm_response: str) -> dict:
    return parse_llm_output(llm_response)
