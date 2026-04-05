import os
from typing import Any, Dict, List
import httpx

from app.services import cad_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:7000")


def _candidate_llm_urls(base_url: str) -> List[str]:
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("/parse") or trimmed.endswith("/generate-command") or trimmed.endswith("/api/v1/parse"):
        return [trimmed]

    return [
        f"{trimmed}/api/v1/parse",
        f"{trimmed}/parse",
        f"{trimmed}/generate-command",
    ]


async def parse_prompt(prompt: str) -> Dict[str, Any]:
    errors: List[str] = []

    async with httpx.AsyncClient(timeout=20.0) as client:
        for llm_parse_url in _candidate_llm_urls(LLM_SERVICE_URL):
            request_payload = {"prompt": prompt}
            if llm_parse_url.endswith("/generate-command"):
                request_payload = {"input": prompt}

            try:
                response = await client.post(llm_parse_url, json=request_payload)
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPError as exc:
                errors.append(f"{llm_parse_url}: {exc}")
                continue

            # New format: LLM returns {"command": "generate_shape", "geometry": {...}, ...}
            if payload.get("command") == "generate_shape":
                return payload  # Return full payload as-is for generate_shape
            
            if payload.get("command") == "generate_gear":
                return payload

            command = payload.get("command")
            if not isinstance(command, dict):
                command = payload.get("structured_command")

            if not isinstance(command, dict):
                # Try treating entire payload as command if it has "action"
                if isinstance(payload, dict) and "action" in payload:
                    return payload
                errors.append(f"{llm_parse_url}: missing command payload")
                continue

            if "file_path" in command and "filePath" not in command:
                command["filePath"] = command.pop("file_path")

            if command.get("action") == "list_entities" and "count" in prompt.lower():
                command = {"action": "get_entity_count"}

            return command

    raise ValueError(
        "LLM service did not return a valid command object. "
        + " | ".join(errors)
    )


def _simulate_agents(command: Dict[str, Any], tool_result: Dict[str, Any]) -> Dict[str, str]:
    action = command.get("action", command.get("command", "unknown"))
    ok = tool_result.get("ok", False)

    structural = (
        f"Structural agent: action {action} executed and CAD state updated."
        if ok
        else f"Structural agent: action {action} failed, model state may be unchanged."
    )
    cost = (
        "Cost agent: no heavy operation detected, compute budget remains low."
        if action in {"get_entity_count", "list_entities"}
        else "Cost agent: model call may increase runtime/memory depending on complexity."
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
    action = command.get("action", command.get("command"))

    # ── New generate_shape pipeline ────────────────────────────────────
    if command.get("command") == "generate_shape":
        steps.append("LLM parsed action: generate_shape")
        audit.append("LLM generated geometry specification")
        steps.append("Forwarding geometry to CAD engine /generate_shape")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{cad_client.CAD_ENGINE_URL}/generate_shape",
                json=command,  # Forward full LLM payload
            )
            response.raise_for_status()
            cad_result = response.json()

        audit.append("CAD engine executed generate_shape")

        return {
            "steps": steps,
            "parsed_command": command,
            "result": {"tool": "generate_shape", "ok": True, "data": cad_result},
            "agents": _simulate_agents({"command": "generate_shape"}, {"ok": True}),
            "audit": audit,
            "name": cad_result.get("name", "generated_shape"),
            "volume_m3": cad_result.get("volume_m3", 0),
            "surface_area_m2": cad_result.get("surface_area_m2", 0),
            "bounding_box": cad_result.get("bounding_box", [0, 0, 0, 1, 1, 1]),
            "step_b64": cad_result.get("step_b64", ""),
            "glb_b64": cad_result.get("glb_b64") or "",
            "mass_kg": cad_result.get("mass_kg", 0),
            "density_kg_m3": cad_result.get("density_kg_m3", 7850),
            "material": cad_result.get("material", "steel"),
            "shape_description": cad_result.get("shape_description", ""),
            "part_type": cad_result.get("part_type") or cad_result.get("shape_description", ""),
        }

    # ── New generate_gear pipeline ─────────────────────────────────────
    if command.get("command") == "generate_gear":
        steps.append("LLM parsed action: generate_gear")
        audit.append("LLM generated gear specification")
        steps.append("Forwarding parameters to CAD engine /generate_gear")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{cad_client.CAD_ENGINE_URL}/generate_gear",
                json=command,
            )
            response.raise_for_status()
            cad_result = response.json()

        audit.append("CAD engine executed generate_gear")

        return {
            "steps": steps,
            "parsed_command": command,
            "result": {"tool": "generate_gear", "ok": True, "data": cad_result},
            "agents": _simulate_agents({"command": "generate_gear"}, {"ok": True}),
            "audit": audit,
            "name": cad_result.get("name", "generated_gear"),
            "id": cad_result.get("id", "gear"),
            "volume_m3": cad_result.get("volume_m3", 0),
            "surface_area_m2": cad_result.get("surface_area_m2", 0),
            "bounding_box": cad_result.get("bounding_box", [0, 0, 0, 1, 1, 1]),
            "step_b64": cad_result.get("step_b64", ""),
            "glb_b64": cad_result.get("glb_b64") or "",
            "mass_kg": cad_result.get("mass_kg", 0),
            "material": cad_result.get("material", "steel"),
            "num_teeth": cad_result.get("num_teeth"),
            "module": cad_result.get("module"),
            "pitch_diameter_mm": cad_result.get("pitch_diameter_mm"),
            "part_type": cad_result.get("part_type", "Gear"),
        }

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

    elif action == "get_bom":
        steps.append("Executing MCP tool: get_bom()")
        tool_result = await cad_client.get_bom()
        audit.append("MCP executed get_bom")

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
        steps.append(f"Executing MCP tool: {action}")
        kwargs = {k: v for k, v in command.items() if k != "action"}
        tool_result = await cad_client.execute_action(action, kwargs)
        audit.append(f"MCP executed {action}")

    agents = _simulate_agents(command, tool_result)
    audit.append("Agent simulation completed")

    result_data = tool_result.get("data", {}) if isinstance(tool_result, dict) else {}
    flat = {}
    if isinstance(result_data, dict) and result_data.get("step_b64"):
        flat = {
            "name": result_data.get("name", "model"),
            "volume_m3": result_data.get("volume_m3", 0),
            "surface_area_m2": result_data.get("surface_area_m2", 0),
            "bounding_box": result_data.get("bounding_box", [0, 0, 0, 1, 1, 1]),
            "step_b64": result_data.get("step_b64", ""),
        }

    return {
        "steps": steps,
        "parsed_command": command,
        "result": tool_result,
        "agents": agents,
        "audit": audit,
        **flat,
    }
