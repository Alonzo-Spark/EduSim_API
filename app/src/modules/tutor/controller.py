from fastapi import HTTPException
from pydantic import BaseModel, Field
from .service import analyze_tutor_query

class TutorQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="The physics question or formula to analyze")

async def analyze_tutor_controller(request: TutorQueryRequest):
    try:
        data = analyze_tutor_query(request.query)
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tutor Analysis Error: {str(e)}"
        )
