"""
observable_schema.py
====================
Observable definition schema for EduSim sandbox_v2.

ARCHITECTURE PHILOSOPHY
-----------------------
An "observable" is a DECLARATION that a particular measurable quantity
should be tracked, displayed, and made available to the Tutor AI for a
specific sandbox object or global scope.

RESPONSIBILITY SPLIT
--------------------
Backend (this schema):
  - Declares WHICH quantities to observe
  - Specifies HOW to derive them (formula, source properties)
  - Specifies WHO cares (tutor, UI panel, graph)
  - Specifies display metadata (unit, label, colour)

Frontend (Matter.js / PixiJS):
  - COMPUTES actual values every frame
  - Reads the observable declarations to know what to track
  - Pushes current values back via the state-sync API

The backend NEVER computes runtime values.  It only describes them.

OBSERVABLE TYPES
----------------
One schema — `SandboxObservable` — covers all observable types:
  - DIRECT    — read a property from the physics body (position, velocity)
  - DERIVED   — compute from multiple properties (KE = 0.5*m*v²)
  - DELTA     — rate of change of another observable (dv/dt = acceleration)
  - AGGREGATE — sum/average across multiple objects (total momentum)

EXTENSIBILITY
-------------
`derivation_formula` is a string (LaTeX or plain text) describing how to
derive the value.  `source_bindings` maps formula symbols to body properties.
New observable types only require updating this metadata — no schema rewrite.

ANTI-PATTERNS AVOIDED
---------------------
- No VelocityObservable, KineticEnergyObservable sub-classes.
- No runtime value storage in this schema.
- No tight coupling to specific scenarios.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ObservableType(str, Enum):
    """
    How the value of this observable is obtained.

    DIRECT    — read a property directly from the physics body state
    DERIVED   — computed from multiple properties via a formula
    DELTA     — time-derivative of another observable
    AGGREGATE — computed across multiple objects (sum, average, max)
    CUSTOM    — frontend uses a custom derivation defined in extra_params
    """
    DIRECT    = "direct"
    DERIVED   = "derived"
    DELTA     = "delta"
    AGGREGATE = "aggregate"
    CUSTOM    = "custom"


class ObservableDisplayMode(str, Enum):
    """How the observable is presented in the sandbox UI."""
    NUMERIC      = "numeric"      # Plain readout (e.g. "12.3 m/s")
    GRAPH        = "graph"        # Time-series graph panel
    VECTOR_ARROW = "vector_arrow" # Drawn as an arrow on the canvas
    GAUGE        = "gauge"        # Gauge/bar display
    HIDDEN       = "hidden"       # Tracked internally but not displayed


class AggregateFunction(str, Enum):
    """Aggregation method for AGGREGATE observable type."""
    SUM     = "sum"
    AVERAGE = "average"
    MAX     = "max"
    MIN     = "min"
    PRODUCT = "product"


# ---------------------------------------------------------------------------
# Source binding
# ---------------------------------------------------------------------------

class ObservableSourceBinding(BaseModel):
    """
    Maps a symbol in the derivation formula to a concrete data source.

    symbol        — formula symbol (e.g. "m", "v", "k")
    object_id     — target SandboxObject; None = global/environment
    property_path — dot-separated path (e.g. "physics.mass", "runtime.velocity.x")
    observable_id — if the source is another observable (for DELTA / DERIVED chains)
    """
    symbol: str                   = Field(..., description="Formula symbol")
    object_id: Optional[str]      = Field(default=None, description="Source object ID")
    property_path: Optional[str]  = Field(default=None, description="e.g. 'physics.mass'")
    observable_id: Optional[str]  = Field(default=None, description="Source observable for chained derivation")


# ---------------------------------------------------------------------------
# Display configuration
# ---------------------------------------------------------------------------

class ObservableDisplay(BaseModel):
    """
    UI display configuration for the observable panel.

    display_mode   — how to present the value (numeric, graph, vector, gauge)
    label          — display label shown in the UI
    unit           — SI unit string (e.g. "m/s", "J", "N")
    color          — hex colour for the graph line or vector arrow
    decimal_places — rounding for numeric display
    min_value / max_value — gauge/graph axis bounds (None = auto-scale)
    """
    model_config = ConfigDict(extra="allow")

    display_mode: ObservableDisplayMode = Field(default=ObservableDisplayMode.NUMERIC)
    label: str                          = Field(..., description="UI display label, e.g. 'Velocity'")
    unit: str                           = Field(..., description="SI unit string, e.g. 'm/s'")
    color: str                          = Field(default="#00D4FF", description="Display colour hex")
    decimal_places: int                 = Field(default=2, ge=0, le=6)
    min_value: Optional[float]          = Field(default=None, description="Axis min for graph/gauge")
    max_value: Optional[float]          = Field(default=None, description="Axis max for graph/gauge")
    show_in_panel: bool                 = Field(default=True, description="Appear in the observable panel")
    show_on_canvas: bool                = Field(default=False, description="Overlay directly on the canvas")


# ---------------------------------------------------------------------------
# Tutor metadata
# ---------------------------------------------------------------------------

class ObservableTutorMeta(BaseModel):
    """
    Metadata consumed by the Tutor AI and RAG system.

    concept_tags    — curriculum concepts this observable illustrates
    tutor_questions — Socratic questions triggered when the value changes
    importance      — how educationally significant this observable is [1, 5]
    """
    concept_tags: List[str]    = Field(default_factory=list)
    tutor_questions: List[str] = Field(default_factory=list, description="Questions triggered on value change")
    importance: int            = Field(default=3, ge=1, le=5, description="Educational importance [1,5]")


# ---------------------------------------------------------------------------
# Core Schema
# ---------------------------------------------------------------------------

class SandboxObservable(BaseModel):
    """
    THE universal observable declaration.

    Covers all measurable quantities — velocity, acceleration, momentum,
    kinetic energy, tension, angular velocity, period, and any future
    derived quantity — through one generic schema.

    KEY FIELDS
    ----------
    id                 — unique within the sandbox
    observable_type    — DIRECT | DERIVED | DELTA | AGGREGATE | CUSTOM
    target_object_ids  — which objects this observable measures (can be multiple)
    derivation_formula — LaTeX formula for DERIVED observables
    source_bindings    — maps formula symbols to property paths
    aggregate_fn       — aggregation method for AGGREGATE type
    delta_source_id    — source observable ID for DELTA type
    display            — UI display configuration
    tutor              — tutor integration metadata
    extra_params       — open dict for future extensions

    EXAMPLES
    --------
    Velocity (DIRECT):
      observable_type = "direct"
      target_object_ids = ["pendulum_bob"]
      source_bindings = [ObservableSourceBinding(symbol="v", object_id="pendulum_bob", property_path="runtime.velocity")]

    Kinetic Energy (DERIVED):
      observable_type = "derived"
      target_object_ids = ["pendulum_bob"]
      derivation_formula = "KE = 0.5 * m * v^2"
      source_bindings = [
        ObservableSourceBinding(symbol="m", object_id="pendulum_bob", property_path="physics.mass"),
        ObservableSourceBinding(symbol="v", observable_id="vel_pendulum_bob"),
      ]

    Total Momentum (AGGREGATE):
      observable_type = "aggregate"
      target_object_ids = ["block_a", "block_b"]
      aggregate_fn = "sum"
    """
    model_config = ConfigDict(use_enum_values=True)

    # --- Identity ---
    id: str   = Field(..., description="Unique observable ID")
    name: str = Field(..., description="Human-readable name, e.g. 'Pendulum Bob Velocity'")

    # --- Type & Scope ---
    observable_type: ObservableType = Field(..., description="How this observable's value is obtained")
    target_object_ids: List[str]    = Field(
        default_factory=list,
        description="IDs of SandboxObjects this observable tracks"
    )

    # --- Derivation (for DERIVED and DELTA) ---
    derivation_formula: Optional[str] = Field(
        default=None,
        description="LaTeX formula for DERIVED observables, e.g. 'KE = 0.5 m v^2'"
    )
    source_bindings: List[ObservableSourceBinding] = Field(
        default_factory=list,
        description="Maps formula symbols to object property paths"
    )

    # --- Aggregation (for AGGREGATE) ---
    aggregate_fn: Optional[AggregateFunction] = Field(
        default=None,
        description="Aggregation function for AGGREGATE type"
    )

    # --- Delta (for DELTA type) ---
    delta_source_id: Optional[str] = Field(
        default=None,
        description="ID of the source observable whose time-derivative this represents"
    )

    # --- Display ---
    display: ObservableDisplay = Field(
        ...,
        description="UI display configuration"
    )

    # --- Tutor ---
    tutor: ObservableTutorMeta = Field(default_factory=ObservableTutorMeta)

    # --- Extensibility ---
    extra_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Future or type-specific parameters"
    )

    @field_validator("id")
    @classmethod
    def id_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SandboxObservable id must not be empty.")
        return v
