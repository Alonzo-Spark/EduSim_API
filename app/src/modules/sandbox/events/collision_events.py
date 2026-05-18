"""
collision_events.py
===================
Collision Processing and Deduplication Engine for EduSim.

This module intercepts physics contact alerts, deduplicates them (ensuring 
(A, B) and (B, A) are treated as a single unique collision), tracks active 
collision states, and dispatches:
- COLLISION_START (first contact frame)
- COLLISION_PERSIST (continuous contact frames)
- COLLISION_END (contact separation frame)
"""

from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple
from app.src.modules.sandbox.events.event_types import CollisionEvents
from app.src.modules.sandbox.events.event_context import EventContext
from app.src.modules.sandbox.events.event_bus import EventBus


class CollisionTracker:
    """
    Stateful manager tracking active physics contacts to generate 
    enter, stay, and exit signals cleanly.
    """
    def __init__(self) -> None:
        # Set of sorted pairs: Tuple[str, str] representing active contacts
        self._active_contacts: Set[Tuple[str, str]] = set()

    def process_collisions(
        self,
        event_bus: EventBus,
        frame_count: int,
        current_collisions: List[Dict[str, Any]]
    ) -> None:
        """
        Processes a list of collision dicts from Matter.js sync payload.
        Resolves sorting order, detects transitions, and dispatches signals.
        """
        # 1. Standardize and deduplicate incoming frame contacts
        incoming_contacts: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for col in current_collisions:
            body_a = col.get("body_a")
            body_b = col.get("body_b")
            if not body_a or not body_b:
                continue

            # Standardize ordering alphabetically to prevent bidirectional duplication
            pair = (min(body_a, body_b), max(body_a, body_b))
            incoming_contacts[pair] = col

        incoming_pairs = set(incoming_contacts.keys())

        # 2. Detect COLLISION_START (new contacts)
        started_pairs = incoming_pairs - self._active_contacts

        # 3. Detect COLLISION_PERSIST (continuous contacts)
        persisted_pairs = (incoming_pairs & self._active_contacts) - started_pairs

        # Now execute COLLISION_START dispatches and add to active contacts
        for pair in started_pairs:
            col_data = incoming_contacts[pair]
            self._active_contacts.add(pair)
            
            context = EventContext.create(
                event_type=CollisionEvents.COLLISION_START.value,
                frame_count=frame_count,
                source_system="physics",
                affected_objects=list(pair),
                metadata={
                    "normal": col_data.get("normal", {"x": 0.0, "y": 0.0}),
                    "penetration": col_data.get("penetration", 0.0),
                    "impulse": col_data.get("impulse", 0.0)
                }
            )
            event_bus.emit(context)

        # Execute COLLISION_PERSIST dispatches
        for pair in persisted_pairs:
            col_data = incoming_contacts[pair]
            
            context = EventContext.create(
                event_type=CollisionEvents.COLLISION_PERSIST.value,
                frame_count=frame_count,
                source_system="physics",
                affected_objects=list(pair),
                metadata={
                    "normal": col_data.get("normal", {"x": 0.0, "y": 0.0}),
                    "penetration": col_data.get("penetration", 0.0),
                    "impulse": col_data.get("impulse", 0.0)
                }
            )
            event_bus.emit(context)

        # 4. Detect COLLISION_END (contact separations)
        ended_pairs = self._active_contacts - incoming_pairs
        for pair in ended_pairs:
            self._active_contacts.remove(pair)
            
            context = EventContext.create(
                event_type=CollisionEvents.COLLISION_END.value,
                frame_count=frame_count,
                source_system="physics",
                affected_objects=list(pair),
                metadata={}
            )
            event_bus.emit(context)

    def reset(self) -> None:
        """Clears all tracked active contacts."""
        self._active_contacts.clear()
