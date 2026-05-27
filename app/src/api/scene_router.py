from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.src.modules.scene_parser.service import parse_scene

scene_router = APIRouter()


class SceneParseRequest(BaseModel):
    user_input: str = Field(
        ...,
        min_length=3,
        description="The physics example/question to parse into a simulation scene"
    )


@scene_router.post("/scene/parse")
async def parse_scene_endpoint(request: SceneParseRequest):
    """
    Parses a natural-language physics example into a structured simulation scene.
    Returns recommended_assets as valid assetsRegistry IDs for the frontend
    to highlight in the floating Asset Library panel.
    """
    try:
        scene = await parse_scene(request.user_input)
        return {
            "success": True,
            "data": scene
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scene Parse Error: {str(e)}"
        )
