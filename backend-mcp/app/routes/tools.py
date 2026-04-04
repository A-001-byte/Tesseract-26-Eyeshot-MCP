import uuid

import httpx
from fastapi import APIRouter, HTTPException

from app.models.request_models import ChatRequest, LoadModelRequest
from app.models.tool_schema import TOOLS
from app.services.cad_client import get_entity_count, list_entities, load_model
from app.services.command_router import route_prompt
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.get("")
async def get_tools_root():
    return {"tools": [tool.model_dump() for tool in TOOLS]}


@router.get("/tools")
async def get_tools_schema():
    return {"tools": [tool.model_dump() for tool in TOOLS]}


@router.post("/tools/load_model")
async def tool_load_model(request: LoadModelRequest):
    try:
        return await load_model(request.filePath)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.error("load_model validation error", exc_info=exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        logger.error("load_model upstream status error", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream error")
    except httpx.TimeoutException as exc:
        logger.error("load_model timeout", exc_info=exc)
        raise HTTPException(status_code=504, detail="Upstream timeout")
    except httpx.RequestError as exc:
        logger.error("load_model upstream error", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream request failed")
    except Exception as exc:
        logger.error("load_model unexpected error", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tools/get_entity_count")
async def tool_get_entity_count():
    try:
        return await get_entity_count()
    except HTTPException:
        raise
    except ValueError as exc:
        logger.error("get_entity_count validation error", exc_info=exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        logger.error("get_entity_count upstream status error", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream error")
    except httpx.TimeoutException as exc:
        logger.error("get_entity_count timeout", exc_info=exc)
        raise HTTPException(status_code=504, detail="Upstream timeout")
    except httpx.RequestError as exc:
        logger.error("get_entity_count upstream error", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream request failed")
    except Exception as exc:
        logger.error("get_entity_count unexpected error", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tools/list_entities")
async def tool_list_entities():
    try:
        return await list_entities()
    except HTTPException:
        raise
    except ValueError as exc:
        logger.error("list_entities validation error", exc_info=exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        logger.error("list_entities upstream status error", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream error")
    except httpx.TimeoutException as exc:
        logger.error("list_entities timeout", exc_info=exc)
        raise HTTPException(status_code=504, detail="Upstream timeout")
    except httpx.RequestError as exc:
        logger.error("list_entities upstream error", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream request failed")
    except Exception as exc:
        logger.error("list_entities unexpected error", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/chat")
async def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())
    logger.info("Received chat request_id=%s prompt_length=%s", request_id, len(request.prompt))
    if logger.isEnabledFor(10):
        preview = (request.prompt or "").strip().replace("\n", " ")[:80]
        logger.debug("Chat prompt preview request_id=%s preview=%s", request_id, preview)
    try:
        return await route_prompt(request.prompt)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.error("chat validation error", exc_info=exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        logger.error("chat upstream status error", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream error")
    except httpx.TimeoutException as exc:
        logger.error("chat timeout", exc_info=exc)
        raise HTTPException(status_code=504, detail="Upstream timeout")
    except httpx.RequestError as exc:
        logger.error("chat upstream error", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream request failed")
    except Exception as exc:
        logger.error("chat unexpected error", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")
