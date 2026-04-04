from app.services.mcp_router import route_to_llm, route_to_cad
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def process_command(instruction: str):
    """
    Orchestrates the flow:
    1. Sends NL instruction to LLM to get structured MCP tools format.
    2. Uses structured format to call CAD operations.
    """
    logger.info("Processing generic command...")
    
    # 1. Parse natural language into structured JSON using LLM Service
    llm_response = await route_to_llm(instruction)
    structured_command = llm_response.get("structured_command")
    
    if not structured_command:
        raise ValueError("Failed to parse instruction via LLM.")

    # 2. Execute against CAD Engine
    cad_response = await route_to_cad(structured_command)
    
    return {
        "parsed_command": structured_command,
        "cad_response": cad_response
    }
