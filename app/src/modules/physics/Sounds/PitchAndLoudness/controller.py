from fastapi import HTTPException
from pydantic import BaseModel, Field

from .services import (
    run_pitch_and_loudness_simulation
)


class PitchAndLoudnessRequest(
    BaseModel
):

    frequency: float = Field(
        ...,
        gt=0
    )

    amplitude: float = Field(
        ...,
        gt=0
    )


async def pitch_and_loudness_controller(
    request: PitchAndLoudnessRequest
):

    try:

        result = (
            run_pitch_and_loudness_simulation(
                request.frequency,
                request.amplitude
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