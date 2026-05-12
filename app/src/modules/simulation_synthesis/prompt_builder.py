import json
from datetime import datetime, timezone

# Example for the new Architecture - Optimized for Matter.js
_EXAMPLE_RESPONSE = {
    "dsl": {
        "meta": {
            "id": "free_fall_001",
            "title": "Free Fall with Drag",
            "topic": "Mechanics",
            "difficulty": "Grade 9",
            "version": "1.0"
        },
        "environment": {
            "gravity": {"x": 0, "y": -9.8},
            "airResistance": 0.1
        },
        "objects": [
            {
                "id": "ball1",
                "type": "dynamicBody",
                "shape": {"type": "circle", "radius": 0.5},
                "position": {"x": 10, "y": 20},
                "velocity": {"x": 0, "y": 0},
                "rotation": 0,
                "physics": {"mass": 2, "movable": True},
                "material": {"friction": 0.1, "restitution": 0.6},
                "visual": {"color": "#e74c3c", "label": "Ball"}
            }
        ],
        "forces": [
            {
                "id": "drag_force",
                "type": "drag",
                "target": "ball1",
                "coefficient": 0.5,
                "enabled": True
            }
        ],
        "interactions": [
            {
                "type": "slider",
                "label": "Ball Mass",
                "bind": "objects[0].physics.mass",
                "min": 1, 
                "max": 10
            }
        ]
    },
    "knowledge": {
        "relevant_formulas": ["F = ma", "F_d = -bv"],
        "related_concepts": ["Terminal Velocity", "Newton's Second Law"],
        "laws": ["Newton's Second Law of Motion"],
        "explanations": ["Gravity pulls the object down while air resistance opposes motion."]
    },
    "metadata": {
        "topic": "Free Fall",
        "subject": "Physics",
        "difficulty": "Intermediate",
        "generated_at": "2024-05-12T10:00:00Z",
        "simulation_type": "Matter.js-RigidBody"
    }
}

def build_dsl_prompt(user_prompt: str, context: str) -> str:
    now = datetime.now(timezone.utc).isoformat()
    
    return f"""You are a Physics Simulation Architect. Return ONLY a valid JSON object.

EXACT STRUCTURE REQUIRED (follow this example precisely):
{json.dumps(_EXAMPLE_RESPONSE, indent=2)}

RULES:
1. SI UNITS (METERS) for positions/dimensions. NOT pixels.
2. NO NULLS. Every object MUST have: id, type, shape (dict with "type" key), position, physics, material, visual.
3. shape MUST be a dict: {{"type": "circle", "radius": 0.5}} or {{"type": "rectangle", "width": 2, "height": 1}}
4. dsl MUST contain: meta (with id, title, topic, difficulty), environment, objects, forces, interactions.
5. Forces and interactions arrays can be empty [] but MUST exist.
6. Generate clean, accurate formulas and laws in "knowledge".

Reference Context:
{context}

Timestamp: {now}
User Request: {user_prompt}

Return ONLY the valid JSON object."""