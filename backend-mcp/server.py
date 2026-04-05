import sys
import logging
import asyncio
import httpx
from mcp.server.fastmcp import FastMCP

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Silence noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)

# Basic MCP server skeleton
mcp = FastMCP("CAD-Engine-MCP")
CAD_API_BASE_URL = "http://localhost:5000"

def log(message: str):
    """
    Simple print logging.
    IMPORTANT: We print to sys.stderr so we don't corrupt the MCP stdio JSON transport layer.
    """
    print(message, file=sys.stderr)

async def check_backend_health():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{CAD_API_BASE_URL}/health", timeout=3)
            return res.status_code == 200
    except:
        return False

@mcp.tool()
async def load_model(file_path: str) -> dict:
    """
    Load a 3D CAD model into the Eyeshot engine from a designated file path.
    """
    log("[MCP] Tool: load_model")
    log(f"[MCP] Input: {file_path}")
    log("[MCP] Calling API: POST /api/cad/load")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CAD_API_BASE_URL}/load_model",
                json={"file": file_path}
            )
            response.raise_for_status()
            
            payload = response.json()
            api_message = f"Successfully loaded model from {file_path}"
            
            log("[MCP] Success: Model loaded successfully")
            return {
                "status": "success",
                "message": api_message,
                "data": payload
            }
            
        except httpx.HTTPStatusError as e:
            msg = f"API returned non-200 status code: {e.response.status_code}"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except httpx.RequestError as e:
            msg = f"Network failure calling API (Connection Refused/Timeout)"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except ValueError:
            msg = "Invalid JSON response from API"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except Exception as e:
            msg = f"Unexpected error: {str(e)}"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}


@mcp.tool()
async def list_entities() -> dict:
    """
    List all entities currently loaded in the Eyeshot CAD engine.
    """
    log("[MCP] Tool: list_entities")
    log("[MCP] Input: None")
    log("[MCP] Calling API: GET /api/cad/entities/list")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CAD_API_BASE_URL}/list_entities")
            response.raise_for_status()
            
            payload = response.json()
            raw_entities = payload if isinstance(payload, list) else payload.get("data", [])
            
            log("[MCP] Success: Entities retrieved successfully")
            return {
                "status": "success",
                "message": f"Successfully retrieved {len(raw_entities)} entities",
                "data": {
                    "entities": raw_entities
                }
            }
            
        except httpx.HTTPStatusError as e:
            msg = f"API returned non-200 status code: {e.response.status_code}"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except httpx.RequestError as e:
            msg = f"Network failure calling API (Connection Refused/Timeout)"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except ValueError:
            msg = "Invalid JSON response from API"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except Exception as e:
            msg = f"Unexpected error: {str(e)}"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}


@mcp.tool()
async def get_properties(entity_id: str) -> dict:
    """
    Get detailed properties for a specific CAD entity by its ID (e.g. type, layer, visibility, colour).
    """
    log("[MCP] Tool: get_properties")
    log(f"[MCP] Input: {entity_id}")
    log(f"[MCP] Calling API: GET /api/cad/entities/{entity_id}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CAD_API_BASE_URL}/api/cad/entities/{entity_id}")
            response.raise_for_status()
            
            # P2 backend maps properties under "data"
            payload = response.json()
            properties = payload.get("data", {})
            
            log(f"[MCP] Success: Retrieved properties for entity {entity_id}")
            return {
                "status": "success",
                "message": f"Properties retrieved for {entity_id}",
                "data": {
                    "properties": properties
                }
            }
            
        except httpx.HTTPStatusError as e:
            msg = f"API returned non-200 status code: {e.response.status_code}"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except httpx.RequestError as e:
            msg = f"Network failure calling API (Connection Refused/Timeout)"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except ValueError:
            msg = "Invalid JSON response from API"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except Exception as e:
            msg = f"Unexpected error: {str(e)}"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}

@mcp.tool()
async def move_object(entity_id: str, translation: list) -> dict:
    """
    Move a CAD entity by a 3D translation vector [x, y, z].
    """
    log("[MCP] Tool: move_object")
    log(f"[MCP] Input: {entity_id}, {translation}")
    log("[MCP] Calling API: POST /move_object")
    
    x, y, z = 0.0, 0.0, 0.0
    if isinstance(translation, list) and len(translation) >= 3:
        x, y, z = translation[0], translation[1], translation[2]
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CAD_API_BASE_URL}/move_object",
                json={
                    "object_id": entity_id,
                    "x": x,
                    "y": y,
                    "z": z
                }
            )
            response.raise_for_status()
            
            payload = response.json()
            
            log(f"[MCP] Success: Moved entity {entity_id}")
            return {
                "status": "success",
                "message": f"Successfully moved entity {entity_id}",
                "data": payload
            }
            
        except httpx.HTTPStatusError as e:
            msg = f"API returned non-200 status code: {e.response.status_code}"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except httpx.RequestError as e:
            msg = f"Network failure calling API (Connection Refused/Timeout)"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except ValueError:
            msg = "Invalid JSON response from API"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}
        except Exception as e:
            msg = f"Unexpected error: {str(e)}"
            log(f"[MCP] Error: {msg}")
            return {"status": "error", "message": msg, "data": {}}


if __name__ == "__main__":
    log("[MCP] Checking backend connectivity...")
    healthy = asyncio.run(check_backend_health())

    if healthy:
        log("[MCP] Backend reachable ✅")
    else:
        log("[MCP] Backend NOT reachable ❌")

    log("[MCP] Starting MCP server...")
    mcp.run()
