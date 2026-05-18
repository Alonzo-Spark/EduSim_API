"""
__init__.py
===========
Public interface for the EduSim Sandbox State Module.

Exposes the centralized RuntimeStore, StateManager, mutations, selectors, 
and timeline snapshot/replay engines to other backend domains (e.g. tutor engines, 
synthesis pipelines, and API sockets).
"""

from .simulation_state import (
    SimulationState
)

from .object_state import (
    StateVector2D,
    ObjectRuntimeState
)

from .observable_state import (
    ObservableRuntimeValue,
    ObservableStateManager
)

from .interaction_state import (
    PointerCoordinate,
    InteractionState
)

from .runtime_store import (
    RuntimeStore
)

from .state_manager import (
    StateManager
)

from .snapshots import (
    SimulationSnapshot,
    take_snapshot,
    restore_snapshot,
    SnapshotTimeline
)

from .mutations import (
    pause_simulation,
    resume_simulation,
    update_mass,
    apply_force,
    update_velocity,
    set_position,
    select_object_mutation,
    update_widget_mutation
)

from .selectors import (
    get_object_state,
    get_object_velocity,
    get_selected_object,
    get_observable_value,
    get_total_energy,
    get_active_relationships,
    get_runtime_bounds
)

__all__ = [
    "SimulationState",
    "StateVector2D",
    "ObjectRuntimeState",
    "ObservableRuntimeValue",
    "ObservableStateManager",
    "InteractionState",
    "PointerCoordinate",
    "RuntimeStore",
    "StateManager",
    "SimulationSnapshot",
    "take_snapshot",
    "restore_snapshot",
    "SnapshotTimeline",
    
    # Mutations
    "pause_simulation",
    "resume_simulation",
    "update_mass",
    "apply_force",
    "update_velocity",
    "set_position",
    "select_object_mutation",
    "update_widget_mutation",
    
    # Selectors
    "get_object_state",
    "get_object_velocity",
    "get_selected_object",
    "get_observable_value",
    "get_total_energy",
    "get_active_relationships",
    "get_runtime_bounds"
]
