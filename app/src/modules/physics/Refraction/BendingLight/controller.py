from fastapi import HTTPException
from pydantic import BaseModel, Field

from .services import get_refraction_result


class RefractionRequest(BaseModel):

    n1: float = Field(..., gt=0)

    n2: float = Field(..., gt=0)

    angle1: float = Field(
        ...,
        ge=0,
        le=90
    )


async def bending_light_controller(
    request: RefractionRequest
):

    try:

        result = get_refraction_result(
            request.dict()
        )

        return {
            "success": True,
            "data": result
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )