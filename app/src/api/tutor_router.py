from fastapi import APIRouter, Query
from typing import Optional
from app.src.modules.tutor.controller import analyze_tutor_controller, TutorQueryRequest
from app.src.modules.tutor import service as tutor_service

tutor_router = APIRouter()


@tutor_router.post("/analyze")
async def analyze_query(request: TutorQueryRequest):
    """
    Analyzes a physics query to detect concepts, formulas, and provide AI/RAG explanations.
    """
    return await analyze_tutor_controller(request)


@tutor_router.get("/search")
async def search_curriculum(q: str = Query(..., min_length=1)):
    """Search the curriculum and return matching subjects/chapters/topics."""
    results = tutor_service.search_curriculum(q)
    return {"query": q, "results": results}


@tutor_router.get("/autocomplete")
async def autocomplete(q: str = Query(..., min_length=1)):
    """Return autocomplete suggestions for curriculum topics/chapters."""
    suggestions = tutor_service.autocomplete_curriculum(q)
    return {"query": q, "results": suggestions, "suggestions": suggestions}


@tutor_router.get("/topic")
async def get_topic(subject: str, class_name: str, chapter: str, topic: Optional[str] = None):
    """Load stored curriculum content for the selected topic/chapter."""
    content = tutor_service.get_topic_content(subject, class_name, chapter, topic)
    return content
