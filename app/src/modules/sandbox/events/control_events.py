"""
control_events.py
=================
UI Controllers, Drag Streams, and Gesture Event Generators for EduSim.

This module translates user gestures (pointer clicks, drag vectors, widget edits) 
into structured interaction events. It checks interaction locks to enforce 
Socratic tutorial constraints, and implements throttling for high-frequency 
mouse drag coordinates.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from app.src.modules.sandbox.events.event_types import InteractionEvents
from app.src.modules.sandbox.events.event_context import EventContext
from app.src.modules.sandbox.events.event_bus import EventBus
from app.src.modules.sandbox.state.runtime_store import RuntimeStore


# Stateful throttling for high-frequency pointer drags
_last_drag_frame: Dict[str, int] = {}


def emit_control_changed(
    event_bus: EventBus,
    frame_count: int,
    control_id: str,
    value: Any,
    store: Optional[RuntimeStore] = None
) -> None:
    """
    Emits control changed event when UI widgets are adjusted.
    Checks interaction locks to prevent modifications if locked.
    """
    if store and store.interaction.interaction_locks.get("controls_edit", False):
        return # Locked by tutorial prompt

    context = EventContext.create(
        event_type=InteractionEvents.CONTROL_CHANGED.value,
        frame_count=frame_count,
        source_system="ui",
        metadata={
            "control_id": control_id,
            "value": value
        }
    )
    event_bus.emit(context)


def emit_object_selected(
    event_bus: EventBus,
    frame_count: int,
    object_id: Optional[str]
) -> None:
    """Emits selection events when a body gets targeted/highlighted."""
    context = EventContext.create(
        event_type=InteractionEvents.OBJECT_SELECTED.value,
        frame_count=frame_count,
        source_system="ui",
        affected_objects=[object_id] if object_id else [],
        metadata={
            "object_id": object_id
        }
    )
    event_bus.emit(context)


def emit_object_dragged(
    event_bus: EventBus,
    frame_count: int,
    object_id: str,
    x: float,
    y: float,
    store: Optional[RuntimeStore] = None
) -> None:
    """
    Emits object dragging event.
    Throttles dispatching so that subscribers are not overloaded.
    Checks interaction locks.
    """
    if store and store.interaction.interaction_locks.get("pointer_drag", False):
        return # Locked by tutorial

    # Throttling: only emit once every 2 frame ticks to keep high-frequency drag light
    last_frame = _last_drag_frame.get(object_id, -1)
    if frame_count - last_frame < 2:
        return
    _last_drag_frame[object_id] = frame_count

    context = EventContext.create(
        event_type=InteractionEvents.OBJECT_DRAGGED.value,
        frame_count=frame_count,
        source_system="ui",
        affected_objects=[object_id],
        metadata={
            "object_id": object_id,
            "x": float(x),
            "y": float(y)
        }
    )
    event_bus.emit(context)


def emit_pointer_down(
    event_bus: EventBus,
    frame_count: int,
    x: float,
    y: float
) -> None:
    """Emits cursor press down signals."""
    context = EventContext.create(
        event_type=InteractionEvents.POINTER_DOWN.value,
        frame_count=frame_count,
        source_system="ui",
        metadata={
            "x": float(x),
            "y": float(y)
        }
    )
    event_bus.emit(context)


def emit_pointer_up(
    event_bus: EventBus,
    frame_count: int,
    x: float,
    y: float
) -> None:
    """Emits cursor release up signals."""
    context = EventContext.create(
        event_type=InteractionEvents.POINTER_UP.value,
        frame_count=frame_count,
        source_system="ui",
        metadata={
            "x": float(x),
            "y": float(y)
        }
    )
    event_bus.emit(context)
