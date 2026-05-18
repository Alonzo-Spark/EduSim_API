"""
snapshot_serializer.py
======================
Simulation Checkpoint & Save State Serializer for EduSim.

Converts SimulationSnapshot model records (deep serializable physical states,
cached variables, clock speeds) into clean importable/exportable JSON contracts
supporting timeline history scrubbers and cloud save files.
"""

from __future__ import annotations

from typing import Any, Dict, List
from app.src.modules.sandbox.state.snapshots import SimulationSnapshot


class SnapshotSerializer:
    """
    Serializes and deserializes timeline snapshots to enable full sandbox 
    checkpoint import/export workflows.
    """

    @classmethod
    def serialize_snapshot(cls, snapshot: SimulationSnapshot) -> Dict[str, Any]:
        """
        Exports a SimulationSnapshot model record into a serializable, 
        generic JSON payload contract.
        """
        return {
            "simulation_state": dict(snapshot.simulation_state),
            "object_states": {
                oid: dict(obj) for oid, obj in snapshot.object_states.items()
            },
            "interaction_state": dict(snapshot.interaction_state),
            "observable_values": {
                oid: float(val) for oid, val in snapshot.observable_values.items()
            }
        }

    @classmethod
    def deserialize_snapshot(cls, payload: Dict[str, Any]) -> SimulationSnapshot:
        """
        Imports and validates a raw dictionary payload, rebuilding a structured 
        SimulationSnapshot model capable of restoring the RuntimeStore.
        """
        # Validate required blocks defensively
        sim_state = payload.get("simulation_state") or {}
        obj_states = payload.get("object_states") or {}
        inter_state = payload.get("interaction_state") or {}
        obs_vals = payload.get("observable_values") or {}

        return SimulationSnapshot(
            simulation_state=sim_state,
            object_states=obj_states,
            interaction_state=inter_state,
            observable_values={k: float(v) for k, v in obs_vals.items()}
        )

    @classmethod
    def serialize_timeline_checkpoints(
        cls,
        history: List[SimulationSnapshot]
    ) -> List[Dict[str, Any]]:
        """Serializes lists of checkpoints into a comprehensive timeline sequence."""
        return [cls.serialize_snapshot(snap) for snap in history]
