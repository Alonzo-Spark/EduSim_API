from typing import Union
from .relationship_mapper import map_runtime_event
from .retriever import retrieve_formulas, retrieve_hints
from .generators.runtime_overlay_generator import generate_runtime_overlay
from .schemas.runtime_payload_schema import RuntimePayloadSchema
from .schemas.runtime_event_schema import RuntimeEventSchema

async def process_runtime_event(payload_or_event: Union[str, RuntimeEventSchema]):
    if isinstance(payload_or_event, str):
        event = payload_or_event
        event_data = event
    else:
        event = payload_or_event.event
        # Build structured data
        event_dict = {
            "event": payload_or_event.event,
            "object": payload_or_event.object,
            "velocity": payload_or_event.velocity,
            "acceleration": payload_or_event.acceleration
        }
        # Filter out None values to keep it clean and minimal
        event_data = {k: v for k, v in event_dict.items() if v is not None}

    topic = map_runtime_event(event)
    formulas = retrieve_formulas(topic)
    hints = retrieve_hints(topic)
    overlay = await generate_runtime_overlay(topic, event_data)

    return RuntimePayloadSchema(
        event=event,
        topic=topic,
        overlay_message=overlay,
        formulas=formulas if isinstance(formulas, list) else formulas.get("formulas", []),
        hints=hints if isinstance(hints, list) else hints.get("hints", [])
    )

