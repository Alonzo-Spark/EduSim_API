from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from app.src.services.rag_service import RagService
from app.src.modules.legacy_rag.controller import rag_query_controller, RagQueryRequest

rag_router = APIRouter()

class RagSearchRequest(BaseModel):
    subject: str = "physics"
    class_name: str = ""
    chapter: str = ""
    query: str = ""

@rag_router.post("/query")
async def query_rag_endpoint(request: RagQueryRequest):
    return await rag_query_controller(request)

@rag_router.post("/search")
async def search_rag(req: RagSearchRequest):
    chunks = RagService.search_chunks(req.subject, req.chapter, req.query)
    return {"chunks": chunks}
