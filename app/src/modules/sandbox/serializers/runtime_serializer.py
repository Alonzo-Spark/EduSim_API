"""
runtime_serializer.py
======================
Authoritative Master Simulation Runtime Serializer for EduSim.

This is the primary serialization coordinator. It pulls parameters from the 
authoritative RuntimeStore and delegates to nested serializers (objects, 
observables, relationships, dynamic controls) to assemble the final 
frontend-safe JSON payload contract.

Supports:
- Full Initial Exports (e.g. full scene definitions with environments and static models)
- Lightweight Sync Frame Exports (high-speed delta/update payloads for websockets)
"""

from __future__ import annotations

from typing import Any, Dict
from app.src.modules.sandbox.state.runtime_store import RuntimeStore

# Import nested serializers
from app.src.modules.sandbox.serializers.object_serializer import ObjectSerializer
from app.src.modules.sandbox.serializers.observable_serializer import ObservableSerializer
from app.src.modules.sandbox.serializers.relationship_serializer import RelationshipSerializer
from app.src.modules.sandbox.serializers.control_serializer import ControlSerializer


class RuntimeSerializer:
    """
    Authoritative simulation payload assembler that bridges the backend 
    RuntimeStore database with frontend Matter.js + PixiJS generic clients.
    """

    @classmethod
    def serialize_full(cls, store: RuntimeStore) -> Dict[str, Any]:
        """
        Performs a full initial export of the entire simulation scene.
        Packages static metadata, environment coefficients, constraint bodies, 
        and all initialized dynamic widgets, observables, and equations.
        """
        schema = store.schema
        meta = schema.metadata or {}
        env = schema.environment or {}

        # 1. Standardize Metadata
        tutor_ctx = getattr(meta, "tutor_context", None)
        tutor_ctx_dict = {}
        if tutor_ctx:
            if hasattr(tutor_ctx, "model_dump"):
                tutor_ctx_dict = tutor_ctx.model_dump()
            elif isinstance(tutor_ctx, dict):
                tutor_ctx_dict = dict(tutor_ctx)

        metadata_payload = {
            "id": getattr(meta, "id", "unknown_scenario"),
            "schema_version": getattr(meta, "schema_version", "2.0.0"),
            "created_at": getattr(meta, "created_at", None),
            "updated_at": getattr(meta, "updated_at", None),
            "author": getattr(meta, "author", "system"),
            "is_template": getattr(meta, "is_template", False),
            "tutor_context": tutor_ctx_dict
        }

        # 2. Standardize Environment properties
        gravity = getattr(env, "gravity", None)
        wind = getattr(env, "wind", None)
        medium = getattr(env, "medium", None)

        environment_payload = {
            "gravity": {
                "x": float(getattr(gravity, "x", 0.0)) if gravity else 0.0,
                "y": float(getattr(gravity, "y", 9.81)) if gravity else 9.81,
                "scale": float(getattr(gravity, "scale", 0.001)) if gravity else 0.001
            },
            "wind": {
                "x": float(getattr(wind, "x", 0.0)) if wind else 0.0,
                "y": float(getattr(wind, "y", 0.0)) if wind else 0.0
            },
            "medium": {
                "medium_type": getattr(medium, "medium_type", "vacuum").value if hasattr(getattr(medium, "medium_type", None), "value") else str(getattr(medium, "medium_type", "vacuum")),
                "density": float(getattr(medium, "density", 1.2)) if medium else 1.2,
                "viscosity": float(getattr(medium, "viscosity", 1.8e-5)) if medium else 1.8e-5
            }
        }

        # 3. Standardize Constraints (e.g. spring rod joints)
        constraints_payload = []
        if schema.constraints:
            for cons in schema.constraints:
                constraints_payload.append({
                    "id": cons.id,
                    "constraint_type": cons.constraint_type.value if hasattr(cons.constraint_type, "value") else str(cons.constraint_type),
                    "body_a": cons.body_a,
                    "body_b": cons.body_b,
                    "length": float(cons.length) if cons.length is not None else None,
                    "stiffness": float(cons.stiffness) if cons.stiffness is not None else None,
                    "damping": float(cons.damping) if cons.damping is not None else None,
                    "render": cons.render.model_dump() if hasattr(cons.render, "model_dump") else dict(cons.render or {})
                })

        # 4. Serialize Nested Collections via specific serializers
        # Extract initial static geometry descriptors for objects
        static_objs_meta = schema.model_dump(mode="json").get("objects", [])
        objects_payload = ObjectSerializer.serialize_objects(store.objects, static_objs_meta)
        
        observables_payload = ObservableSerializer.serialize_observables(
            schema.observables,
            store.observables.values
        )

        relationships_payload = RelationshipSerializer.serialize_relationships(
            schema.relationships
        )

        controls_payload = ControlSerializer.serialize_controls(
            schema.controls,
            store
        )

        # 5. Build global 'runtime' state block
        runtime_config = getattr(meta, "runtime_config", None)
        canvas_w = float(getattr(runtime_config, "canvas_width", 1280)) if runtime_config else 1280.0
        canvas_h = float(getattr(runtime_config, "canvas_height", 720)) if runtime_config else 720.0

        runtime_payload = {
            "is_paused": store.simulation.is_paused,
            "current_frame": store.simulation.frame_count,
            "simulated_time_s": round(float(store.simulation.simulation_time), 4),
            "time_delta": round(float(store.simulation.delta_time), 5),
            "substeps": store.simulation.substeps,
            "speed_multiplier": round(float(store.simulation.playback_speed), 2),
            "active_scene_id": store.simulation.active_scene_id,
            "bounds": {
                "min": {"x": 0.0, "y": 0.0},
                "max": {"x": canvas_w, "y": canvas_h}
            },
            "interaction_state": {
                "pointer": {
                    "x": float(store.interaction.pointer.x),
                    "y": float(store.interaction.pointer.y),
                    "is_down": store.interaction.pointer.is_down
                },
                "dragged_body_id": getattr(store.interaction, "dragged_object_id", None),
                "hovered_body_id": getattr(store.interaction, "hovered_object_id", None),
                "selected_body_id": getattr(store.interaction, "selected_object_id", None),
                "interaction_locks": dict(store.interaction.interaction_locks)
            }
        }

        # Assemble Authoritative generic payload contract
        return {
            "metadata": metadata_payload,
            "environment": environment_payload,
            "objects": objects_payload,
            "constraints": constraints_payload,
            "controls": controls_payload,
            "observables": observables_payload,
            "relationships": relationships_payload,
            "runtime": runtime_payload
        }

    @classmethod
    def serialize_sync_frame(cls, store: RuntimeStore) -> Dict[str, Any]:
        """
        Lightweight sync frame export for real-time WebSocket messaging.
        Excludes heavy static environments and formulas, delivering only live 
        physical and educational delta updates.
        """
        # 1. Export live object coordinates and interactive indicators
        objects_sync = []
        for oid, obj in store.objects.items():
            objects_sync.append({
                "id": oid,
                "physics": {
                    "position": ObjectSerializer.serialize_vector(obj.position),
                    "velocity": ObjectSerializer.serialize_vector(obj.velocity),
                    "acceleration": ObjectSerializer.serialize_vector(obj.acceleration),
                    "angle": round(float(obj.angle), 5),
                    "angular_velocity": round(float(obj.angular_velocity), 5)
                },
                "derived": {
                    "kinetic_energy": round(float(obj.get_kinetic_energy()), 5),
                    "momentum": ObjectSerializer.serialize_vector(obj.get_momentum_vector())
                },
                "interaction": {
                    "is_selected": obj.is_selected,
                    "is_hovered": obj.is_hovered,
                    "colliding_with": list(obj.colliding_with)
                }
            })

        # 2. Export live calculated observable values
        observables_sync = []
        for oid, val in store.observables.values.items():
            observables_sync.append({
                "id": oid,
                "value": round(float(val.value), 4)
            })

        # 3. Export global simulation clock coordinates
        runtime_sync = {
            "is_paused": store.simulation.is_paused,
            "current_frame": store.simulation.frame_count,
            "simulated_time_s": round(float(store.simulation.simulation_time), 4),
            "interaction_state": {
                "pointer": {
                    "x": float(store.interaction.pointer.x),
                    "y": float(store.interaction.pointer.y),
                    "is_down": store.interaction.pointer.is_down
                },
                "dragged_body_id": getattr(store.interaction, "dragged_object_id", None),
                "interaction_locks": dict(store.interaction.interaction_locks)
            }
        }

        # Return standardized minimal sync package
        return {
            "objects": objects_sync,
            "observables": observables_sync,
            "runtime": runtime_sync
        }
