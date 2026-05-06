from fastapi import HTTPException
from pydantic import BaseModel, Field

from .services import run_projectile_simulation


class SimulationRequest(BaseModel):

    velocity: float = Field(..., gt=0)

    angle: float = Field(
        ...,
        ge=0,
        le=90
    )

    gravity: float = Field(
        default=9.8,
        gt=0
    )


async def projectile_controller(
    request: SimulationRequest
):

    try:

        result = run_projectile_simulation(
            velocity=request.velocity,
            angle=request.angle,
            gravity=request.gravity
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