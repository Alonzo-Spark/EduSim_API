from fastapi import HTTPException
from pydantic import BaseModel, Field
from .service import analyze_tutor_query

class ChatMessage(BaseModel):
    role: str
    content: str

class TutorQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="The physics question or formula to analyze")
    class_name: str | None = None
    subject: str | None = None
    chapter: str | None = None
    topic: str | None = None
    history: list[ChatMessage] | None = None
    session_id: str | None = None

async def analyze_tutor_controller(request: TutorQueryRequest, student_profile: dict | None = None):
    try:
        history_dicts = None
        if request.history:
            history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
        data = await analyze_tutor_query(
            request.query,
            history=history_dicts,
            subject=request.subject,
            chapter=request.chapter,
            topic=request.topic,
            student_profile=student_profile
        )
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tutor Analysis Error: {str(e)}"
        )
