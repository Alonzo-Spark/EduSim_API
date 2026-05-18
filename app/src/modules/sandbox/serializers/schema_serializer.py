"""
schema_serializer.py
====================
Introspection and Version-Tracking Schema Serializer for EduSim.

Provides utility functions to dump baseline sandbox schemas and inspect versioning 
tokens, enabling metadata catalog listings.
"""

from __future__ import annotations

from typing import Any, Dict
from pydantic import BaseModel
from app.src.modules.sandbox.schemas.sandbox_schema import SandboxSchema


class SchemaSerializer:
    """
    Serializes and introspects high-level Sandbox schemas, extracting 
    version descriptors, author details, and physical composition summaries.
    """

    @classmethod
    def serialize_schema(cls, schema: BaseModel) -> Dict[str, Any]:
        """Generic validator dump converting Pydantic models into native dicts."""
        if hasattr(schema, "model_dump"):
            return schema.model_dump(mode="json")
        return {}

    @classmethod
    def export_schema_metadata(cls, sandbox: SandboxSchema) -> Dict[str, Any]:
        """
        Extracts high-level composition metadata from a compiled SandboxSchema 
        for dashboard catalog lists.
        """
        meta = sandbox.metadata or {}
        env = sandbox.environment or {}
        
        return {
            "id": getattr(meta, "id", "unknown_scenario"),
            "schema_version": getattr(meta, "schema_version", "2.0.0"),
            "author": getattr(meta, "author", "system"),
            "is_template": getattr(meta, "is_template", False),
            "created_at": getattr(meta, "created_at", None),
            "summary": {
                "objects_count": len(sandbox.objects) if sandbox.objects else 0,
                "constraints_count": len(sandbox.constraints) if sandbox.constraints else 0,
                "observables_count": len(sandbox.observables) if sandbox.observables else 0,
                "relationships_count": len(sandbox.relationships) if sandbox.relationships else 0,
                "controls_count": len(sandbox.controls) if sandbox.controls else 0
            },
            "environment_settings": {
                "gravity": {
                    "y": getattr(env.gravity, "y", 9.81) if hasattr(env, "gravity") else 9.81
                },
                "wind": {
                    "x": getattr(env.wind, "x", 0.0) if hasattr(env, "wind") else 0.0
                }
            }
        }
