from fastapi import HTTPException
from pydantic import BaseModel, Field

from .services import (
    run_wave_visualization_simulation
)


class WaveVisualizationRequest(
    BaseModel
):

    amplitude: float = Field(
        ...,
        gt=0
    )

    frequency: float = Field(
        ...,
        gt=0
    )


async def wave_visualization_controller(
    request: WaveVisualizationRequest
):

    try:

        result = (
            run_wave_visualization_simulation(
                request.amplitude,
                request.frequency
            )
        )

        return {

            "success": True,

            "data": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )