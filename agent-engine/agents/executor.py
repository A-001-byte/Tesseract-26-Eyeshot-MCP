import audit_trail

def execute_step(tool_name: str, args: dict, tool_map: dict) -> dict:
    fn = tool_map.get(tool_name)
    if not fn:
        result = {"error": f"Unknown tool: {tool_name}"}
        audit_trail.log("Executor", tool_name, args, result, status="error")
        return result

    try:
        output = fn(**args)
        audit_trail.log("Executor", tool_name, args, output, status="ok")
        return {"output": output}
    except Exception as e:
        result = {"error": str(e)}
        audit_trail.log("Executor", tool_name, args, result, status="error")
        return result