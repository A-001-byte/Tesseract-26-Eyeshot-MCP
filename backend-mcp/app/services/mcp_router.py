# This module acts as the pseudo-MCP (Model Context Protocol) abstraction layer
import json
import httpx
from app.models.tool_schema import STUB_TOOL_SCHEMA
from app.utils.logger import get_logger

logger = get_logger(__name__)

# LLM Service url
LLM_SERVICE_URL = "http://localhost:8001/api/v1/parse"
# CAD Engine url
CAD_ENGINE_URL = "http://localhost:5000/api/cad"

async def route_to_llm(instruction: str) -> dict:
    """Sends natural language to the LLM Service to get structured CAD commands."""
    logger.info("Routing instruction to LLM Service...")
    async with httpx.AsyncClient() as client:
        response = await client.post(LLM_SERVICE_URL, json={"prompt": instruction})
        response.raise_for_status()
        return response.json()

async def route_to_cad(structured_command: dict) -> dict:
    """Sends the structured JSON command to the CAD Engine."""
    logger.info(f"Routing command to CAD Engine: {structured_command}")
    
    # We map the action from the JSON command to the respective CAD endpoint
    action = structured_command.get("action")
    
    async with httpx.AsyncClient() as client:
        # Example mapping logic
        if action == "load_model":
            res = await client.post(f"{CAD_ENGINE_URL}/load", json={
                "filePath": structured_command.get("file_path", "")
            })
        elif action == "list_entities":
            res = await client.get(f"{CAD_ENGINE_URL}/entities")
        else:
            return {"error": f"Unknown action: {action}"}
            
        res.raise_for_status()
        return res.json()
