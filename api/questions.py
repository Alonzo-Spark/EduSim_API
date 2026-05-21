from fastapi import APIRouter
from pydantic import BaseModel
from services.question_service import QuestionService
from models.question_models import QuestionGenerationResponse

router = APIRouter()

class QuestionRequest(BaseModel):
    subject: str = "physics"
    class_name: str = ""
    chapter: str = ""
    topic: str = ""

@router.post("/generate", response_model=QuestionGenerationResponse)
async def generate_questions(req: QuestionRequest):
    return await QuestionService.generate_questions(req.subject, req.class_name, req.chapter, req.topic)
