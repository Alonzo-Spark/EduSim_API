from fastapi import HTTPException
from pydantic import BaseModel, Field

from .services import (
    run_optical_fibre_simulation
)


class OpticalFibreRequest(
    BaseModel
):

    incident_angle: float = Field(
        ...,
        gt=0,
        lt=90
    )

    core_refractive_index: float = Field(
        ...,
        gt=1
    )

    cladding_refractive_index: float = Field(
        ...,
        gt=1
    )

    fibre_length: float = Field(
        ...,
        gt=0
    )

    initial_intensity: float = Field(
        ...,
        gt=0
    )

    attenuation_coefficient: float = Field(
        ...,
        gt=0
    )


async def optical_fibre_controller(
    request: OpticalFibreRequest
):

    try:

        result = (
            run_optical_fibre_simulation(
                request.incident_angle,
                request.core_refractive_index,
                request.cladding_refractive_index,
                request.fibre_length,
                request.initial_intensity,
                request.attenuation_coefficient
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