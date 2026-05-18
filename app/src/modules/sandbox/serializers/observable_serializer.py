"""
observable_serializer.py
========================
Educational Observable State Serializer for EduSim.

Combines live calculated physical metrics (speeds, energies, momentum values) 
with static pedagogical configurations (formulas, overlays, concept tags)
into frontend-ready observable payloads.
"""

from __future__ import annotations

from typing import Any, Dict, List
from app.src.modules.sandbox.schemas.observable_schema import SandboxObservable
from app.src.modules.sandbox.state.observable_state import ObservableRuntimeValue


class ObservableSerializer:
    """
    Translates active educational observables (live calculations) into 
    frontend-safe structures capable of rendering gauges, overlays, or sidebars.
    """

    @classmethod
    def serialize_observable(
        cls,
        schema: SandboxObservable,
        live_val: ObservableRuntimeValue
    ) -> Dict[str, Any]:
        """
        Combines the static sandbox schema layout with its live computed float value 
        to build a standardized generic observable contract.
        """
        # 1. Base display layout options
        display = schema.display or {}
        display_mode_raw = getattr(display, "display_mode", "numeric")
        display_mode_str = display_mode_raw.value if hasattr(display_mode_raw, "value") else str(display_mode_raw)

        display_dict = {
            "display_mode": display_mode_str,
            "color": getattr(display, "color", "#00D4FF"),
            "visible": getattr(display, "show_in_panel", True),
            "show_on_canvas": getattr(display, "show_on_canvas", False),
            "label": getattr(display, "label", schema.name),
            "min_value": float(getattr(display, "min_value", 0.0)) if getattr(display, "min_value", None) is not None else None,
            "max_value": float(getattr(display, "max_value", 100.0)) if getattr(display, "max_value", None) is not None else None
        }

        # 2. Extract tutor alerts details
        tutor = schema.tutor or {}
        tutor_dict = {
            "concept_tags": getattr(tutor, "concept_tags", []),
            "tutor_questions": getattr(tutor, "tutor_questions", []),
            "importance": int(getattr(tutor, "importance", 3))
        }

        # 3. Assemble unified contract
        payload = {
            "id": schema.id,
            "name": schema.name,
            "observable_type": schema.observable_type.value if hasattr(schema.observable_type, "value") else str(schema.observable_type),
            "value": round(float(live_val.value), 4),
            "unit": schema.display.unit if (schema.display and hasattr(schema.display, "unit")) else "",
            "derivation_formula": schema.derivation_formula,
            "target_object_ids": schema.target_object_ids,
            "display": display_dict,
            "tutor": tutor_dict
        }

        return payload

    @classmethod
    def serialize_observables(
        cls,
        schemas: List[SandboxObservable] | Dict[str, SandboxObservable],
        live_vals: Dict[str, ObservableRuntimeValue]
    ) -> List[Dict[str, Any]]:
        """Serializes multiple educational observables."""
        serialized_list = []
        
        # Standardize schemas to a list representation
        schema_list = schemas.values() if isinstance(schemas, dict) else schemas
        
        for schema in schema_list:
            oid = schema.id
            # Retrieve live value (default to 0.0 if not yet evaluated)
            val = live_vals.get(oid) or ObservableRuntimeValue(id=oid)
            serialized_list.append(cls.serialize_observable(schema, val))
            
        return sorted(serialized_list, key=lambda x: x["id"])
