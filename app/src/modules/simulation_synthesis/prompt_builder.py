import json
from datetime import datetime, timezone

# Example for the new Architecture - Optimized for Matter.js
_EXAMPLE_RESPONSE = {
  "dsl": {
    "meta": {
      "id": "pendulum_demo",
      "title": "Pendulum Motion",
      "topic": "Oscillation",
      "difficulty": "Grade 10",
      "version": "1.0"
    },

    "environment": {
      "gravity": { "x": 0.0, "y": 1.0 },
      "airResistance": 0.005,
      "background": { "color": "#0f172a" },
      "world": { "width": 800, "height": 600 }
    },

    "objects": [
      {
        "id": "anchor",
        "type": "staticBody",
        "shape": { "type": "circle", "radius": 0.3 },
        "position": { "x": 20.0, "y": 3.0 },
        "velocity": { "x": 0.0, "y": 0.0 },
        "rotation": 0.0,
        "physics": {
          "mass": 0.0,
          "isSensor": False
        },
        "material": {
          "friction": 0.0,
          "restitution": 0.0
        },
        "visual": {
          "color": "#ffffff",
          "label": "Anchor"
        }
      },
      {
        "id": "bob",
        "type": "dynamicBody",
        "shape": { "type": "circle", "radius": 1.0 },
        "position": { "x": 26.0, "y": 8.0 },
        "velocity": { "x": 0.0, "y": 0.0 },
        "rotation": 0.0,
        "physics": {
          "mass": 4.0,
          "isSensor": False
        },
        "material": {
          "friction": 0.05,
          "restitution": 0.2
        },
        "visual": {
          "color": "#3b82f6",
          "label": "Pendulum Bob",
          "showVelocityVector": True
        }
      }
    ],

    "forces": [],
    "constraints": [
      {
        "id": "rope",
        "type": "rope",
        "bodyA": "anchor",
        "bodyB": "bob",
        "length": 6.0,
        "stiffness": 0.9
      }
    ],
    "behaviors": [
      {
        "id": "air_drag",
        "type": "drag",
        "targets": ["bob"],
        "coefficient": 0.01,
        "enabled": True
      }
    ],
    "interactions": [
      {
        "id": "gravity_slider",
        "type": "slider",
        "label": "Gravity",
        "bind": "environment.gravity.y",
        "min": 0.0,
        "max": 2.0,
        "step": 0.1
      },
      {
        "id": "drag_toggle",
        "type": "toggle",
        "label": "Enable Drag",
        "bind": "behaviors[0].enabled"
      }
    ],
    "runtime": {
      "engine": "matter-js",
      "fps": 60,
      "scale": 40
    }
  },
  "knowledge": {
    "relevant_formulas": [
      "T = 2π√(L/g)",
      "F = ma"
    ],
    "related_concepts": [
      "Oscillation",
      "Gravity",
      "Periodic Motion"
    ],
    "laws": [
      "Newton's Second Law",
      "Conservation of Energy"
    ],
    "explanations": [
      "Gravity creates restoring motion in a pendulum.",
      "Longer rope length increases oscillation period."
    ]
  },
  "metadata": {
    "subject": "Physics",
    "difficulty": "Intermediate",
    "simulation_type": "Matter.js-RigidBody"
  }
}

def build_dsl_prompt(user_prompt: str, context: str) -> str:
    now = datetime.now(timezone.utc).isoformat()

    return f"""
You are an AI Physics Simulation Architect for EduSim.
Your task is to generate a high-quality, runtime-ready Matter.js-compatible physics simulation DSL (v1).

### CRITICAL RULES:
1. SI UNITS (METERS): Use meters for all positions and dimensions. (e.g., x: 10, y: 5). NOT pixels.
2. NORMALIZED GRAVITY: Use scaled gravity values. (Standard is y: 1.0). Avoid using raw 9.8 unless specifically requested.
3. BODY TYPES: Use only "dynamicBody" or "staticBody".
4. STATIC BODIES: MUST always have "physics": {{"mass": 0.0, "isSensor": false}}.
5. NO DEPRECATED FIELDS: NEVER generate "movable" or "groundFriction".
6. MANDATORY SECTIONS: Always include "forces", "constraints", "behaviors", and "interactions" as arrays, even if empty [].
7. INTERACTION VALIDATION:
   - Sliders MUST have "min", "max", and "step".
   - Toggles/Buttons MUST NOT have "min", "max", or "step".
8. COORDINATE SYSTEM: Positive X is right, Positive Y is down.
- Every object must contain:
  id, type, shape, position, velocity, rotation, physics, material, visual
- Every force must contain:
  id, type, target, vector, enabled
- Every constraint must contain:
  id, type, bodyA, bodyB, length, stiffness
- Every behavior must contain:
  id, type, targets (array of object IDs), coefficient, enabled
- visual must contain:
  color, label
- Prevent overlapping objects.

### RESPONSE ARCHITECTURE:
Return ONLY a valid JSON object with exactly:
- "dsl" (Executable contract)
- "knowledge" (Educational content)
- "metadata" (Versioning/Difficulty)

### DSL v1 SCHEMA REFERENCE:
{json.dumps(_EXAMPLE_RESPONSE, indent=2)}

### REFERENCE CONTEXT:
{context}

Current Timestamp: {now}
USER REQUEST:
{user_prompt}

Return ONLY the valid JSON object.
"""
