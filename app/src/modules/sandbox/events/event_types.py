"""
event_types.py
==============
Canonical Event Types and Namespaces for EduSim.

Defines enums and structured namespaces for runtime, collision, observable, 
interaction, tutor, and timeline replay event signals. 

Utilizes standard string-based enums to facilitate seamless cross-domain 
serialization (e.g., via websockets).
"""

from enum import Enum


class EventNamespace(str, Enum):
    """Event namespaces used for filtering and wildcard subscriptions."""
    RUNTIME = "runtime"
    COLLISION = "collision"
    OBSERVABLE = "observable"
    INTERACTION = "interaction"
    TUTOR = "tutor"
    SYSTEM = "system"


class RuntimeEvents(str, Enum):
    """Lifecycle events emitted during sandbox simulation stepping."""
    SIMULATION_STARTED = "runtime.simulation_started"
    SIMULATION_PAUSED = "runtime.simulation_paused"
    SIMULATION_RESUMED = "runtime.simulation_resumed"
    SIMULATION_RESET = "runtime.simulation_reset"
    FRAME_ADVANCED = "runtime.frame_advanced"


class CollisionEvents(str, Enum):
    """Signals generated during physics contacts."""
    COLLISION_START = "collision.start"
    COLLISION_PERSIST = "collision.persist"
    COLLISION_END = "collision.end"


class ObservableEvents(str, Enum):
    """Signals reflecting changes in calculated educational variables."""
    OBSERVABLE_UPDATED = "observable.updated"
    THRESHOLD_EXCEEDED = "observable.threshold_exceeded"
    FORMULA_RECOMPUTED = "observable.formula_recomputed"


class InteractionEvents(str, Enum):
    """Signals indicating pointer coordinates or controller input updates."""
    OBJECT_SELECTED = "interaction.object_selected"
    OBJECT_DRAGGED = "interaction.object_dragged"
    CONTROL_CHANGED = "interaction.control_changed"
    POINTER_DOWN = "interaction.pointer_down"
    POINTER_UP = "interaction.pointer_up"


class TutorEvents(str, Enum):
    """Tutoring state alerts, hints, and Socratic dialogues."""
    TUTOR_HINT_TRIGGERED = "tutor.hint_triggered"
    MISCONCEPTION_DETECTED = "tutor.misconception_detected"
    QUESTION_GENERATED = "tutor.question_generated"


class SystemEvents(str, Enum):
    """General checkpoints, undos, redos, and analytics triggers."""
    SNAPSHOT_RECORDED = "system.snapshot_recorded"
    SNAPSHOT_RESTORED = "system.snapshot_restored"
    REPLAY_STARTED = "system.replay_started"
