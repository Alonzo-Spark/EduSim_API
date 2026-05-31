"""
controller.py
=============
Lightweight FastAPI Controller/Router Layer for EduSim Sandbox Orchestration.

Exposes REST boundaries to manage simulation generation, state synchronization,
dynamic parameter manipulation, and checkpoint/snapshot workflows.

Maintains structural separation by delegating all execution logic to the service layer.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Path, Body, status, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.src.config.database import get_db
from app.src.services.persistence_service import record_activity, record_sandbox_event, resolve_user_from_authorization, save_sandbox_state
from app.src.modules.sandbox import service

# Initialize APIRouter
sandbox_router = APIRouter(prefix="/sandbox", tags=["Sandbox"])


# ============================================================================
# Pydantic Request Models
# ============================================================================

class GenerateRequest(BaseModel):
    """Payload to synthesize a custom scenario from a natural language prompt."""
    prompt: str = Field(..., min_length=4, description="Physics prompt description")
    topic: Optional[str] = Field(None, description="Optional textbook subject topic")


class LoadRequest(BaseModel):
    """Payload to retrieve an active simulation session."""
    simulation_id: str = Field(..., description="UUID of the active simulation session")


class ResetRequest(BaseModel):
    """Payload to reset a simulation back to its initial Frame 0 config."""
    simulation_id: str = Field(..., description="UUID of the active simulation session")


class ControlUpdateRequest(BaseModel):
    """Payload to apply slider or coordinate changes to active objects."""
    simulation_id: str = Field(..., description="UUID of the active simulation session")
    control_id: str = Field(..., description="Widget ID mapped in sandbox controls")
    value: Any = Field(..., description="Target value to apply (mass, gravity, etc)")


class SnapshotRestoreRequest(BaseModel):
    """Payload containing complete snapshot parameters to restore sandbox state."""
    snapshot: Dict[str, Any] = Field(..., description="Lightweight snapshot record")


# ============================================================================
# API Routes
# ============================================================================

@sandbox_router.post(
    "/generate",
    status_code=status.HTTP_201_CREATED,
    summary="Synthesize and initialize a new physical simulation"
)
async def generate_sandbox_simulation(
    request: GenerateRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    RAG textbook context is queried, dynamic scenarios are synthesized by the LLM,
    objects are normalized, and an active RuntimeStore session is registered.
    """
    try:
        data = service.generate_simulation(prompt=request.prompt, topic=request.topic)
        user = resolve_user_from_authorization(authorization, db)
        if user:
            save_sandbox_state(
                db,
                user=user,
                payload={
                    "simulation_id": data.get("simulation_id") or data.get("id") or request.prompt[:120],
                    "prompt": request.prompt,
                    "topic": request.topic,
                    "title": data.get("title"),
                    "description": data.get("description"),
                    "dsl_json": data,
                    "runtime_json": data.get("runtime"),
                    "snapshot_json": data.get("snapshot"),
                    "ui_state_json": data.get("ui_state"),
                },
            )
            record_activity(
                db,
                user=user,
                domain="sandbox",
                action="generate",
                entity_type="simulation",
                entity_id=str(data.get("simulation_id") or data.get("id") or request.prompt[:120]),
                source="/api/sandbox/generate",
                metadata={"topic": request.topic},
            )
            db.commit()
        return {
            "success": True,
            **data
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed during synthesis: {val_err}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation generation failed: {exc}"
        )


@sandbox_router.post(
    "/load",
    summary="Fetch current serialized parameters of an active session"
)
async def load_sandbox_simulation(
    request: LoadRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Returns the initial state configuration or current coordinates of the active ID.
    """
    try:
        data = service.load_simulation(simulation_id=request.simulation_id)
        user = resolve_user_from_authorization(authorization, db)
        if user:
            record_activity(
                db,
                user=user,
                domain="sandbox",
                action="load",
                entity_type="simulation",
                entity_id=request.simulation_id,
                source="/api/sandbox/load",
            )
            db.commit()
        return {
            "success": True,
            **data
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation retrieval failed: {exc}"
        )


@sandbox_router.post(
    "/reset",
    summary="Reset active simulation session to its start frame"
)
async def reset_sandbox_simulation(
    request: ResetRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Restores positions, velocities, clocks, and observables back to initial values.
    """
    try:
        data = service.reset_simulation(simulation_id=request.simulation_id)
        user = resolve_user_from_authorization(authorization, db)
        if user:
            record_activity(
                db,
                user=user,
                domain="sandbox",
                action="reset",
                entity_type="simulation",
                entity_id=request.simulation_id,
                source="/api/sandbox/reset",
            )
            db.commit()
        return {
            "success": True,
            **data
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation reset failed: {exc}"
        )


@sandbox_router.post(
    "/control/update",
    summary="Apply parameter updates to dynamic elements"
)
async def update_sandbox_control(
    request: ControlUpdateRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Applies widget value mutations and triggers reactive observable re-evaluation.
    """
    try:
        data = service.update_control(
            simulation_id=request.simulation_id,
            control_id=request.control_id,
            value=request.value
        )
        user = resolve_user_from_authorization(authorization, db)
        if user:
            record_sandbox_event(
                db,
                user=user,
                payload={
                    "simulation_id": request.simulation_id,
                    "event_type": "control-update",
                    "payload_json": {"control_id": request.control_id, "value": request.value},
                },
            )
            db.commit()
        return {
            "success": True,
            **data
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parameter modification failed: {exc}"
        )


@sandbox_router.get(
    "/runtime/{id}",
    summary="Get dynamic tick sync parameters"
)
async def get_sandbox_runtime(
    simulation_id: str = Path(..., alias="id", description="Active simulation UUID"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Fetches real-time ticks, speed clocks, pointer positions, and canvas bounds.
    """
    try:
        data = service.get_runtime_payload(simulation_id=simulation_id)
        user = resolve_user_from_authorization(authorization, db)
        if user:
            record_activity(
                db,
                user=user,
                domain="sandbox",
                action="runtime",
                entity_type="simulation",
                entity_id=simulation_id,
                source="/api/sandbox/runtime",
            )
            db.commit()
        return {
            "success": True,
            **data
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch runtime tick: {exc}"
        )


@sandbox_router.get(
    "/snapshot/{id}",
    summary="Download deep serializable state checkpoint"
)
async def get_sandbox_snapshot(
    simulation_id: str = Path(..., alias="id", description="Active simulation UUID"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Captures complete positions, coordinates, forces, and observables for undo/replays.
    """
    try:
        data = service.get_snapshot(simulation_id=simulation_id)
        user = resolve_user_from_authorization(authorization, db)
        if user:
            record_activity(
                db,
                user=user,
                domain="sandbox",
                action="snapshot",
                entity_type="simulation",
                entity_id=simulation_id,
                source="/api/sandbox/snapshot",
            )
            db.commit()
        return {
            "success": True,
            **data
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to capture snapshot: {exc}"
        )


@sandbox_router.post(
    "/snapshot/{id}/restore",
    summary="Restore state coordinates from checkpoint upload"
)
async def restore_sandbox_snapshot(
    simulation_id: str = Path(..., alias="id", description="Active simulation UUID"),
    request: SnapshotRestoreRequest = Body(...),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Restores velocities, coordinates, and calculations from deep snapshot dictionary.
    """
    try:
        data = service.restore_snapshot(
            simulation_id=simulation_id,
            snapshot_data=request.snapshot
        )
        user = resolve_user_from_authorization(authorization, db)
        if user:
            record_activity(
                db,
                user=user,
                domain="sandbox",
                action="restore-snapshot",
                entity_type="simulation",
                entity_id=simulation_id,
                source="/api/sandbox/snapshot/restore",
                metadata={"snapshot": request.snapshot},
            )
            db.commit()
        return {
            "success": True,
            **data
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore state snapshot: {exc}"
        )
