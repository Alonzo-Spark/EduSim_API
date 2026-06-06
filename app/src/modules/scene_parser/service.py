"""
EduSim Scene Parser Service
Parses a physics example into a structured simulation scene description,
including recommended sandbox asset IDs that match the frontend assetsRegistry.
"""

import re
import json
import logging
from typing import Any, Dict, List

from app.src.modules.legacy_rag.generator import generate_openrouter_text_async

logger = logging.getLogger(__name__)

# ─── Asset ID lookup table ───────────────────────────────────────────────────
# Maps generic LLM-returned object types → actual asset IDs used in assetsRegistry.ts

ASSET_ID_MAP: Dict[str, str] = {
    # Blocks / cubes
    "block":          "cube-small",
    "cube":           "cube-small",
    "small_block":    "cube-small",
    "large_block":    "cube-large",
    "small_cube":     "cube-small",
    "large_cube":     "cube-large",
    # Spheres / balls
    "sphere":         "ball-small",
    "ball":           "ball-small",
    "small_ball":     "ball-small",
    "large_ball":     "ball-large",
    "bouncy_ball":    "bouncy-ball",
    "rubber_ball":    "bouncy-ball",
    # Inclined planes / ramps / wedges
    "inclined_plane": "wedge",
    "ramp":           "wedge",
    "wedge":          "wedge",
    "slope":          "wedge",
    # Surfaces / structures
    "floor":          "platform",
    "platform":       "platform",
    "surface":        "platform",
    "ground":         "platform",
    "wall":           "wall",
    # Springs
    "spring":         "bouncy-ball",
    # Masses / weights
    "hanging_mass":   "weight",
    "weight":         "weight",
    "mass":           "weight",
    "test_mass":      "test-mass",
    # Projectiles
    "projectile":     "projectile",
    # Pendulums
    "pendulum":       "ball-small",
    "pendulum_bob":   "ball-small",
    # Celestial
    "planet":         "earth",
    "earth":          "earth",
    "moon":           "moon",
    "satellite":      "satellite",
    "star":           "sun",
    "sun":            "sun",
    "asteroid":       "asteroid",
    # Vehicles
    "vehicle":        "car",
    "car":            "car",
    # Physics specials
    "heavy_disk":     "heavy-disk",
    "plank":          "plank",
    "disk":           "heavy-disk",
    "pillar":         "pillar",
    "cork":           "cork",
    "ice_cube":       "ice-cube",
    "lead_ball":      "lead-ball",
    "sensor":         "sensor-ball",
    "rubber_block":   "rubber-cube",
}

def _map_asset_ids(recommended: List[str]) -> List[str]:
    """
    Convert generic LLM asset type names into actual assetsRegistry IDs.
    Preserves order and deduplicates.
    """
    seen: set = set()
    result: List[str] = []

    for item in recommended:
        normalized = item.lower().replace("-", "_").replace(" ", "_")
        asset_id = ASSET_ID_MAP.get(normalized, normalized)
        if asset_id not in seen:
            seen.add(asset_id)
            result.append(asset_id)

    return result


# ─── Scene parser prompt ──────────────────────────────────────────────────────

_SCENE_PARSER_PROMPT = """You are the AI Scene Understanding Engine for EduSim.

Analyze the physics example below and return ONLY valid JSON matching this exact schema.

STRICT RULES:
- Return ONLY valid JSON. No markdown. No explanations. No extra text.
- Use lowercase snake_case for all type fields.
- recommended_assets MUST only contain values from this approved list:
  block, cube, sphere, ball, small_ball, large_ball, bouncy_ball,
  inclined_plane, ramp, wedge, floor, platform, surface, wall,
  hanging_mass, weight, mass, projectile, pendulum, pendulum_bob,
  spring, planet, earth, moon, satellite, star, sun, asteroid,
  vehicle, car, plank, pillar, heavy_disk, disk, lead_ball,
  ice_cube, rubber_block, sensor

OUTPUT SCHEMA:
{
  "topic": "",
  "scene_type": "",
  "difficulty": "easy|medium|hard",
  "objects": [
    {
      "id": "obj_1",
      "type": "",
      "count": 1,
      "properties": {},
      "tags": []
    }
  ],
  "relationships": [
    {
      "from": "obj_1",
      "to": "obj_2",
      "type": "",
      "properties": {}
    }
  ],
  "physics_concepts": [],
  "environment": {
    "gravity": true,
    "friction": false,
    "air_resistance": false,
    "magnetic_field": false,
    "electric_field": false,
    "surface": "",
    "reference_frame": "ground"
  },
  "constraints": [],
  "recommended_assets": [],
  "simulation_goals": [],
  "confidence": 0.0
}

PHYSICS EXAMPLE:
"""


async def parse_scene(user_input: str) -> Dict[str, Any]:
    """
    Parse a physics example string and return a structured simulation scene dict
    with recommended asset IDs mapped to the frontend assetsRegistry.
    """
    if not user_input or not user_input.strip():
        return _empty_scene("Empty input provided.")

    prompt = _SCENE_PARSER_PROMPT + user_input.strip()

    try:
        raw = await generate_openrouter_text_async(
            prompt=prompt,
            temperature=0.1,      # deterministic
            max_output_tokens=800,
            system_prompt=None,   # no extra system prompt — JSON only
            response_format={"type": "json_object"}
        )

        if not raw or "Error:" in raw:
            logger.warning("[SceneParser] LLM returned empty or error response.")
            return _empty_scene("LLM failed to parse scene.")

        # Extract JSON block robustly
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not json_match:
            logger.warning("[SceneParser] No JSON found in LLM output: %s", raw[:200])
            return _empty_scene("No valid JSON returned by LLM.")

        parsed: Dict[str, Any] = json.loads(json_match.group())

        # Map LLM asset names → actual assetsRegistry IDs
        raw_assets: List[str] = parsed.get("recommended_assets", [])
        parsed["recommended_assets"] = _map_asset_ids(raw_assets)

        logger.info(
            "[SceneParser] Parsed scene: topic=%s | assets=%s",
            parsed.get("topic", "?"),
            parsed["recommended_assets"],
        )

        return parsed

    except json.JSONDecodeError as e:
        logger.error("[SceneParser] JSON decode error: %s", e)
        return _empty_scene(f"JSON parse error: {e}")
    except Exception as e:
        logger.error("[SceneParser] Unexpected error: %s", e)
        return _empty_scene(f"Scene parser error: {e}")


def _empty_scene(reason: str) -> Dict[str, Any]:
    return {
        "topic": "",
        "scene_type": "",
        "difficulty": "",
        "objects": [],
        "relationships": [],
        "physics_concepts": [],
        "environment": {
            "gravity": True,
            "friction": False,
            "air_resistance": False,
            "magnetic_field": False,
            "electric_field": False,
            "surface": "",
            "reference_frame": "ground",
        },
        "constraints": [],
        "recommended_assets": [],
        "simulation_goals": [],
        "confidence": 0.0,
        "error": reason,
    }
