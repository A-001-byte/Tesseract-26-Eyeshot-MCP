import json
import re

def enforce_json_output(llm_response: str) -> dict:
    """
    Extracts JSON from LLM text output in case it wrapped it in markdown.
    """
    try:
        # First attempt a direct parse
        return json.loads(llm_response)
    except json.JSONDecodeError:
        pass

    # Try extracting markdown blocks
    match = re.search(r'```(?:json)?(.*?)```', llm_response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
            
    # Fallback to raising exception
    raise ValueError(f"Could not extract valid JSON from LLM output: {llm_response}")
