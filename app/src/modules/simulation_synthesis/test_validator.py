"""
Manual test for the DSL validator.
Run from the EduSim root directory:
  source venv/bin/activate && python -m app.src.modules.simulation_synthesis.test_validator
"""

from app.src.modules.simulation_synthesis.validator import validate_simulation


# --- Test 1: Valid DSL ---
valid_sample = {
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
    "equations": ["F = ma", "a = F_net / m"]
}

# --- Test 2: Missing required top-level fields ---
invalid_sample = {
    "topic": "Motion",
}

# --- Test 3: Bad entity type (non-standard) ---
bad_entity_type_sample = {**valid_sample, "entities": [
    {"id": "car1", "type": "car", "mass": 5.0, "properties": {}}
]}

# --- Test 4: Interaction targets unknown entity ---
bad_target_sample = {**valid_sample, "interactions": [
    {"type": "apply_force", "target": "unknown_entity", "parameters": {"force": [20, 0]}}
]}

# --- Test 5: Bad visualization type ---
bad_viz_sample = {**valid_sample, "visualizations": [
    {"type": "html_canvas_renderer"}
]}

TESTS = [
    ("Valid DSL", valid_sample, True),
    ("Missing required fields", invalid_sample, False),
    ("Bad entity type", bad_entity_type_sample, False),
    ("Interaction targets unknown entity", bad_target_sample, False),
    ("Bad visualization type", bad_viz_sample, False),
]

print("=" * 60)
for name, sample, expected_success in TESTS:
    result = validate_simulation(sample)
    status = "PASS" if result["success"] == expected_success else "FAIL"
    print(f"[{status}] {name}")
    if result["success"]:
        print(f"       Keys: {list(result['data'].keys())}")
    else:
        print(f"       Error: {result['errors']}")
print("=" * 60)