import json
from pathlib import Path
from typing import Any, Dict

from .agentic_models import CurriculumProfile
from .models import SimulationTopic
from .llm_client import call_llm


CURRICULUM_FILE = Path("app/src/data/curriculum.json")

DEFAULT_CURRICULUM = {
    "physics": {
        "class_8": {
            "chapters": {
                "Force and Pressure": {
                    "outcomes": [
                        "Explain contact and non-contact forces",
                        "Relate force to motion changes",
                    ],
                    "prerequisites": ["Basic motion", "Units"],
                }
            }
        }
    }
}


def _load_curriculum() -> Dict[str, Any]:
    if not CURRICULUM_FILE.exists():
        return DEFAULT_CURRICULUM

    try:
        raw = CURRICULUM_FILE.read_text(encoding="utf-8").strip()
        if not raw:
            return DEFAULT_CURRICULUM
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else DEFAULT_CURRICULUM
    except (json.JSONDecodeError, Exception):
        return DEFAULT_CURRICULUM


def map_curriculum(
    topic: SimulationTopic,
    class_level: str | None,
    board: str | None,
    chapter: str | None,
    difficulty: str | None,
    subject_override: str | None,
) -> CurriculumProfile:
    """
    Map a simulation topic to the appropriate curriculum profile.
    """
    curriculum = _load_curriculum()
    subject = (subject_override or topic.subject or "physics").lower()
    
    class_label = class_level or topic.grade_level or "8"
    class_key = f"class_{str(class_label).replace('class ', '').strip()}"
    
    # Try rule-based chapter inference
    chapter_label = chapter or _infer_chapter(topic.topic)
    
    subject_map = curriculum.get(subject, {})
    class_map = subject_map.get(class_key, {})
    chapter_map = class_map.get("chapters", {}).get(chapter_label, {})
    
    outcomes = chapter_map.get("outcomes", [])
    prerequisites = chapter_map.get("prerequisites", [])

    # If rule-based mapping is sparse, use LLM intelligence
    if not outcomes or chapter_label == "General":
        llm_mapping = _map_curriculum_with_llm(topic, class_label, board)
        chapter_label = chapter or llm_mapping.get("chapter", chapter_label)
        outcomes = outcomes or llm_mapping.get("outcomes", [])
        prerequisites = prerequisites or llm_mapping.get("prerequisites", [])

    progression = _build_progression(prerequisites, chapter_label, topic.topic)

    return CurriculumProfile(
        class_level=str(class_label),
        board=board or "CBSE",
        subject=subject,
        chapter=chapter_label,
        difficulty=difficulty or topic.complexity,
        outcomes=outcomes,
        prerequisites=prerequisites,
        progression_path=progression,
    )


def _map_curriculum_with_llm(topic: SimulationTopic, grade: str, board: str | None) -> Dict[str, Any]:
    """
    Use LLM to infer curriculum details when local data is missing.
    """
    prompt = f"""
    # Task: Map Topic to Curriculum
    Identify the appropriate chapter, learning outcomes, and prerequisites for this topic.
    
    Topic: {topic.topic}
    Subject: {topic.subject}
    Grade: {grade}
    Board: {board or 'Standard K-12'}
    
    ## Output Format
    Return ONLY a JSON object:
    {{
        "chapter": "string",
        "outcomes": ["string"],
        "prerequisites": ["string"]
    }}
    """
    try:
        response = call_llm(prompt, temperature=0.1, response_mime_type="application/json")
        return json.loads(response)
    except Exception:
        return {{"chapter": "General", "outcomes": ["Understand the concept"], "prerequisites": []}}


def _infer_chapter(topic_name: str) -> str:
    t = topic_name.lower()
    if any(k in t for k in ["projectile", "motion", "kinematic", "speed", "velocity"]):
        return "Motion"
    if any(k in t for k in ["light", "refraction", "reflection", "lens", "mirror"]):
        return "Light"
    if any(k in t for k in ["force", "newton", "pressure", "gravity"]):
        return "Force and Pressure"
    return "General"


def _build_progression(prerequisites: list[str], chapter: str, topic: str) -> list[str]:
    path = []
    path.extend(prerequisites)
    path.append(chapter)
    if topic.lower() not in chapter.lower():
        path.append(topic)
    path.append("Assessment and reinforcement")
    return path
