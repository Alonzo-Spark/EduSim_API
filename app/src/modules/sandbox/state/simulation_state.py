"""
simulation_state.py
===================
Global simulation lifecycle state for EduSim.

Tracks whether the simulation is running, paused, current simulation frames, 
delta timesteps, substeps, playback speeds, and target active scenes. 

It provides simple, standardized mutators for pacing, frame stepping, 
and speed throttling (e.g. slow motion).
"""

from __future__ import annotations

from typing import Dict, Any
from pydantic import BaseModel, Field


class SimulationState(BaseModel):
    """
    State container for the global execution loop, stepping rate, 
    and frame metrics of the sandbox.
    """
    is_running: bool = Field(default=False, description="Whether simulation clock is ticking")
    is_paused: bool = Field(default=True, description="Authoritative pause flag")
    
    simulation_time: float = Field(default=0.0, description="Accumulated physical simulation time in seconds")
    frame_count: int = Field(default=0, description="Total physical engine steps executed")
    tick_rate: int = Field(default=60, description="Target engine frames per second")
    delta_time: float = Field(default=1.0/60.0, description="Timestep interval per tick in seconds")
    
    playback_speed: float = Field(default=1.0, description="Throttling multiplier (e.g. 0.5 for half speed slow-mo)")
    substeps: int = Field(default=1, ge=1, le=10, description="Matter.js execution substeps")
    
    active_scene_id: str = Field(default="default_scene", description="Identifier of the active scenario")
    runtime_flags: Dict[str, Any] = Field(default_factory=dict, description="Open runtime configuration toggles")

    def pause(self) -> None:
        """Halts the state clock."""
        self.is_running = False
        self.is_paused = True

    def resume(self) -> None:
        """Resumes simulation progression."""
        self.is_running = True
        self.is_paused = False

    def step(self) -> None:
        """
        Advances the simulation by a single step.
        Called during manual stepping when paused or every execution frame tick.
        """
        effective_dt = self.delta_time * self.playback_speed
        self.simulation_time += effective_dt
        self.frame_count += 1

    def set_speed(self, multiplier: float) -> None:
        """Sets slow-mo or fast-forward speed multiplier."""
        self.playback_speed = max(0.0, multiplier)

    def reset(self) -> None:
        """Resets the execution metrics to pristine initial states."""
        self.is_running = False
        self.is_paused = True
        self.simulation_time = 0.0
        self.frame_count = 0
