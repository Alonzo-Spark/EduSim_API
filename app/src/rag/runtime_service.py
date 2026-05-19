from .relationship_mapper import map_runtime_event
from .retriever import retrieve_formulas, retrieve_hints
from .generators.runtime_overlay_generator import generate_runtime_overlay
from .schemas.runtime_payload_schema import RuntimePayloadSchema

async def process_runtime_event(event: str):
    topic = map_runtime_event(event)
    formulas = retrieve_formulas(topic)
    hints = retrieve_hints(topic)
    overlay = await generate_runtime_overlay(topic, event)

    return RuntimePayloadSchema(
        event=event,
        topic=topic,
        overlay_message=overlay,
        formulas=formulas if isinstance(formulas, list) else formulas.get("formulas", []),
        hints=hints if isinstance(hints, list) else hints.get("hints", [])
    )
