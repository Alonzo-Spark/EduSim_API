"""
DSL Prompt Builder for EduSim Simulation Synthesis.

Generates a structured, schema-aware prompt that instructs Gemini to produce
a valid Physics DSL JSON object — no HTML, no JS, no rendering logic.
"""

import json

# =========================================================
# Few-Shot Examples
# =========================================================

_EXAMPLE_NEWTON_SECOND_LAW = {
    "simulation_type": "newton_second_law",
    "topic": "Motion",
    "environment": {
        "gravity": 9.8,
        "friction": 0.2,
        "air_resistance": 0.0
    },
    "entities": [
        {
            "id": "block1",
            "type": "block",
            "mass": 5.0,
            "properties": {}
        }
    ],
    "interactions": [
        {
            "type": "apply_force",
            "target": "block1",
            "parameters": {"force": [20, 0]}
        },
        {
            "type": "friction",
            "target": "block1",
            "parameters": {"mu_kinetic": 0.2, "mu_static": 0.3}
        }
    ],
    "visualizations": [
        {"type": "force_vectors"},
        {"type": "acceleration_graph"}
    ],
    "equations": ["F = ma", "a = F_net / m", "F_friction = mu * N"]
}

_EXAMPLE_PROJECTILE_MOTION = {
    "simulation_type": "projectile_motion",
    "topic": "Projectile Motion",
    "environment": {
        "gravity": 9.8,
        "friction": 0.0,
        "air_resistance": 0.0
    },
    "entities": [
        {
            "id": "projectile1",
            "type": "projectile",
            "mass": 1.0,
            "properties": {}
        }
    ],
    "interactions": [
        {
            "type": "projectile_launch",
            "target": "projectile1",
            "parameters": {"angle_deg": 45.0, "initial_speed": 20.0}
        },
        {
            "type": "gravity",
            "target": "projectile1",
            "parameters": {"g": 9.8}
        }
    ],
    "visualizations": [
        {"type": "trajectory_path"},
        {"type": "velocity_graph"},
        {"type": "motion_trace"}
    ],
    "equations": [
        "x = v0 * cos(theta) * t",
        "y = v0 * sin(theta) * t - 0.5 * g * t^2",
        "R = v0^2 * sin(2*theta) / g"
    ]
}

_EXAMPLE_INCLINED_PLANE = {
    "simulation_type": "inclined_plane_friction",
    "topic": "Inclined Plane",
    "environment": {
        "gravity": 9.8,
        "friction": 0.3,
        "air_resistance": 0.0
    },
    "entities": [
        {
            "id": "block1",
            "type": "block",
            "mass": 3.0,
            "properties": {}
        },
        {
            "id": "plane1",
            "type": "plane",
            "mass": None,
            "properties": {"angle_deg": 30.0}
        }
    ],
    "interactions": [
        {
            "type": "incline",
            "target": "block1",
            "parameters": {"angle_deg": 30.0}
        },
        {
            "type": "gravity",
            "target": "block1",
            "parameters": {"g": 9.8}
        },
        {
            "type": "normal_force",
            "target": "block1",
            "parameters": {"surface_normal": [0, 1]}
        },
        {
            "type": "friction",
            "target": "block1",
            "parameters": {"mu_kinetic": 0.3, "mu_static": 0.4}
        }
    ],
    "visualizations": [
        {"type": "force_vectors"},
        {"type": "velocity_graph"},
        {"type": "energy_bar"}
    ],
    "equations": [
        "F_parallel = m * g * sin(theta)",
        "F_normal = m * g * cos(theta)",
        "F_friction = mu * F_normal",
        "a = g * (sin(theta) - mu * cos(theta))"
    ]
}


# =========================================================
# Prompt Builder
# =========================================================

def build_dsl_prompt(user_prompt: str, context: str, extracted: dict) -> str:
    """
    Builds a structured, schema-enforced DSL prompt for Gemini.
    Includes few-shot examples, strict JSON rules, and vocabulary constraints.
    """

    examples_block = "\n".join([
        f"Example {i+1}:\n```json\n{json.dumps(ex, indent=2)}\n```"
        for i, ex in enumerate([
            _EXAMPLE_NEWTON_SECOND_LAW,
            _EXAMPLE_PROJECTILE_MOTION,
            _EXAMPLE_INCLINED_PLANE,
        ])
    ])

    formulas = extracted.get("formulas", [])
    laws = extracted.get("laws", [])
    constants = extracted.get("constants", [])

    return f"""You are a Physics DSL Compiler. Your ONLY job is to convert a natural language physics simulation request into a structured JSON object following the Physics DSL schema below. You must not generate any HTML, CSS, JavaScript, markdown, prose, or explanations.

=== PHYSICS DSL SCHEMA ===

{{
  "simulation_type": "<snake_case string identifying the simulation>",
  "topic": "<human-readable topic name>",
  "environment": {{
    "gravity": <float, m/s^2>,
    "friction": <float, global coefficient>,
    "air_resistance": <float>
  }},
  "entities": [
    {{
      "id": "<unique snake_case id>",
      "type": "<one of: block, sphere, projectile, pendulum, spring, plane, particle>",
      "mass": <float or null>,
      "properties": {{}}
    }}
  ],
  "interactions": [
    {{
      "type": "<interaction type string>",
      "target": "<entity id string>",
      "parameters": {{}}
    }}
  ],
  "visualizations": [
    {{
      "type": "<one of: force_vectors, velocity_graph, acceleration_graph, trajectory_path, energy_bar, motion_trace>"
    }}
  ],
  "equations": ["<physics equation string>"]
}}

=== ENTITY TYPE RULES ===

ONLY use these entity types:
- block, sphere, projectile, pendulum, spring, plane, particle

=== VISUALIZATION TYPE RULES ===

ONLY use these visualization types:
- force_vectors, velocity_graph, acceleration_graph, trajectory_path, energy_bar, motion_trace

=== INTERACTION RULES ===

Every interaction MUST have:
- "type": a snake_case string
- "target": the id of the affected entity
- "parameters": a dict with physics-relevant values

Common interaction types:
- apply_force: {{ "force": [Fx, Fy] }}
- gravity: {{ "g": 9.8 }}
- friction: {{ "mu_kinetic": float, "mu_static": float }}
- normal_force: {{ "surface_normal": [x, y] }}
- collision: {{ "with_entity": id, "restitution": float }}
- projectile_launch: {{ "angle_deg": float, "initial_speed": float }}
- spring_force: {{ "spring_constant": float, "natural_length": float, "anchor": [x, y] }}
- incline: {{ "angle_deg": float }}

=== STRICT OUTPUT RULES ===

- Return ONLY a single valid JSON object
- No markdown code fences (no ```)
- No explanation text before or after the JSON
- No HTML, CSS, or JavaScript
- No frame-by-frame animation logic
- No rendering instructions
- Do not invent new schema keys
- Entity ids must be unique snake_case strings
- All interactions must target a valid entity id from the entities list

=== FEW-SHOT EXAMPLES ===

{examples_block}

=== RETRIEVED PHYSICS CONTEXT ===

{context if context else "No additional context retrieved."}

=== EXTRACTED PHYSICS KNOWLEDGE ===

Formulas: {formulas}
Laws: {laws}
Constants: {constants}

=== USER REQUEST ===

{user_prompt}

Generate the Physics DSL JSON now:"""