"""
interaction_state.py
====================
Runtime interaction, pointer, and UI gesture state for EduSim.

Tracks active pointer coordinate vectors, button presses, dragged objects, 
active widget configurations (e.g., live slider mass selections), and 
dynamic modal panel visual states. 

It exposes locks to temporarily suspend interaction during tutor prompts 
or replay steps.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class PointerCoordinate(BaseModel):
    """Simple 2D screen or canvas coordinate tracker."""
    x: float = 0.0
    y: float = 0.0
    is_down: bool = False


class InteractionState(BaseModel):
    """
    Central database tracking pointer movements, active widget properties, 
    gestures, and visual interaction locks.
    """
    # Active targeting references
    selected_object_id: Optional[str] = Field(default=None, description="Currently selected SandboxObject ID")
    hovered_object_id: Optional[str] = Field(default=None, description="Object ID under active cursor hover")
    dragged_object_id: Optional[str] = Field(default=None, description="Object ID actively dragged by user")
    
    # Editor tool and manipulation states
    active_tool: str = Field(default="select", description="Current sandbox tool: 'select' | 'spawn_circle' | 'spawn_rectangle' | 'delete' | 'connect_spring' etc.")
    manipulation_mode: str = Field(default="translate", description="Current manipulation mode: 'translate' | 'rotate' | 'scale'")

    # Mouse / Touch coordinates
    pointer: PointerCoordinate = Field(default_factory=PointerCoordinate)

    # Active widget values: map of control_id -> current numerical/string value
    widget_values: Dict[str, Any] = Field(default_factory=dict, description="Live value selections on controls")

    # UI / Overlay parameters
    active_panels: Dict[str, bool] = Field(
        default_factory=lambda: {"observables": True, "tutor": True, "graphs": False},
        description="Sidebar display triggers"
    )
    
    # Collaborative and gesture states
    active_gestures: Dict[str, Any] = Field(default_factory=dict, description="Pinch or rotation tracking")
    interaction_locks: Dict[str, bool] = Field(
        default_factory=lambda: {"pointer_drag": False, "controls_edit": False},
        description="Blocks applied by Socratic tutorials"
    )

    # --- Mutators ---

    def select_object(self, obj_id: Optional[str]) -> None:
        """Sets the selected object targeting reference."""
        self.selected_object_id = obj_id

    def set_hover(self, obj_id: Optional[str]) -> None:
        """Sets the hovered object cursor reference."""
        self.hovered_object_id = obj_id

    def start_dragging(self, obj_id: str) -> None:
        """Attaches dragged body reference if dragging is not locked."""
        if not self.interaction_locks.get("pointer_drag", False):
            self.dragged_object_id = obj_id

    def stop_dragging(self) -> None:
        """Detaches dragged body reference."""
        self.dragged_object_id = None

    def update_pointer(self, x: float, y: float, is_down: Optional[bool] = None) -> None:
        """Synchronizes cursor placement and click pressure."""
        self.pointer.x = x
        self.pointer.y = y
        if is_down is not None:
            self.pointer.is_down = is_down

    def update_widget(self, control_id: str, value: Any) -> None:
        """Updates UI control state cache (e.g. mass slider value)."""
        if not self.interaction_locks.get("controls_edit", False):
            self.widget_values[control_id] = value

    def set_lock(self, action_key: str, is_locked: bool) -> None:
        """Applies/releases a visual interaction lock (e.g. during tutor steps)."""
        self.interaction_locks[action_key] = is_locked

    def change_tool(self, tool_name: str) -> None:
        """Changes the active sandbox editing tool."""
        self.active_tool = tool_name

    def change_manipulation_mode(self, mode: str) -> None:
        """Changes the transform mode (translate, rotate, scale)."""
        self.manipulation_mode = mode

    def reset(self) -> None:
        """Clears target focus and locks to pristine states."""
        self.selected_object_id = None
        self.hovered_object_id = None
        self.dragged_object_id = None
        self.active_tool = "select"
        self.manipulation_mode = "translate"
        self.pointer = PointerCoordinate()
        self.widget_values.clear()
        self.interaction_locks = {"pointer_drag": False, "controls_edit": False}
