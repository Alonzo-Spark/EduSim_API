"""
test_relationships.py
=====================
Production-grade test suite verifying the EduSim relationships, formulas,
educational mappings, registries, and dependency graph modules.
"""

import sys
import os

# Ensure the root of the app is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.src.modules.sandbox.schemas.sandbox_schema import SandboxSchema, SandboxMetadata
from app.src.modules.sandbox.schemas.object_schema import SandboxObject, ShapeType, ObjectRole, Vector2D
from app.src.modules.sandbox.schemas.observable_schema import (
    SandboxObservable,
    ObservableType,
    ObservableDisplay,
    ObservableDisplayMode
)
from app.src.modules.sandbox.schemas.constaraint_schema import SandboxConstraint, ConstraintAnchor
from app.src.modules.sandbox.relationships import (
    registry,
    RelationshipBuilder,
    ConceptualDependencyGraph,
    FORMULA_LIBRARY,
    CONCEPT_LIBRARY
)


def create_mock_pendulum_sandbox() -> SandboxSchema:
    """Helper to construct a valid SandboxSchema with a pendulum composition."""
    # 1. Pivot Anchor object
    pivot = SandboxObject(
        id="pivot_anchor",
        name="Fixed Ceiling Pivot",
        shape_type=ShapeType.CIRCLE,
        object_type="anchor",
        role=ObjectRole.ANCHOR,
        position=Vector2D(x=640, y=100),
        radius=10.0,
        is_static=True
    )
    
    # 2. Pendulum Bob object
    bob = SandboxObject(
        id="bob_1",
        name="Heavy Pendulum Bob",
        shape_type=ShapeType.CIRCLE,
        object_type="pendulum_bob",
        role=ObjectRole.BODY,
        position=Vector2D(x=640, y=400),
        radius=25.0,
        tags=["pendulum_bob"]
    )
    
    # 3. Distance constraint (rod/rope)
    string = SandboxConstraint(
        id="rod_1",
        name="Pendulum Rod",
        constraint_type="distance",
        anchor_a=ConstraintAnchor(body_id="pivot_anchor", offset={"x": 0.0, "y": 0.0}),
        anchor_b=ConstraintAnchor(body_id="bob_1", offset={"x": 0.0, "y": 0.0}),
        stiffness=1.0,
        tags=["spring"] # Tagged as spring-like or standard connection
    )
    
    # 4. Standard Velocity & Acceleration Observables
    vel_obs = SandboxObservable(
        id="vel_bob_1",
        name="Velocity of Bob 1",
        observable_type=ObservableType.DIRECT,
        target_object_ids=["bob_1"],
        display=ObservableDisplay(
            display_mode=ObservableDisplayMode.NUMERIC,
            label="Velocity",
            unit="m/s"
        )
    )
    
    accel_obs = SandboxObservable(
        id="accel_bob_1",
        name="Acceleration of Bob 1",
        observable_type=ObservableType.DIRECT,
        target_object_ids=["bob_1"],
        display=ObservableDisplay(
            display_mode=ObservableDisplayMode.NUMERIC,
            label="Acceleration",
            unit="m/s^2"
        )
    )

    return SandboxSchema(
        metadata=SandboxMetadata(author="test_runner"),
        objects=[pivot, bob],
        constraints=[string],
        observables=[vel_obs, accel_obs]
    )


def test_formulas_library():
    print("Testing Formulas Library...")
    assert len(FORMULA_LIBRARY) >= 8
    assert "newtons_second_law" in FORMULA_LIBRARY
    f = FORMULA_LIBRARY["newtons_second_law"]
    assert f.formula_latex == "F = m a"
    assert f.get_variable("m").name == "Mass"
    print("✅ Formulas library check passed.")


def test_educational_mappings():
    print("Testing Educational Mappings...")
    assert "simple_harmonic_motion" in CONCEPT_LIBRARY
    shm = CONCEPT_LIBRARY["simple_harmonic_motion"]
    assert len(shm.misconceptions) > 0
    assert shm.misconceptions[0].id == "amplitude_affects_period"
    print("✅ Educational mappings check passed.")


def test_registry():
    print("Testing Relationship Registry...")
    template = registry.get_template("hookes_law")
    assert template is not None
    assert template.name == "Hooke's Law"
    
    # Check that mutable changes don't affect registry
    template.name = "Mutated Name"
    template2 = registry.get_template("hookes_law")
    assert template2.name == "Hooke's Law"
    print("✅ Registry templates cloning check passed.")


def test_builder_and_dependency_graph():
    print("Testing RelationshipBuilder and ConceptualDependencyGraph...")
    sandbox = create_mock_pendulum_sandbox()
    
    # 1. Attach Relationships dynamically
    builder = RelationshipBuilder()
    hydrated_sandbox = builder.attach_relationships(sandbox)
    
    # We expect Newtonian (since bob is a dynamic body), Drag (since atmosphere density is > 0 by default),
    # and Pendulum relationships to be attached
    rel_ids = [r.id for r in hydrated_sandbox.relationships]
    print(f"   Attached relationships: {rel_ids}")
    
    assert any("newton" in rid for rid in rel_ids)
    assert any("pendulum" in rid for rid in rel_ids)
    
    # 2. Build Dependency Graph
    graph = ConceptualDependencyGraph.build_from_sandbox(hydrated_sandbox)
    
    # Verify graph exists and has connected nodes
    assert len(graph.nodes) > 0
    
    # Trace upstream dependencies for acceleration observable
    accel_deps = graph.trace_upstream("accel_bob_1")
    print(f"   Acceleration upstream factors: {accel_deps}")
    
    # Trace downstream influences of mass change
    mass_influences = graph.trace_downstream("bob_1.physics.mass")
    print(f"   Mass downstream influences: {mass_influences}")
    
    # Verify path tracing
    causal_path = graph.explain_causal_path("bob_1.physics.mass", "relationship.momentum_bob_1")
    print(f"   Causal path from mass to momentum: {causal_path}")
    assert len(causal_path) > 0
    
    print("✅ Relationship builder and causal graph tests passed.")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING RELATIONSHIPS SYSTEM UNIT TESTS")
    print("=" * 60)
    try:
        test_formulas_library()
        test_educational_mappings()
        test_registry()
        test_builder_and_dependency_graph()
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
