"""
test_serializers.py
===================
Production-grade test suite to verify the EduSim serialization system, 
including object vector mapping, bidirectional snapshot save states, 
dynamic control resolvers, real-time WebSocket sync payloads, and initial exports.
"""

import sys
import os

# Ensure the root of the app is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.src.modules.sandbox.initialization.sandbox_initializer import SandboxInitializer
from app.src.modules.sandbox.state.runtime_store import RuntimeStore
from app.src.modules.sandbox.state.snapshots import take_snapshot
from app.src.modules.sandbox.events.event_context import EventContext

from app.src.modules.sandbox.serializers import (
    RuntimeSerializer,
    ObjectSerializer,
    ObservableSerializer,
    RelationshipSerializer,
    ControlSerializer,
    EventSerializer,
    SnapshotSerializer,
    SchemaSerializer
)


def get_compiled_sandbox():
    """Helper compiling a mock pendulum swinging block."""
    raw_spec = {
        "metadata": {
            "id": "massive_swinging_block",
            "name": "Massive Swinging Block",
            "description": "Pendulum with drag coefficient",
            "author": "tester",
            "runtime_config": {
                "max_fps": 60,
                "canvas_width": 1280,
                "canvas_height": 720,
                "simulation_speed": 1.0,
                "substeps": 1
            }
        },
        "environment": {
            "gravity": {"x": 0.0, "y": 9.8},
            "medium": {"medium_type": "air", "density": 1.225}
        },
        "objects": [
            {
                "id": "block_1",
                "role": "bob",
                "shape": "rectangle",
                "dimensions": {"width": 60.0, "height": 60.0},
                "position": [640.0, 360.0],
                "physics": {
                    "mass": "12 kg",
                    "friction": 0.1
                },
                "runtime": {
                    "initial_velocity": [10.0, 0.0]
                }
            }
        ],
        "controls": [
            {
                "id": "mass_slider",
                "label": "Block Mass Slider",
                "widget_type": "slider",
                "widget_config": {
                    "min_value": 1.0,
                    "max_value": 50.0,
                    "step": 0.5,
                    "default_value": 12.0,
                    "unit": "kg"
                },
                "binding": {
                    "scope": "object",
                    "object_id": "block_1",
                    "property_path": "physics.mass"
                }
            }
        ],
        "observables": [
            {
                "id": "vel_block",
                "name": "Block Speed",
                "observable_type": "direct",
                "target_object_ids": ["block_1"],
                "source_bindings": [
                    {
                        "symbol": "v",
                        "description": "velocity magnitude",
                        "object_id": "block_1",
                        "property_path": "physics.velocity"
                    }
                ],
                "display": {
                    "display_mode": "numeric",
                    "unit": "m/s",
                    "min_value": 0.0,
                    "max_value": 50.0
                }
            },
            {
                "id": "ke_block",
                "name": "Kinetic Energy",
                "observable_type": "derived",
                "target_object_ids": ["block_1"],
                "derivation_formula": "KE = 0.5 * m * v^2",
                "source_bindings": [
                    {
                        "symbol": "m",
                        "description": "mass",
                        "object_id": "block_1",
                        "property_path": "physics.mass"
                    },
                    {
                        "symbol": "v",
                        "description": "speed magnitude",
                        "observable_id": "vel_block"
                    }
                ],
                "display": {
                    "display_mode": "gauge",
                    "unit": "J",
                    "min_value": 0.0,
                    "max_value": 1000.0
                }
            }
        ]
    }
    initializer = SandboxInitializer()
    return initializer.pipeline.execute(raw_spec)


def test_object_and_observable_serializers():
    print("Testing Object and Observable Serializer Outputs...")
    sandbox = get_compiled_sandbox()
    store = RuntimeStore(sandbox)

    # 1. Run initial evaluation so observable values are computed
    store.observables.evaluate_all(store.objects, store.get_gravity_y(), 0)

    # 2. Serialize bob block
    obj_state = store.objects["block_1"]
    static_meta = sandbox.model_dump(mode="json")["objects"][0]
    serialized_obj = ObjectSerializer.serialize_object(obj_state, static_meta)

    assert serialized_obj["id"] == "block_1"
    assert serialized_obj["shape"] == "rectangle"
    assert serialized_obj["physics"]["mass"] == 12.0
    assert serialized_obj["physics"]["position"] == {"x": 640.0, "y": 360.0}
    assert serialized_obj["derived"]["kinetic_energy"] == 600.0 # 0.5 * 12 * 10^2
    assert serialized_obj["interaction"]["colliding_with"] == []
    print("   Object live state serialization verified successfully.")

    # 3. Serialize speed and KE observables
    schemas_map = sandbox.observables
    live_vals = store.observables.values
    serialized_obs = ObservableSerializer.serialize_observables(schemas_map, live_vals)

    assert len(serialized_obs) == 2
    assert serialized_obs[0]["id"] == "ke_block"
    assert serialized_obs[0]["value"] == 600.0
    assert serialized_obs[0]["display"]["display_mode"] == "gauge"
    assert serialized_obs[1]["id"] == "vel_block"
    assert serialized_obs[1]["value"] == 10.0
    assert serialized_obs[1]["unit"] == "m/s"
    print("   Observables live state serialization verified successfully.")


