from fastapi import APIRouter
from app.src.modules.tutor.controller import analyze_tutor_controller, TutorQueryRequest

tutor_router = APIRouter()

@tutor_router.post("/analyze")
async def analyze_query(request: TutorQueryRequest):
    """
    Analyzes a physics query to detect concepts, formulas, and provide AI/RAG explanations.
    """
    return await analyze_tutor_controller(request)
