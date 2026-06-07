"""
tests/test_rocket_scenario.py
==============================
Demonstrates the schema system handling a Rocket Launch scenario —
completely different from a pendulum, using the SAME schema files.

Run from EduSim_API root:
    python tests/test_rocket_scenario.py
"""

import json, sys
sys.path.insert(0, ".")

from app.src.modules.sandbox.schemas import (
    SandboxSchema, SandboxMetadata, AIContext, TutorContext, RuntimeConfig,
    SandboxObject, ShapeType, ObjectRole, PhysicsProperties, VisualHints,
    RuntimeMetadata, EducationalMetadata, Vector2D,
    SandboxConstraint, ConstraintAnchor, ConstraintEducation,
    SandboxEnvironment, GravityField, WindField, AtmosphereField,
    MagneticField, FluidField, LightingEnvironment, AtmosphereType,
    EducationalRelationship, VariableBinding, RelationshipScope, CurriculumLevel,
    SandboxObservable, ObservableType, ObservableDisplay, ObservableDisplayMode,
    ObservableSourceBinding, ObservableTutorMeta,
    SandboxControl, ControlBinding, ControlScope, WidgetType, SliderConfig, SelectConfig, SelectOption,
)

RESET = "\033[0m"; BOLD = "\033[1m"; GREEN = "\033[92m"
YELLOW = "\033[93m"; CYAN = "\033[96m"; BLUE = "\033[94m"

def header(t): print(f"\n{BOLD}{CYAN}{'═'*70}\n  {t}\n{'═'*70}{RESET}")
def section(t): print(f"\n{BOLD}{YELLOW}  ▶  {t}\n  {'─'*60}{RESET}")
def ok(m): print(f"{GREEN}  ✅  {m}{RESET}")
def info(m): print(f"{BLUE}  ℹ   {m}{RESET}")
def pj(label, obj):
    section(label)
    raw = obj.model_dump() if hasattr(obj, "model_dump") else obj
    import textwrap
    print(textwrap.indent(json.dumps(raw, indent=2, default=str), "    "))


# ── OBJECTS ────────────────────────────────────────────────────────────────

# Launch pad — static ground platform
launch_pad = SandboxObject(
    id="launch_pad",
    name="Launch Pad",
    shape_type=ShapeType.RECTANGLE,
    object_type="ground_platform",
    role=ObjectRole.SURFACE,
    position=Vector2D(x=640, y=680),
    width=200, height=20,
    is_static=True,
    tags=["ground", "static_surface"],
    visuals=VisualHints(color="#555555", label="Launch Pad"),
)

# Rocket body — carries fuel_mass as a custom physics property
rocket_body = SandboxObject(
    id="rocket_body",
    name="Rocket Body",
    shape_type=ShapeType.RECTANGLE,
    object_type="rocket_body",
    role=ObjectRole.EMITTER,
    position=Vector2D(x=640, y=580),
    width=40, height=100,
    tags=["rocket", "observable_target", "energy_tracked", "thrust_source"],
    physics=PhysicsProperties(
        mass=10.0,
        restitution=0.1,
        friction=0.3,
        gravity_scale=1.0,
        # Custom property — the schema accepts it via extra='allow'
        fuel_mass=50.0,
        drag_coefficient=0.47,
    ),
    visuals=VisualHints(color="#E63946", label="Rocket", texture_key="rocket_sprite"),
    runtime=RuntimeMetadata(
        initial_velocity=Vector2D(x=0, y=0),
        air_resistance=0.02,
    ),
    education=EducationalMetadata(
        concept_tags=["newtons_third_law", "thrust", "momentum", "projectile_motion"],
        observable_ids=["obs_altitude", "obs_velocity_y", "obs_acceleration"],
        difficulty=4,
        notes="Rocket demonstrates Newton's 3rd Law via exhaust thrust.",
    ),
)

# Nose cone — separate body joined to rocket via constraint
nose_cone = SandboxObject(
    id="nose_cone",
    name="Nose Cone",
    shape_type=ShapeType.POLYGON,
    object_type="rocket_nose",
    role=ObjectRole.BODY,
    position=Vector2D(x=640, y=528),
    vertices=[
        Vector2D(x=-20, y=0),
        Vector2D(x=20, y=0),
        Vector2D(x=0, y=-50),
    ],
    tags=["rocket_component"],
    physics=PhysicsProperties(mass=2.0, restitution=0.1),
    visuals=VisualHints(color="#FF6B6B"),
)

