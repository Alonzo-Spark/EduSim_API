"""
free_fall.py
============
Production-grade Free Fall primitive for the EduSim backend sandbox architecture.

This module defines the `FreeFallPrimitive` generator, which compiles a pristine,
reusable, and interactive sandbox scene illustrating gravitational free fall
mechanics and Newton's laws. It generates a complete, validated SandboxSchema.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from app.src.modules.sandbox.schemas import (
    SandboxSchema,
    SandboxMetadata,
    AIContext,
    TutorContext,
    RuntimeConfig,
    SandboxEnvironment,
    GravityField,
    AtmosphereField,
    AtmosphereType,
    WindField,
    MagneticField,
    FluidField,
    LightingEnvironment,
    SandboxObject,
    ObjectRole,
    ShapeType,
    PhysicsProperties,
    VisualHints,
    RuntimeMetadata,
    EducationalMetadata,
    Vector2D,
    SandboxControl,
    ControlBinding,
    ControlScope,
    WidgetType,
    SliderConfig,
    SandboxObservable,
    ObservableType,
    ObservableDisplay,
    ObservableDisplayMode,
    ObservableSourceBinding,
    ObservableTutorMeta,
    EducationalRelationship,
    VariableBinding,
    RelationshipScope,
    CurriculumLevel,
)


class FreeFallPrimitive:
    """
    Configurable educational primitive generating a complete SandboxSchema payload 
    for gravity and free fall mechanics.
    """

    def __init__(
        self,
        mass: float = 1.0,
        radius: float = 15.0,
        initial_height: float = 400.0,  # height above the ground in pixels
        initial_velocity: float = 0.0,  # initial downward velocity in m/s
        gravity_strength: float = 1.0,  # vertical gravity acceleration y-component
        restitution: float = 0.5,       # bounciness of collision
        air_resistance: float = 0.01,   # drag coefficient (frictionAir)
        color: str = "#FF5733"          # Hex color of the falling body
    ):
        """
        Initializes the FreeFallPrimitive with configurable simulation properties.
        """
        # Validate inputs to avoid division by zero or unstable bounds
        if mass <= 0:
            raise ValueError("Mass must be strictly positive.")
        if radius <= 0:
            raise ValueError("Radius must be strictly positive.")
        if initial_height < 0:
            raise ValueError("Initial height cannot be negative.")
        if restitution < 0 or restitution > 1:
            raise ValueError("Restitution must be between 0.0 and 1.0.")
        if air_resistance < 0 or air_resistance > 1:
            raise ValueError("Air resistance must be between 0.0 and 1.0.")

        self.mass = mass
        self.radius = radius
        self.initial_height = initial_height
        self.initial_velocity = initial_velocity
        self.gravity_strength = gravity_strength
        self.restitution = restitution
        self.air_resistance = air_resistance
        self.color = color

    def _build_metadata(self) -> SandboxMetadata:
        """
        Generates standard metadata details for RAG, Tutor AI, and canvas sizing.
        """
        return SandboxMetadata(
            author="system",
            is_template=True,
            ai_context=AIContext(
                original_prompt="Create a free fall sandbox simulation with gravity and air resistance",
                scenario_name="Free Fall and Gravity Mechanics",
                scenario_tags=["gravity", "free_fall", "mechanics", "newtons_laws"],
                curriculum_topics=["Gravity", "Acceleration", "Energy Conservation", "Inertial Mass"],
                difficulty=1,
                generation_notes="Pristine pre-compiled canonical gravity simulation primitive for EduSim backend."
            ),
            tutor_context=TutorContext(
                learning_objectives=[
                    "Understand that gravity acts as a constant downward acceleration on a free-falling body.",
                    "Demonstrate that potential energy converts to kinetic energy as a body falls.",
                    "Verify Galileo's principle of mass independence in a vacuum.",
                    "Analyze the effect of air resistance (drag) on falling speed and terminal velocity."
                ],
                key_concepts=["gravity", "acceleration", "kinematics", "kinetic_energy", "potential_energy", "inertia"]
            ),
            runtime_config=RuntimeConfig(
                canvas_width=1280,
                canvas_height=720,
                pixels_per_meter=100.0,
                simulation_speed=1.0,
                show_debug_overlay=False,
                enable_sleeping=False,
                substeps=2
            )
        )

    def _build_environment(self) -> SandboxEnvironment:
        """
        Initializes gravity field strength and atmospheric density bounds.
        """
        return SandboxEnvironment(
            gravity=GravityField(
                x=0.0,
                y=self.gravity_strength,
                scale=1.0
            ),
            atmosphere=AtmosphereField(
                type=AtmosphereType.EARTH if self.air_resistance > 0 else AtmosphereType.VACUUM,
                air_density=1.225 if self.air_resistance > 0 else 0.0,
                drag_coeff=0.47
            ),
            lighting=LightingEnvironment(
                background_color="#12121c",
                ambient_light=0.9,
                theme="dark"
            )
        )

    def _build_objects(self) -> List[SandboxObject]:
        """
        Positions the falling object and ground plane relative to the coordinate space.
        """
        # Ground plane center Y coordinate: spans the bottom of the screen (height = 40.0 px)
        ground_center_y = 660.0
        ground_height = 40.0
        ground_top_y = ground_center_y - (ground_height / 2.0)
        
        # Calculate Y starting coordinate based on height above ground plane surface
        falling_y = ground_top_y - self.initial_height - self.radius

        falling_body = SandboxObject(
            id="falling_body",
            name="Falling Body",
            shape_type=ShapeType.CIRCLE,
            object_type="falling_body",
            role=ObjectRole.BODY,
            position=Vector2D(x=640.0, y=falling_y),
            radius=self.radius,
            physics=PhysicsProperties(
                mass=self.mass,
                restitution=self.restitution,
                friction=0.1,
                friction_static=0.2,
                gravity_scale=1.0
            ),
            visuals=VisualHints(
                color=self.color,
                label="Falling Body",
                z_index=1
            ),
            runtime=RuntimeMetadata(
                initial_velocity=Vector2D(x=0.0, y=self.initial_velocity),
                air_resistance=self.air_resistance
            ),
            education=EducationalMetadata(
                concept_tags=["free_fall", "gravity", "kinematics"],
                difficulty=1
            )
        )

        ground = SandboxObject(
            id="ground",
            name="Ground Plane",
            shape_type=ShapeType.RECTANGLE,
            object_type="ground",
            role=ObjectRole.SURFACE,
            position=Vector2D(x=640.0, y=ground_center_y),
            width=1280.0,
            height=ground_height,
            is_static=True,
            physics=PhysicsProperties(
                mass=9999.0,  # highly massive anchor body
                restitution=self.restitution,
                friction=0.5
            ),
            visuals=VisualHints(
                color="#3e4a59",
                label="Ground",
                z_index=0
            ),
            education=EducationalMetadata(
                concept_tags=["environment"],
                difficulty=1
            )
        )

        return [falling_body, ground]

    def _build_controls(self) -> List[SandboxControl]:
        """
        Creates declarative UI control sliders to bind directly to physics and environment bounds.
        """
        controls = []

        # 1. Gravity Slider
        controls.append(
            SandboxControl(
                id="gravity_slider",
                label="Gravity (g)",
                widget_type=WidgetType.SLIDER,
                widget_config=SliderConfig(
                    min_value=0.0,
                    max_value=2.0,
                    step=0.1,
                    default_value=self.gravity_strength,
                    unit="m/s^2"
                ),
                binding=ControlBinding(
                    scope=ControlScope.ENVIRONMENT,
                    property_path="gravity.y"
                ),
                group="Environment",
                display_order=1,
                tooltip="Adjust the vertical acceleration of gravity in the environment",
                educational_impact=["gravity", "acceleration"]
            )
        )

        # 2. Mass Slider
        controls.append(
            SandboxControl(
                id="mass_slider",
                label="Mass",
                widget_type=WidgetType.SLIDER,
                widget_config=SliderConfig(
                    min_value=1.0,
                    max_value=20.0,
                    step=0.5,
                    default_value=self.mass,
                    unit="kg"
                ),
                binding=ControlBinding(
                    scope=ControlScope.OBJECT,
                    object_id="falling_body",
                    property_path="physics.mass"
                ),
                group="Body Properties",
                display_order=2,
                tooltip="Change the mass of the falling body",
                educational_impact=["inertia", "mass"]
            )
        )

        # 3. Initial Velocity Slider
        controls.append(
            SandboxControl(
                id="init_velocity_slider",
                label="Initial Velocity (Y)",
                widget_type=WidgetType.SLIDER,
                widget_config=SliderConfig(
                    min_value=-20.0,
                    max_value=20.0,
                    step=1.0,
                    default_value=self.initial_velocity,
                    unit="m/s"
                ),
                binding=ControlBinding(
                    scope=ControlScope.OBJECT,
                    object_id="falling_body",
                    property_path="runtime.initial_velocity.y"
                ),
                group="Initial State",
                display_order=3,
                tooltip="Set initial vertical velocity (negative is upward, positive is downward)",
                educational_impact=["velocity", "kinematics"]
            )
        )

        # 4. Air Resistance Slider
        controls.append(
            SandboxControl(
                id="air_resistance_slider",
                label="Air Resistance",
                widget_type=WidgetType.SLIDER,
                widget_config=SliderConfig(
                    min_value=0.0,
                    max_value=1.0,
                    step=0.01,
                    default_value=self.air_resistance,
                    unit="coeff"
                ),
                binding=ControlBinding(
                    scope=ControlScope.OBJECT,
                    object_id="falling_body",
                    property_path="runtime.air_resistance"
                ),
                group="Environment",
                display_order=4,
                tooltip="Modify the body air drag coefficient",
                educational_impact=["drag", "forces"]
            )
        )

        return controls

    def _build_observables(self) -> List[SandboxObservable]:
        """
        Compiles dynamic and derived observables to present live state data on the canvas and UI.
        """
        observables = []

        # 1. Velocity Observable
        observables.append(
            SandboxObservable(
                id="vel_obs",
                name="Velocity",
                observable_type=ObservableType.DIRECT,
                target_object_ids=["falling_body"],
                source_bindings=[
                    ObservableSourceBinding(
                        symbol="v",
                        object_id="falling_body",
                        property_path="runtime.velocity"
                    )
                ],
                display=ObservableDisplay(
                    display_mode=ObservableDisplayMode.VECTOR_ARROW,
                    label="Velocity",
                    unit="m/s",
                    color="#00D4FF",
                    show_in_panel=True,
                    show_on_canvas=True
                ),
                tutor=ObservableTutorMeta(
                    concept_tags=["velocity", "kinematics"],
                    importance=5
                )
            )
        )

        # 2. Acceleration Observable
        observables.append(
            SandboxObservable(
                id="accel_obs",
                name="Acceleration",
                observable_type=ObservableType.DIRECT,
                target_object_ids=["falling_body"],
                source_bindings=[
                    ObservableSourceBinding(
                        symbol="a",
                        object_id="falling_body",
                        property_path="runtime.acceleration"
                    )
                ],
                display=ObservableDisplay(
                    display_mode=ObservableDisplayMode.NUMERIC,
                    label="Acceleration",
                    unit="m/s^2",
                    color="#FF007F",
                    show_in_panel=True,
                    show_on_canvas=False
                ),
                tutor=ObservableTutorMeta(
                    concept_tags=["acceleration", "gravity"],
                    importance=4
                )
            )
        )

        # 3. Height Observable
        observables.append(
            SandboxObservable(
                id="height_obs",
                name="Height",
                observable_type=ObservableType.DERIVED,
                target_object_ids=["falling_body", "ground"],
                derivation_formula="h = y_g - 20.0 - y_b - r",
                source_bindings=[
                    ObservableSourceBinding(
                        symbol="y_g",
                        object_id="ground",
                        property_path="position.y"
                    ),
                    ObservableSourceBinding(
                        symbol="y_b",
                        object_id="falling_body",
                        property_path="position.y"
                    ),
                    ObservableSourceBinding(
                        symbol="r",
                        object_id="falling_body",
                        property_path="radius"
                    )
                ],
                display=ObservableDisplay(
                    display_mode=ObservableDisplayMode.NUMERIC,
                    label="Height above Ground",
                    unit="m",
                    color="#FFDD00",
                    show_in_panel=True,
                    show_on_canvas=True
                ),
                tutor=ObservableTutorMeta(
                    concept_tags=["displacement", "kinematics"],
                    importance=4
                )
            )
        )

        # 4. Kinetic Energy Observable
        observables.append(
            SandboxObservable(
                id="ke_obs",
                name="Kinetic Energy",
                observable_type=ObservableType.DERIVED,
                target_object_ids=["falling_body"],
                derivation_formula="KE = 0.5 * m * v^2",
                source_bindings=[
                    ObservableSourceBinding(
                        symbol="m",
                        object_id="falling_body",
                        property_path="physics.mass"
                    ),
                    ObservableSourceBinding(
                        symbol="v",
                        observable_id="vel_obs"
                    )
                ],
                display=ObservableDisplay(
                    display_mode=ObservableDisplayMode.GRAPH,
                    label="Kinetic Energy",
                    unit="J",
                    color="#39FF14",
                    show_in_panel=True
                ),
                tutor=ObservableTutorMeta(
                    concept_tags=["energy", "kinetic_energy"],
                    importance=5
                )
            )
        )

        # 5. Potential Energy Observable
        observables.append(
            SandboxObservable(
                id="pe_obs",
                name="Potential Energy",
                observable_type=ObservableType.DERIVED,
                target_object_ids=["falling_body"],
                derivation_formula="PE = m * g * h",
                source_bindings=[
                    ObservableSourceBinding(
                        symbol="m",
                        object_id="falling_body",
                        property_path="physics.mass"
                    ),
                    ObservableSourceBinding(
                        symbol="g",
                        property_path="gravity.y"
                    ),
                    ObservableSourceBinding(
                        symbol="h",
                        observable_id="height_obs"
                    )
                ],
                display=ObservableDisplay(
                    display_mode=ObservableDisplayMode.GRAPH,
                    label="Potential Energy",
                    unit="J",
                    color="#DA70D6",
                    show_in_panel=True
                ),
                tutor=ObservableTutorMeta(
                    concept_tags=["energy", "potential_energy"],
                    importance=5
                )
            )
        )

        # 6. Gravity Force Observable
        observables.append(
            SandboxObservable(
                id="fg_obs",
                name="Force of Gravity",
                observable_type=ObservableType.DERIVED,
                target_object_ids=["falling_body"],
                derivation_formula="F_g = m * g",
                source_bindings=[
                    ObservableSourceBinding(
                        symbol="m",
                        object_id="falling_body",
                        property_path="physics.mass"
                    ),
                    ObservableSourceBinding(
                        symbol="g",
                        property_path="gravity.y"
                    )
                ],
                display=ObservableDisplay(
                    display_mode=ObservableDisplayMode.VECTOR_ARROW,
                    label="Gravity Force",
                    unit="N",
                    color="#FF5733",
                    show_in_panel=True,
                    show_on_canvas=True
                ),
                tutor=ObservableTutorMeta(
                    concept_tags=["forces", "gravity"],
                    importance=4
                )
            )
        )

        return observables

    def _build_relationships(self) -> List[EducationalRelationship]:
        """
        Creates standard educational mappings and equations to feed the Tutor AI engine.
        """
        relationships = []

        # 1. Newton's Second Law
        relationships.append(
            EducationalRelationship(
                id="newton_2nd_law_fall",
                name="Newton's Second Law",
                formula_latex="F = m a",
                formula_description="The net force acting on the body equals its mass multiplied by its acceleration.",
                scope=RelationshipScope.OBJECT,
                curriculum_level=CurriculumLevel.HIGH_SCHOOL,
                concept_tags=["forces", "newtons_laws"],
                object_ids=["falling_body"],
                variable_map=[
                    VariableBinding(
                        symbol="F",
                        description="Force of gravity acting on the body",
                        object_id="falling_body",
                        observable_id="fg_obs",
                        unit="N"
                    ),
                    VariableBinding(
                        symbol="m",
                        description="Mass of the body",
                        object_id="falling_body",
                        property_path="physics.mass",
                        unit="kg"
                    ),
                    VariableBinding(
                        symbol="a",
                        description="Downward acceleration of the body",
                        object_id="falling_body",
                        observable_id="accel_obs",
                        unit="m/s^2"
                    )
                ],
                tutor_hints=[
                    "Does doubling the mass change the acceleration? Hint: Look at the acceleration observable.",
                    "Why does the net force vector point in the exact same direction as the acceleration vector?"
                ]
            )
        )

        # 2. Gravity ↔ Acceleration
        relationships.append(
            EducationalRelationship(
                id="gravity_accel_relationship",
                name="Gravity and Acceleration",
                formula_latex="a_y = g",
                formula_description="In the absence of other forces, the downward acceleration of a falling object is exactly equal to the gravitational field strength.",
                scope=RelationshipScope.GLOBAL,
                curriculum_level=CurriculumLevel.MIDDLE_SCHOOL,
                concept_tags=["gravity", "kinematics"],
                object_ids=["falling_body"],
                variable_map=[
                    VariableBinding(
                        symbol="a_y",
                        description="Vertical acceleration of the body",
                        object_id="falling_body",
                        observable_id="accel_obs",
                        unit="m/s^2"
                    ),
                    VariableBinding(
                        symbol="g",
                        description="Gravitational field strength",
                        object_id=None,
                        property_path="gravity.y",
                        unit="m/s^2"
                    )
                ],
                tutor_hints=[
                    "What happens to the acceleration of the falling body if you adjust the gravity slider?",
                    "If you turn gravity off completely (g = 0), how does the body behave when released?"
                ]
            )
        )

        # 3. Mass Independence (Galileo's Principle)
        relationships.append(
            EducationalRelationship(
                id="mass_independence",
                name="Mass Independence in Free Fall",
                formula_latex="a_y = \\frac{F_g}{m} = \\frac{m g}{m} = g",
                formula_description="Although a larger mass experiences a stronger gravitational pull (weight), it also exhibits proportionately higher inertia resisting acceleration. These two factors cancel out, ensuring all bodies fall at the same rate in a vacuum.",
                scope=RelationshipScope.SYSTEM,
                curriculum_level=CurriculumLevel.HIGH_SCHOOL,
                concept_tags=["free_fall", "gravity", "mass"],
                object_ids=["falling_body"],
                variable_map=[
                    VariableBinding(
                        symbol="a_y",
                        description="Vertical acceleration of the body",
                        object_id="falling_body",
                        observable_id="accel_obs",
                        unit="m/s^2"
                    ),
                    VariableBinding(
                        symbol="m",
                        description="Mass of the body",
                        object_id="falling_body",
                        property_path="physics.mass",
                        unit="kg"
                    ),
                    VariableBinding(
                        symbol="g",
                        description="Gravitational acceleration constant",
                        object_id=None,
                        property_path="gravity.y",
                        unit="m/s^2"
                    )
                ],
                tutor_hints=[
                    "If you increase the mass slider from 1.0kg to 20.0kg, does the acceleration of the ball change? Why or why not?",
                    "What does this teach us about the equivalence of gravitational and inertial mass?"
                ]
            )
        )

        # 4. Energy Conversion
        relationships.append(
            EducationalRelationship(
                id="energy_conservation_fall",
                name="Conservation of Mechanical Energy",
                formula_latex="E_{total} = KE + PE = \\text{const}",
                formula_description="As the body falls, gravitational potential energy (PE) converts into kinetic energy (KE). The total mechanical energy is conserved in the absence of air resistance.",
                scope=RelationshipScope.OBJECT,
                curriculum_level=CurriculumLevel.HIGH_SCHOOL,
                concept_tags=["energy", "energy_conservation"],
                object_ids=["falling_body"],
                variable_map=[
                    VariableBinding(
                        symbol="KE",
                        description="Kinetic energy of motion",
                        object_id="falling_body",
                        observable_id="ke_obs",
                        unit="J"
                    ),
                    VariableBinding(
                        symbol="PE",
                        description="Gravitational potential energy",
                        object_id="falling_body",
                        observable_id="pe_obs",
                        unit="J"
                    )
                ],
                tutor_hints=[
                    "Look at the Kinetic Energy and Potential Energy graphs. When one line goes up, does the other go down by the same amount?",
                    "How does enabling air resistance affect this energy conservation? Where does the 'lost' mechanical energy go?"
                ]
            )
        )

        return relationships

    def build(self) -> SandboxSchema:
        """
        Assembles all components into a validated Pydantic SandboxSchema.
        """
        metadata = self._build_metadata()
        environment = self._build_environment()
        objects = self._build_objects()
        controls = self._build_controls()
        observables = self._build_observables()
        relationships = self._build_relationships()

        return SandboxSchema(
            metadata=metadata,
            environment=environment,
            objects=objects,
            constraints=[],
            controls=controls,
            observables=observables,
            relationships=relationships
        )
