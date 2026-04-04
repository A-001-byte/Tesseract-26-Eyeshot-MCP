from pydantic import BaseModel, Field
from typing import Optional

class StructuredCommand(BaseModel):
    action: str = Field(description="The CAD action to perform (e.g., load_model)")
    file_path: Optional[str] = Field(None, description="Path to model file if loading")
    entity_id: Optional[str] = Field(None, description="ID of entity if querying")