# Exhaust flame — a sensor body (no collision response)
exhaust = SandboxObject(
    id="exhaust_plume",
    name="Exhaust Plume",
    shape_type=ShapeType.CIRCLE,
    object_type="thrust_emitter",
    role=ObjectRole.SENSOR,
    position=Vector2D(x=640, y=632),
    radius=15,
    tags=["sensor", "exhaust", "visual_only"],
    physics=PhysicsProperties(mass=0.001, is_sensor=True, gravity_scale=0.0),
    visuals=VisualHints(color="#FF9F1C", opacity=0.7, label=""),
)


# ── CONSTRAINTS ───────────────────────────────────────────────────────────

# Weld nose cone to rocket body (rigid joint)
nose_joint = SandboxConstraint(
    id="nose_cone_weld",
    constraint_type="pivot",
    anchor_a=ConstraintAnchor(body_id="rocket_body", offset={"x": 0, "y": -50}),
    anchor_b=ConstraintAnchor(body_id="nose_cone",   offset={"x": 0, "y":   0}),
    stiffness=1.0,
    damping=1.0,
    education=ConstraintEducation(
        display_name="Nose Weld",
        concept_tags=["rigid_body", "compound_structure"],
    ),
)

# Exhaust plume tracks rocket bottom
exhaust_joint = SandboxConstraint(
    id="exhaust_attachment",
    constraint_type="distance",
    anchor_a=ConstraintAnchor(body_id="rocket_body",   offset={"x": 0, "y": 50}),
    anchor_b=ConstraintAnchor(body_id="exhaust_plume", offset={"x": 0, "y":  0}),
    stiffness=1.0,
    damping=1.0,
    length=0.0,
    is_visible=False,
)


# ── OBSERVABLES ───────────────────────────────────────────────────────────

obs_altitude = SandboxObservable(
    id="obs_altitude",
    name="Altitude",
    observable_type=ObservableType.DIRECT,
    target_object_ids=["rocket_body"],
    source_bindings=[ObservableSourceBinding(
        symbol="y", object_id="rocket_body", property_path="position.y"
    )],
    display=ObservableDisplay(
        label="Altitude", unit="m", color="#00F5D4",
        display_mode=ObservableDisplayMode.GRAPH,
        show_on_canvas=True,
    ),
    tutor=ObservableTutorMeta(
        concept_tags=["kinematics", "displacement"],
        tutor_questions=["How does altitude change as fuel burns?"],
        importance=5,
    ),
)

obs_velocity_y = SandboxObservable(
    id="obs_velocity_y",
    name="Vertical Velocity",
    observable_type=ObservableType.DIRECT,
    target_object_ids=["rocket_body"],
    source_bindings=[ObservableSourceBinding(
        symbol="vy", object_id="rocket_body", property_path="runtime.velocity.y"
    )],
    display=ObservableDisplay(
        label="Vertical Velocity", unit="m/s", color="#FFD166",
        display_mode=ObservableDisplayMode.GRAPH,
    ),
)

obs_acceleration = SandboxObservable(
    id="obs_acceleration",
    name="Net Acceleration",
    observable_type=ObservableType.DELTA,
    target_object_ids=["rocket_body"],
    delta_source_id="obs_velocity_y",
    display=ObservableDisplay(
        label="Acceleration", unit="m/s²", color="#EF476F",
        display_mode=ObservableDisplayMode.NUMERIC,
    ),
    tutor=ObservableTutorMeta(
        concept_tags=["newtons_second_law", "net_force"],
        tutor_questions=["What is the net force when acceleration is 0?"],
        importance=5,
    ),
)

obs_momentum = SandboxObservable(
    id="obs_momentum",
    name="Rocket Momentum",
    observable_type=ObservableType.DERIVED,
    target_object_ids=["rocket_body"],
    derivation_formula=r"p = m \cdot v",
    source_bindings=[
        ObservableSourceBinding(symbol="m",  object_id="rocket_body", property_path="physics.mass"),
        ObservableSourceBinding(symbol="v",  observable_id="obs_velocity_y"),
    ],
    display=ObservableDisplay(
        label="Momentum", unit="kg·m/s", color="#06D6A0",
        display_mode=ObservableDisplayMode.GRAPH,
    ),
    tutor=ObservableTutorMeta(
        concept_tags=["momentum", "newtons_second_law"],
        tutor_questions=["How does momentum change as fuel is burned?"],
        importance=4,
    ),
)


# ── CONTROLS ──────────────────────────────────────────────────────────────

ctrl_thrust = SandboxControl(
    id="ctrl_thrust",
    label="Thrust Force",
    widget_type=WidgetType.SLIDER,
    binding=ControlBinding(
        scope=ControlScope.OBJECT,
        object_id="rocket_body",
        property_path="physics.thrust_force",  # custom property applied by frontend
    ),
    widget_config=SliderConfig(min_value=0, max_value=5000, step=50, default_value=0, unit="N"),
    group="Rocket Controls",
    tooltip="Apply upward thrust to the rocket",
    educational_impact=["newtons_third_law", "net_force", "acceleration"],
    display_order=1,
)

