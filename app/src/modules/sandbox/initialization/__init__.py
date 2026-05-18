"""
__init__.py
===========
Public interface for the EduSim Sandbox Initialization Module.

Exposes the initialization orchestrators, factories, pipelines, normalizers, 
and dependency resolvers to the rest of the backend.
"""

from .sandbox_initializer import (
    initialize_sandbox,
    SandboxInitializer,
    initializer
)

from .object_initializer import (
    object_registry,
    initialize_objects
)

from .environment_initializer import (
    initialize_environment
)

from .dependency_resolver import (
    DependencyResolver,
    DependencyResolutionError
)

from .pipeline import (
    InitializationPipeline,
    PipelineStage,
    PipelineContext
)

from .runtime_builder import (
    RuntimeBuilder
)

from .normalizers import (
    normalize_sandbox_payload,
    normalize_number,
    normalize_vector_2d
)

__all__ = [
    "initialize_sandbox",
    "SandboxInitializer",
    "initializer",
    "object_registry",
    "initialize_objects",
    "initialize_environment",
    "DependencyResolver",
    "DependencyResolutionError",
    "InitializationPipeline",
    "PipelineStage",
    "PipelineContext",
    "RuntimeBuilder",
    "normalize_sandbox_payload",
    "normalize_number",
    "normalize_vector_2d"
]
