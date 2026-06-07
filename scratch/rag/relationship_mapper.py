import json
from pathlib import Path

REGISTRY_PATH = (
    Path(__file__).parent /
    "registry" /
    "relationship_registry.json"
)

with open(REGISTRY_PATH, "r", encoding="utf-8") as file:
    RELATIONSHIPS = json.load(file)

def map_runtime_event(event: str):
    return RELATIONSHIPS.get(event, "unknown")
