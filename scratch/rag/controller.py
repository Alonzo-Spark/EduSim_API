from fastapi import APIRouter

from .service import query_educational_service
from .schemas.topic_request import TopicRequest
from .schemas.educational_payload import EducationalPayload
from .generators.tutor_response_generator import generate_tutor_response

from .runtime_service import process_runtime_event
from .schemas.runtime_event_schema import RuntimeEventSchema

router = APIRouter()

@router.post(
    "/educational/topic",
    response_model=EducationalPayload
)
async def educational_topic(payload: TopicRequest):
    response = await query_educational_service(payload.topic)
    return response

@router.post("/educational/tutor")
async def tutor_question(payload: dict):
    response = await generate_tutor_response(
        payload["topic"],
        payload["question"]
    )
    return {
        "response": response
    }

@router.post("/educational/runtime")
async def runtime_event(payload: RuntimeEventSchema):
    response = await process_runtime_event(payload)
    return response
