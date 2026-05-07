from fastapi import HTTPException
from pydantic import BaseModel, Field
from .services import query_rag

class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="The textbook question to ask the AI")

async def rag_query_controller(request: RagQueryRequest):
    try:
        answer = query_rag(query=request.query)
        
        return {
            "success": True,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RAG Error: {str(e)}"
        )
