from fastapi import HTTPException
from pydantic import BaseModel, Field

from .services import run_action_reaction_simulation


class SimulationRequest(BaseModel):

    mass1: float = Field(..., gt=0)
    mass2: float = Field(..., gt=0)
    force: float = Field(..., gt=0)


async def action_reaction_controller(
    request: SimulationRequest
):

    try:

        result = run_action_reaction_simulation(
            mass1=request.mass1,
            mass2=request.mass2,
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