"""
test_initialization.py
======================
Production-grade test suite to verify the EduSim initialization layer,
normalizers, pipeline, object factories, environment builders,
dependency resolvers, and runtime serializers.
"""

import sys
import os

# Ensure the root of the app is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.src.modules.sandbox.initialization import initialize_sandbox


def get_raw_ai_payload() -> dict:
    """Helper to simulate an imperfect, inconsistent AI output payload."""
    return {
        "metadata": {
            "author": "gemini_synthesis",
            "ai_context": {
                "scenario_name": "Oscillating Heavy Block",
                "original_prompt": "Create a massive dynamic block swinging from a ceiling anchor in space."
            }
        },
        "environment": {
            # Inconsistent gravity representations: represented as a single scalar
            "gravity": 9.8,
            "wind": {
                "enabled": True,
                "magnitude": "15 m/s", # String unit format
                "direction_deg": 180
            }
        },
        "objects": [
            # Pivot ceiling: Static circle anchor
            {
                "id": "ceiling_pivot",
                "name": "Anchor Point",
                "shape_type": "circle",
                "is_static": True,
                "role": "anchor",
                # Position is given as standard array instead of coordinates
                "position": [640, 100],
                "radius": 15
            },
            # Dynamic massive block
            {
                "id": "massive_block",
                "name": "Massive Swinging Block",
                "shape_type": "rectangle",
                "is_static": False,
                "role": "body",
                "position": {"x": 640, "y": 400},
                # Width and height given as strings with px units
                "width": "80px",
                "height": "40px",
                "physics": {
                    "mass": "25.5 kg", # Mass with units
                    "restitution": 0.8
                },
                "tags": ["pendulum_bob"]
            }
        ],
        "constraints": [
            # Rope connection
            {
                "id": "rope_connection",
                "constraint_type": "distance",
                "anchor_a": {"body_id": "ceiling_pivot", "offset": [0, 0]},
                "anchor_b": {"body_id": "massive_block", "offset": [0, 0]},
                "stiffness": 1.0,
                "length": 300
            }
        ],
        "controls": [
            # UI control to alter mass
            {
                "id": "mass_slider",
                "label": "Block Mass",
                "widget_type": "slider",
                "binding": {
                    "scope": "object",
                    "object_id": "massive_block",
                    "property_path": "physics.mass"
                },
                "widget_config": {
                    "min_value": 1.0,
                    "max_value": "50kg",
                    "step": 0.5,
                    "default_value": "25.5"
                }
            }
        ],
        "observables": [
            # Track dynamic velocity
            {
                "id": "vel_block",
                "name": "Velocity",
                "observable_type": "direct",
                "target_object_ids": ["massive_block"],
                "source_bindings": [
                    {
                        "symbol": "v",
                        "object_id": "massive_block",
                        "property_path": "runtime.velocity"
                    }
                ],
                "display": {
                    "display_mode": "numeric",
                    "label": "Live Speed",
                    "unit": "m/s"
                }
            },
            # Chained observable: Kinetic energy depends on velocity
            {
                "id": "ke_block",
                "name": "Kinetic Energy",
                "observable_type": "derived",
                "target_object_ids": ["massive_block"],
                "derivation_formula": "KE = 0.5 * m * v^2",
                "source_bindings": [
                    {
                        "symbol": "m",
                        "object_id": "massive_block",
                        "property_path": "physics.mass"
                    },
                    {
                        "symbol": "v",
                        "observable_id": "vel_block" # Depends on velocity observable
                    }
                ],
                "display": {
                    "display_mode": "numeric",
                    "label": "Kinetic Energy",
                    "unit": "J"
                }
            }
        ]
    }


