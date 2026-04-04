# Simulates MCP server responses until P2 is ready
import random

def load_model(file_path: str):
    return {"status": "success", "model": file_path, "entities": 5}

def list_entities():
    return [
        {"id": "entity_1", "type": "Box", "volume": 1000.0},
        {"id": "entity_2", "type": "Cylinder", "volume": 314.15},
    ]

def get_properties(entity_id: str):
    props = {
        "entity_1": {"type": "Box", "width": 10, "height": 10, "depth": 10},
        "entity_2": {"type": "Cylinder", "radius": 5, "height": 20},
    }
    return props.get(entity_id, {"error": "Entity not found"})

def move_object(entity_id: str, translation: list):
    return {"status": "moved", "entity_id": entity_id, "delta": translation}
