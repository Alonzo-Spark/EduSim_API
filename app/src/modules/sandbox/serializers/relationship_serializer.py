"""
relationship_serializer.py
==========================
Educational Relationship Schema Serializer for EduSim.

Converts complex EducationalRelationship graphs, LaTeX formula strings, 
misconceptions, and variable binding maps into generic frontend-safe contracts 
for displaying educational panels, equations, and tutorial sidebars.
"""

from __future__ import annotations

from typing import Any, Dict, List
from app.src.modules.sandbox.schemas.relationship_schema import EducationalRelationship


class RelationshipSerializer:
    """
    Serializes educational relationships, removing deep Python objects and 
    cleaning symbol bindings for UI/UX overlay presentations.
    """

    @classmethod
    def serialize_variable_binding(cls, binding: Any) -> Dict[str, Any]:
        """Converts a VariableBinding model into a standard serializable dictionary."""
        return {
            "symbol": getattr(binding, "symbol", ""),
            "description": getattr(binding, "description", ""),
            "object_id": getattr(binding, "object_id", None),
            "property_path": getattr(binding, "property_path", None),
            "observable_id": getattr(binding, "observable_id", None),
            "unit": getattr(binding, "unit", "")
        }

    @classmethod
    def serialize_relationship(cls, rel: EducationalRelationship) -> Dict[str, Any]:
        """Converts an EducationalRelationship model into a frontend-safe dict."""
        
        # 1. Map variable bindings cleanly
        variable_bindings = []
        if hasattr(rel, "variable_map") and rel.variable_map:
            # Could be list or dict
            if isinstance(rel.variable_map, dict):
                for binding in rel.variable_map.values():
                    variable_bindings.append(cls.serialize_variable_binding(binding))
            elif isinstance(rel.variable_map, list):
                for binding in rel.variable_map:
                    variable_bindings.append(cls.serialize_variable_binding(binding))

        # 2. Serialize misconception templates
        misconceptions = []
        if hasattr(rel, "misconceptions") and rel.misconceptions:
            for mis in rel.misconceptions:
                misconceptions.append({
                    "id": getattr(mis, "id", "mis_unknown"),
                    "name": getattr(mis, "name", "Misconception"),
                    "description": getattr(mis, "description", ""),
                    "remediation_questions": getattr(mis, "remediation_questions", [])
                })

        # 3. Assemble unified contract payload
        payload = {
            "id": rel.id,
            "name": rel.name,
            "scope": rel.scope.value if hasattr(rel.scope, "value") else str(rel.scope),
            "concept_tags": list(rel.concept_tags) if rel.concept_tags else [],
            "formula_latex": rel.formula_latex,
            "formula_sympy": rel.formula_sympy,
            "variable_map": variable_bindings,
            "curriculum_level": rel.curriculum_level.value if hasattr(rel.curriculum_level, "value") else str(rel.curriculum_level),
            "misconceptions": misconceptions,
            "tutor_hints": list(rel.tutor_hints) if rel.tutor_hints else [],
            "extra_context": dict(rel.extra_context) if rel.extra_context else {}
        }

        return payload

    @classmethod
    def serialize_relationships(
        cls,
        relationships: List[EducationalRelationship]
    ) -> List[Dict[str, Any]]:
        """Serializes multiple educational relationships."""
        return [cls.serialize_relationship(r) for r in relationships]
