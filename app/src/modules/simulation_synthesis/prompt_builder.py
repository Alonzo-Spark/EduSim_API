import json

#Example for the new Schema
_EXAMPLE_NEWTON_SECOND_LAW = {
    "meta": {
        "id": "newton_second_law_001",
        "title": "Newton's Second Law",
        "topic": "Mechanics",
        "difficulty": "Grade 8",
        "version": "1.0"
    },
    "environment": {
        "gravity": {"x": 0, "y": 9.8},
        "airResistance": 0.01,
        "groundFriction": 0.2
    },
    "objects": [
        {
            "id": "block1",
            "type": "dynamicBody",
            "shape": {"type": "rectangle", "width": 100, "height": 50},
            "position": {"x": 200, "y": 400},
            "rotation": 0,
            "physics": {"mass": 5, "movable": True},
            "material": {"friction": 0.3, "restitution": 0.1},
            "visual": {"color": "#3498db", "label": "Block"}
        }
    ],
    "forces": [
        {
            "id": "push_force",
            "type": "applied",
            "target": "block1",
            "vector": {"x": 50, "y": 0}
        }
    ],
    "interactions": [
        {
            "type": "slider",
            "label": "Push Force",
            "bind": "forces[0].vector.x",
            "min": 0, "max": 100
        },
        {
            "type": "slider",
            "label": "Block Mass",
            "bind": "objects[0].physics.mass",
            "min": 1, "max": 50
        }
    ]
}

def build_dsl_prompt(user_prompt: str, context: str, extracted: dict) -> str:
    # Instructions for the AI to use the new Path-Binding system
    return f"""You are a Physics DSL Compiler. 
    Convert the user request into a JSON object using the following sections: 
    'meta', 'environment', 'objects', 'forces', and 'interactions'.

    CRITICAL RULES:
    1. Everything is declarative.
    2. Use the 'bind' property in interactions to map UI controls to state paths.
    3. Paths for 'bind' must be dot-notation strings like 'objects[0].physics.mass'.
    4. SI Units only (m, kg, s).
    5. No markdown code blocks.
    
    Example Structure:
    {json.dumps(_EXAMPLE_NEWTON_SECOND_LAW, indent=2)}

    Context: {context}
    User Request: {user_prompt}
    """