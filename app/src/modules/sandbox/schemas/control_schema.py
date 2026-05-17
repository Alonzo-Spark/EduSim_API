"""
control_schema.py
=================
Metadata-driven sandbox control schema for EduSim sandbox_v2.

ARCHITECTURE PHILOSOPHY
-----------------------
A "control" is a UI element DECLARATION.  It tells the frontend:
  - What kind of widget to render (slider, toggle, button, select, numericInput)
  - What sandbox property or environment field it binds to
  - What label, min/max, step to display
  - What educational concept it exercises

Controls are METADATA, not executable code.  The frontend:
  1. Reads the control declarations at sandbox initialisation.
  2. Renders the appropriate widgets dynamically.
  3. When a user interacts, applies the value change to the sandbox via the
     runtime property-sync API (separate from this schema).

The backend NEVER renders widgets or handles UI events.

DESIGN CHOICES
--------------
1. One schema — `SandboxControl` — covers all widget types via `widget_type`
   string and `widget_config` open dict.  No SliderSchema, ToggleSchema, etc.

2. `binding` precisely describes which object property or environment field
   the control affects, enabling the frontend to apply changes with zero
   additional configuration.

3. `educational_impact` tells the Tutor AI which concept the user is currently
   exploring when they touch this control.

EXTENSIBILITY
-------------
New widget types (e.g. "joystick", "color_picker") are supported by adding a
new `widget_type` string and a corresponding `widget_config` dict — no schema
rewrite required.

ANTI-PATTERNS AVOIDED
---------------------
- No GravitySliderSchema, MassSliderSchema, etc.
- No event handler logic.
- No frontend rendering code.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class WidgetType(str, Enum):
    """
    Supported UI widget types.

    SLIDER        — continuous range input (most common)
    TOGGLE        — boolean on/off switch
    BUTTON        — momentary action trigger
    SELECT        — dropdown option selector
    NUMERIC_INPUT — text field for precise numeric entry
    CUSTOM        — frontend resolves widget from widget_config
    """
    SLIDER        = "slider"
    TOGGLE        = "toggle"
    BUTTON        = "button"
    SELECT        = "select"
    NUMERIC_INPUT = "numeric_input"
    CUSTOM        = "custom"


class ControlScope(str, Enum):
    """
    What the control targets.

    OBJECT      — modifies a property of a specific SandboxObject
    ENVIRONMENT — modifies a global environment field
    SIMULATION  — controls simulation state (pause, reset, speed)
    CUSTOM      — frontend interprets from binding
    """
    OBJECT      = "object"
    ENVIRONMENT = "environment"
    SIMULATION  = "simulation"
    CUSTOM      = "custom"


# ---------------------------------------------------------------------------
# Binding definition
# ---------------------------------------------------------------------------

class ControlBinding(BaseModel):
    """
    Describes exactly WHAT the control modifies in the sandbox.

    scope         — OBJECT | ENVIRONMENT | SIMULATION | CUSTOM
    object_id     — target SandboxObject ID (only for OBJECT scope)
    property_path — dot-separated path into the target schema
                   (e.g. "physics.mass", "gravity.y", "wind.magnitude")
    action        — for BUTTON type: action identifier sent to frontend
                   (e.g. "reset", "launch", "pause")
    """
    scope: ControlScope           = Field(default=ControlScope.OBJECT)
    object_id: Optional[str]      = Field(default=None, description="Target object for OBJECT scope")
    property_path: Optional[str]  = Field(default=None, description="e.g. 'physics.mass'")
    action: Optional[str]         = Field(default=None, description="Action name for BUTTON type")

    @model_validator(mode="after")
    def validate_binding(self) -> "ControlBinding":
        if self.scope == ControlScope.OBJECT and self.object_id is None:
            raise ValueError("OBJECT-scoped control must specify object_id.")
        if self.scope == ControlScope.OBJECT and self.property_path is None:
            raise ValueError("OBJECT-scoped control must specify property_path.")
        if self.scope == ControlScope.ENVIRONMENT and self.property_path is None:
            raise ValueError("ENVIRONMENT-scoped control must specify property_path.")
        return self


# ---------------------------------------------------------------------------
# Slider configuration sub-schema
# ---------------------------------------------------------------------------

class SliderConfig(BaseModel):
    """Typed configuration for SLIDER widgets."""
    model_config = ConfigDict(extra="allow")

    min_value: float  = Field(..., description="Minimum slider value")
    max_value: float  = Field(..., description="Maximum slider value")
    step: float       = Field(default=0.1, gt=0, description="Slider step increment")
    default_value: float = Field(..., description="Initial slider position")
    unit: Optional[str]  = Field(default=None, description="Display unit label (e.g. 'kg', 'm/s')")


class SelectOption(BaseModel):
    """A single option in a SELECT widget."""
    value: Union[str, float, int, bool]
    label: str


class SelectConfig(BaseModel):
    """Typed configuration for SELECT widgets."""
    options: List[SelectOption] = Field(..., description="Available options")
    default_value: Union[str, float, int, bool] = Field(..., description="Initial selected value")


# ---------------------------------------------------------------------------
# Core Schema
# ---------------------------------------------------------------------------

class SandboxControl(BaseModel):
    """
    THE universal control declaration.

    Covers sliders, toggles, buttons, selects, and numeric inputs through one
    schema with typed `widget_config` and an extensibility escape hatch.

    KEY FIELDS
    ----------
    id                  — unique within the sandbox
    label               — UI display label
    widget_type         — SLIDER | TOGGLE | BUTTON | SELECT | NUMERIC_INPUT | CUSTOM
    binding             — what property/action this control affects
    widget_config       — typed configuration for known widgets; Dict for CUSTOM
    is_enabled          — initial enabled state
    is_visible          — initial visibility
    group               — UI panel group name for layout (e.g. "Forces", "Environment")
    educational_impact  — concept tags triggered when user interacts
    tooltip             — hover description shown in UI
    display_order       — sort order within its group
    extra_params        — open dict for future widget types

    EXAMPLES
    --------
    Mass Slider:
      widget_type = "slider"
      binding = ControlBinding(scope=OBJECT, object_id="block_1", property_path="physics.mass")
      widget_config = SliderConfig(min=0.1, max=50.0, step=0.1, default=5.0, unit="kg")

    Gravity Toggle:
      widget_type = "toggle"
      binding = ControlBinding(scope=ENVIRONMENT, property_path="gravity.y")

    Launch Button:
      widget_type = "button"
      binding = ControlBinding(scope=SIMULATION, action="launch")
    """
    model_config = ConfigDict(use_enum_values=True)

    # --- Identity ---
    id: str    = Field(..., description="Unique control ID")
    label: str = Field(..., description="UI display label, e.g. 'Bob Mass'")

    # --- Widget ---
    widget_type: WidgetType = Field(..., description="Widget type")
    widget_config: Any      = Field(
        default=None,
        description="SliderConfig | SelectConfig | Dict for CUSTOM | None for TOGGLE/BUTTON"
    )

    # --- Binding ---
    binding: ControlBinding = Field(..., description="What this control modifies in the sandbox")

    # --- State ---
    is_enabled: bool = Field(default=True,  description="Initially enabled")
    is_visible: bool = Field(default=True,  description="Initially visible")

    # --- UI Layout ---
    group: str           = Field(default="General", description="UI panel group name")
    display_order: int   = Field(default=0,          description="Sort order within group")
    tooltip: Optional[str] = Field(default=None,     description="Hover tooltip text")

    # --- Educational ---
    educational_impact: List[str] = Field(
        default_factory=list,
        description="Concept tags triggered by user interaction (e.g. ['newtons_second_law'])"
    )

    # --- Extensibility ---
    extra_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Future or CUSTOM widget-type parameters"
    )

    @field_validator("id")
    @classmethod
    def id_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SandboxControl id must not be empty.")
        return v