def test_compilation_and_normalization():
    print("Testing Compiling & Normalizing Sandbox Payload...")
    raw = get_raw_ai_payload()

    # Orchestrated pipeline execution
    runtime_payload = initialize_sandbox(raw)

    # 1. Verify general contract structure
    assert "metadata" in runtime_payload
    assert "environment" in runtime_payload
    assert "objects" in runtime_payload
    assert "constraints" in runtime_payload
    assert "relationships" in runtime_payload
    assert "observables" in runtime_payload
    assert "controls" in runtime_payload
    assert "runtime" in runtime_payload

    # 2. Verify Gravity Normalization
    env = runtime_payload["environment"]
    assert env["gravity"]["x"] == 0.0
    assert env["gravity"]["y"] == 9.8
    assert env["gravity"]["scale"] == 1.0

    # 3. Verify Wind Unit Normalization
    assert env["wind"]["enabled"] is True
    assert env["wind"]["magnitude"] == 15.0
    assert env["wind"]["direction_deg"] == 180.0

    # 4. Verify Object Geometries, Colors, and Mass Normalization
    objects = runtime_payload["objects"]
    assert len(objects) == 2

    # Pivot Circle
    pivot = next(o for o in objects if o["id"] == "ceiling_pivot")
    assert pivot["shape_type"] == "circle"
    assert pivot["radius"] == 15.0
    assert pivot["is_static"] is True
    assert pivot["role"] == "anchor"
    assert pivot["position"]["x"] == 640.0
    assert pivot["position"]["y"] == 100.0
    assert pivot["visuals"]["color"] == "#4A4E69" # Steel static color default

    # Massive Block Rectangle
    block = next(o for o in objects if o["id"] == "massive_block")
    assert block["shape_type"] == "rectangle"
    assert block["width"] == 80.0
    assert block["height"] == 40.0
    assert block["physics"]["mass"] == 25.5
    assert block["physics"]["restitution"] == 0.8
    assert block["position"]["x"] == 640.0
    assert block["position"]["y"] == 400.0
    assert block["visuals"]["color"] == "#3A86FF" # Blue rectangle default

    # 5. Verify Controls Slider Config Normalization
    controls = runtime_payload["controls"]
    assert len(controls) == 1
    slider = controls[0]
    assert slider["widget_type"] == "slider"
    assert slider["widget_config"]["min_value"] == 1.0
    assert slider["widget_config"]["max_value"] == 50.0
    assert slider["widget_config"]["default_value"] == 25.5
    assert slider["binding"]["object_id"] == "massive_block"

    # 6. Verify Topological Sort of Observables
    observables = runtime_payload["observables"]
    assert len(observables) == 2
    # Velocity ('vel_block') must be evaluated BEFORE Kinetic Energy ('ke_block') due to derivation link
    vel_idx = next(i for i, o in enumerate(observables) if o["id"] == "vel_block")
    ke_idx = next(i for i, o in enumerate(observables) if o["id"] == "ke_block")
    assert vel_idx < ke_idx
    print("✅ Topological sort of Observables verified successfully.")

    # 7. Verify Auto-Attached Educational Relationships
    relationships = runtime_payload["relationships"]
    assert len(relationships) > 0
    rel_names = [r["name"] for r in relationships]
    print(f"   Attached Educational Relationships: {rel_names}")
    # Since bob has tag 'pendulum_bob', it should have pendulum period, Newtonian dynamics, drag, etc.
    assert any("pendulum" in r["id"].lower() for r in relationships)
    assert any("newton" in r["id"].lower() for r in relationships)

    # 8. Verify generic runtime state parameters
    runtime = runtime_payload["runtime"]
    assert runtime["is_paused"] is True
    assert runtime["bounds"]["max"]["x"] == 1280.0
    assert runtime["bounds"]["max"]["y"] == 720.0

    print("✅ All sandbox compilation and normalization tests completed successfully!")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING INITIALIZATION SYSTEM COMPILER TESTS")
    print("=" * 60)
    try:
        test_compilation_and_normalization()
        print("\n🎉 ALL COMPILER TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ COMPILER TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
