"""
object_schema.py
================
Universal SandboxObject schema — the atom of the EduSim sandbox system.

ARCHITECTURE PHILOSOPHY
-----------------------
Every physical entity in a sandbox (pendulum bob, rocket body, spring block,
planet, pulley wheel, anti-gravity cube …) is represented by one schema:
`SandboxObject`.  There are NO sub-classes such as RocketSchema or
PendulumSchema.  Extensibility is achieved through three mechanisms:

1. `object_type`  — a string identifier that AI and the frontend use to
   select rendering/behaviour presets (e.g. "circle", "rectangle", "polygon").
   This maps 1-to-1 to a Matter.js body shape hint; it is NOT a scenario type.

2. `physics_properties` — a strongly-typed, open-ended model (ConfigDict
   extra='allow') that carries known physics fields *and* arbitrary future
   properties (charge, fuel_mass, luminosity …) without a schema rewrite.

3. `tags` — a list of semantic strings used for relationship attachment,
   observable binding, and tutor targeting (e.g. ["pendulum_bob",
   "observable_target", "energy_tracked"]).

SCALABILITY
-----------
Adding support for electromagnetics requires only two changes:
  - injecting `charge: float` into an object's `physics_properties` via the
    AI / service layer.
  - adding a tag  `["charged_particle"]` to enable the relationship engine.
No schema rewrite is needed.

ANTI-PATTERNS AVOIDED
---------------------
- No subclasses per simulation scenario.
- No hardcoded simulation-specific fields at the top level.
- No runtime logic (velocity integration, force accumulation) in this file.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations (stable, forward-compatible)
# ---------------------------------------------------------------------------

class ShapeType(str, Enum):
    """
    Geometric shape hints passed to the frontend renderer and Matter.js body
    factory.  These are SHAPE descriptors, not scenario descriptors.

    Future shapes (e.g. "capsule", "torus") can be added here without
    touching any other schema.
    """
    CIRCLE    = "circle"
    RECTANGLE = "rectangle"
    POLYGON   = "polygon"
    COMPOUND  = "compound"   # Multiple shapes joined as one rigid body
    CUSTOM    = "custom"     # Frontend resolves shape from visual hints


class ObjectRole(str, Enum):
    """
    High-level semantic role of the object within its scenario.
    Used by the tutor and relationship engine — NOT by the physics engine.
    """
    ANCHOR      = "anchor"       # Static attachment point (pivot, wall, ground)
    BODY        = "body"         # Primary dynamic physics body
    SURFACE     = "surface"      # Ground, ramp, or boundary
    EMITTER     = "emitter"      # Rockets, thrust sources
    SENSOR      = "sensor"       # Invisible detector (collision zone, trigger)
    REFERENCE   = "reference"    # Non-physical visual reference (ruler, grid mark)


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------

class Vector2D(BaseModel):
    """
    Immutable 2D vector used for positions, velocities, forces, etc.
    Frontend expects SI units normalised to canvas scale via runtime metadata.
    """
    x: float = 0.0
    y: float = 0.0


class PhysicsProperties(BaseModel):
    """
    Core physics parameters known at sandbox-initialisation time.

    ConfigDict(extra='allow') is the key extensibility mechanism:
    any unknown field injected by the AI (e.g. `charge`, `magnetic_moment`,
    `drag_coefficient`) is silently accepted, validated as-is, and forwarded
    to the frontend in the serialised payload.

    KNOWN FIELDS (documented for IDE support + validation)
    -------------------------------------------------------
    mass            — kg; must be > 0 for dynamic bodies
    restitution     — coefficient of restitution [0, 1]
    friction        — kinetic friction coefficient [0, ∞)
    friction_static — static friction coefficient [0, ∞)
    density         — kg/m²; if provided, overrides mass with area calculation
    is_sensor       — body generates collision events but has no physical response
    gravity_scale   — per-body gravity multiplier (0 = anti-gravity; -1 = inverted)

    EXTENSIBLE FIELDS (examples, NOT exhaustive)
    ---------------------------------------------
    charge           — Coulombs; enables electromagnetic relationship
    fuel_mass        — kg; for rocket scenarios
    spring_constant  — N/m; used when this body IS the spring representation
    """
    model_config = ConfigDict(extra="allow")

    mass: float             = Field(default=1.0,  gt=0,    description="Body mass in kg")
    restitution: float      = Field(default=0.5,  ge=0, le=1, description="Coefficient of restitution")
    friction: float         = Field(default=0.1,  ge=0,    description="Kinetic friction coefficient")
    friction_static: float  = Field(default=0.05, ge=0,    description="Static friction coefficient")
    density: Optional[float] = Field(default=None, gt=0,   description="Density in kg/m²; overrides mass if set")
    is_sensor: bool         = Field(default=False,          description="Sensor body — no collision response")
    gravity_scale: float    = Field(default=1.0,            description="Per-body gravity scale (0=weightless, -1=inverted)")


class VisualHints(BaseModel):
    """
    Metadata for the PixiJS renderer.  This is HINTS only — the frontend
    has final say over pixel-level presentation.

    texture_key is resolved by the frontend asset registry.
    tint overrides texture colour (hex string, e.g. "#FF5733").
    z_index controls draw order; higher = drawn on top.
    visible allows AI to spawn invisible sensor objects.
    """
    model_config = ConfigDict(extra="allow")

    color: Optional[str]       = Field(default=None, description="CSS hex colour, e.g. '#3A86FF'")
    tint: Optional[str]        = Field(default=None, description="Override tint on texture")
    texture_key: Optional[str] = Field(default=None, description="Asset registry key")
    z_index: int               = Field(default=0,    description="PixiJS draw order")
    visible: bool              = Field(default=True, description="Whether the object is rendered")
    opacity: float             = Field(default=1.0,  ge=0, le=1, description="Opacity [0,1]")
    label: Optional[str]       = Field(default=None, description="Display label shown in UI")


class RuntimeMetadata(BaseModel):
    """
    Runtime configuration that the frontend reads ONCE during sandbox
    initialisation to configure the Matter.js body before the first frame.

    initial_velocity    — m/s in canvas space
    initial_angle       — radians; initial rotation of the body
    initial_angular_vel — rad/s
    air_resistance      — frictionAir in Matter.js [0, 1]
    is_sleeping         — spawn body in the sleeping state
    collision_filter    — Matter.js collision filter object
    """
    model_config = ConfigDict(extra="allow")

    initial_velocity: Vector2D    = Field(default_factory=Vector2D)
    initial_angle: float          = Field(default=0.0,   description="Initial rotation in radians")
    initial_angular_vel: float    = Field(default=0.0,   description="Initial angular velocity rad/s")
    air_resistance: float         = Field(default=0.01,  ge=0, le=1, description="frictionAir in Matter.js")
    is_sleeping: bool             = Field(default=False)
    collision_filter: Dict[str, Any] = Field(
        default_factory=lambda: {"category": 0x0001, "mask": 0xFFFF, "group": 0},
        description="Matter.js collision filter"
    )


class EducationalMetadata(BaseModel):
    """
    Metadata consumed ONLY by the Tutor and the Relationship Engine.
    The physics engine and renderer ignore this block entirely.

    concept_tags    — curriculum concepts this object illustrates
    observable_ids  — IDs of observables that target this object
    notes           — freeform tutor annotation
    difficulty      — 1 (beginner) → 5 (advanced)
    """
    concept_tags: List[str]     = Field(default_factory=list,  description="e.g. ['newtons_second_law', 'gravity']")
    observable_ids: List[str]   = Field(default_factory=list,  description="Observable IDs bound to this object")
    notes: Optional[str]        = Field(default=None,          description="Tutor free-text annotation")
    difficulty: int             = Field(default=1, ge=1, le=5,  description="Conceptual difficulty level")


# ---------------------------------------------------------------------------
# Core Schema
# ---------------------------------------------------------------------------

class SandboxObject(BaseModel):
    """
    THE universal physics object.

    One schema rules them all — pendulums, rockets, planets, spring blocks,
    pulley wheels, anti-gravity cubes, and every future object type.

    FIELD OVERVIEW
    --------------
    id              — unique identifier within the sandbox (e.g. "bob_1")
    name            — human-readable display name
    shape_type      — geometric shape hint for Matter.js body creation
    object_type     — semantic label for AI/service layer (e.g. "pendulum_bob")
    role            — high-level role for relationship engine
    position        — spawn position in canvas space (px)
    width/height    — dimensions for RECTANGLE shape
    radius          — radius for CIRCLE shape
    vertices        — vertex list for POLYGON shape
    is_static       — immovable anchor body (e.g. pivot point)
    tags            — arbitrary semantic markers (e.g. ["pendulum_bob", "energy_tracked"])
    physics         — PhysicsProperties (extensible)
    visuals         — VisualHints (extensible)
    runtime         — RuntimeMetadata (extensible)
    education       — EducationalMetadata
    """
    model_config = ConfigDict(
        use_enum_values=True,
        validate_default=True,
    )

    # --- Identity ---
    id: str          = Field(..., description="Unique object ID within sandbox")
    name: str        = Field(..., description="Human-readable label, e.g. 'Pendulum Bob'")

    # --- Classification ---
    shape_type: ShapeType   = Field(..., description="Geometric shape for physics body construction")
    object_type: str         = Field(..., description="Semantic type, e.g. 'pendulum_bob', 'rocket_body'")
    role: ObjectRole         = Field(default=ObjectRole.BODY, description="Semantic role in the scenario")

    # --- Geometry ---
    position: Vector2D       = Field(...,                    description="Spawn position in canvas pixels")
    width: Optional[float]   = Field(default=None, gt=0,    description="Width for rectangle shapes (px)")
    height: Optional[float]  = Field(default=None, gt=0,    description="Height for rectangle shapes (px)")
    radius: Optional[float]  = Field(default=None, gt=0,    description="Radius for circle shapes (px)")
    vertices: Optional[List[Vector2D]] = Field(default=None, description="Polygon vertices in local space")

    # --- State ---
    is_static: bool = Field(default=False, description="Immovable anchor body (e.g. pivot, wall)")

    # --- Semantic tags ---
    tags: List[str] = Field(
        default_factory=list,
        description="Semantic markers consumed by AI, relationships, and observables"
    )

    # --- Sub-schemas ---
    physics:   PhysicsProperties   = Field(default_factory=PhysicsProperties)
    visuals:   VisualHints         = Field(default_factory=VisualHints)
    runtime:   RuntimeMetadata     = Field(default_factory=RuntimeMetadata)
    education: EducationalMetadata = Field(default_factory=EducationalMetadata)

    # --- Geometry validation ---
    @model_validator(mode="after")
    def validate_geometry(self) -> "SandboxObject":
        if self.shape_type == ShapeType.CIRCLE and self.radius is None:
            raise ValueError(f"Object '{self.id}' has shape_type='circle' but no radius is set.")
        if self.shape_type == ShapeType.RECTANGLE:
            if self.width is None or self.height is None:
                raise ValueError(f"Object '{self.id}' has shape_type='rectangle' but width/height missing.")
        if self.shape_type == ShapeType.POLYGON and not self.vertices:
            raise ValueError(f"Object '{self.id}' has shape_type='polygon' but no vertices provided.")
        return self

    @field_validator("id")
    @classmethod
    def id_must_be_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SandboxObject id must not be empty or whitespace.")
        return v
