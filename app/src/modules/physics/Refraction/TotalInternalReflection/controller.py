from fastapi import HTTPException
from pydantic import BaseModel, Field

from .services import get_tir_result


class TIRRequest(BaseModel):

    n1: float = Field(..., gt=0)

    n2: float = Field(..., gt=0)

    angle1: float = Field(
        ...,
        ge=0,
        le=90
    )


async def total_internal_reflection_controller(
    request: TIRRequest
):

    try:

        result = get_tir_result(
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