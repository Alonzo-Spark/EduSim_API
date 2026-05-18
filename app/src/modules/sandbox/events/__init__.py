"""
__init__.py
===========
Public interface for the EduSim Sandbox Event Module.

Exposes the centralized EventBus, event context metadata formats, canonical enums, 
stateful triggers, and standard plug-and-play subscribers to other backend systems.
"""

from .event_types import (
    EventNamespace,
    RuntimeEvents,
    CollisionEvents,
    ObservableEvents,
    InteractionEvents,
    TutorEvents,
    SystemEvents
)

from .event_context import (
    EventContext
)

from .event_bus import (
    SubscriptionListener,
    EventBus
)

from .runtime_events import (
    emit_simulation_started,
    emit_simulation_paused,
    emit_simulation_resumed,
    emit_simulation_reset,
    emit_frame_advanced
)

from .collision_events import (
    CollisionTracker
)

from .observable_events import (
    emit_observable_updated,
    emit_threshold_exceeded,
    emit_formula_recomputed
)

from .control_events import (
    emit_control_changed,
    emit_object_selected,
    emit_object_dragged,
    emit_pointer_down,
    emit_pointer_up
)

from .tutor_events import (
    TutorTriggerManager,
    class_tutor_trigger_manager
)

from .subscribers import (
    LoggingSubscriber,
    ReplayRecorderSubscriber,
    AnalyticsSubscriber,
    WebSocketSubscriber,
    TutorSubscriber
)

__all__ = [
    # Event Types & Namespaces
    "EventNamespace",
    "RuntimeEvents",
    "CollisionEvents",
    "ObservableEvents",
    "InteractionEvents",
    "TutorEvents",
    "SystemEvents",
    
    # Event Context
    "EventContext",
    
    # Event Bus
    "SubscriptionListener",
    "EventBus",
    
    # Emitters
    "emit_simulation_started",
    "emit_simulation_paused",
    "emit_simulation_resumed",
    "emit_simulation_reset",
    "emit_frame_advanced",
    "emit_observable_updated",
    "emit_threshold_exceeded",
    "emit_formula_recomputed",
    "emit_control_changed",
    "emit_object_selected",
    "emit_object_dragged",
    "emit_pointer_down",
    "emit_pointer_up",
    
    # Stateful Managers
    "CollisionTracker",
    "TutorTriggerManager",
    "class_tutor_trigger_manager",
    
    # Standard Subscribers
    "LoggingSubscriber",
    "ReplayRecorderSubscriber",
    "AnalyticsSubscriber",
    "WebSocketSubscriber",
    "TutorSubscriber"
]
