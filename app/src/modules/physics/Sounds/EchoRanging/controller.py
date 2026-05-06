from fastapi import HTTPException
from pydantic import BaseModel, Field

from .services import (
    run_echo_ranging_simulation
)


class EchoRangingRequest(BaseModel):

    speed_of_sound: float = Field(
        ...,
        gt=0
    )

    echo_time: float = Field(
        ...,
        gt=0
    )

    obstacle_distance: float = Field(
        ...,
        gt=0
    )


async def echo_ranging_controller(
    request: EchoRangingRequest
):

    try:

        result = (
            run_echo_ranging_simulation(
                request.speed_of_sound,
                request.echo_time,
                request.obstacle_distance
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