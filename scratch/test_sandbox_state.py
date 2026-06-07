"""
test_sandbox_state.py
=====================
Comprehensive integration test suite validating the evolved EduSim Central Editable
Runtime World State System.
"""

import sys
import os

# Append project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.src.modules.sandbox.primitives.mechanics.gravity.free_fall import FreeFallPrimitive
from app.src.modules.sandbox.schemas.sandbox_schema import SandboxSchema
from app.src.modules.sandbox.schemas.object_schema import SandboxObject, ShapeType, PhysicsProperties, VisualHints, RuntimeMetadata
from app.src.modules.sandbox.schemas.constaraint_schema import SandboxConstraint, ConstraintAnchor, ConstraintEducation
from app.src.modules.sandbox.state import (
    RuntimeStore,
    StateManager,
    add_object,
    remove_object,
    update_object,
    add_constraint,
    remove_constraint,
    update_environment,
    get_dynamic_objects,
    get_constraints_for_object,
    get_object_by_id
)


def test_sandbox_state_refactored() -> None:
    print("Initializing FreeFallPrimitive scene...")
    primitive = FreeFallPrimitive(mass=5.0, radius=25.0)
    sandbox = primitive.build()

    print("Initializing Authoritative RuntimeStore and StateManager...")
    store = RuntimeStore(sandbox)
    manager = StateManager(store)

    # 1. Verify baseline objects populated
    assert len(store.objects) == 2, "Should have 2 objects initially (falling body and ground)"
    falling_body = store.objects.get("falling_body")
    assert falling_body is not None
    assert falling_body.mass == 5.0, "Initial mass should be 5.0"

    print("SUCCESS: Baseline objects verified!")

    # 2. Test standard mutations
    print("Testing basic mass and position updates...")
    update_object(store, "falling_body", {"mass": 10.0, "position": {"x": 200.0, "y": 300.0}})
    assert falling_body.mass == 10.0
    assert falling_body.position.x == 200.0
    assert falling_body.position.y == 300.0
    
    # Confirm underlying schema is kept in sync
    schema_fb = next(o for o in store.schema.objects if o.id == "falling_body")
    assert schema_fb.physics.mass == 10.0
    assert schema_fb.position.x == 200.0
    assert schema_fb.position.y == 300.0

    print("SUCCESS: Basic mutations verified!")

    # 3. Record timeline checkpoint
    print("Recording pristine checkpoint...")
    manager.record_checkpoint()

    # 4. Test dynamic spawning: Add Object
    print("Testing dynamic object spawning (add_object)...")
    new_circle = SandboxObject(
        id="extra_ball",
        name="Extra Ball",
        shape_type=ShapeType.CIRCLE,
        object_type="custom_ball",
        radius=15.0,
        position={"x": 400.0, "y": 100.0},
        physics=PhysicsProperties(mass=2.0, restitution=0.8),
        visuals=VisualHints(color="#ff0000", visible=True),
        runtime=RuntimeMetadata(initial_velocity={"x": 5.0, "y": 0.0})
    )

    added_state = add_object(store, new_circle)
    assert added_state is not None
    assert "extra_ball" in store.objects
    assert len(store.objects) == 3
    assert any(o.id == "extra_ball" for o in store.schema.objects)
    assert store.objects["extra_ball"].velocity.x == 5.0

    print("SUCCESS: Dynamic object spawning verified!")

    # 5. Test adding a dynamic constraint anchoring to the spawned object
    print("Testing dynamic constraint linkage (add_constraint)...")
    spring = SandboxConstraint(
        id="custom_spring",
        constraint_type="spring",
        anchor_a=ConstraintAnchor(body_id="falling_body", offset={"x": 0.0, "y": 0.0}),
        anchor_b=ConstraintAnchor(body_id="extra_ball", offset={"x": 0.0, "y": 0.0}),
        stiffness=0.5,
        damping=0.1,
        length=100.0,
        is_visible=True,
        education=ConstraintEducation(display_name="Tether Spring", formula="F = -k*x")
    )

    add_constraint(store, spring)
    assert "custom_spring" in store.constraints
    assert len(store.schema.constraints) == 1
    assert store.constraints["custom_spring"].stiffness == 0.5

    # Test constraint selectors
    linked = get_constraints_for_object(store, "extra_ball")
    assert len(linked) == 1
    assert linked[0].id == "custom_spring"

    print("SUCCESS: Dynamic constraint linkage verified!")

    # 6. Test deep undo/redo of dynamic spawning
    print("Testing checkpoint UNDO rollback...")
    # Rollback to pristine state (before extra ball and spring were added)
    success = manager.undo()
    assert success
    assert "extra_ball" not in store.objects, "extra_ball should have been garbage collected"
    assert "custom_spring" not in store.constraints, "custom_spring should have been garbage collected"
    assert len(store.objects) == 2
    assert len(store.schema.objects) == 2
    assert len(store.schema.constraints or []) == 0

    print("SUCCESS: Checkpoint UNDO restored baseline state perfectly!")

    print("Testing checkpoint REDO roll forward...")
    success = manager.redo()
    assert success
    assert "extra_ball" in store.objects
    assert "custom_spring" in store.constraints
    assert len(store.objects) == 3
    assert len(store.schema.objects) == 3
    assert len(store.schema.constraints or []) == 1

    print("SUCCESS: Checkpoint REDO restored dynamic spawned states perfectly!")

    # 7. Test robust cascading delete
    print("Testing cascading delete (remove_object)...")
    # Deleting "extra_ball" should automatically delete associated constraints (custom_spring)
    remove_object(store, "extra_ball")
    assert "extra_ball" not in store.objects
    assert "custom_spring" not in store.constraints, "Linked spring constraint should have cascaded out"
    assert len(store.schema.constraints or []) == 0

    print("SUCCESS: Cascading delete verified!")


if __name__ == "__main__":
    try:
        test_sandbox_state_refactored()
        print("\n==================================================")
        print("CONGRATULATIONS: All sandbox state integration tests passed!")
        print("==================================================")
        sys.exit(0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
