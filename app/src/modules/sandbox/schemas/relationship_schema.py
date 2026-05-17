"""
relationship_schema.py
======================
Educational relationship schema for EduSim sandbox_v2.

ARCHITECTURE PHILOSOPHY
-----------------------
A "relationship" is an EDUCATIONAL MAPPING, not a runtime physics constraint.
It encodes:
  - The physics formula governing the interaction (e.g. "F = -kx")
  - Which sandbox objects and properties participate
  - What observables are related
  - What curriculum concepts are illustrated
  - How the Tutor should reason about it

Relationships are consumed by:
  1. The Tutor AI  — to explain why things happen
  2. The Observable system — to know which quantities are causally linked
  3. The RAG system — to retrieve relevant curriculum content
  4. The dependency graph — to track which values change when parameters change

Relationships are NOT consumed by:
  - Matter.js runtime
  - PixiJS renderer
  - Any physics integration loop

DESIGN
------
One schema — `EducationalRelationship` — covers Newton's Laws, Hooke's Law,
Pendulum period, energy conservation, gravitational attraction, Bernoulli,
and every future relationship.

Extensibility is achieved through:
  - `formula_latex`  — human/tutor-readable formula
  - `formula_sympy`  — optional machine-parseable form
  - `variable_map`   — maps formula symbols to sandbox object property paths
  - `extra_context`  — open dict for future tutor reasoning metadata

ANTI-PATTERNS AVOIDED
---------------------
- No NewtonsLawSchema, HookesLawSchema, etc.
- No runtime physics calculation in this file.
- No tight coupling to specific scenario types.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class RelationshipScope(str, Enum):
    """
    Defines which layer of the system the relationship is most relevant to.
    """
    GLOBAL    = "global"    # Applies across the whole sandbox (e.g. gravity)
    PAIRWISE  = "pairwise"  # Between exactly two objects (e.g. spring force)
    OBJECT    = "object"    # Intrinsic to a single object (e.g. kinetic energy)
    SYSTEM    = "system"    # Emergent property of the full system (e.g. total momentum)


class CurriculumLevel(str, Enum):
    """
    Approximate educational curriculum level for tutor difficulty filtering.
    """
    PRIMARY         = "primary"
    MIDDLE_SCHOOL   = "middle_school"
    HIGH_SCHOOL     = "high_school"
    UNDERGRADUATE   = "undergraduate"
    ADVANCED        = "advanced"


# ---------------------------------------------------------------------------
# Variable mapping
# ---------------------------------------------------------------------------

class VariableBinding(BaseModel):
    """
    Maps one symbol in a formula to a concrete property path in the sandbox.

    symbol       — the formula symbol (e.g. "m", "k", "v")
    description  — human-readable meaning (e.g. "mass of the pendulum bob")
    object_id    — which SandboxObject this symbol refers to (None = environment)
    property_path — dot-separated path into the object's schema
                   (e.g. "physics.mass", "runtime.initial_velocity.x")
    observable_id — if the symbol maps to a live observable rather than a
                    static property
    unit         — SI unit string (e.g. "kg", "m/s", "N")
    """
    symbol: str                   = Field(..., description="Formula symbol, e.g. 'm'")
    description: str              = Field(..., description="Human-readable meaning")
    object_id: Optional[str]      = Field(default=None, description="Target object ID; None = environment/global")
    property_path: Optional[str]  = Field(default=None, description="e.g. 'physics.mass'")
    observable_id: Optional[str]  = Field(default=None, description="Observable ID if live-measured")
    unit: Optional[str]           = Field(default=None, description="SI unit, e.g. 'kg'")


# ---------------------------------------------------------------------------
# Core Schema
# ---------------------------------------------------------------------------

class EducationalRelationship(BaseModel):
    """
    THE universal educational relationship.

    Examples of what one EducationalRelationship represents:

    Newton's Second Law:
      id            = "newtons_second_law"
      formula       = "F = ma"
      scope         = PAIRWISE
      variable_map  = [
        VariableBinding(symbol="F", description="Net force", object_id="block_1", property_path="runtime.net_force"),
        VariableBinding(symbol="m", description="Mass", object_id="block_1", property_path="physics.mass"),
        VariableBinding(symbol="a", description="Acceleration", object_id="block_1", observable_id="accel_block_1"),
      ]

    Hooke's Law:
      id            = "hookes_law_spring_1"
      formula       = "F = -k * x"
      scope         = PAIRWISE
      depends_on    = ["spring_constant_spring_1", "displacement_spring_1"]

    FIELD OVERVIEW
    --------------
    id               — unique within the sandbox
    name             — human-readable name (e.g. "Newton's Second Law")
    formula_latex    — LaTeX-formatted formula for display
    formula_sympy    — Optional SymPy-parseable string for symbolic computation
    scope            — RelationshipScope
    concept_tags     — curriculum tags (e.g. ["newtons_second_law", "kinematics"])
    curriculum_level — educational level
    object_ids       — IDs of SandboxObjects this relationship involves
    variable_map     — symbol → object property bindings
    depends_on       — IDs of other relationships this one builds upon
    tutor_hints      — ordered list of Socratic questions or explanations
    extra_context    — open dict for future tutor reasoning metadata
    """
    model_config = ConfigDict(use_enum_values=True)

    # --- Identity ---
    id: str   = Field(..., description="Unique relationship ID, e.g. 'hookes_law_spring_1'")
    name: str = Field(..., description="Human-readable name, e.g. \"Hooke's Law\"")

    # --- Formula ---
    formula_latex: str          = Field(..., description="LaTeX formula string, e.g. 'F = -kx'")
    formula_sympy: Optional[str] = Field(default=None, description="SymPy-parseable formula for symbolic computation")
    formula_description: str    = Field(default="", description="Plain-English explanation of the formula")

    # --- Scope & Classification ---
    scope: RelationshipScope       = Field(default=RelationshipScope.PAIRWISE)
    curriculum_level: CurriculumLevel = Field(default=CurriculumLevel.HIGH_SCHOOL)
    concept_tags: List[str]        = Field(default_factory=list, description="e.g. ['hookes_law', 'oscillation']")

    # --- Object linkage ---
    object_ids: List[str] = Field(
        default_factory=list,
        description="IDs of SandboxObjects involved in this relationship"
    )

    # --- Variable bindings ---
    variable_map: List[VariableBinding] = Field(
        default_factory=list,
        description="Maps formula symbols to concrete sandbox property paths"
    )

    # --- Dependency graph ---
    depends_on: List[str] = Field(
        default_factory=list,
        description="IDs of other EducationalRelationships this one depends on"
    )

    # --- Tutor integration ---
    tutor_hints: List[str] = Field(
        default_factory=list,
        description="Ordered Socratic questions/prompts for the Tutor AI"
    )
    rag_query_template: Optional[str] = Field(
        default=None,
        description="Template prompt for RAG retrieval, e.g. 'Explain {name} for {curriculum_level} students'"
    )

    # --- Extensibility ---
    extra_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Future tutor reasoning metadata not yet modelled"
    )

    @field_validator("id")
    @classmethod
    def id_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("EducationalRelationship id must not be empty.")
        return v
