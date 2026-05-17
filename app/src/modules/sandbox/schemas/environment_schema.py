"""
environment_schema.py
=====================
Strongly-typed, extensible environment schema for EduSim sandbox_v2.

ARCHITECTURE PHILOSOPHY
-----------------------
The environment describes the *world conditions* in which all sandbox objects
exist.  It is composed of multiple sub-schemas, each covering one physical
domain (gravity, wind, atmosphere, magnetic field, fluid, light).

DESIGN CHOICES
--------------
1. Strongly-typed sub-schemas (NOT a single flat `Dict[str, Any]`) for the
   known environment domains.  This gives IDE support, validation, and clear
   ownership of each field.

2. `extra_fields: Dict[str, Any]` on the root `SandboxEnvironment` absorbs
   future domain additions (e.g., an electric field, a radiation zone) without
   a schema rewrite.

3. All sub-schemas use `ConfigDict(extra='allow')` to accept future fields
   within their domain without failing validation.

ANTI-PATTERNS AVOIDED
---------------------
- No flat `environment: Dict[str, Any]` — unvalidated, undocumented.
- No hardcoded scenario assumptions ("pendulum mode", "space mode").
- No runtime physics integration in this file.

FRONTEND CONTRACT
-----------------
The frontend reads the serialised `SandboxEnvironment` once during sandbox
initialisation and applies it to the Matter.js world and PixiJS scene:
  - `gravity`  → Matter.World.gravity
  - `wind`     → per-frame external force applied to non-static bodies
  - `fluid`    → drag coefficient applied by frontend physics loop
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class AtmosphereType(str, Enum):
    """
    Preset atmosphere types — determines default air density, drag, and sound.
    The service layer may override individual fluid/atmosphere fields after
    selecting a preset.
    """
    VACUUM    = "vacuum"     # No air resistance, no sound propagation
    EARTH     = "earth"      # Standard atmosphere
    WATER     = "water"      # Dense fluid
    MOON      = "moon"       # Negligible atmosphere
    MARS      = "mars"       # Thin CO₂ atmosphere
    CUSTOM    = "custom"     # All fields set explicitly


# ---------------------------------------------------------------------------
# Domain sub-schemas
# ---------------------------------------------------------------------------

class GravityField(BaseModel):
    """
    Global gravity applied to all bodies proportional to their gravity_scale.

    x, y are acceleration components in m/s² (SI), converted to canvas space
    by the frontend scale factor.

    Setting y = 0.0 and x = 0.0 produces a zero-gravity environment.
    Setting y = -9.81 inverts gravity (anti-gravity).
    Per-body overrides are handled via `SandboxObject.physics.gravity_scale`.
    """
    model_config = ConfigDict(extra="allow")

    x: float = Field(default=0.0,   description="Horizontal gravity component m/s²")
    y: float = Field(default=9.81,  description="Vertical gravity component m/s² (positive = downward)")
    scale: float = Field(default=1.0, ge=0, description="Global gravity magnitude multiplier")


class WindField(BaseModel):
    """
    Constant wind force applied as a horizontal acceleration to all
    non-static, non-sensor bodies each frame.

    The frontend applies this as a proportional external force:
      F_wind = wind.magnitude * body.mass * wind.direction_vector
    """
    model_config = ConfigDict(extra="allow")

    enabled: bool  = Field(default=False)
    magnitude: float = Field(default=0.0, ge=0, description="Wind speed in m/s")
    direction_deg: float = Field(default=0.0, description="Wind bearing in degrees (0=East, 90=North)")
    turbulence: float = Field(default=0.0, ge=0, le=1, description="Random variation [0,1]")


class AtmosphereField(BaseModel):
    """
    Fluid/atmospheric properties that produce drag on moving bodies.

    air_density   — kg/m³; 1.225 = Earth sea level
    drag_coeff    — dimensionless; multiplied with body cross-section
    sound_speed   — m/s; used by future audio/shock-wave simulations
    """
    model_config = ConfigDict(extra="allow")

    type: AtmosphereType = Field(default=AtmosphereType.EARTH)
    air_density: float   = Field(default=1.225, ge=0, description="Air density kg/m³")
    drag_coeff: float    = Field(default=0.47,  ge=0, description="Drag coefficient (sphere ≈ 0.47)")
    sound_speed: float   = Field(default=343.0, gt=0, description="Speed of sound m/s")


class MagneticField(BaseModel):
    """
    Uniform magnetic field for future electromagnetic simulation scenarios.

    strength — Tesla (T)
    direction — unit vector components of B field
    Only affects objects tagged with ["charged_particle"] and carrying
    `physics_properties.charge`.
    """
    model_config = ConfigDict(extra="allow")

    enabled: bool     = Field(default=False)
    strength: float   = Field(default=0.0, ge=0, description="Magnetic flux density in Tesla")
    direction_x: float = Field(default=0.0, description="B field X component (normalised)")
    direction_y: float = Field(default=0.0, description="B field Y component (normalised)")
    direction_z: float = Field(default=1.0, description="B field Z component (normalised, out-of-plane)")


class FluidField(BaseModel):
    """
    Fluid immersion zone.  When enabled, all bodies within the fluid zone
    experience buoyancy and increased drag.

    density     — kg/m³ (water ≈ 1000, mercury ≈ 13600)
    viscosity   — dynamic viscosity Pa·s (water ≈ 0.001)
    zone_y      — canvas Y coordinate of the fluid surface (px from top)
    """
    model_config = ConfigDict(extra="allow")

    enabled: bool     = Field(default=False)
    density: float    = Field(default=1000.0, gt=0, description="Fluid density kg/m³")
    viscosity: float  = Field(default=0.001,  ge=0, description="Dynamic viscosity Pa·s")
    zone_y: Optional[float] = Field(default=None, description="Y-coord of fluid surface in canvas px")


class LightingEnvironment(BaseModel):
    """
    Ambient scene lighting hints for the PixiJS renderer.
    Has no effect on physics simulation.

    background_color — hex colour of the canvas background
    ambient_light    — overall brightness [0, 1]
    theme            — renderer theme preset
    """
    model_config = ConfigDict(extra="allow")

    background_color: str = Field(default="#1a1a2e", description="Canvas background hex colour")
    ambient_light: float  = Field(default=0.8, ge=0, le=1, description="Global lighting intensity")
    theme: str            = Field(default="dark", description="Renderer theme: 'dark' | 'light' | 'space' | 'underwater'")


# ---------------------------------------------------------------------------
# Root Environment Schema
# ---------------------------------------------------------------------------

class SandboxEnvironment(BaseModel):
    """
    THE sandbox environment contract.

    Combines all physical domain fields into one structure that is:
    - Passed to the frontend at sandbox initialisation.
    - Used by the relationship engine for formula context (e.g., g in F=mg).
    - Used by the Tutor AI to explain environmental effects.

    EXTENSIBILITY
    -------------
    `extra_fields` absorbs future domains (electric fields, radiation zones,
    temperature gradients) without a schema rewrite.
    """
    gravity:    GravityField      = Field(default_factory=GravityField)
    wind:       WindField         = Field(default_factory=WindField)
    atmosphere: AtmosphereField   = Field(default_factory=AtmosphereField)
    magnetic:   MagneticField     = Field(default_factory=MagneticField)
    fluid:      FluidField        = Field(default_factory=FluidField)
    lighting:   LightingEnvironment = Field(default_factory=LightingEnvironment)

    # Open extension bag for future domains
    extra_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Future environment domains not yet modelled (e.g., electric_field, temperature)"
    )
