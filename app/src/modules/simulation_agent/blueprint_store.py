import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

BLUEPRINT_FILE = Path("data/simulation_blueprints.json")


def _read_blueprints():
    if not BLUEPRINT_FILE.exists():
        return []
    with open(BLUEPRINT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_blueprints(items):
    BLUEPRINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BLUEPRINT_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=True)


def list_blueprints(limit: int = 30):
    return _read_blueprints()[:limit]


def get_blueprint(simulation_id: str):
    for item in _read_blueprints():
        if item.get("id") == simulation_id:
            return item
    return None


def store_blueprint(blueprint: Dict[str, Any]):
    items = _read_blueprints()
    blueprint_entry = {
        "id": blueprint.get("id"),
        "prompt": blueprint.get("prompt"),
        "topic": blueprint.get("topic"),
        "formulas": blueprint.get("formulas", []),
        "structure": blueprint.get("structure", {}),
        "html_path": blueprint.get("html_path"),
        "created_at": blueprint.get("created_at", datetime.utcnow().isoformat()),
        "versions": blueprint.get("versions", []),
        "repair_history": blueprint.get("repair_history", []),
        "quality_score": blueprint.get("quality_score", None),
    }
    items.insert(0, blueprint_entry)
    # Keep last 200
    items = items[:200]
    _write_blueprints(items)
    return blueprint_entry


def append_repair_history(simulation_id: str, repair_entry: Dict[str, Any]):
    items = _read_blueprints()
    for item in items:
        if item.get("id") == simulation_id:
            hist = item.get("repair_history", [])
            hist.append(repair_entry)
            item["repair_history"] = hist
            _write_blueprints(items)
            return item
    return None


def update_quality_score(simulation_id: str, score: float):
    items = _read_blueprints()
    for item in items:
        if item.get("id") == simulation_id:
            item["quality_score"] = score
            _write_blueprints(items)
            return item
    return None


def add_blueprint_version(simulation_id: str, version_label: str, html_path: str):
    items = _read_blueprints()
    for item in items:
        if item.get("id") == simulation_id:
            versions = item.get("versions", [])
            versions.append({"version": version_label, "path": html_path})
            item["versions"] = versions
            _write_blueprints(items)
            return item
    return None
