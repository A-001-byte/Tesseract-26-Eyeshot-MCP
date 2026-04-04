import json
import os
import requests

SYSTEM_PROMPT = """
You are a CAD operation planner. Convert user instructions into a structured JSON plan.

Available tools:
- load_model(file_path: str)  ← must use exactly "file_path"

- list_entities()
- get_properties(entity_id: str)
- move_object(entity_id: str, translation: [x, y, z])

Rules:
- Always return ONLY a valid JSON array, no explanation, no markdown
- Each step must have "tool" and "args" keys
- If entity IDs are not mentioned, use "entity_1", "entity_2" as defaults

Example output:
[
  {"tool": "load_model", "args": {"file_path": "assembly.stp"}},
  {"tool": "list_entities", "args": {}}
]
"""

def generate_plan(user_prompt: str) -> list:
    api_key = os.getenv("GEMINI_API_KEY")  # or OPENAI_API_KEY, swap as needed

    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        headers={"Content-Type": "application/json"},
        params={"key": api_key},


        json={
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": user_prompt}]}]
        }
    )

    raw = response.json()
    if "error" in raw:
        raise ValueError(f"Gemini API returned an error: {raw['error']}")
        
    if "candidates" not in raw:
        raise ValueError(f"Unexpected API response: {raw}")

    text = raw["candidates"][0]["content"]["parts"][0]["text"]

    # Strip markdown fences if model adds them
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    return json.loads(text)