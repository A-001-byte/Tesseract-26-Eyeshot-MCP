import os
from typing import Any, Dict

import httpx


CAD_ENGINE_URL = os.getenv("CAD_ENGINE_URL", "http://localhost:5000")


async def load_model(file_path: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{CAD_ENGINE_URL}/load_model",
            json={"file": file_path},
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
        response = await client.get(f"{CAD_ENGINE_URL}/list_entities")
        response.raise_for_status()
        return {
            "tool": "get_entity_count",
            "ok": True,
            "status_code": response.status_code,
            "data": {"count": len(response.json())},
        }


async def list_entities() -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{CAD_ENGINE_URL}/list_entities")
        response.raise_for_status()
        return {
            "tool": "list_entities",
            "ok": True,
            "status_code": response.status_code,
            "data": response.json(),
        }


async def get_bom() -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{CAD_ENGINE_URL}/bom")
        response.raise_for_status()
        return {
            "tool": "get_bom",
            "ok": True,
            "status_code": response.status_code,
            "data": response.json(),
        }


async def execute_action(action: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{CAD_ENGINE_URL}/{action}",
            json=kwargs,
        )
        response.raise_for_status()
        return {
            "tool": action,
            "ok": True,
            "status_code": response.status_code,
            "data": response.json(),
        }
