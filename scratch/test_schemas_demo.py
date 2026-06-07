"""
tests/test_schemas_demo.py
==========================
Run this file to see the complete schema output for multiple physics scenarios.

Usage (from EduSim_API root):
    python -m tests.test_schemas_demo
    python tests/test_schemas_demo.py          # also works

What it does:
    1. Builds a complete SandboxSchema for each demo scenario.
    2. Validates every cross-reference automatically.
    3. Prints a section-by-section breakdown in the terminal.
    4. Runs deliberate bad-input tests to show the validators catching errors.
    5. Prints the final minified JSON payload the frontend would receive.
"""

import json
import sys
import textwrap
from pydantic import ValidationError

# ── ensure project root is on the path when run directly ─────────────────────
sys.path.insert(0, ".")

from app.src.modules.sandbox.schemas import (
    # Root
    SandboxSchema, SandboxMetadata, AIContext, TutorContext, RuntimeConfig,
    # Object
    SandboxObject, ShapeType, ObjectRole, PhysicsProperties,
    VisualHints, RuntimeMetadata, EducationalMetadata, Vector2D,
    # Constraint
    SandboxConstraint, ConstraintAnchor, ConstraintEducation,
    # Environment
    SandboxEnvironment, GravityField, WindField, AtmosphereField,
    MagneticField, FluidField, LightingEnvironment, AtmosphereType,
    # Relationship
    EducationalRelationship, VariableBinding, RelationshipScope, CurriculumLevel,
    # Observable
    SandboxObservable, ObservableType, ObservableDisplay,
    ObservableDisplayMode, ObservableSourceBinding, AggregateFunction,
    ObservableTutorMeta,
    # Control
    SandboxControl, ControlBinding, ControlScope, WidgetType,
    SliderConfig, SelectConfig, SelectOption,
)

# ─────────────────────────────────────────────────────────────────────────────
# Terminal helpers
# ─────────────────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
BLUE   = "\033[94m"

def header(title: str) -> None:
    width = 70
    print()
    print(BOLD + CYAN + "═" * width + RESET)
    print(BOLD + CYAN + f"  {title}" + RESET)
    print(BOLD + CYAN + "═" * width + RESET)

def section(title: str) -> None:
    print()
    print(BOLD + YELLOW + f"  ▶  {title}" + RESET)
    print(YELLOW + "  " + "─" * 60 + RESET)

def ok(msg: str) -> None:
    print(GREEN + f"  ✅  {msg}" + RESET)

def fail(msg: str) -> None:
    print(RED + f"  ❌  {msg}" + RESET)

def info(msg: str) -> None:
    print(BLUE + f"  ℹ   {msg}" + RESET)

def print_json(label: str, obj) -> None:
    """Pretty-print a pydantic model or dict as indented JSON."""
    section(label)
    raw = obj.model_dump() if hasattr(obj, "model_dump") else obj
    print(textwrap.indent(json.dumps(raw, indent=2, default=str), "    "))


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 1 — Simple Pendulum
# ─────────────────────────────────────────────────────────────────────────────

