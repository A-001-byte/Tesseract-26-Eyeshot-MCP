import os
import json
import re
from dotenv import load_dotenv
import openai

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

SYSTEM_PROMPT = """
You are a CAD command interpreter for an engineering platform.
Given any natural language instruction, return ONLY valid JSON. No markdown, no explanation, no backticks.

You must determine whether the user wants to:
1. CREATE/GENERATE a new shape → use command "generate_shape"
2. ROTATE an object → use action "rotate_object"
3. MOVE/TRANSLATE an object → use action "move_object"
4. SCALE an object → use action "scale_object"
5. MIRROR an object → use action "mirror_object"
6. COUNT entities → use action "get_entity_count"
7. LIST entities → use action "list_entities"
8. LOAD a file → use action "load_model"
9. GENERATE A GEAR → use command "generate_gear"

═══════════════════════════════════════
FORMAT 1 — Shape Generation (create, make, build, generate, design):
═══════════════════════════════════════
{
  "command": "generate_shape",
  "shape_description": "<user description>",
  "name": "<snake_case_name>",
  "material": "<steel|aluminum|plastic|concrete|wood|marble>",
  "geometry": {
    "type": "<box|cylinder|sphere|cone|torus>",
    "dimensions": {
      "width": <num>, "height": <num>, "depth": <num>,
      "radius": <num>, "inner_radius": <num>, "top_radius": <num>
    },
    "operations": [
      {
        "type": "<fuse|cut>",
        "shape": "<box|cylinder|sphere|cone|torus>",
        "dimensions": { "width": <n>, "height": <n>, "depth": <n>, "radius": <n>, "inner_radius": <n>, "top_radius": <n> },
        "position": {"x": <n>, "y": <n>, "z": <n>}
      }
    ]
  }
}

Dimension rules (centimeters):
- Room: base box 500×280×400, cut box 480×260×380 at (10,10,0), door cut 90×210×20 at (200,-5,0)
- Table: top box 120×4×60, legs are 4 cylinders radius=2 height=70
- Simple shapes: reasonable engineering sizes (5-50cm)
- inner_radius < radius by at least 0.5
- operations can be empty []

═══════════════════════════════════════
FORMAT 3 — Gear Generation (gear, spur gear, cog, cogwheel, sprocket):
═══════════════════════════════════════
{
  "command": "generate_gear",
  "num_teeth": <number between 8 and 60, default 24>,
  "module": <float between 0.5 and 10.0, default 2.0>,
  "thickness": <float between 2.0 and 50.0, default 8.0>,
  "bore_radius": <float, default 8.0>,
  "material": "<steel|aluminum|plastic|cast_iron>"
}

Gear parameter extraction rules:
- If user mentions a number before "teeth" (e.g. "40 teeth"), use it as num_teeth.
- If user mentions "module" followed by a number, use it as module.
- If user mentions "thick", "thickness", or "depth" followed by a number, use it as thickness.

═══════════════════════════════════════
FORMAT 2 — Actions on existing objects (rotate, move, scale, mirror, count, list):
═══════════════════════════════════════
For rotate:   {"action": "rotate_object", "object_id": "<name or 'last'>", "axis": "<X|Y|Z>", "angle": <degrees>}
For move:     {"action": "move_object", "object_id": "<name or 'last'>", "x": <n>, "y": <n>, "z": <n>}
For scale:    {"action": "scale_object", "object_id": "<name or 'last'>", "factor": <n>}
For mirror:   {"action": "mirror_object", "object_id": "<name or 'last'>", "plane": "<XY|XZ|YZ>"}
For count:    {"action": "get_entity_count"}
For list:     {"action": "list_entities"}
For load:     {"action": "load_model", "filePath": "<path>"}

RULES:
- If user says "rotate" without specifying axis, default to Z axis.
- If user says "rotate 45 degrees", angle = 45.
- If user says "count" or "how many", return get_entity_count.
- If user says "list" or "show entities", return list_entities.
- object_id defaults to "last" if not specified.
- Return ONLY JSON. No other text.
"""


def clean_llm_response(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'^```\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    raw = raw.strip()
    return raw

def call_llm(user_prompt: str) -> dict:
    if not OPENROUTER_API_KEY:
        return get_fallback_shape(user_prompt)
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        raw = response.choices[0].message.content
        cleaned = clean_llm_response(raw)
        parsed = json.loads(cleaned)
        return parsed
    except json.JSONDecodeError:
        try:
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return get_fallback_shape(user_prompt)
    except Exception as e:
        print(f"LLM call failed: {e}")
        return get_fallback_shape(user_prompt)

def get_fallback_shape(prompt: str) -> dict:
    prompt_lower = prompt.lower()
    if any(w in prompt_lower for w in ["room", "house", "building", "wall"]):
        geo = {"type": "box", "dimensions": {"width": 500, "height": 280, "depth": 400, "radius": 1, "inner_radius": 0.5, "top_radius": 0.5}, "operations": []}
        name = "room_structure"
    elif any(w in prompt_lower for w in ["bearing", "ball bearing"]):
        geo = {"type": "cylinder", "dimensions": {"width": 3, "height": 1.5, "depth": 3, "radius": 3, "inner_radius": 1.5, "top_radius": 1}, "operations": [{"type": "cut", "shape": "cylinder", "dimensions": {"width": 1.5, "height": 1.5, "depth": 1.5, "radius": 1.5, "inner_radius": 0.5, "top_radius": 0.5}, "position": {"x": 0, "y": 0, "z": 0}}]}
        name = "ball_bearing"
    elif any(w in prompt_lower for w in ["shaft", "rod", "pipe"]):
        geo = {"type": "cylinder", "dimensions": {"width": 2, "height": 20, "depth": 2, "radius": 2, "inner_radius": 1, "top_radius": 1}, "operations": []}
        name = "shaft"
    elif any(w in prompt_lower for w in ["gear", "disc", "disk"]):
        geo = {"type": "cylinder", "dimensions": {"width": 5, "height": 1.2, "depth": 5, "radius": 5, "inner_radius": 1, "top_radius": 1}, "operations": []}
        name = "gear"
    elif any(w in prompt_lower for w in ["sphere", "ball", "globe"]):
        geo = {"type": "sphere", "dimensions": {"width": 5, "height": 5, "depth": 5, "radius": 5, "inner_radius": 1, "top_radius": 1}, "operations": []}
        name = "sphere"
    elif any(w in prompt_lower for w in ["cone", "nozzle", "funnel"]):
        geo = {"type": "cone", "dimensions": {"width": 3, "height": 10, "depth": 3, "radius": 3, "inner_radius": 1, "top_radius": 0.5}, "operations": []}
        name = "cone"
    else:
        geo = {"type": "box", "dimensions": {"width": 5, "height": 5, "depth": 5, "radius": 2.5, "inner_radius": 1, "top_radius": 1}, "operations": []}
        name = prompt_lower.replace(" ", "_")[:20]
    return {"command": "generate_shape", "shape_description": prompt, "name": name, "material": "steel", "geometry": geo}
