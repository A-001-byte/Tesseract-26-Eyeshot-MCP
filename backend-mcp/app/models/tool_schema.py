from pydantic import BaseModel
from typing import List, Optional

class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True

class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: List[ToolParameter]

# Example MCP Tool Schema representation
STUB_TOOL_SCHEMA = {
    "tools": [
        {
            "name": "load_model",
            "description": "Loads a 3D model file into the CAD workspace",
            "parameters": [
                {
                    "name": "file_path",
                    "type": "string",
                    "description": "Absolute or relative path to the STEP/IGES file",
                    "required": True
                }
            ]
        }
    ]
}
