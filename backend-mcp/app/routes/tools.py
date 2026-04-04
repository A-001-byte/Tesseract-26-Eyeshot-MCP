from fastapi import APIRouter, HTTPException

from app.models.request_models import ChatRequest, LoadModelRequest
from app.models.tool_schema import TOOLS
from app.services.cad_client import get_entity_count, list_entities, load_model
from app.services.command_router import route_prompt
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.get("/tools")
async def get_tools_schema():
    return {"tools": [tool.model_dump() for tool in TOOLS]}


@router.post("/tools/load_model")
async def tool_load_model(request: LoadModelRequest):
    try:
        return await load_model(request.filePath)
    except Exception as e:
        logger.error(f"Error in load_model tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/get_entity_count")
async def tool_get_entity_count():
    try:
        return await get_entity_count()
    except Exception as e:
        logger.error(f"Error in get_entity_count tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/list_entities")
async def tool_list_entities():
    try:
        return await list_entities()
    except Exception as e:
        logger.error(f"Error in list_entities tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(request: ChatRequest):
    logger.info(f"Received chat prompt: {request.prompt}")
    try:
        return await route_prompt(request.prompt)
    except Exception as e:
        logger.error(f"Error in /chat flow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
