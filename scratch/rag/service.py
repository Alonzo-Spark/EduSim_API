from .schemas.educational_payload import EducationalPayload
from .retriever import (
    retrieve_concept,
    retrieve_formulas,
    retrieve_misconceptions,
    retrieve_experiments,
    retrieve_hints
)
from .topic_classifier import normalize_topic
from .generators.explanation_generator import generate_ai_explanation

async def query_educational_service(topic: str):
    normalized_topic = normalize_topic(topic)
    
    concept = retrieve_concept(normalized_topic)
    formulas = retrieve_formulas(normalized_topic)
    misconceptions = retrieve_misconceptions(normalized_topic)
    experiments = retrieve_experiments(normalized_topic)
    hints = retrieve_hints(normalized_topic)

    ai_explanation = await generate_ai_explanation(
        normalized_topic,
        concept.get("concept_explanation", "")
    )

    return EducationalPayload(
        topic=normalized_topic,
        concept_explanation=concept.get("concept_explanation", ""),
        ai_explanation=ai_explanation,
        formulas=formulas if isinstance(formulas, list) else formulas.get("formulas", []),
        misconceptions=misconceptions if isinstance(misconceptions, list) else misconceptions.get("misconceptions", []),
        experiments=experiments if isinstance(experiments, list) else experiments.get("experiments", []),
        observables=concept.get("observables", []),
        hints=hints if isinstance(hints, list) else hints.get("hints", []),
        assets=concept.get("assets", []),
        relationships=concept.get("relationships", [])
    )
