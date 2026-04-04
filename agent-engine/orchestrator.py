import real_mcp as mock_mcp
import audit_trail
from agents.validator import validate_tool_call

USE_REAL_MCP = True  # ✅ Flipped to True! Our proxy server is ready!

if USE_REAL_MCP:
    import real_mcp as mcp
else:
    import mock_mcp as mcp

TOOL_MAP = {
    "load_model": mcp.load_model,
    "list_entities": mcp.list_entities,
    "get_properties": mcp.get_properties,
    "move_object":mcp.move_object,
}

import json

def unwrap_response(output) -> dict:
    if hasattr(output, 'content') and isinstance(output.content, list) and len(output.content) > 0:
        try:
            output = json.loads(output.content[0].text)
        except Exception:
            pass
            
    if isinstance(output, dict) and output.get("status") == "error":
        print(f"MCP gracefully handled error: {output.get('message')}")
        
    return output.get("data", output) if isinstance(output, dict) else output

def execute_plan(plan: list):
    results = []
    for step in plan:
        tool = step["tool"]
        args = step.get("args", {})

        validation = validate_tool_call(tool, args)
        if not validation["valid"]:
            audit_trail.log("Orchestrator", tool, args,
                            {"skipped": True, "reason": validation["errors"]}, status="error")
            results.append({"step": step, "skipped": True, "errors": validation["errors"]})
            continue

        fn = TOOL_MAP.get(tool)
        if not fn:
            results.append({"step": step, "error": "Unknown tool"})
            continue

        output = fn(**args)
        output = unwrap_response(output)   # ← added here, right after tool executes
        audit_trail.log("Orchestrator", tool, args, output)
        results.append({"step": step, "output": output})

    return results