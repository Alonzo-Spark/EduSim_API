from fastapi import APIRouter, Depends, Header
from typing import Optional
from sqlalchemy.orm import Session

from app.src.config.database import get_db
from app.src.services.persistence_service import record_activity, resolve_user_from_authorization

from app.src.modules.simulation_synthesis.controller import (
    AgentGenerateRequest,
    synthesis_generate_controller,
    synthesis_list_controller,
    synthesis_get_controller,
    synthesis_export_controller,
    synthesis_generate_stream_controller,
)

simulation_router = APIRouter()


@simulation_router.post("/synthesis/generate")
async def generate_synthesized_simulation(
    request: AgentGenerateRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    response = await synthesis_generate_controller(request)
    user = resolve_user_from_authorization(authorization, db)
    if user:
        record_activity(
            db,
            user=user,
            domain="simulation",
            action="synthesis-generate",
            entity_type="simulation",
            entity_id=str(response.get("id") or request.prompt[:120]),
            source="/api/simulations/synthesis/generate",
            metadata={"topic": request.topic},
        )
        try:
            db.commit()
            print("[Database] Activity logs saved in the database: updated")
            if isinstance(response, dict):
                response["message"] = "Simulation progress saved successfully."
        except Exception as e:
            db.rollback()
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to save simulation progress."})
    return response


@simulation_router.get("/synthesis/list")
async def list_synthesized_simulations(limit: int = 30):
    return await synthesis_list_controller(limit=limit)


@simulation_router.get("/synthesis/{simulation_id}")
async def get_synthesized_simulation(simulation_id: str):
    return await synthesis_get_controller(simulation_id=simulation_id)


@simulation_router.get("/synthesis/{simulation_id}/export")
async def export_synthesized_simulation(simulation_id: str):
    return await synthesis_export_controller(simulation_id=simulation_id)


@simulation_router.post("/synthesis/generate-stream")
async def generate_synthesized_simulation_stream(
    request: AgentGenerateRequest,
):
    return await synthesis_generate_stream_controller(request)


# ============================================================================
# SIMPLIFIED AI SIMULATION ENDPOINTS
# ============================================================================

@simulation_router.post("/agent/generate")
async def generate_with_agent(request: AgentGenerateRequest):
    return await synthesis_generate_controller(request)


@simulation_router.post("/agent/generate-stream")
async def generate_with_agent_stream(request: AgentGenerateRequest):
    return await synthesis_generate_stream_controller(request)


@simulation_router.post("/agent/error-report")
async def report_agent_error(simulation_id: str | None = None, payload: dict | None = None):
    return {"success": True, "detail": "Telemetry disabled by design."}


@simulation_router.post("/runtime/report")
async def report_runtime_intelligence(report_data: dict):
    return {"success": True, "detail": "Telemetry disabled by design."}
