import json
from pathlib import Path

BASE_PATH = Path(__file__).parent / "curriculum"

def load_json(path: Path, fallback=None):
    if path.exists():
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    return fallback or {}

def retrieve_concept(topic: str):
    path = BASE_PATH / "concepts" / f"{topic}.json"
    fallback_path = BASE_PATH / "concepts" / "default.json"
    fallback = load_json(fallback_path)
    return load_json(path, fallback)

def retrieve_formulas(topic: str):
    path = BASE_PATH / "formulas" / f"{topic}.json"
    return load_json(path, {"formulas": []})

def retrieve_misconceptions(topic: str):
    path = BASE_PATH / "misconceptions" / f"{topic}.json"
    return load_json(path, {"misconceptions": []})

def retrieve_experiments(topic: str):
    path = BASE_PATH / "experiments" / f"{topic}.json"
    return load_json(path, {"experiments": []})

def retrieve_hints(topic: str):
    path = BASE_PATH / "hints" / f"{topic}.json"
    return load_json(path, {"hints": []})

def build_metadata(topic_data: dict):
    return {
        "difficulty": topic_data.get("difficulty"),
        "relationships": topic_data.get("relationships", []),
        "aliases": topic_data.get("aliases", [])
    }
