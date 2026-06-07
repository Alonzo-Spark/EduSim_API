"""
tests/sandbox_playground.py
============================
Change PROMPT below and run:

    python tests/sandbox_playground.py

The LLM generates a SandboxSchema JSON, which is validated and printed.
Nothing else needs to change — ever.
"""

import sys, json, re, textwrap, os
from pathlib import Path
sys.path.insert(0, ".")

# Load .env from the project root BEFORE importing anything that reads env vars
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# ─────────────────────────────────────────────────────────────────────────────
# ✏️  CHANGE ONLY THIS LINE
# ─────────────────────────────────────────────────────────────────────────────
PROMPT = "a rocket launching against gravity with thrust controls"
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import ValidationError
from app.src.modules.rag.generator import generate_llm_text
from app.src.modules.sandbox.schemas import SandboxSchema

# ── Terminal colours ──────────────────────────────────────────────────────────
R="\033[0m"; B="\033[1m"; G="\033[92m"; Y="\033[93m"; C="\033[96m"; RE="\033[91m"; BL="\033[94m"
def hdr(t): print(f"\n{B}{C}{'═'*70}\n  {t}\n{'═'*70}{R}")
def sec(t): print(f"\n{B}{Y}  ▶  {t}\n  {'─'*60}{R}")
def ok(m):  print(f"{G}  ✅  {m}{R}")
def err(m): print(f"{RE}  ❌  {m}{R}")
def inf(m): print(f"{BL}  ℹ   {m}{R}")
def pj(label, obj):
    sec(label)
    raw = obj.model_dump() if hasattr(obj, "model_dump") else obj
    print(textwrap.indent(json.dumps(raw, indent=2, default=str), "    "))

# ── System prompt sent to the LLM ─────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are the EduSim Sandbox AI.

Your job is to generate a valid SandboxSchema JSON for the physics scenario described below.

