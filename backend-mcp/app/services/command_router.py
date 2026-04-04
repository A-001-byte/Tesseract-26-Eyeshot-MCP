import os
from typing import Any, Dict, List

import httpx

from app.services import cad_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:7000")


async def parse_prompt(prompt: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(f"{LLM_SERVICE_URL}/parse", json={"prompt": prompt})
        response.raise_for_status()
        payload = response.json()

    command = payload.get("command")
    if not isinstance(command, dict):
        raise ValueError("LLM service did not return a valid command object.")
    return command


def _simulate_agents(command: Dict[str, Any], tool_result: Dict[str, Any]) -> Dict[str, str]:
    action = command.get("action", "unknown")
    ok = tool_result.get("ok", False)

    structural = (
        f"Structural agent: action {action} executed and CAD state updated."
        if ok
        else f"Structural agent: action {action} failed, model state may be unchanged."
    )
    cost = (
        "Cost agent: no heavy operation detected, compute budget remains low."
        if action in {"get_entity_count", "list_entities"}
        else "Cost agent: model load may increase runtime/memory depending on file size."
    )
    validation = (
        "Validation agent: response schema is valid and includes tool output."
        if ok
        else "Validation agent: execution failed, check audit trail and upstream service status."
    )

    return {
        "structural": structural,
        "cost": cost,
        "validation": validation,
    }


async def route_prompt(prompt: str) -> Dict[str, Any]:
    steps: List[str] = []
    audit: List[str] = []

    audit.append("User submitted prompt")

    command = await parse_prompt(prompt)
    action = command.get("action")

    steps.append(f"LLM parsed action: {action}")
    audit.append("LLM generated structured command")

    if action == "load_model":
        file_path = command.get("filePath")
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("load_model requires a non-empty filePath")
        steps.append(f"Executing MCP tool: load_model({file_path})")
        tool_result = await cad_client.load_model(file_path)
        audit.append("MCP executed load_model")

    elif action == "get_entity_count":
        steps.append("Executing MCP tool: get_entity_count()")
        tool_result = await cad_client.get_entity_count()
        audit.append("MCP executed get_entity_count")

    elif action == "list_entities":
        steps.append("Executing MCP tool: list_entities()")
        tool_result = await cad_client.list_entities()
        audit.append("MCP executed list_entities")

    elif action == "load_and_count":
        file_path = command.get("filePath")
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("load_and_count requires a non-empty filePath")
        steps.append(f"Executing MCP tool: load_model({file_path})")
        load_result = await cad_client.load_model(file_path)
        steps.append("MCP executed load_model")
        audit.append("MCP executed load_model")
        steps.append("Executing MCP tool: get_entity_count()")
        try:
            count_result = await cad_client.get_entity_count()
            tool_result = {
                "tool": "load_and_count",
                "ok": load_result.get("ok", False) and count_result.get("ok", False),
                "data": {
                    "load": load_result,
                    "count": count_result,
                },
            }
            audit.append("MCP executed get_entity_count")
        except Exception as exc:
            logger.error("load_and_count failed during get_entity_count", exc_info=exc)
            tool_result = {
                "tool": "load_and_count",
                "ok": False,
                "data": {
                    "load": load_result,
                    "count_error": str(exc),
                },
            }
            audit.append("MCP get_entity_count failed")

    else:
        raise ValueError(f"Unsupported action: {action}")

    agents = _simulate_agents(command, tool_result)
    audit.append("Agent simulation completed")

    return {
        "steps": steps,
        "parsed_command": command,
        "result": tool_result,
        "agents": agents,
        "audit": audit,
    }
