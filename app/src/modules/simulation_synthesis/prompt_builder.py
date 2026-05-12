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
1. SI UNITS (METERS): Use real-world meters for positions and dimensions (e.g., x: 10, y: 20). DO NOT use pixel coordinates (e.g., 400, 500). The runtime scales meters to pixels.
2. NO NULLS / NO NOISE: 
   - Omit unused shape fields (Circles ONLY have 'radius'; Rectangles ONLY have 'width' and 'height').
   - Omit 'initialState' entirely if it is empty.
   - Omit null vectors or unused coefficients in 'forces'.
3. NO REDUNDANT GRAVITY: Global gravity belongs ONLY in 'environment.gravity'. DO NOT include a 'gravity' force object in the 'forces' array.
4. SEMANTIC KNOWLEDGE: Generate clean, human-readable formulas and relevant laws using LLM reasoning. Avoid noisy OCR fragments.
5. MATTER.JS COMPATIBILITY: 
   - Shapes: 'circle' | 'rectangle'
   - Bodies: 'dynamicBody' | 'staticBody'
   - Forces: 'drag' | 'friction' | 'applied'
   - Interactions: 'slider' | 'toggle'

Example Structure (SI Units + Clean JSON):
{json.dumps(_EXAMPLE_RESPONSE, indent=2)}

Reference Context (For conceptual inspiration):
{context}

Current Timestamp: {now}
User Request: {user_prompt}

Return ONLY the valid JSON object.
"""