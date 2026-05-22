from fastapi import APIRouter

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
):
    return await synthesis_generate_controller(request)


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