"""
event_serializer.py
===================
Signal Event Serializer for EduSim.

Converts EventContext signals (interactions, collisions, Socratic tutor cues) 
into compact websocket-safe or verbose analytical JSON payloads.
"""

from __future__ import annotations

from typing import Any, Dict, List
from app.src.modules.sandbox.events.event_context import EventContext


class EventSerializer:
    """
    Serializes event context payloads, removing internal system flags 
    (such as bubble cancellation keys) to deliver optimized transport payloads.
    """

    @classmethod
    def serialize_event(
        cls,
        context: EventContext,
        compact: bool = False
    ) -> Dict[str, Any]:
        """
        Serializes an EventContext signal.
        If compact=True, trims metadata and returns a high-density, low-latency 
        websocket payload.
        """
        # 1. Base copy of metadata
        meta = dict(context.metadata)
        
        # Invalidate internal system-only keys (e.g. propagation locks)
        if "_cancelled" in meta:
            del meta["_cancelled"]

        # 2. Return compact format (low packet size for high-frequency ticks)
        if compact:
            return {
                "id": context.event_id[:8], # high density short ID
                "type": context.event_type,
                "frame": context.frame_count,
                "objs": context.affected_objects,
                "meta": {k: v for k, v in meta.items() if k in ["value", "impulse", "normal", "control_id"]}
            }

        # 3. Complete analytical/replay-safe verbose payload
        return {
            "event_id": context.event_id,
            "event_type": context.event_type,
            "timestamp": round(float(context.timestamp), 4),
            "frame_count": context.frame_count,
            "source_system": context.source_system,
            "affected_objects": list(context.affected_objects),
            "observable_ids": list(context.observable_ids),
            "priority": context.priority,
            "metadata": meta
        }

    @classmethod
    def serialize_events(
        cls,
        events: List[EventContext],
        compact: bool = False
    ) -> List[Dict[str, Any]]:
        """Serializes lists of event signals."""
        return [cls.serialize_event(e, compact) for e in events]
