"""
__init__.py
===========
Public interface for the EduSim Sandbox Relationships Module.

This package exposes the educational physics intelligence layer, canonical formulas,
dynamic builders, concept registries, and dependency graph utilities to the rest
of the EduSim backend (tutor, synthesis orchestration, and APIs).

Usage:
  from app.src.modules.sandbox.relationships import (
      registry,
      RelationshipBuilder,
      ConceptualDependencyGraph,
      CONCEPT_LIBRARY
  )
"""

from .formulas import (
    PhysicsFormula,
    FormulaVariable,
    FORMULA_LIBRARY
)

from .educational_mappings import (
    ConceptDefinition,
    Misconception,
    CONCEPT_LIBRARY
)

from .registry import (
    registry,
    RelationshipRegistry
)

from .dependency_graph import (
    ConceptualDependencyGraph,
    DependencyNode
)

from .relationship_builder import (
    RelationshipBuilder,
    RelationshipDetector
)

__all__ = [
    # --- Formulas ---
    "PhysicsFormula",
    "FormulaVariable",
    "FORMULA_LIBRARY",
    # --- Educational Mappings ---
    "ConceptDefinition",
    "Misconception",
    "CONCEPT_LIBRARY",
    # --- Registry ---
    "registry",
    "RelationshipRegistry",
    # --- Dependency Graph ---
    "ConceptualDependencyGraph",
    "DependencyNode",
    # --- Relationship Builder ---
    "RelationshipBuilder",
    "RelationshipDetector"
]
