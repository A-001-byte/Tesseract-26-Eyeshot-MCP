import os
from typing import Any, Dict

import httpx


CAD_ENGINE_URL = os.getenv("CAD_ENGINE_URL", "http://localhost:5000")


async def load_model(file_path: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{CAD_ENGINE_URL}/api/cad/load",
            json={"filePath": file_path},
        )
        response.raise_for_status()
        return {
            "tool": "load_model",
            "ok": True,
            "status_code": response.status_code,
            "data": response.json(),
        }


async def get_entity_count() -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{CAD_ENGINE_URL}/api/cad/entities/count")
        response.raise_for_status()
        return {
            "tool": "get_entity_count",
            "ok": True,
            "status_code": response.status_code,
            "data": response.json(),
        }


async def list_entities() -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{CAD_ENGINE_URL}/api/cad/entities/list")
        response.raise_for_status()
        return {
            "tool": "list_entities",
            "ok": True,
            "status_code": response.status_code,
            "data": response.json(),
        }