def test_relationship_and_control_serializers():
    print("\nTesting Relationship and Control Serializer Outputs...")
    sandbox = get_compiled_sandbox()
    store = RuntimeStore(sandbox)

    # 1. Serialize educational relationships
    serialized_rels = RelationshipSerializer.serialize_relationships(sandbox.relationships)
    assert len(serialized_rels) > 0
    assert serialized_rels[0]["formula_latex"] != ""
    assert serialized_rels[0]["variable_map"] != []
    print("   Educational relationships serialization verified successfully.")

    # 2. Serialize Dynamic slider controls
    serialized_ctrls = ControlSerializer.serialize_controls(sandbox.controls, store)
    assert len(serialized_ctrls) == 1
    assert serialized_ctrls[0]["id"] == "mass_slider"
    assert serialized_ctrls[0]["current_value"] == 12.0
    assert serialized_ctrls[0]["is_enabled"] is True
    assert serialized_ctrls[0]["is_locked"] is False
    print("   Control live value mapping verified successfully.")

    # Lock interaction and verify enabled resolution change
    store.interaction.interaction_locks["controls_edit"] = True
    serialized_ctrls_locked = ControlSerializer.serialize_controls(sandbox.controls, store)
    assert serialized_ctrls_locked[0]["is_enabled"] is False
    assert serialized_ctrls_locked[0]["is_locked"] is True
    print("   Socratic lock validation verified successfully.")


def test_event_and_bidirectional_snapshot_serializers():
    print("\nTesting Event Context & Bidirectional Snapshot Save States...")
    
    # 1. Compact event validation
    context = EventContext.create(
        event_type="interaction.control_changed",
        frame_count=45,
        source_system="ui",
        metadata={"control_id": "mass_slider", "value": 15.0, "_cancelled": True}
    )
    compact_payload = EventSerializer.serialize_event(context, compact=True)
    assert compact_payload["frame"] == 45
    assert "_cancelled" not in compact_payload["meta"]
    assert compact_payload["meta"]["value"] == 15.0
    print("   Compact transport event context verified successfully.")

    # 2. Bidirectional Snapshot validation
    sandbox = get_compiled_sandbox()
    store = RuntimeStore(sandbox)
    
    # Take live physical state snapshot
    snap_orig = take_snapshot(store)
    serialized_snap = SnapshotSerializer.serialize_snapshot(snap_orig)
    
    # Verify save state serializability
    assert "simulation_state" in serialized_snap
    assert "object_states" in serialized_snap
    assert "interaction_state" in serialized_snap
    assert "observable_values" in serialized_snap
    print("   Lightweight snapshot serializing validated successfully.")

    # Deserialize back and check equality
    snap_restored = SnapshotSerializer.deserialize_snapshot(serialized_snap)
    assert snap_restored.simulation_state == snap_orig.simulation_state
    assert snap_restored.object_states == snap_orig.object_states
    assert snap_restored.interaction_state == snap_orig.interaction_state
    assert snap_restored.observable_values == snap_orig.observable_values
    print("   Bidirectional snapshot reconstruction verified successfully.")


def test_master_runtime_serializer():
    print("\nTesting Authoritative Master Runtime Serializer...")
    sandbox = get_compiled_sandbox()
    store = RuntimeStore(sandbox)

    # Force tick step to verify live updates propagate
    store.simulation.frame_count = 120
    store.simulation.simulation_time = 2.0
    store.objects["block_1"].position.x = 750.0

    # 1. Full payload export
    full_payload = RuntimeSerializer.serialize_full(store)
    assert "metadata" in full_payload
    assert "environment" in full_payload
    assert "objects" in full_payload
    assert "controls" in full_payload
    assert "observables" in full_payload
    assert "relationships" in full_payload
    assert "runtime" in full_payload

    assert full_payload["runtime"]["current_frame"] == 120
    assert full_payload["runtime"]["simulated_time_s"] == 2.0
    assert full_payload["objects"][0]["physics"]["position"]["x"] == 750.0
    print("   Initial full payload master assembler verified successfully.")

    # 2. WebSocket Sync payload export
    sync_payload = RuntimeSerializer.serialize_sync_frame(store)
    assert "metadata" not in sync_payload
    assert "environment" not in sync_payload
    assert "objects" in sync_payload
    assert "observables" in sync_payload
    assert "runtime" in sync_payload
    
    assert sync_payload["runtime"]["current_frame"] == 120
    assert sync_payload["objects"][0]["physics"]["position"]["x"] == 750.0
    print("   WebSocket real-time delta sync assembler verified successfully.")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING RUNTIME SERIALIZATION SYSTEM ARCHITECTURE TESTS")
    print("=" * 60)
    try:
        test_object_and_observable_serializers()
        test_relationship_and_control_serializers()
        test_event_and_bidirectional_snapshot_serializers()
        test_master_runtime_serializer()
        print("\n🎉 ALL RUNTIME SERIALIZATION ARCHITECTURE TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ RUNTIME SERIALIZATION ARCHITECTURE TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
