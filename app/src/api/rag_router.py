from fastapi import APIRouter
from app.src.modules.physics.rag.controller import rag_query_controller, RagQueryRequest

rag_router = APIRouter()

@rag_router.post("/query")
async def query_rag_endpoint(request: RagQueryRequest):
    return await rag_query_controller(request)
