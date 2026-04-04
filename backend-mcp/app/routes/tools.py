from fastapi import APIRouter, HTTPException
from app.models.request_models import CommandRequest
from app.services.command_handler import process_command
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.post("/execute")
async def execute_tool(request: CommandRequest):
    """
    Primary MCP tool execution endpoint.
    Expects natural language or structured instruction, which is handled accordingly.
    """
    logger.info(f"Received instruction to process: {request.instruction}")
    try:
        # Route to the command handler that talks to LLM and then CAD Engine
        response = await process_command(request.instruction)
        return {"status": "success", "result": response}
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
