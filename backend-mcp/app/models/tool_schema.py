from typing import List
from pydantic import BaseModel


class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True


class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: List[ToolParameter]


TOOLS = [
    ToolSchema(
        name="load_model",
        description="Load a CAD file into the current workspace.",
        parameters=[
            ToolParameter(
                name="filePath",
                type="string",
                description="Absolute or relative model path, for example gear.step",
                required=True,
            )
        ],
    ),
    ToolSchema(
        name="get_entity_count",
        description="Return number of entities in the current CAD workspace.",
        parameters=[],
    ),
    ToolSchema(
        name="list_entities",
        description="Return entity IDs in the current CAD workspace.",
        parameters=[],
    ),
]
