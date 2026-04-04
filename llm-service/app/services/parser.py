import json


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


def enforce_json_output(llm_response: str) -> dict:
    return parse_llm_output(llm_response)
