"""
test_state.py
=============
Production-grade test suite to verify the EduSim runtime state architecture,
reactive updates, Matter.js synchronization, timeline snapshots, 
and Socratic tutor trigger integrations.
"""

import sys
import os

# Ensure the root of the app is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.src.modules.sandbox.initialization import initialize_sandbox
from app.src.modules.sandbox.schemas.sandbox_schema import SandboxSchema
from app.src.modules.sandbox.state import (
    RuntimeStore,
    StateManager,
    take_snapshot,
    restore_snapshot,
    SnapshotTimeline,
    update_mass,
    update_widget_mutation,
    get_observable_value,
    get_total_energy,
    get_object_velocity
)


def get_compiled_sandbox() -> SandboxSchema:
    """Uses our sandbox initializer compiler to build a pristine SandboxSchema."""
    raw_payload = {
        "metadata": {
            "author": "gemini_synthesis",
            "ai_context": {
                "scenario_name": "Heavy Swinging Cart"
            }
        },
        "environment": {
            "gravity": 9.81
        },
        "objects": [
            {
                "id": "cart",
                "name": "Physics Cart",
                "shape_type": "rectangle",
                "is_static": False,
                "role": "body",
                "position": [200, 300],
                "width": 100,
                "height": 50,
                "physics": {
                    "mass": 2.0, # 2.0 kg starting mass
                    "restitution": 0.5
                },
                "runtime": {
                    "initial_velocity": [10.0, 0.0] # 10.0 m/s moving horizontal
                }
            }
        ],
        "controls": [
            {
                "id": "mass_slider",
                "label": "Cart Mass",
                "widget_type": "slider",
                "binding": {
                    "scope": "object",
                    "object_id": "cart",
                    "property_path": "physics.mass"
                },
                "widget_config": {
                    "min_value": 0.5,
                    "max_value": 10.0,
                    "step": 0.5,
                    "default_value": 2.0
                }
            }
        ],
        "observables": [
            # Direct velocity
            {
                "id": "vel_cart",
                "name": "Cart Speed",
                "observable_type": "direct",
                "target_object_ids": ["cart"],
                "source_bindings": [
                    {
                        "symbol": "v",
                        "object_id": "cart",
                        "property_path": "runtime.velocity"
                    }
                ],
                "display": {
                    "display_mode": "numeric",
                    "label": "Live Speed",
                    "unit": "m/s"
                },
                "tutor": {
                    "importance": 5,
                    "tutor_questions": ["What happens to momentum as speed doubles?"]
                }
            },
            # Derived Kinetic Energy: KE = 0.5 * m * v^2
            {
                "id": "ke_cart",
                "name": "Kinetic Energy",
                "observable_type": "derived",
                "target_object_ids": ["cart"],
                "derivation_formula": "KE = 0.5 * m * v^2",
                "source_bindings": [
                    {
                        "symbol": "m",
                        "object_id": "cart",
                        "property_path": "physics.mass"
                    },
                    {
                        "symbol": "v",
                        "observable_id": "vel_cart"
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

    # Run initialization pipeline compile
    runtime_payload = initialize_sandbox(raw_payload)
    return SandboxSchema.model_validate(runtime_payload)


def test_reactive_update_cycle():
    print("Testing Reactive Mutation & Calculation Cycle...")
    sandbox = get_compiled_sandbox()
    
    # 1. Initialize Central State RuntimeStore & StateManager
    store = RuntimeStore(sandbox)
    manager = StateManager(store)

    # Verify initial physical states
    cart = store.objects["cart"]
    assert cart.mass == 2.0
    assert cart.velocity.x == 10.0
    assert cart.position.x == 200.0
    
    # Initial evaluation check
    g_y = store.get_gravity_y()
    store.observables.evaluate_all(store.objects, g_y, 0)
    
    initial_ke = get_observable_value(store, "ke_cart")
    # KE = 0.5 * m * v^2 = 0.5 * 2.0 * (10.0^2) = 100.0 Joules
    assert initial_ke == 100.0
    print(f"   Initial Kinetic Energy verified: {initial_ke} J")

    # 2. Slider Mass Change Mutation propagation: mass updated from 2.0kg to 5.0kg
    # Flow: Slider Update -> update_mass -> invalidate cache -> recompute observables -> notify
    update_widget_mutation(store, "mass_slider", 5.0)

    # Verify mass updated in object state
    assert cart.mass == 5.0

    # Verify dependent observable reactively recomputed
    new_ke = get_observable_value(store, "ke_cart")
    # KE = 0.5 * 5.0 * (10.0^2) = 250.0 Joules
    assert new_ke == 250.0
    print(f"   Reactively Recomputed Kinetic Energy: {new_ke} J (Correctly increased!)")
    print("✅ Reactive state propagation verified successfully.")


def test_matter_js_sync_and_tutor_events():
    print("\nTesting Matter.js Synchronization & Tutor triggers...")
    sandbox = get_compiled_sandbox()
    store = RuntimeStore(sandbox)
    manager = StateManager(store)

    # Hook up tutor trigger alert listener
    triggered_events = []
    def tutor_listener(event_key: str, data: Any):
        triggered_events.append((event_key, data))
    manager.register_tutor_trigger(tutor_listener)

    # Capture a physics sync frame payload dispatched from Matter.js runtime
    # Represents cart accelerating to vx=20.0 m/s
    sync_payload = {
        "frame_count": 12,
        "simulation_time": 0.2,
        "objects": [
            {
                "id": "cart",
                "position": {"x": 240.0, "y": 300.0},
                "velocity": {"x": 20.0, "y": 0.0},
                "acceleration": {"x": 5.0, "y": 0.0},
                "angle": 0.0,
                "angular_velocity": 0.0,
                "net_force": {"x": 10.0, "y": 0.0},
                "torque": 0.0,
                "is_sleeping": False
            }
        ],
        "collisions": []
    }

    # Execute sync
    manager.sync_frame_from_frontend(sync_payload)

    # 1. Verify authoritative Object state is updated
    cart = store.objects["cart"]
    assert cart.position.x == 240.0
    assert cart.velocity.x == 20.0
    assert cart.acceleration.x == 5.0

    # 2. Verify derived observables recalculated automatically on sync
    new_ke = get_observable_value(store, "ke_cart")
    # KE = 0.5 * 2.0 * (20.0^2) = 400.0 Joules
    assert new_ke == 400.0
    print(f"   Synced Kinetic Energy: {new_ke} J")

    # 3. Verify Socratic tutor triggers fired because vx = 20m/s > 15m/s
    assert len(triggered_events) > 0
    event_key, event_data = triggered_events[0]
    assert event_key == "threshold_exceeded"
    assert event_data["observable_id"] == "vel_cart"
    assert event_data["value"] == 20.0
    print(f"   Tutor Socratic Trigger fired successfully: {event_data['questions']}")
    print("✅ Matter.js frame sync and Socratic alerting verified successfully.")


def test_timeline_replay_checkpoints():
    print("\nTesting Timeline Snapshot Replay Systems...")
    sandbox = get_compiled_sandbox()
    store = RuntimeStore(sandbox)
    
    # Run initial evaluation so standard values are calculated before checkpointing
    g_y = store.get_gravity_y()
    store.observables.evaluate_all(store.objects, g_y, 0)
    
    timeline = SnapshotTimeline(store)

    # 1. Record starting checkpoint
    timeline.record_checkpoint()
    
    # 2. Mutate state parameters: mass to 6.0kg and velocity to 12.0m/s
    update_mass(store, "cart", 6.0)
    cart = store.objects["cart"]
    cart.velocity.x = 12.0
    
    # Force evaluate to refresh observables
    g_y = store.get_gravity_y()
    store.observables.evaluate_all(store.objects, g_y, 1)

    assert cart.mass == 6.0
    assert cart.velocity.x == 12.0
    changed_ke = get_observable_value(store, "ke_cart")
    # KE = 0.5 * 6.0 * (12.0^2) = 432.0 J
    assert changed_ke == 432.0
    print(f"   State altered: mass={cart.mass}kg, vel={cart.velocity.x}m/s, KE={changed_ke}J")

    # 3. Trigger Undo Rollback Checkpoint
    success = timeline.undo()
    assert success is True

    # 4. Verify original parameters and calculations perfectly restored
    assert cart.mass == 2.0
    assert cart.velocity.x == 10.0
    restored_ke = get_observable_value(store, "ke_cart")
    assert restored_ke == 100.0
    print(f"   Rollback Undo Restored state: mass={cart.mass}kg, vel={cart.velocity.x}m/s, KE={restored_ke}J")

    # 5. Trigger Redo Forward Checkpoint
    success_redo = timeline.redo()
    assert success_redo is True

    # Verify altered states are back
    assert cart.mass == 6.0
    assert cart.velocity.x == 12.0
    redo_ke = get_observable_value(store, "ke_cart")
    assert redo_ke == 432.0
    print(f"   Rollback Redo Restored state: mass={cart.mass}kg, vel={cart.velocity.x}m/s, KE={redo_ke}J")

    print("✅ Timeline replay and checkpoint restoration verified successfully.")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING RUNTIME STATE ENGINE ARCHITECTURE TESTS")
    print("=" * 60)
    try:
        test_reactive_update_cycle()
        test_matter_js_sync_and_tutor_events()
        test_timeline_replay_checkpoints()
        print("\n🎉 ALL RUNTIME STATE ENGINE TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ RUNTIME STATE ENGINE TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
