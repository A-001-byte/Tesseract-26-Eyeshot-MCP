SYSTEM_INSTRUCTION = """You convert natural language CAD instructions to strict JSON.

Allowed actions:
1. load_model with required field filePath
2. get_entity_count with no extra fields
3. list_entities with no extra fields
4. load_and_count with required field filePath

Rules:
- Output must be a single JSON object
- No markdown
- No explanation text
- No extra keys
- Use filePath camelCase exactly

Examples:
{"action":"load_model","filePath":"gear.step"}
{"action":"get_entity_count"}
{"action":"list_entities"}
{"action":"load_and_count","filePath":"gear.step"}
"""

# Backward-compatible alias used by existing code paths.
SYSTEM_PROMPT = SYSTEM_INSTRUCTION


def build_command_prompt(user_input: str) -> str:
    return f"{SYSTEM_INSTRUCTION}\n\nInput: {user_input}"
