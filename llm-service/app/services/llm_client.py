import json
import os
import re

import httpx

from app.services.prompt_templates import SYSTEM_PROMPT


def _extract_file_name(prompt: str) -> str:
    match = re.search(r"([\w\-]+\.(?:step|stp|iges|igs|obj))", prompt, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return "gear.step"


def _fallback_command(prompt: str) -> dict:
    text = prompt.lower()
    file_name = _extract_file_name(prompt)

    if "load" in text and ("count" in text or "how many" in text):
        return {"action": "load_and_count", "filePath": file_name}
    if "load" in text:
        return {"action": "load_model", "filePath": file_name}
    if "count" in text or "how many" in text:
        return {"action": "get_entity_count"}
    if "list" in text or "entities" in text:
        return {"action": "list_entities"}

    return {"action": "get_entity_count"}


async def call_llm(user_prompt: str) -> str:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    api_url = os.getenv("LLM_API_URL", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()

    if not api_key or not api_url or not model:
        return json.dumps(_fallback_command(user_prompt))

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()

    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        return json.dumps(_fallback_command(user_prompt))
    return content