ctrl_mass = SandboxControl(
    id="ctrl_rocket_mass",
    label="Rocket Mass (dry)",
    widget_type=WidgetType.SLIDER,
    binding=ControlBinding(
        scope=ControlScope.OBJECT,
        object_id="rocket_body",
        property_path="physics.mass",
    ),
    widget_config=SliderConfig(min_value=1, max_value=50, step=0.5, default_value=10, unit="kg"),
    group="Rocket Controls",
    educational_impact=["newtons_second_law", "weight"],
    display_order=2,
)

ctrl_gravity = SandboxControl(
    id="ctrl_gravity",
    label="Gravity",
    widget_type=WidgetType.SLIDER,
    binding=ControlBinding(scope=ControlScope.ENVIRONMENT, property_path="gravity.y"),
    widget_config=SliderConfig(min_value=0, max_value=25, step=0.1, default_value=9.81, unit="m/s²"),
    group="Environment",
    educational_impact=["gravity", "weight", "escape_velocity"],
    display_order=3,
)

ctrl_atmosphere = SandboxControl(
    id="ctrl_atmosphere",
    label="Atmosphere",
    widget_type=WidgetType.SELECT,
    binding=ControlBinding(scope=ControlScope.ENVIRONMENT, property_path="atmosphere.type"),
    widget_config=SelectConfig(
        default_value="earth",
        options=[
            SelectOption(value="earth",  label="Earth (1.225 kg/m³)"),
            SelectOption(value="mars",   label="Mars (thin CO₂)"),
            SelectOption(value="moon",   label="Moon (no atmosphere)"),
            SelectOption(value="vacuum", label="Vacuum"),
        ],
    ),
    group="Environment",
    educational_impact=["drag", "air_resistance", "terminal_velocity"],
    display_order=4,
)

ctrl_launch = SandboxControl(
    id="ctrl_launch_btn",
    label="🚀 Launch",
    widget_type=WidgetType.BUTTON,
    binding=ControlBinding(scope=ControlScope.SIMULATION, action="launch_rocket"),
    group="Rocket Controls",
    educational_impact=["newtons_third_law", "impulse"],
    display_order=0,
)


# ── RELATIONSHIPS ─────────────────────────────────────────────────────────

rel_thrust = EducationalRelationship(
    id="newtons_third_law_thrust",
    name="Newton's 3rd Law — Thrust",
    formula_latex=r"F_{thrust} = \dot{m} \cdot v_{exhaust}",
    formula_description="Rocket thrust equals mass flow rate times exhaust velocity. For every action (exhaust down) there is an equal/opposite reaction (rocket up).",
    scope=RelationshipScope.OBJECT,
    curriculum_level=CurriculumLevel.HIGH_SCHOOL,
    concept_tags=["newtons_third_law", "thrust", "rocket_propulsion"],
    object_ids=["rocket_body", "exhaust_plume"],
    variable_map=[
        VariableBinding(symbol="F", description="Thrust force", unit="N",
                        object_id="rocket_body", property_path="physics.thrust_force"),
        VariableBinding(symbol="m_dot", description="Mass flow rate", unit="kg/s",
                        object_id="rocket_body", property_path="physics.fuel_mass"),
    ],
    tutor_hints=[
        "Why does the rocket move upward when exhaust shoots downward?",
        "What happens to thrust as fuel runs out?",
        "How does this relate to a garden hose recoiling?",
    ],
    rag_query_template="Explain rocket propulsion and Newton's 3rd Law for {curriculum_level} students.",
)

rel_net_force = EducationalRelationship(
    id="net_force_rocket",
    name="Net Force on Rocket",
    formula_latex=r"F_{net} = F_{thrust} - mg - F_{drag}",
    formula_description="The rocket accelerates only when thrust exceeds gravity and drag combined.",
    scope=RelationshipScope.OBJECT,
    curriculum_level=CurriculumLevel.HIGH_SCHOOL,
    concept_tags=["newtons_second_law", "net_force", "drag"],
    object_ids=["rocket_body"],
    depends_on=["newtons_third_law_thrust"],
    tutor_hints=[
        "At what thrust does the rocket just barely lift off?",
        "How does drag change with altitude?",
        "What is the rocket's acceleration at liftoff?",
    ],
)


# ── ENVIRONMENT ───────────────────────────────────────────────────────────

