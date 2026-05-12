import json
from datetime import datetime, timezone

# Example for the new Architecture - Optimized for Matter.js
_EXAMPLE_RESPONSE = {
    "dsl": {
        "meta": {
            "id": "projectile_demo",
            "title": "Projectile Motion",
            "topic": "Mechanics",
            "difficulty": "Grade 9",
            "version": "1.0"
        },
        "environment": {
            "gravity": {"x": 0, "y": 1.0}, # Positive Y is DOWN in Matter.js
            "airResistance": 0.01
        },
        "objects": [
            {
                "id": "ball_1",
                "type": "dynamicBody",
                "shape": {"type": "circle", "radius": 0.5},
                "position": {"x": 2, "y": 10}, # SI Units (Meters)
                "velocity": {"x": 15, "y": -10},
                "rotation": 0,
                "physics": {"mass": 1, "movable": True, "isSensor": False},
                "material": {"friction": 0.1, "restitution": 0.8},
                "visual": {"color": "#3498db", "label": "Ball"}
            },
            {
                "id": "ground",
                "type": "staticBody",
                "shape": {"type": "rectangle", "width": 40, "height": 1},
                "position": {"x": 20, "y": 14},
                "physics": {"mass": 0, "movable": False, "isSensor": False},
                "material": {"friction": 0.5, "restitution": 0.5},
                "visual": {"color": "#27ae60", "label": "Ground"}
            }
        ],
        "forces": [],
        "interactions": [
            {
                "type": "slider",
                "label": "Initial Velocity X",
                "bind": "objects[0].velocity.x",
                "min": 0, 
                "max": 50,
                "step": 1
            }
        ]
    },
    "knowledge": {
        "relevant_formulas": ["v = u + at", "s = ut + 0.5at^2"],
        "related_concepts": ["Parabolic Path", "Independence of Velocities"],
        "laws": ["Newton's First Law of Motion"],
        "explanations": ["The ball follows a parabolic path because gravity only acts vertically."]
    },
    "metadata": {
        "topic": "Kinematics",
        "subject": "Physics",
        "difficulty": "Intermediate",
        "generated_at": "2024-05-12T10:00:00Z",
        "simulation_type": "Matter.js-RigidBody"
    }
}

def build_dsl_prompt(user_prompt: str, context: str) -> str:
    """
    Constructs a prompt for the LLM to generate the refined EduSimResponse structure.
    Strictly enforces SI units, no nulls, and Matter.js optimization.
    """
    now = datetime.now(timezone.utc).isoformat()
    
    return f"""You are a Physics Simulation Engine Architect and Educational Content Creator.
Your task is to convert a user request into a high-quality, runtime-ready simulation blueprint.

RESPONSE ARCHITECTURE:
You MUST return a single JSON object with exactly three top-level keys:
1. "dsl": Runtime-executable Matter.js simulation data.
2. "knowledge": Semantically generated educational information.
3. "metadata": Organizational information.

CRITICAL RULES:
1. SI UNITS (METERS): Use real-world meters for positions and dimensions (e.g., x: 10, y: 20). 
   - Note: The runtime scales these by 40 (SCALE=40). 
   - A typical ground should be at y: 14 (which becomes 560px).
2. COORDINATE SYSTEM: 
   - Positive X is RIGHT.
   - Positive Y is DOWN (standard for Matter.js/Canvas). Gravity Y should be POSITIVE (e.g., 1.0) to pull downwards.
3. NO NULLS / NO NOISE: 
   - Omit unused shape fields.
   - Omit 'initialState' entirely.
4. MATTER.JS COMPATIBILITY: 
   - Body Types: MUST be 'dynamicBody' or 'staticBody'.
   - Shapes: MUST be 'circle' (with 'radius') or 'rectangle' (with 'width', 'height').
   - Visuals: Always include 'color' and 'label' in the 'visual' object.

Example Structure (SI Units + Clean JSON):
{json.dumps(_EXAMPLE_RESPONSE, indent=2)}

Reference Context (For conceptual inspiration):
{context}

Current Timestamp: {now}
User Request: {user_prompt}

Return ONLY the valid JSON object.
"""