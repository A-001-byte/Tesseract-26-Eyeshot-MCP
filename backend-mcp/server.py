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
CAD_API_BASE_URL = "http://172.168.0.6:5005"

def log(message: str):
    """
    Simple print logging.
    IMPORTANT: We print to sys.stderr so we don't corrupt the MCP stdio JSON transport layer.
    """
    print(message, file=sys.stderr)

async def check_backend_health():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{CAD_API_BASE_URL}/api/cad/list_entities", timeout=3)
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
    log("[MCP] Calling API: POST /api/cad/load_model")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CAD_API_BASE_URL}/api/cad/load_model",
                json={"filePath": file_path}  # EXACT MATCH: API expects "filePath"
            )
            response.raise_for_status()
            
            # The backend API returns { "message": "Model loaded successfully." }
            payload = response.json()
            api_message = payload.get("message", f"Successfully loaded model from {file_path}")
            
            log("[MCP] Success: Model loaded successfully")
            return {
                "status": "success",
                "message": api_message,
                "data": {}
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
    log("[MCP] Calling API: GET /api/cad/list_entities")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CAD_API_BASE_URL}/api/cad/list_entities")
            response.raise_for_status()
            
            # The backend returns a raw array: [{ "id": "...", "type": "Line" }]
            payload = response.json()
            
            log("[MCP] Success: Entities retrieved successfully")
            return {
                "status": "success",
                "message": f"Successfully retrieved {len(payload)} entities",
                "data": {
                    "entities": payload
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


if __name__ == "__main__":
    log("[MCP] Checking backend connectivity...")
    healthy = asyncio.run(check_backend_health())

    if healthy:
        log("[MCP] Backend reachable ✅")
    else:
        log("[MCP] Backend NOT reachable ❌")

    log("[MCP] Starting MCP server...")
    mcp.run()