OUTPUT RULES — READ CAREFULLY:
- Output ONLY a single valid JSON object.
- Do NOT include markdown fences (no ```json), no explanation, no comments.
- The JSON must conform EXACTLY to this structure:

{
  "metadata": {
    "author": "ai",
    "ai_context": {
      "scenario_name": "<string>",
      "scenario_tags": ["<string>"],
      "curriculum_topics": ["<string>"],
      "difficulty": <1-5>,
      "generation_notes": "<string>"
    },
    "tutor_context": {
      "learning_objectives": ["<string>"],
      "key_concepts": ["<string>"],
      "assessment_questions": ["<string>"]
    },
    "runtime_config": {
      "canvas_width": 1280,
      "canvas_height": 720,
      "pixels_per_meter": 100.0,
      "simulation_speed": 1.0
    }
  },
  "environment": {
    "gravity": { "x": 0.0, "y": 9.81, "scale": 1.0 },
    "wind": { "enabled": false, "magnitude": 0.0, "direction_deg": 0.0, "turbulence": 0.0 },
    "atmosphere": { "type": "earth", "air_density": 1.225, "drag_coeff": 0.47, "sound_speed": 343.0 },
    "magnetic": { "enabled": false, "strength": 0.0, "direction_x": 0.0, "direction_y": 0.0, "direction_z": 1.0 },
    "fluid": { "enabled": false, "density": 1000.0, "viscosity": 0.001 },
    "lighting": { "background_color": "#0d1b2a", "ambient_light": 0.8, "theme": "dark" }
  },
  "objects": [
    {
      "id": "<unique_string>",
      "name": "<string>",
      "shape_type": "circle|rectangle|polygon",
      "object_type": "<string>",
      "role": "anchor|body|surface|emitter|sensor|reference",
      "position": { "x": <float>, "y": <float> },
      "radius": <float_or_null>,
      "width": <float_or_null>,
      "height": <float_or_null>,
      "is_static": <bool>,
      "tags": ["<string>"],
      "physics": {
        "mass": <float>,
        "restitution": <0-1>,
        "friction": <float>,
        "friction_static": <float>,
        "gravity_scale": 1.0
      },
      "visuals": { "color": "<hex>", "label": "<string>" }
    }
  ],
  "constraints": [
    {
      "id": "<unique_string>",
      "constraint_type": "distance|spring|pivot|pulley|slider",
      "anchor_a": { "body_id": "<object_id>" },
      "anchor_b": { "body_id": "<object_id>" },
      "stiffness": <0-1>,
      "damping": <0-1>,
      "length": <float_or_null>
    }
  ],
  "observables": [
    {
      "id": "<unique_string>",
      "name": "<string>",
      "observable_type": "direct|derived|delta|aggregate",
      "target_object_ids": ["<object_id>"],
      "display": { "label": "<string>", "unit": "<string>", "color": "<hex>", "display_mode": "numeric|graph|vector_arrow" }
    }
  ],
  "controls": [
    {
      "id": "<unique_string>",
      "label": "<string>",
      "widget_type": "slider|toggle|button|select",
      "binding": {
        "scope": "object|environment|simulation",
        "object_id": "<object_id_or_null>",
        "property_path": "<string_or_null>",
        "action": "<string_or_null>"
      },
      "widget_config": {
        "min_value": <float>,
        "max_value": <float>,
        "step": <float>,
        "default_value": <float>,
        "unit": "<string>"
      },
      "group": "<string>",
      "educational_impact": ["<string>"]
    }
  ],
  "relationships": [
    {
      "id": "<unique_string>",
      "name": "<string>",
      "formula_latex": "<latex_string>",
      "formula_description": "<string>",
      "scope": "global|pairwise|object|system",
      "concept_tags": ["<string>"],
      "object_ids": ["<object_id>"],
      "tutor_hints": ["<string>"]
    }
  ]
}

RULES:
- Every constraint's anchor body_id MUST match an existing object id.
- Every observable's target_object_ids must match existing object ids.
- Every control with scope=object must have an object_id matching an existing object.
- Every relationship object_ids must match existing objects.
- circle objects MUST have radius set (not null).
- rectangle objects MUST have width and height set (not null).
- All object ids must be unique. All constraint ids must be unique.
- Use educationally meaningful objects, labels, and relationships.
- Keep it realistic — 2 to 6 objects is ideal.

SCENARIO TO GENERATE:
"""


def extract_json(raw: str) -> str:
    """Strip markdown fences and extract the first { ... } block."""
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    start = raw.find("{")
    end   = raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM response.")
    return raw[start:end+1]


def sanitise(data: dict) -> dict:
    """
    Auto-fix known LLM quirks before Pydantic validation.
    Logs each fix so you can see what was corrected.
    """
    fixes = []
    for obj in data.get("objects", []):
        physics = obj.get("physics", {})
        # LLMs often set mass=0 for static bodies — schema requires mass > 0
        if isinstance(physics.get("mass"), (int, float)) and physics["mass"] <= 0:
            physics["mass"] = 1.0
            fixes.append(f"  • Fixed zero/negative mass on object '{obj.get('id')}' → 1.0")
        # Null mass
        if physics.get("mass") is None:
            physics["mass"] = 1.0
            fixes.append(f"  • Fixed null mass on object '{obj.get('id')}' → 1.0")
    if fixes:
        sec("Auto-fixes applied (LLM quirk corrections)")
        for f in fixes:
            print(f"\033[93m{f}\033[0m")
    return data


def main():
    hdr(f"EduSim Sandbox Playground")
    inf(f"Prompt: \"{PROMPT}\"")

    # 1. Call LLM
    sec("Calling LLM (OpenRouter)…")
    full_prompt = SYSTEM_PROMPT + PROMPT
    raw = generate_llm_text(full_prompt, temperature=0.2, max_output_tokens=4096)

    sec("Raw LLM response (first 300 chars)")
    print(f"    {raw[:300]}{'…' if len(raw) > 300 else ''}")

    # 2. Extract JSON
    sec("Extracting JSON from response")
    try:
        json_str = extract_json(raw)
        data = json.loads(json_str)
        ok("JSON parsed successfully")
    except Exception as e:
        err(f"JSON extraction failed: {e}")
        print(f"\n  Full raw response:\n{raw}")
        return

    # 2b. Sanitise common LLM mistakes
    data = sanitise(data)

    # 3. Validate against SandboxSchema
    sec("Validating against SandboxSchema (Pydantic)")
    try:
        sandbox = SandboxSchema.model_validate(data)
        ok("SandboxSchema validation passed ✓")
    except ValidationError as e:
        err("SandboxSchema validation FAILED")
        print(f"\n{e}")
        sec("Raw parsed JSON (for debugging)")
        print(textwrap.indent(json.dumps(data, indent=2), "    "))
        return

    # 4. Print results
    hdr(f"RESULTS — {sandbox.metadata.ai_context.scenario_name}")

    sec("Summary")
    inf(f"Scenario     : {sandbox.metadata.ai_context.scenario_name}")
    inf(f"Difficulty   : {sandbox.metadata.ai_context.difficulty}/5")
    inf(f"Objects      : {len(sandbox.objects)}  — {[o.id for o in sandbox.objects]}")
    inf(f"Constraints  : {len(sandbox.constraints)}")
    inf(f"Observables  : {len(sandbox.observables)}")
    inf(f"Controls     : {len(sandbox.controls)}")
    inf(f"Relationships: {len(sandbox.relationships)}")

    sec("Learning Objectives")
    for obj in sandbox.metadata.tutor_context.learning_objectives:
        print(f"    • {obj}")

    sec("Key Concepts")
    print(f"    {sandbox.metadata.tutor_context.key_concepts}")

    for obj in sandbox.objects:
        pj(f"Object — {obj.name} ({obj.object_type})", obj)

    for c in sandbox.constraints:
        pj(f"Constraint — {c.id} ({c.constraint_type})", c)

    for o in sandbox.observables:
        pj(f"Observable — {o.name}", o)

    for ctrl in sandbox.controls:
        pj(f"Control — {ctrl.label} ({ctrl.widget_type})", ctrl)

    for r in sandbox.relationships:
        pj(f"Relationship — {r.name}", r)

    pj("Environment", sandbox.environment)

    sec("JSON Round-trip verification")
    restored = SandboxSchema.model_validate(sandbox.model_dump())
    assert restored.metadata.ai_context.scenario_name == sandbox.metadata.ai_context.scenario_name
    ok("Round-trip: model_dump() → model_validate() ✓")

    sec("Full payload size")
    payload = json.dumps(sandbox.model_dump(), default=str)
    inf(f"Total payload: {len(payload):,} characters")

    hdr("DONE ✅")


if __name__ == "__main__":
    main()
