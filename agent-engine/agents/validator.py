# Checks if a planned operation is safe/valid before execution
import audit_trail

KNOWN_ENTITY_IDS = {"entity_1", "entity_2"}  # Will come from real MCP later

def validate_tool_call(tool: str, args: dict) -> dict:
    errors = []

    if tool == "get_properties":
        if args.get("entity_id") not in KNOWN_ENTITY_IDS:
            errors.append(f"Unknown entity_id: {args['entity_id']}")

    if tool == "move_object":
        if args.get("entity_id") not in KNOWN_ENTITY_IDS:
            errors.append(f"Unknown entity_id: {args['entity_id']}")
            
        t = args.get("translation", [])
        if len(t) != 3:
            errors.append("Translation must be [x, y, z]")
        if any(abs(v) > 1000 for v in t):
            errors.append("Translation value seems unreasonably large")

    result = {"valid": len(errors) == 0, "errors": errors}
    audit_trail.log("Validator", f"validate:{tool}", args, result,
                    status="ok" if result["valid"] else "warning")
    return result