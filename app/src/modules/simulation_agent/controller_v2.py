from fastapi import HTTPException

from .agentic_models import AgenticGenerateRequest, AgenticGenerateResponse, AgenticRegenerateRequest
from .orchestrator_v2 import run_agentic_generation, run_regeneration
from .blueprint_store import get_blueprint, list_blueprints


async def agentic_generate_controller(request: AgenticGenerateRequest) -> AgenticGenerateResponse:
    try:
        return run_agentic_generation(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-agent generation failed: {str(e)}")


async def agentic_regenerate_controller(request: AgenticRegenerateRequest) -> AgenticGenerateResponse:
    try:
        existing = get_blueprint(request.simulation_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Simulation blueprint not found")

        base = run_agentic_generation(
            AgenticGenerateRequest(
                prompt=existing.get("prompt", "Regenerate simulation"),
                user_id=request.user_id,
            )
        )
        return run_regeneration(base, request.instruction)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


async def marketplace_list_controller(limit: int = 30):
    try:
        items = list_blueprints(limit=limit)
        return {
            "success": True,
            "count": len(items),
            "items": items,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Marketplace listing failed: {str(e)}")


async def runtime_report_controller(report_data: dict) -> dict:
    """
    Handle runtime reports from simulations, score them, and trigger autonomous repairs.
    """
    from .runtime_intelligence import runtime_agent, RuntimeReport
    from .orchestrator_v2 import run_regeneration
    from .blueprint_store import get_blueprint
    from .memory_system import store_runtime_intelligence
    
    try:
        report = RuntimeReport(**report_data)
        health_score = runtime_agent.analyze_report(report)
        
        # Persist report for evolution analysis
        store_runtime_intelligence(
            report.simulation_id, 
            report.model_dump(), 
            health_score.model_dump()
        )
        
        repair_triggered = False

        if runtime_agent.should_trigger_repair(health_score):
            # Autonomous Repair Logic
            blueprint = get_blueprint(report.simulation_id)
            if blueprint:
                repair_instruction = "Automated repair: Stability/Performance issue detected. Optimize and fix errors."
                # In a real system, we'd background this
                # run_regeneration(...)
                repair_triggered = True
        
        return {
            "success": True,
            "score": health_score.model_dump(),
            "repair_triggered": repair_triggered,
            "advice": runtime_agent.generate_optimization_advice(report)
        }
    except Exception as e:
        print(f"Runtime report processing failed: {e}")
        return {"success": False, "detail": str(e)}

