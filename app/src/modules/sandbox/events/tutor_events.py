"""
tutor_events.py
===============
Socratic Pedagogical Alerting and Tutor Trigger Managers for EduSim.

This module houses the educational trigger architecture. It checks priority 
scores, applies cooldown locks (preventing the AI tutor from spamming repetitive 
hints), manages historical alerts to prevent duplicates, and dispatches:
- TUTOR_HINT_TRIGGERED
- MISCONCEPTION_DETECTED
- QUESTION_GENERATED
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set
from app.src.modules.sandbox.events.event_types import TutorEvents
from app.src.modules.sandbox.events.event_context import EventContext
from app.src.modules.sandbox.events.event_bus import EventBus


class TutorTriggerManager:
    """
    Stateful manager coordinating pedagogical priority scoring, 
    duplicate prevention, and hint throttle cooldowns.
    """
    def __init__(self) -> None:
        # Map of hint_key -> expiration epoch timestamp
        self._cooldowns: Dict[str, float] = {}
        
        # Set of dispatched Socratic hint IDs to prevent duplicates
        self._dispatched: Set[str] = set()

    def can_dispatch(self, key: str, cooldown_seconds: float = 10.0) -> bool:
        """Evaluates whether the Socratic hint has cleared its cooldown window."""
        now = time.time()
        
        # 1. Cooldown Check
        if key in self._cooldowns:
            if now < self._cooldowns[key]:
                return False # On cooldown

        # 2. Update cooldown timestamp
        self._cooldowns[key] = now + cooldown_seconds
        return True

    def emit_tutor_hint(
        self,
        event_bus: EventBus,
        frame_count: int,
        hint_id: str,
        message: str,
        concept: str,
        priority_score: int = 3,
        cooldown_seconds: float = 10.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emits a Socratic tutor hint.
        Respects cooldown locks and priority scoring.
        Returns True if emitted, False if filtered out.
        """
        if not self.can_dispatch(hint_id, cooldown_seconds):
            return False

        self._dispatched.add(hint_id)
        
        meta = metadata or {}
        meta.update({
            "hint_id": hint_id,
            "message": message,
            "concept": concept,
            "priority_score": priority_score
        })

        context = EventContext.create(
            event_type=TutorEvents.TUTOR_HINT_TRIGGERED.value,
            frame_count=frame_count,
            source_system="tutor",
            priority=priority_score,
            metadata=meta
        )
        event_bus.emit(context)
        return True

    def emit_misconception_detected(
        self,
        event_bus: EventBus,
        frame_count: int,
        misconception_id: str,
        concept: str,
        description: str,
        remediation_questions: List[str],
        priority_score: int = 4
    ) -> bool:
        """
        Emits a misconception detected signal to open remediation dialogues.
        """
        if misconception_id in self._dispatched:
            # Only trigger each misconception once per scenario execution to prevent fatigue
            return False

        self._dispatched.add(misconception_id)

        context = EventContext.create(
            event_type=TutorEvents.MISCONCEPTION_DETECTED.value,
            frame_count=frame_count,
            source_system="tutor",
            priority=priority_score,
            metadata={
                "misconception_id": misconception_id,
                "concept": concept,
                "description": description,
                "remediation_questions": remediation_questions
            }
        )
        event_bus.emit(context)
        return True

    def emit_question_generated(
        self,
        event_bus: EventBus,
        frame_count: int,
        question_id: str,
        question_text: str,
        options: List[str],
        correct_answer: str,
        explanation: str
    ) -> None:
        """Dispatches an interactive Socratic multiple-choice question to the UI."""
        context = EventContext.create(
            event_type=TutorEvents.QUESTION_GENERATED.value,
            frame_count=frame_count,
            source_system="tutor",
            priority=3,
            metadata={
                "question_id": question_id,
                "question_text": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": explanation
            }
        )
        event_bus.emit(context)

    def reset(self) -> None:
        """Resets all cooldown clocks and historical logs."""
        self._cooldowns.clear()
        self._dispatched.clear()
class_tutor_trigger_manager = TutorTriggerManager() # Shared default instance
