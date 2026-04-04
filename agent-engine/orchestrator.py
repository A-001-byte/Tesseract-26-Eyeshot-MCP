import json
import audit_trail
from agents.validator import validate_tool_call

USE_REAL_MCP = True  # ✅ Flipped to True! Our proxy server is ready!


if USE_REAL_MCP:
    import real_mcp as mcp
else:
    import mock_mcp as mcp

import audit_trail
from agents.validator import validate_tool_call
from agents.executor import execute_step
from agents.critic import review_results

TOOL_MAP = {
    "load_model": mcp.load_model,
    "list_entities": mcp.list_entities,
    "get_properties": mcp.get_properties,
    "move_object": mcp.move_object,
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

def execute_plan(plan: list, user_prompt: str = "") -> dict:
    results = []

    for step in plan:
        tool = step["tool"]
        args = step.get("args", {})

        # Validator Agent
        validation = validate_tool_call(tool, args)
        if not validation["valid"]:
            audit_trail.log("Orchestrator", tool, args,
                            {"skipped": True, "reason": validation["errors"]}, status="error")
            results.append({"step": step, "skipped": True, "errors": validation["errors"]})
            continue

        # Executor Agent
        result = execute_step(tool, args, TOOL_MAP)
        if "output" in result:
            result["output"] = unwrap_response(result["output"])
        results.append({"step": step, **result})

    # Critic Agent — reviews everything after execution
    review = {}
    if user_prompt:
        print("\n=== CRITIC AGENT REVIEWING ===")
        review = review_results(user_prompt, results)
        print(json.dumps(review, indent=2))

    return {"results": results, "review": review}