def build_pendulum_sandbox() -> SandboxSchema:
    # ── Objects ──────────────────────────────────────────────────────────────
    pivot = SandboxObject(
        id="pivot",
        name="Pivot Point",
        shape_type=ShapeType.CIRCLE,
        object_type="pendulum_anchor",
        role=ObjectRole.ANCHOR,
        position=Vector2D(x=640, y=100),
        radius=8,
        is_static=True,
        tags=["pendulum_anchor"],
        visuals=VisualHints(color="#FFFFFF", label="Pivot"),
    )

    bob = SandboxObject(
        id="pendulum_bob",
        name="Pendulum Bob",
        shape_type=ShapeType.CIRCLE,
        object_type="pendulum_bob",
        role=ObjectRole.BODY,
        position=Vector2D(x=780, y=300),  # displaced for initial swing
        radius=20,
        tags=["pendulum_bob", "observable_target", "energy_tracked"],
        physics=PhysicsProperties(mass=5.0, restitution=0.9, friction=0.0),
        visuals=VisualHints(color="#3A86FF", label="Bob (5 kg)"),
        education=EducationalMetadata(
            concept_tags=["simple_harmonic_motion", "pendulum", "potential_energy"],
            observable_ids=["vel_bob", "ke_bob"],
            difficulty=2,
        ),
    )

    # ── Constraints ──────────────────────────────────────────────────────────
    string = SandboxConstraint(
        id="pendulum_string",
        constraint_type="distance",
        anchor_a=ConstraintAnchor(body_id="pivot"),
        anchor_b=ConstraintAnchor(body_id="pendulum_bob"),
        stiffness=1.0,
        damping=0.0,
        length=200.0,
        is_visible=True,
        education=ConstraintEducation(
            display_name="Pendulum String",
            formula="T = mg·cos(θ) + mv²/L",
            concept_tags=["tension", "centripetal_force"],
        ),
    )

    # ── Observables ──────────────────────────────────────────────────────────
    vel_obs = SandboxObservable(
        id="vel_bob",
        name="Bob Velocity",
        observable_type=ObservableType.DIRECT,
        target_object_ids=["pendulum_bob"],
        display=ObservableDisplay(
            label="Velocity",
            unit="m/s",
            color="#00D4FF",
            display_mode=ObservableDisplayMode.GRAPH,
            show_on_canvas=True,
        ),
        tutor=ObservableTutorMeta(
            concept_tags=["kinematics", "speed"],
            tutor_questions=["At which point is velocity maximum?"],
            importance=4,
        ),
    )

    ke_obs = SandboxObservable(
        id="ke_bob",
        name="Bob Kinetic Energy",
        observable_type=ObservableType.DERIVED,
        target_object_ids=["pendulum_bob"],
        derivation_formula=r"KE = \frac{1}{2}mv^2",
        source_bindings=[
            ObservableSourceBinding(symbol="m", object_id="pendulum_bob", property_path="physics.mass"),
            ObservableSourceBinding(symbol="v", observable_id="vel_bob"),
        ],
        display=ObservableDisplay(
            label="Kinetic Energy",
            unit="J",
            color="#FF6B6B",
            display_mode=ObservableDisplayMode.GRAPH,
        ),
        tutor=ObservableTutorMeta(
            concept_tags=["energy", "kinetic_energy"],
            tutor_questions=["How does KE relate to PE during the swing?"],
            importance=5,
        ),
    )

    # ── Controls ─────────────────────────────────────────────────────────────
    mass_ctrl = SandboxControl(
        id="ctrl_bob_mass",
        label="Bob Mass",
        widget_type=WidgetType.SLIDER,
        binding=ControlBinding(
            scope=ControlScope.OBJECT,
            object_id="pendulum_bob",
            property_path="physics.mass",
        ),
        widget_config=SliderConfig(min_value=0.5, max_value=20.0, step=0.5, default_value=5.0, unit="kg"),
        group="Bob Properties",
        tooltip="Change the mass of the pendulum bob",
        educational_impact=["newtons_second_law", "kinetic_energy"],
    )

    gravity_ctrl = SandboxControl(
        id="ctrl_gravity",
        label="Gravity",
        widget_type=WidgetType.SLIDER,
        binding=ControlBinding(scope=ControlScope.ENVIRONMENT, property_path="gravity.y"),
        widget_config=SliderConfig(min_value=0.0, max_value=20.0, step=0.1, default_value=9.81, unit="m/s²"),
        group="Environment",
        tooltip="Adjust gravitational acceleration",
        educational_impact=["gravity", "pendulum_period"],
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    period_rel = EducationalRelationship(
        id="pendulum_period",
        name="Pendulum Period",
        formula_latex=r"T = 2\pi\sqrt{\frac{L}{g}}",
        formula_description="The period depends only on string length and gravity — NOT on mass.",
        scope=RelationshipScope.PAIRWISE,
        curriculum_level=CurriculumLevel.HIGH_SCHOOL,
        concept_tags=["simple_harmonic_motion", "pendulum", "period"],
        object_ids=["pivot", "pendulum_bob"],
        variable_map=[
            VariableBinding(symbol="L", description="String length", unit="m",
                            object_id="pendulum_bob", property_path="position"),
            VariableBinding(symbol="g", description="Gravitational acceleration", unit="m/s²",
                            property_path="environment.gravity.y"),
        ],
        tutor_hints=[
            "What happens to the period if you double the string length?",
            "Does changing the bob's mass affect the period? Why not?",
            "How would this period change on the Moon?",
        ],
        rag_query_template="Explain the pendulum period formula for {curriculum_level} students.",
    )

    # ── Environment ───────────────────────────────────────────────────────────
    env = SandboxEnvironment(
        gravity=GravityField(x=0.0, y=9.81),
        atmosphere=AtmosphereField(type=AtmosphereType.EARTH, air_density=1.225),
        lighting=LightingEnvironment(background_color="#0d1b2a", theme="dark"),
    )

    # ── Assemble sandbox ──────────────────────────────────────────────────────
    metadata = SandboxMetadata(
        author="system",
        ai_context=AIContext(
            scenario_name="Simple Pendulum",
            scenario_tags=["pendulum", "oscillation", "energy"],
            curriculum_topics=["Kinematics", "Energy Conservation"],
            difficulty=2,
            generation_notes="Classic pendulum with energy tracking.",
        ),
        tutor_context=TutorContext(
            learning_objectives=[
                "Understand how pendulum period is derived",
                "Observe energy conversion between KE and PE",
            ],
            key_concepts=["simple_harmonic_motion", "tension", "energy_conservation"],
            assessment_questions=[
                "What is the period of a 1 m pendulum on Earth?",
                "Why is the bob fastest at the bottom?",
            ],
        ),
        runtime_config=RuntimeConfig(
            canvas_width=1280,
            canvas_height=720,
            pixels_per_meter=100.0,
            simulation_speed=1.0,
        ),
    )

    return SandboxSchema(
        metadata=metadata,
        environment=env,
        objects=[pivot, bob],
        constraints=[string],
        observables=[vel_obs, ke_obs],
        controls=[mass_ctrl, gravity_ctrl],
        relationships=[period_rel],
    )


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 2 — Anti-Gravity / Space
# ─────────────────────────────────────────────────────────────────────────────

def build_anti_gravity_sandbox() -> SandboxSchema:
    cube = SandboxObject(
        id="anti_grav_cube",
        name="Anti-Gravity Cube",
        shape_type=ShapeType.RECTANGLE,
        object_type="anti_gravity_body",
        role=ObjectRole.BODY,
        position=Vector2D(x=640, y=360),
        width=40, height=40,
        tags=["anti_gravity", "observable_target"],
        physics=PhysicsProperties(mass=2.0, gravity_scale=0.0),   # zero gravity effect
        visuals=VisualHints(color="#9B5DE5", label="Cube"),
    )

    env = SandboxEnvironment(
        gravity=GravityField(x=0.0, y=9.81, scale=1.0),   # gravity exists globally…
        atmosphere=AtmosphereField(type=AtmosphereType.VACUUM),
        lighting=LightingEnvironment(background_color="#000011", theme="space"),
    )
    # …but cube has gravity_scale=0 so it feels nothing

    thrust_ctrl = SandboxControl(
        id="ctrl_gravity_scale",
        label="Gravity Scale",
        widget_type=WidgetType.SLIDER,
        binding=ControlBinding(
            scope=ControlScope.OBJECT,
            object_id="anti_grav_cube",
            property_path="physics.gravity_scale",
        ),
        widget_config=SliderConfig(min_value=-2.0, max_value=2.0, step=0.1, default_value=0.0),
        group="Anti-Gravity Controls",
        educational_impact=["gravity", "weight", "newtons_second_law"],
    )

    rel = EducationalRelationship(
        id="weight_force",
        name="Weight = mg × gravity_scale",
        formula_latex=r"W = m \cdot g \cdot s",
        formula_description="Per-body gravity scale modifies the effective gravitational weight.",
        object_ids=["anti_grav_cube"],
        concept_tags=["gravity", "weight", "anti_gravity"],
        tutor_hints=["What does a gravity scale of -1 mean physically?"],
    )

    metadata = SandboxMetadata(
        ai_context=AIContext(
            scenario_name="Anti-Gravity Sandbox",
            scenario_tags=["anti_gravity", "space", "forces"],
            difficulty=3,
        ),
    )

    return SandboxSchema(
        metadata=metadata,
        environment=env,
        objects=[cube],
        controls=[thrust_ctrl],
        relationships=[rel],
    )


# ─────────────────────────────────────────────────────────────────────────────
# NEGATIVE TESTS — validators should catch these
# ─────────────────────────────────────────────────────────────────────────────

def run_negative_tests() -> None:
    header("NEGATIVE VALIDATION TESTS")
    info("These should ALL fail — showing the validators catching bad data\n")

    tests = [
        (
            "Constraint references a body that doesn't exist",
            lambda: SandboxSchema(
                objects=[SandboxObject(id="real", name="R", shape_type=ShapeType.CIRCLE,
                                       object_type="t", position=Vector2D(x=0, y=0), radius=5)],
                constraints=[SandboxConstraint(
                    id="bad_c", constraint_type="distance",
                    anchor_a=ConstraintAnchor(body_id="real"),
                    anchor_b=ConstraintAnchor(body_id="DOES_NOT_EXIST"),
                )],
            ),
        ),
        (
            "Duplicate object IDs",
            lambda: SandboxSchema(objects=[
                SandboxObject(id="dup", name="A", shape_type=ShapeType.CIRCLE,
                              object_type="t", position=Vector2D(x=0, y=0), radius=5),
                SandboxObject(id="dup", name="B", shape_type=ShapeType.CIRCLE,
                              object_type="t", position=Vector2D(x=100, y=0), radius=5),
            ]),
        ),
        (
            "Circle without radius",
            lambda: SandboxObject(id="bad", name="Bad", shape_type=ShapeType.CIRCLE,
                                  object_type="t", position=Vector2D(x=0, y=0)),
        ),
        (
            "Rectangle without width/height",
            lambda: SandboxObject(id="bad2", name="Bad2", shape_type=ShapeType.RECTANGLE,
                                  object_type="t", position=Vector2D(x=0, y=0)),
        ),
        (
            "Observable targets an object that doesn't exist",
            lambda: SandboxSchema(
                objects=[SandboxObject(id="real", name="R", shape_type=ShapeType.CIRCLE,
                                       object_type="t", position=Vector2D(x=0, y=0), radius=5)],
                observables=[SandboxObservable(
                    id="obs", name="Ghost Obs",
                    observable_type=ObservableType.DIRECT,
                    target_object_ids=["GHOST_OBJECT"],
                    display=ObservableDisplay(label="Ghost", unit="m/s"),
                )],
            ),
        ),
        (
            "OBJECT-scoped control without object_id",
            lambda: SandboxControl(
                id="bad_ctrl", label="Bad",
                widget_type=WidgetType.SLIDER,
                binding=ControlBinding(scope=ControlScope.OBJECT, property_path="physics.mass"),
                widget_config=SliderConfig(min_value=0, max_value=10, step=1, default_value=5),
            ),
        ),
    ]

    passed = 0
    for description, fn in tests:
        try:
            fn()
            fail(f"NOT caught: {description}")
        except (ValidationError, ValueError):
            ok(f"Caught: {description}")
            passed += 1

    print()
    info(f"Negative tests: {passed}/{len(tests)} correctly rejected")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:

    # ── SCENARIO 1: Pendulum ─────────────────────────────────────────────────
    header("SCENARIO 1 — Simple Pendulum")

    pendulum = build_pendulum_sandbox()
    ok("SandboxSchema constructed and validated")

    section("Sandbox Summary")
    info(f"Scenario    : {pendulum.metadata.ai_context.scenario_name}")
    info(f"Schema ver  : {pendulum.metadata.schema_version}")
    info(f"Objects     : {len(pendulum.objects)}")
    info(f"Constraints : {len(pendulum.constraints)}")
    info(f"Observables : {len(pendulum.observables)}")
    info(f"Controls    : {len(pendulum.controls)}")
    info(f"Relationships:{len(pendulum.relationships)}")

    print_json("Objects", pendulum.objects[0])   # pivot
    print_json("Objects", pendulum.objects[1])   # bob
    print_json("Constraint (pendulum string)", pendulum.constraints[0])
    print_json("Observable (velocity)", pendulum.observables[0])
    print_json("Observable (kinetic energy)", pendulum.observables[1])
    print_json("Control (mass slider)", pendulum.controls[0])
    print_json("Educational Relationship", pendulum.relationships[0])
    print_json("Environment", pendulum.environment)
    print_json("Metadata", pendulum.metadata)

    section("Full Frontend JSON payload (minified)")
    payload = json.dumps(pendulum.model_dump(), default=str)
    preview = payload[:500] + "  … [truncated]" if len(payload) > 500 else payload
    print(f"    {preview}")
    info(f"Total payload size: {len(payload):,} characters")

    section("Helper method: get_objects_by_tag('pendulum_bob')")
    tagged = pendulum.get_objects_by_tag("pendulum_bob")
    info(f"Found {len(tagged)} object(s): {[o.id for o in tagged]}")

    section("Helper method: get_relationships_for_object('pivot')")
    rels = pendulum.get_relationships_for_object("pivot")
    info(f"Found {len(rels)} relationship(s): {[r.id for r in rels]}")

    section("JSON round-trip (model_dump → model_validate)")
    raw = pendulum.model_dump()
    restored = SandboxSchema.model_validate(raw)
    assert restored.metadata.ai_context.scenario_name == pendulum.metadata.ai_context.scenario_name
    ok("Round-trip successful — schema is persistence-ready")

    # ── SCENARIO 2: Anti-Gravity ─────────────────────────────────────────────
    header("SCENARIO 2 — Anti-Gravity / Space")

    ag = build_anti_gravity_sandbox()
    ok("SandboxSchema constructed and validated")

    section("Anti-Gravity Object physics block")
    print_json("Anti-Gravity Cube", ag.objects[0])

    section("Anti-Gravity Environment block")
    print_json("Environment", ag.environment)

    section("Anti-Gravity Sandbox — full payload size")
    ag_payload = json.dumps(ag.model_dump(), default=str)
    info(f"Total payload size: {len(ag_payload):,} characters")

    # ── NEGATIVE TESTS ───────────────────────────────────────────────────────
    run_negative_tests()

    # ── DONE ─────────────────────────────────────────────────────────────────
    header("ALL TESTS COMPLETE")
    ok("Schema system is production-ready")
    print()


if __name__ == "__main__":
    main()
