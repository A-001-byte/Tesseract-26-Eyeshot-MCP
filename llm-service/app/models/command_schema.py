from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StructuredCommand(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: Literal[
        "load_model",
        "list_entities",
        "get_entity_properties",
        "measure_distance",
        "load_and_count",
        "boolean_union",
        "boolean_cut",
        "get_mass_properties",
        "move_object",
        "fillet_edges",
        "scale_object",
        "mirror_object",
        "create_assembly",
        "get_scene",
        "modify_dimensions",
        "generate_scene",
    ]
    file_path: Optional[str] = Field(default=None)
    entity_id: Optional[str] = Field(default=None)
    entity1: Optional[str] = Field(default=None)
    entity2: Optional[str] = Field(default=None)
    object_id: Optional[str] = Field(default=None)
    radius: Optional[float] = Field(default=None)
    factor: Optional[float] = Field(default=None)
    plane: Optional[str] = Field(default=None)
    parameter: Optional[str] = Field(default=None)
    value: Optional[float] = Field(default=None)
    unit: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def validate_fields(self):
        normalized_file_path = (self.file_path or "").strip()
        normalized_entity_id = (self.entity_id or "").strip()
        normalized_entity1 = (self.entity1 or "").strip()
        normalized_entity2 = (self.entity2 or "").strip()

        if self.action in {"load_model", "load_and_count"} and normalized_file_path == "":
            raise ValueError("file_path is required for load actions")
        if self.action == "get_entity_properties" and normalized_entity_id == "":
            raise ValueError("entity_id is required for get_entity_properties")
        if self.action == "measure_distance" and (
            normalized_entity1 == "" or normalized_entity2 == ""
        ):
            raise ValueError("entity1 and entity2 are required for measure_distance")
        return self