env = SandboxEnvironment(
    gravity=GravityField(x=0.0, y=9.81),
    wind=WindField(enabled=True, magnitude=2.0, direction_deg=270.0, turbulence=0.1),
    atmosphere=AtmosphereField(type=AtmosphereType.EARTH, air_density=1.225, drag_coeff=0.47),
    lighting=LightingEnvironment(background_color="#03071e", theme="dark", ambient_light=0.6),
)


# ── METADATA ──────────────────────────────────────────────────────────────

metadata = SandboxMetadata(
    author="system",
    ai_context=AIContext(
        scenario_name="Rocket Launch",
        scenario_tags=["rocket", "thrust", "propulsion", "newtons_laws"],
        curriculum_topics=["Newton's Laws", "Momentum", "Energy", "Drag"],
        difficulty=4,
        generation_notes="Multi-body rocket with thrust, drag, and fuel depletion dynamics.",
    ),
    tutor_context=TutorContext(
        learning_objectives=[
            "Understand Newton's 3rd Law through rocket thrust",
            "Calculate net force as thrust minus weight minus drag",
            "Observe momentum change during fuel burn",
        ],
        key_concepts=["newtons_third_law", "net_force", "drag", "momentum"],
        assessment_questions=[
            "What minimum thrust is needed for liftoff?",
            "How does the rocket's acceleration change as fuel burns?",
            "Why does the rocket go faster in a vacuum?",
        ],
    ),
    runtime_config=RuntimeConfig(
        canvas_width=1280,
        canvas_height=720,
        pixels_per_meter=50.0,   # smaller scale for rocket height
        simulation_speed=1.0,
        show_debug_overlay=False,
    ),
)


# ── ASSEMBLE & VALIDATE ───────────────────────────────────────────────────

sandbox = SandboxSchema(
    metadata=metadata,
    environment=env,
    objects=[launch_pad, rocket_body, nose_cone, exhaust],
    constraints=[nose_joint, exhaust_joint],
    observables=[obs_altitude, obs_velocity_y, obs_acceleration, obs_momentum],
    controls=[ctrl_launch, ctrl_thrust, ctrl_mass, ctrl_gravity, ctrl_atmosphere],
    relationships=[rel_thrust, rel_net_force],
)


# ── PRINT RESULTS ─────────────────────────────────────────────────────────

header("SCENARIO — Rocket Launch")
ok(f"SandboxSchema constructed and validated with {len(sandbox.objects)} objects")

section("Summary")
info(f"Scenario     : {sandbox.metadata.ai_context.scenario_name}")
info(f"Objects      : {len(sandbox.objects)} — {[o.id for o in sandbox.objects]}")
info(f"Constraints  : {len(sandbox.constraints)}")
info(f"Observables  : {len(sandbox.observables)}")
info(f"Controls     : {len(sandbox.controls)}")
info(f"Relationships: {len(sandbox.relationships)}")

pj("Rocket Body (with custom fuel_mass, drag_coefficient)", rocket_body)
pj("Nose Cone (polygon vertices)", nose_cone)
pj("Exhaust Plume (sensor body — no collision)", exhaust)
pj("Constraint — Nose Cone Weld (pivot)", nose_joint)
pj("Observable — Altitude (DIRECT)", obs_altitude)
pj("Observable — Momentum (DERIVED: p=mv)", obs_momentum)
pj("Observable — Acceleration (DELTA of velocity)", obs_acceleration)
pj("Control — Thrust Slider", ctrl_thrust)
pj("Control — Atmosphere SELECT", ctrl_atmosphere)
pj("Control — Launch BUTTON", ctrl_launch)
pj("Relationship — Newton's 3rd Law (Thrust)", rel_thrust)
pj("Relationship — Net Force", rel_net_force)
pj("Environment (Earth + light wind)", env)

section("Helper: get_objects_by_tag('rocket')")
tagged = sandbox.get_objects_by_tag("rocket")
info(f"Found: {[o.id for o in tagged]}")

section("Helper: get_objects_by_tag('sensor')")
sensors = sandbox.get_objects_by_tag("sensor")
info(f"Sensor objects: {[o.id for o in sensors]}")

section("Helper: get_relationships_for_object('rocket_body')")
rels = sandbox.get_relationships_for_object("rocket_body")
info(f"Found {len(rels)} relationships: {[r.id for r in rels]}")

section("JSON Round-trip")
restored = SandboxSchema.model_validate(sandbox.model_dump())
assert restored.metadata.ai_context.scenario_name == "Rocket Launch"
ok("Round-trip successful")

section("Full payload size")
payload = json.dumps(sandbox.model_dump(), default=str)
info(f"Total payload: {len(payload):,} characters")

header("DONE — Rocket Launch schema verified ✅")
