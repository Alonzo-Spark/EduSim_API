"""
scratch/test_prompt_synthesis.py
================================
Authoritative Developer CLI Tool for EduSim Prompt-to-Payload Compilation.

Allows developers to change a single natural language prompt string at the top,
then automatically:
1. Queries RAG to extract verified educational textbook contexts.
2. Invokes the LLM to synthesize a full custom physics sandbox specification.
   - If API keys are missing/offline, it seamlessly switches to offline high-fidelity templates.
3. Compiles the specification using the backend SandboxInitializer pipeline.
4. Hydrates the central RuntimeStore.
5. Performs ticks and evaluates reactive direct & derived observables.
6. Serializes and outputs the final master frontend JSON payload contract!
"""

import sys
import os
import json

# Ensure absolute app path and modular namespaces are in python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "app", "src"))
sys.path.append(os.path.join(root_dir, "app", "src", "modules"))

from app.src.modules.simulation_synthesis.service import (
    retrieve_context,
    build_dsl_prompt,
    generate_dsl,
    sanitize_dsl,
    validate_dsl
)
from app.src.modules.sandbox.initialization.sandbox_initializer import SandboxInitializer
from app.src.modules.sandbox.state.runtime_store import RuntimeStore
from app.src.modules.sandbox.serializers import RuntimeSerializer

# ===========================================================================
# 🎯 DEVELOPER CONFIGURATION: CHANGE THE PROMPT STRING BELOW!
# ===========================================================================
USER_PROMPT = "Simulate a spring-loaded mass with high air resistance to analyze damped oscillations, amplitude decay, and energy loss."

# ===========================================================================

