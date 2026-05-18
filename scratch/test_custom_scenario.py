"""
scratch/test_custom_scenario.py
===============================
Custom prompt compiler and serialization test for a "Spring Launcher Projectile Sandbox".
"""

import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.src.modules.sandbox.initialization.sandbox_initializer import SandboxInitializer
from app.src.modules.sandbox.state.runtime_store import RuntimeStore
from app.src.modules.sandbox.serializers import RuntimeSerializer

# Define our completely new, rich scenario specification
projectile_spec = {
    "metadata": {
        "id": "spring_projectile_launcher",
        "name": "Spring-Loaded Projectile Launcher",
        "description": "Educational sandbox analyzing launch speed, angle, and medium density drag forces.",
        "author": "Antigravity Compiler",
        "runtime_config": {
            "max_fps": 60,
            "canvas_width": 1920,
            "canvas_height": 1080,
            "simulation_speed": 1.0,
            "substeps": 2
        }
    },
    "environment": {
        "gravity": {"x": 0.0, "y": 9.81},
        "medium": {"medium_type": "air", "density": 1.293} # Standard Earth air density
    },
    "objects": [
        {
            "id": "cannon_bob",
            "role": "bob",
            "shape": "circle",
            "dimensions": {"radius": 25.0},
            "position": [200.0, 800.0],
            "physics": {
                "mass": "5.0 kg",
                "friction": 0.05,
                "drag_coefficient": 0.47 # Sphere drag coefficient
            },
            "runtime": {
                "initial_velocity": [45.0, -35.0] # High upward and forward launch speed
            }
        }
    ],
    "controls": [
        {
            "id": "gravity_slider",
            "label": "Acceleration due to Gravity",
            "widget_type": "slider",
            "widget_config": {
                "min_value": 0.0,
                "max_value": 25.0,
                "step": 0.1,
                "default_value": 9.81,
                "unit": "m/s^2"
            },
            "binding": {
                "scope": "environment",
                "property_path": "gravity.y"
            }
        },
        {
            "id": "drag_density_slider",
            "label": "Medium Density (Air Drag)",
            "widget_type": "slider",
            "widget_config": {
                "min_value": 0.0,
                "max_value": 5.0,
                "step": 0.05,
                "default_value": 1.293,
                "unit": "kg/m^3"
            },
            "binding": {
                "scope": "environment",
                "property_path": "medium.density"
            }
        }
    ],
    "observables": [
        {
            "id": "live_vel",
            "name": "Live Launch Speed",
            "observable_type": "direct",
            "target_object_ids": ["cannon_bob"],
            "source_bindings": [
                {
                    "symbol": "v",
                    "description": "velocity magnitude",
                    "object_id": "cannon_bob",
                    "property_path": "physics.velocity"
                }
            ],
            "display": {
                "display_mode": "numeric",
                "unit": "m/s",
                "color": "#FFC300"
            }
        },
        {
            "id": "drag_force_calc",
            "name": "Live Fluid Air Drag Force",
            "observable_type": "derived",
            "target_object_ids": ["cannon_bob"],
            "derivation_formula": "Fd = 0.5 * rho * v^2 * Cd * A",
            "source_bindings": [
                {
                    "symbol": "rho",
                    "description": "fluid density",
                    "property_path": "medium.density"
                },
                {
                    "symbol": "v",
                    "description": "speed magnitude",
                    "observable_id": "live_vel"
                }
            ],
            "display": {
                "display_mode": "graph",
                "unit": "N",
                "color": "#E74C3C",
                "min_value": 0.0,
                "max_value": 500.0
            }
        }
    ]
}

def run_custom_test():
    print("=" * 60)
    print("COMPILING CUSTOM SPRING PROJECTILE LAUNCHER SCENARIO...")
    print("=" * 60)

    # 1. Compile the scenario
    initializer = SandboxInitializer()
    sandbox_schema = initializer.pipeline.execute(projectile_spec)
    print(f"✅ Dynamic compilation successful. Title: '{sandbox_schema.metadata.ai_context.scenario_name}'")
    print(f"   Compiled controls count: {len(sandbox_schema.controls)}")
    print(f"   Compiled observables count: {len(sandbox_schema.observables)}")
    print(f"   Contextually attached relationships: {[r.name for r in sandbox_schema.relationships]}")

    # 2. Load into central RuntimeStore
    store = RuntimeStore(sandbox_schema)
    
    # Tick/evaluate the store once so observables compute
    store.observables.evaluate_all(store.objects, store.get_gravity_y(), 0)

    # 3. Serialize output payloads
    full_export = RuntimeSerializer.serialize_full(store)
    sync_export = RuntimeSerializer.serialize_sync_frame(store)

    print("\n✅ Initial Serialized Output Metadata:")
    print(json.dumps(full_export["metadata"], indent=2))

    print("\n✅ Initial Serialized Object Derived metrics:")
    print(json.dumps(full_export["objects"][0]["derived"], indent=2))

    print("\n✅ Initial Serialized Custom Observables:")
    print(json.dumps(full_export["observables"], indent=2))

    print("\n🎉 ALL CUSTOM SCENARIO COMPILATION AND SERIALIZATION TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_custom_test()
