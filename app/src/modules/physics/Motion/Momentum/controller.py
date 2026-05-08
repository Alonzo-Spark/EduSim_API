from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .services import run_momentum_simulation

class SimulationRequest(BaseModel):
    mass: float = Field(..., gt=0)
    force: float = Field(...)

async def momentum_controller(
    request: SimulationRequest
):
    try:
        result = run_momentum_simulation(
            mass=request.mass,
            force=request.force
        )

        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
