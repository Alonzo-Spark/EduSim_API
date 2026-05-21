from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from services.rag_service import RagService

router = APIRouter()

class RagSearchRequest(BaseModel):
    subject: str = "physics"
    class_name: str = ""
    chapter: str = ""
    query: str = ""

@router.post("/search")
async def search_rag(req: RagSearchRequest):
    chunks = RagService.search_chunks(req.subject, req.chapter, req.query)
    return {"chunks": chunks}
