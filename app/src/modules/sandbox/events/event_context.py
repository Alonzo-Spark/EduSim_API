"""
event_context.py
================
Standardized Event Context Payload for EduSim.

Defines the core EventContext model. Every emitted signal carries this model, 
providing metadata (timestamps, frames, priority, affected body IDs) to enable 
deterministic timeline replays, analytical logging, and WebSocket syncing.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EventContext(BaseModel):
    """
    Unified context payload dispatched across the EduSim Event Bus.
    """
    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event ID signature for deduplication"
    )
    event_type: str = Field(..., description="Canonical dot-separated event type string")
    
    timestamp: float = Field(
        default_factory=lambda: time.time(),
        description="Epoch timestamp in seconds"
    )
    frame_count: int = Field(default=0, description="Step index of the simulation loop")
    
    source_system: str = Field(default="system", description="E.g., physics, tutor, UI, analytics")
    
    # Context references
    affected_objects: List[str] = Field(default_factory=list, description="Target body IDs involved")
    observable_ids: List[str] = Field(default_factory=list, description="Target observable IDs involved")
    
    # Priority & Routing
    priority: int = Field(default=3, ge=1, le=5, description="Priority rating (1=lowest, 5=highest)")
    
    # Custom extensible dictionary
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom payloads containing forces, mass adjustments, or Socratic cues"
    )

    def serialize(self) -> Dict[str, Any]:
        """Convenience serializer for transmission or logging."""
        return self.model_dump()

    @classmethod
    def create(
        cls,
        event_type: str,
        frame_count: int = 0,
        source_system: str = "system",
        affected_objects: Optional[List[str]] = None,
        observable_ids: Optional[List[str]] = None,
        priority: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventContext:
        """Helper factory to build standard signals quickly."""
        return cls(
            event_type=event_type,
            frame_count=frame_count,
            source_system=source_system,
            affected_objects=affected_objects or [],
            observable_ids=observable_ids or [],
            priority=priority,
            metadata=metadata or {}
        )
