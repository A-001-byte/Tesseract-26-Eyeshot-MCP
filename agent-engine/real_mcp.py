import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import sys

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["../backend-mcp/server.py"],  # adjust path to P2's server.py
)

def call_tool(tool_name: str, args: dict) -> dict:
    return asyncio.run(_call_tool_async(tool_name, args))

async def _call_tool_async(tool_name: str, args: dict) -> dict:
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
            return result

# Same interface as mock_mcp.py — orchestrator calls these
def load_model(file_path: str) -> dict:
    return call_tool("load_model", {"file_path": file_path})

def list_entities() -> dict:
    return call_tool("list_entities", {})

def get_properties(entity_id: str) -> dict:
    return call_tool("get_properties", {"entity_id": entity_id})

def move_object(entity_id: str, translation: list) -> dict:
    return call_tool("move_object", {"entity_id": entity_id, "translation": translation})