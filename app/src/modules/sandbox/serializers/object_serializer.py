"""
object_serializer.py
====================
Physical Body Runtime State Serializer for EduSim.

Converts deep backend ObjectRuntimeState tracking parameters (positions, 
velocities, accelerations, forces, collisions) into frontend-safe, 
serializable JSON contracts matching generic Matter.js/PixiJS coordinate expectations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.src.modules.sandbox.state.object_state import ObjectRuntimeState


class ObjectSerializer:
    """
    Serializes live backend physics body coordinates and states, removing 
    internal references and formatting vectors to be compatible with frontend renderers.
    """

    @staticmethod
    def serialize_vector(vector: Any) -> Dict[str, float]:
        """Ensures a vector payload has standard, serializable floating point coordinates."""
        if hasattr(vector, "x") and hasattr(vector, "y"):
            return {
                "x": round(float(vector.x), 5),
                "y": round(float(vector.y), 5)
            }
        elif isinstance(vector, dict):
            return {
                "x": round(float(vector.get("x", 0.0)), 5),
                "y": round(float(vector.get("y", 0.0)), 5)
            }
        return {"x": 0.0, "y": 0.0}

    @classmethod
    def serialize_object(
        cls,
        obj_state: ObjectRuntimeState,
        static_meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Converts a live ObjectRuntimeState physical body, combining it with 
        optional initial static geometry/render properties (color, shape, role, labels).
        """
        meta = static_meta or {}
        
        # 1. Base static descriptors
        payload = {
            "id": obj_state.id,
            "role": meta.get("role", "dynamic"),
            "shape": meta.get("shape", "rectangle"),
            "dimensions": meta.get("dimensions", {}),
            "label": meta.get("label", obj_state.id.capitalize()),
            "render": meta.get("render", {
                "color": "#4A90E2",
                "stroke_color": "#2C3E50",
                "stroke_width": 2,
                "visible": obj_state.is_visible
            })
        }

        # 2. Add Live Physical State Parameters
        payload["physics"] = {
            "position": cls.serialize_vector(obj_state.position),
            "velocity": cls.serialize_vector(obj_state.velocity),
            "acceleration": cls.serialize_vector(obj_state.acceleration),
            "angle": round(float(obj_state.angle), 5),
            "angular_velocity": round(float(obj_state.angular_velocity), 5),
            "angular_acceleration": round(float(obj_state.angular_acceleration), 5),
            "net_force": cls.serialize_vector(obj_state.net_force),
            "torque": round(float(obj_state.torque), 5),
            "mass": round(float(obj_state.mass), 5),
            "inertia": round(float(obj_state.inertia), 5),
            "is_static": obj_state.is_static,
            "is_sleeping": obj_state.is_sleeping,
            "is_sensor": obj_state.is_sensor
        }

        # 3. Add derived physics overlay descriptors
        payload["derived"] = {
            "kinetic_energy": round(float(obj_state.get_kinetic_energy()), 5),
            "rotational_energy": round(float(obj_state.get_rotational_energy()), 5),
            "momentum": cls.serialize_vector(obj_state.get_momentum_vector())
        }

        # 4. Add interactive and state markers
        payload["interaction"] = {
            "is_visible": obj_state.is_visible,
            "is_selected": obj_state.is_selected,
            "is_hovered": obj_state.is_hovered,
            "colliding_with": list(obj_state.colliding_with)
        }

        return payload

    @classmethod
    def serialize_objects(
        cls,
        objects_states: Dict[str, ObjectRuntimeState],
        static_objects_meta: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Serializes multiple active objects into a clean, flat list contract."""
        meta_map = {m.get("id"): m for m in (static_objects_meta or []) if m.get("id")}
        
        serialized_list = []
        for oid, state in objects_states.items():
            static_meta = meta_map.get(oid)
            serialized_list.append(cls.serialize_object(state, static_meta))
            
        return serialized_list
