"""
runtime_events.py
==================
Simulation Lifecycle Event Generators for EduSim.

This module maps SimulationState clock actions into standardized event contexts.
It generates signals when simulations pause, resume, reset, or execute tick 
stepping frames, packaging them with execution diagnostics.
"""

from __future__ import annotations

from app.src.modules.sandbox.events.event_types import RuntimeEvents
from app.src.modules.sandbox.events.event_context import EventContext
from app.src.modules.sandbox.events.event_bus import EventBus
from app.src.modules.sandbox.state.runtime_store import RuntimeStore


def emit_simulation_started(event_bus: EventBus, store: RuntimeStore) -> None:
    """Emits a simulation started lifecycle signal."""
    context = EventContext.create(
        event_type=RuntimeEvents.SIMULATION_STARTED.value,
        frame_count=store.simulation.frame_count,
        source_system="runtime",
        metadata={
            "simulation_time": store.simulation.simulation_time,
            "playback_speed": store.simulation.playback_speed,
            "tick_rate": store.simulation.tick_rate
        }
    )
    event_bus.emit(context)


def emit_simulation_paused(event_bus: EventBus, store: RuntimeStore) -> None:
    """Emits a simulation paused lifecycle signal."""
    context = EventContext.create(
        event_type=RuntimeEvents.SIMULATION_PAUSED.value,
        frame_count=store.simulation.frame_count,
        source_system="runtime",
        metadata={
            "simulation_time": store.simulation.simulation_time
        }
    )
    event_bus.emit(context)


def emit_simulation_resumed(event_bus: EventBus, store: RuntimeStore) -> None:
    """Emits a simulation resumed lifecycle signal."""
    context = EventContext.create(
        event_type=RuntimeEvents.SIMULATION_RESUMED.value,
        frame_count=store.simulation.frame_count,
        source_system="runtime",
        metadata={
            "simulation_time": store.simulation.simulation_time,
            "playback_speed": store.simulation.playback_speed
        }
    )
    event_bus.emit(context)


def emit_simulation_reset(event_bus: EventBus, store: RuntimeStore) -> None:
    """Emits a simulation reset lifecycle signal."""
    context = EventContext.create(
        event_type=RuntimeEvents.SIMULATION_RESET.value,
        frame_count=0,
        source_system="runtime",
        metadata={
            "simulation_time": 0.0
        }
    )
    event_bus.emit(context)


def emit_frame_advanced(event_bus: EventBus, store: RuntimeStore) -> None:
    """
    Emits a high-frequency frame advanced step signal.
    Appends diagnostic payloads (active velocities, active mechanical energies).
    """
    from app.src.modules.sandbox.state.selectors import get_total_energy
    
    context = EventContext.create(
        event_type=RuntimeEvents.FRAME_ADVANCED.value,
        frame_count=store.simulation.frame_count,
        source_system="physics",
        metadata={
            "simulation_time": store.simulation.simulation_time,
            "delta_time": store.simulation.delta_time,
            "total_energy": get_total_energy(store)
        }
    )
    event_bus.emit(context)
