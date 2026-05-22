from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.src.modules.simulation_synthesis.service import (
    retrieve_context,
    build_dsl_prompt,
    generate_dsl,
    validate_dsl,
    sanitize_dsl
)

generate_router = APIRouter()

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=4, description="User prompt for simulation generation")

@generate_router.post("/generate")
async def generate_simulation(request: GenerateRequest):
    """
    POST /api/generate
    
    1. Accept user NLP physics prompt
    2. Retrieve RAG context
    3. Build the DSL prompt
    4. Call the LLM
    5. Sanitize the DSL
    6. Validate the DSL
    7. Return the final JSON response
    """
    try:
        # 1. Retrieve RAG context
        context = retrieve_context(request.prompt)
        
        # 2. Build the DSL prompt
        dsl_prompt = build_dsl_prompt(request.prompt, context)
        
        # 3. Call the LLM
        raw_text = generate_dsl(dsl_prompt)
        
        # 4. Sanitize the DSL
        sanitized_json = sanitize_dsl(raw_text)
        
        # 5. Validate the DSL
        valid_dsl = validate_dsl(sanitized_json)
        
        # 6. Return the final JSON response (dsl, knowledge, metadata)
        return valid_dsl

    except ValueError as e:
        # Validation or sanitization error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected internal error
        raise HTTPException(status_code=500, detail=f"Simulation generation failed: {str(e)}")