# High-Fidelity offline templates for fallback
OFFLINE_TEMPLATES = {
    "pendulum": {
        "metadata": {
            "id": "double_pendulum_simulation",
            "name": "Double Pendulum Oscillations",
            "description": "Double pendulum chaotic dynamics analyzing gravity and string tension conservation.",
            "author": "Offline Builder",
            "ai_context": {
                "scenario_name": "Double Pendulum swinging under high gravity",
                "scenario_tags": ["oscillations", "pendulum", "gravity"]
            },
            "runtime_config": {
                "max_fps": 60,
                "canvas_width": 1280,
                "canvas_height": 720,
                "simulation_speed": 1.0,
                "substeps": 2
            }
        },
        "environment": {
            "gravity": {"x": 0.0, "y": 15.0}, # High gravity
            "medium": {"medium_type": "air", "density": 1.2}
        },
        "objects": [
            {
                "id": "bob_1",
                "role": "bob",
                "shape": "circle",
                "dimensions": {"radius": 20.0},
                "position": [640.0, 360.0],
                "physics": {"mass": "10 kg", "friction": 0.0},
                "runtime": {"initial_velocity": [12.0, 0.0]}
            },
            {
                "id": "bob_2",
                "role": "bob",
                "shape": "circle",
                "dimensions": {"radius": 15.0},
                "position": [640.0, 500.0],
                "physics": {"mass": "5 kg", "friction": 0.0},
                "runtime": {"initial_velocity": [20.0, 0.0]}
            }
        ],
        "controls": [
            {
                "id": "gravity_slider",
                "label": "Gravity Strength",
                "widget_type": "slider",
                "widget_config": {
                    "min_value": 0.0,
                    "max_value": 30.0,
                    "step": 0.5,
                    "default_value": 15.0,
                    "unit": "m/s^2"
                },
                "binding": {
                    "scope": "environment",
                    "property_path": "gravity.y"
                }
            }
        ],
        "observables": [
            {
                "id": "ke_bob1",
                "name": "Bob 1 Kinetic Energy",
                "observable_type": "derived",
                "target_object_ids": ["bob_1"],
                "derivation_formula": "KE = 0.5 * m * v^2",
                "source_bindings": [
                    {"symbol": "m", "object_id": "bob_1", "property_path": "physics.mass"},
                    {"symbol": "v", "object_id": "bob_1", "property_path": "physics.velocity"}
                ],
                "display": {"display_mode": "numeric", "unit": "J", "color": "#00D4FF"}
            }
        ]
    },
    "spring": {
        "metadata": {
            "id": "spring_projectile_simulation",
            "name": "Spring-Loaded Projectile Launch",
            "description": "High velocity launch analyzing atmospheric fluid friction drag.",
            "author": "Offline Builder",
            "ai_context": {
                "scenario_name": "Spring Projectile Drag Simulator",
                "scenario_tags": ["projectiles", "drag", "fluid"]
            },
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
            "medium": {"medium_type": "air", "density": 1.293}
        },
        "objects": [
            {
                "id": "cannonball",
                "role": "bob",
                "shape": "circle",
                "dimensions": {"radius": 25.0},
                "position": [200.0, 800.0],
                "physics": {"mass": "5.0 kg", "drag_coefficient": 0.47},
                "runtime": {"initial_velocity": [45.0, -35.0]}
            }
        ],
        "controls": [
            {
                "id": "density_slider",
                "label": "Air Density",
                "widget_type": "slider",
                "widget_config": {
                    "min_value": 0.0,
                    "max_value": 5.0,
                    "step": 0.1,
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
                "id": "projectile_speed",
                "name": "Live Speed",
                "observable_type": "direct",
                "target_object_ids": ["cannonball"],
                "source_bindings": [
                    {"symbol": "v", "object_id": "cannonball", "property_path": "physics.velocity"}
                ],
                "display": {"display_mode": "numeric", "unit": "m/s", "color": "#FFC300"}
            }
        ]
    },
    "collision": {
        "metadata": {
            "id": "rocket_collision_simulation",
            "name": "Rocket Elastic Collision Sandbox",
            "description": "Momentum conservation between a massive rocket and space debris.",
            "author": "Offline Builder",
            "ai_context": {
                "scenario_name": "Rocket Momentum Collision Sandbox",
                "scenario_tags": ["collisions", "momentum", "impact"]
            },
            "runtime_config": {
                "max_fps": 60,
                "canvas_width": 1280,
                "canvas_height": 720,
                "simulation_speed": 1.0
            }
        },
        "environment": {
            "gravity": {"x": 0.0, "y": 0.0}, # Zero gravity
            "medium": {"medium_type": "vacuum", "density": 0.0}
        },
        "objects": [
            {
                "id": "rocket_body",
                "role": "bob",
                "shape": "rectangle",
                "dimensions": {"width": 100.0, "height": 40.0},
                "position": [300.0, 360.0],
                "physics": {"mass": "500 kg", "restitution": 0.9},
                "runtime": {"initial_velocity": [15.0, 0.0]}
            },
            {
                "id": "debris",
                "role": "bob",
                "shape": "circle",
                "dimensions": {"radius": 15.0},
                "position": [900.0, 360.0],
                "physics": {"mass": "20 kg", "restitution": 0.9},
                "runtime": {"initial_velocity": [-5.0, 0.0]}
            }
        ],
        "controls": [
            {
                "id": "rocket_mass",
                "label": "Rocket Payload Mass",
                "widget_type": "slider",
                "widget_config": {
                    "min_value": 100.0,
                    "max_value": 2000.0,
                    "step": 50.0,
                    "default_value": 500.0,
                    "unit": "kg"
                },
                "binding": {
                    "scope": "object",
                    "object_id": "rocket_body",
                    "property_path": "physics.mass"
                }
            }
        ],
        "observables": [
            {
                "id": "rocket_momentum",
                "name": "Rocket Momentum",
                "observable_type": "derived",
                "target_object_ids": ["rocket_body"],
                "derivation_formula": "p = m * v",
                "source_bindings": [
                    {"symbol": "m", "object_id": "rocket_body", "property_path": "physics.mass"},
                    {"symbol": "v", "object_id": "rocket_body", "property_path": "physics.velocity"}
                ],
                "display": {"display_mode": "numeric", "unit": "kg*m/s", "color": "#00FF66"}
            }
        ]
    },
    "incline": {
        "metadata": {
            "id": "inclined_plane_simulation",
            "name": "Inclined Plane Friction Sandbox",
            "description": "Analysis of static/kinetic friction and gravitational slip forces down a slope.",
            "author": "Offline Builder",
            "ai_context": {
                "scenario_name": "Inclined Plane Friction Sandbox",
                "scenario_tags": ["forces", "friction", "inclined_plane", "gravity"]
            },
            "runtime_config": {
                "max_fps": 60,
                "canvas_width": 1280,
                "canvas_height": 720,
                "simulation_speed": 1.0
            }
        },
        "environment": {
            "gravity": {"x": 0.0, "y": 9.81},
            "medium": {"medium_type": "air", "density": 1.2}
        },
        "objects": [
            {
                "id": "sliding_block",
                "role": "bob",
                "shape": "rectangle",
                "dimensions": {"width": 80.0, "height": 50.0},
                "position": [300.0, 300.0],
                "physics": {"mass": "8.0 kg", "friction": 0.25},
                "runtime": {"initial_velocity": [5.0, 3.0]}
            }
        ],
        "controls": [
            {
                "id": "friction_slider",
                "label": "Surface Kinetic Friction",
                "widget_type": "slider",
                "widget_config": {
                    "min_value": 0.0,
                    "max_value": 1.0,
                    "step": 0.05,
                    "default_value": 0.25,
                    "unit": "dimensionless"
                },
                "binding": {
                    "scope": "object",
                    "object_id": "sliding_block",
                    "property_path": "physics.friction"
                }
            }
        ],
        "observables": [
            {
                "id": "normal_force",
                "name": "Normal Contact Force (Fn)",
                "observable_type": "derived",
                "target_object_ids": ["sliding_block"],
                "derivation_formula": "Fn = m * g * cos(theta)",
                "source_bindings": [
                    {"symbol": "m", "object_id": "sliding_block", "property_path": "physics.mass"}
                ],
                "display": {"display_mode": "numeric", "unit": "N", "color": "#FF5733"}
            }
        ]
    }
}

def detect_offline_fallback(prompt: str) -> dict:
    """Matches keywords in the prompt to return one of our premium offline templates."""
    lowered = prompt.lower()
    if any(k in lowered for k in ["spring", "projectile", "launch", "drag", "cannon"]):
        return OFFLINE_TEMPLATES["spring"]
    elif any(k in lowered for k in ["collision", "impact", "debris", "rocket", "momentum"]):
        return OFFLINE_TEMPLATES["collision"]
    elif any(k in lowered for k in ["inclined", "incline", "slope", "slide", "plane"]):
        return OFFLINE_TEMPLATES["incline"]
    else:
        # Default to pendulum template
        return OFFLINE_TEMPLATES["pendulum"]

def run_prompt_synthesis_flow():
    print("=" * 70)
    print("      🚀 EDUSIM PROMPT-TO-PAYLOAD SYNTHESIS ENGINE CLI TOOL 🚀")
    print("=" * 70)
    print(f"👉 INPUT PROMPT: '{USER_PROMPT}'\n")

    # Step 1: Query RAG for educational context
    print("Step 1/6: Retrieving textbook physics context from RAG vector database...")
    try:
        context = retrieve_context(USER_PROMPT)
        print("✅ RAG Context Extracted successfully!")
        print("-" * 50)
        preview = context[:400] + "..." if len(context) > 400 else context
        print(f"Textbook Context Excerpt:\n{preview}")
        print("-" * 50)
    except Exception as e:
        print(f"⚠️ RAG Retrieval bypass (using default textbooks): {e}")
        context = "Physics of oscillations: Pendulum gravity restoration forces. KE = 0.5*m*v^2, PE = m*g*h."

    # Step 2: Build final system prompt
    print("\nStep 2/6: Constructing system instruction templates for the LLM...")
    dsl_prompt = build_dsl_prompt(USER_PROMPT, context)
    print("✅ System prompt compiled.")

    # Step 3 & 4: LLM Generation with Dynamic fallback matching
    print("\nStep 3/6: Synthesizing physics sandbox specification...")
    
    spec_data = None
    has_api_key = bool(os.getenv("OPENROUTER_API_KEY"))
    
    if has_api_key:
        try:
            raw_generated = generate_dsl(dsl_prompt)
            if "Error:" not in raw_generated:
                print("✅ Raw specification successfully synthesized by LLM!")
                print("\nStep 4/6: Sanitizing and validating Pydantic schema contract...")
                response_json = sanitize_dsl(raw_generated)
                validated_dict = validate_dsl(response_json)
                spec_data = validated_dict.get("dsl", validated_dict)
                print("✅ Pydantic contract validated successfully against EduSim v2.0 Schema!")
        except Exception as e:
            print(f"⚠️ LLM processing failed: {e}. Switching to offline template fallback...")

    if spec_data is None:
        print("⚠️ OpenRouter API offline or unauthenticated.")
        print(f"💡 Activating Offline high-fidelity Template Matching for: '{USER_PROMPT}'...")
        spec_data = detect_offline_fallback(USER_PROMPT)
        print("✅ Matching offline schema loaded successfully!")

    # Step 5: Compile with SandboxInitializer
    print("\nStep 5/6: Processing pipeline compiler (normalizing shapes, coordinates & attaching relationships)...")
    try:
        initializer = SandboxInitializer()
        sandbox_schema = initializer.pipeline.execute(spec_data)
        print(f"✅ Compiler pipeline finished! Title: '{sandbox_schema.metadata.ai_context.scenario_name}'")
        print(f"   Attached Educational Relationships: {[r.name for r in sandbox_schema.relationships]}")
    except Exception as e:
        print(f"❌ Physical compiler failed: {e}")
        sys.exit(1)

    # Step 6: Load RuntimeStore, evaluate ticks, and run Authoritative Serializers
    print("\nStep 6/6: Hydrating Runtime Store and generating master JSON payloads...")
    try:
        store = RuntimeStore(sandbox_schema)
        # Evaluate direct and derived observables
        store.observables.evaluate_all(store.objects, store.get_gravity_y(), 0)

        # Generate serialized outputs
        full_payload = RuntimeSerializer.serialize_full(store)
        sync_payload = RuntimeSerializer.serialize_sync_frame(store)
        print("✅ Payloads successfully serialized!")

        print("\n" + "=" * 60)
        print("🎉 SUCCESS! FINAL SERIALIZER PAYLOADS SUCCESSFULLY GENERATED")
        print("=" * 60)

        # Write generated payloads to temporary files for inspection
        full_path = "scratch/full_initial_payload.json"
        sync_path = "scratch/websocket_sync_payload.json"
        
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(full_payload, f, indent=2)
        with open(sync_path, "w", encoding="utf-8") as f:
            json.dump(sync_payload, f, indent=2)

        print(f"💾 Full scene initial payload saved to: {full_path}")
        print(f"💾 Real-time WebSocket sync delta saved to: {sync_path}")
        print("-" * 60)
        
        # Display preview
        print("📊 Serialized Observables Preview:")
        print(json.dumps(full_payload["observables"], indent=2))
        
        print("\n📊 Physical Objects Preview:")
        for obj in full_payload["objects"]:
            print(f" - Object: '{obj['id']}' | Mass: {obj['physics']['mass']} kg | Position: {obj['physics']['position']} | Derived KE: {obj['derived']['kinetic_energy']} J")
        
    except Exception as e:
        print(f"❌ Runtime serialization failure: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_prompt_synthesis_flow()
