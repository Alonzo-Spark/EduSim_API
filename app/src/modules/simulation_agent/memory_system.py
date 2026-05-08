import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


MEMORY_FILE = Path("data/educational_memory.json")


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def _similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _read_memory() -> list[dict[str, Any]]:
    if not MEMORY_FILE.exists():
        return []
    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_memory(items: list[dict[str, Any]]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=True), encoding="utf-8")


def store_generation_memory(payload: Dict[str, Any]) -> None:
    items = _read_memory()
    prompt = payload.get("prompt", "")
    tokens = sorted(_tokenize(prompt))

    entry = {
        "id": payload.get("id"),
        "prompt": prompt,
        "subject": payload.get("subject"),
        "topic": payload.get("topic"),
        "difficulty": payload.get("difficulty"),
        "blueprint": payload.get("blueprint", {}),
        "quality_score": payload.get("quality_score"),
        "repair_history": payload.get("repair_history", []),
        "tokens": tokens,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    items.insert(0, entry)
    _write_memory(items[:300])


def retrieve_similar_memories(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    query_tokens = _tokenize(query)
    scored = []
    for item in _read_memory():
        score = _similarity(query_tokens, set(item.get("tokens", [])))
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "id": item.get("id"),
            "topic": item.get("topic"),
            "difficulty": item.get("difficulty"),
            "quality_score": item.get("quality_score"),
            "similarity": round(score, 3),
        }
        for score, item in scored[:limit]
    ]


def update_learning_profile(user_id: str | None, interaction_event: Dict[str, Any]) -> Dict[str, Any]:
    profile_file = Path("data/learning_profiles.json")
    if profile_file.exists():
        try:
            profiles = json.loads(profile_file.read_text(encoding="utf-8"))
        except Exception:
            profiles = []
    else:
        profiles = []

    uid = user_id or "anonymous"
    profile_raw = next((p for p in profiles if p.get("user_id") == uid), None)
    
    if profile_raw is None:
        profile_raw = {
            "user_id": uid,
            "weak_topics": [],
            "strong_topics": [],
            "completed_simulations": [],
            "interaction_patterns": {"events": 0, "total_depth": 0, "retries": 0},
            "cognitive": {
                "learning_style": "visual",
                "learning_speed": 1.0,
                "engagement_score": 50,
                "retry_frequency": 0.0
            },
            "quiz_scores": [],
            "mastery": {}, # topic -> MasteryState
        }
        profiles.append(profile_raw)

    event_type = interaction_event.get("type", "generic")
    topic = interaction_event.get("topic")
    simulation_id = interaction_event.get("simulation_id")

    # Update basics
    profile_raw["interaction_patterns"]["events"] += 1
    
    if event_type == "simulation_interaction":
        profile_raw["interaction_patterns"]["total_depth"] += 1
    
    if event_type == "simulation_retry":
        profile_raw["interaction_patterns"]["retries"] = profile_raw["interaction_patterns"].get("retries", 0) + 1
        # Update cognitive speed (heuristic: more retries = slower speed)
        profile_raw["cognitive"]["learning_speed"] = max(0.5, profile_raw["cognitive"]["learning_speed"] * 0.95)
        profile_raw["cognitive"]["retry_frequency"] = profile_raw["interaction_patterns"]["retries"] / profile_raw["interaction_patterns"]["events"]

    if event_type == "quiz_completed":
        score = interaction_event.get("score", 0)
        profile_raw["quiz_scores"].append({"topic": topic, "score": score, "date": datetime.now(timezone.utc).isoformat()})
        
        # Mastery logic
        if topic not in profile_raw["mastery"]:
            profile_raw["mastery"][topic] = {"conceptual": 0, "practical": 0, "overall": 0}
        
        curr_mastery = profile_raw["mastery"][topic]
        curr_mastery["conceptual"] = int((curr_mastery["conceptual"] + score) / 2)
        curr_mastery["overall"] = curr_mastery["conceptual"]

        # Strong vs Weak
        if score > 80:
            if topic not in profile_raw["strong_topics"]: profile_raw["strong_topics"].append(topic)
            if topic in profile_raw["weak_topics"]: profile_raw["weak_topics"].remove(topic)
        elif score < 50:
            if topic not in profile_raw["weak_topics"]: profile_raw["weak_topics"].append(topic)
            if topic in profile_raw["strong_topics"]: profile_raw["strong_topics"].remove(topic)

    if simulation_id and simulation_id not in profile_raw["completed_simulations"]:
        profile_raw["completed_simulations"].append(simulation_id)

    profile_file.parent.mkdir(parents=True, exist_ok=True)
    profile_file.write_text(json.dumps(profiles, indent=2, ensure_ascii=True), encoding="utf-8")
    return profile_raw




def store_runtime_intelligence(simulation_id: str, report: Dict[str, Any], score: Dict[str, Any]) -> None:
    """Store runtime health and telemetry for simulation evolution."""
    runtime_file = Path("data/runtime_intelligence_history.json")
    if runtime_file.exists():
        try:
            history = json.loads(runtime_file.read_text(encoding="utf-8"))
        except Exception:
            history = []
    else:
        history = []

    entry = {
        "simulation_id": simulation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "report": report,
        "score": score
    }
    
    history.insert(0, entry)
    runtime_file.parent.mkdir(parents=True, exist_ok=True)
    runtime_file.write_text(json.dumps(history[:500], indent=2, ensure_ascii=True), encoding="utf-8")

