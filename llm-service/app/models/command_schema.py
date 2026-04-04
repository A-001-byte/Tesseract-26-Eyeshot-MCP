from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StructuredCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["load_model", "get_entity_count", "list_entities", "load_and_count"]
    filePath: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def validate_fields(self):
        normalized = (self.filePath or "").strip()
        if self.action in {"load_model", "load_and_count"} and normalized == "":
            raise ValueError("filePath is required for load actions")
        if self.action in {"get_entity_count", "list_entities"} and normalized != "":
            raise ValueError("filePath is not allowed for this action")
        return self
