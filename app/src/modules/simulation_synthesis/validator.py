from .schema import SimulationDSL
from .interaction_templates import ALLOWED_ENTITY_TYPES, ALLOWED_VISUALIZATION_TYPES


def _check_entities(entities: list) -> list[str]:
    """Validate each entity has required fields and uses a standardized type."""
    errors = []
    seen_ids = set()
    for i, entity in enumerate(entities):
        if "id" not in entity:
            errors.append(f"Entity[{i}] is missing required field 'id'.")
        elif entity["id"] in seen_ids:
            errors.append(f"Entity[{i}] has duplicate id '{entity['id']}'.")
        else:
            seen_ids.add(entity["id"])

        if "type" not in entity:
            errors.append(f"Entity[{i}] is missing required field 'type'.")
        elif entity["type"] not in ALLOWED_ENTITY_TYPES:
            errors.append(
                f"Entity[{i}] has non-standard type '{entity['type']}'. "
                f"Allowed: {sorted(ALLOWED_ENTITY_TYPES)}"
            )
    return errors


def _check_interactions(interactions: list, entity_ids: set) -> list[str]:
    """Validate each interaction has type, target, and parameters."""
    errors = []
    for i, interaction in enumerate(interactions):
        if "type" not in interaction:
            errors.append(f"Interaction[{i}] is missing required field 'type'.")
        if "target" not in interaction:
            errors.append(f"Interaction[{i}] is missing required field 'target'.")
        elif interaction["target"] not in entity_ids:
            errors.append(
                f"Interaction[{i}] targets unknown entity id '{interaction['target']}'. "
                f"Known ids: {sorted(entity_ids)}"
            )
        if "parameters" not in interaction:
            errors.append(f"Interaction[{i}] is missing required field 'parameters'.")
        elif not isinstance(interaction["parameters"], dict):
            errors.append(f"Interaction[{i}] 'parameters' must be a dict.")
    return errors


def _check_visualizations(visualizations: list) -> list[str]:
    """Validate visualizations use standardized types."""
    errors = []
    for i, vis in enumerate(visualizations):
        if "type" not in vis:
            errors.append(f"Visualization[{i}] is missing required field 'type'.")
        elif vis["type"] not in ALLOWED_VISUALIZATION_TYPES:
            errors.append(
                f"Visualization[{i}] has non-standard type '{vis['type']}'. "
                f"Allowed: {sorted(ALLOWED_VISUALIZATION_TYPES)}"
            )
    return errors


def validate_simulation(data: dict) -> dict:
    """
    Validate AI-generated simulation JSON against the SimulationDSL schema.

    Runs two validation passes:
    1. Pydantic structural validation (schema fields, types)
    2. Semantic validation (entity vocab, interaction completeness, visualization vocab)

    Returns:
        {
            "success": bool,
            "data": dict | None,
            "errors": str | None,
            "warnings": list[str]
        }
    """
    warnings = []

    # --- Pass 1: Pydantic schema validation ---
    try:
        validated = SimulationDSL(**data)
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "errors": str(e),
            "warnings": warnings,
        }

    validated_data = validated.dict()

    # --- Pass 2: Semantic validation ---
    entity_ids = {e["id"] for e in validated_data.get("entities", [])}

    entity_errors = _check_entities(validated_data.get("entities", []))
    interaction_errors = _check_interactions(validated_data.get("interactions", []), entity_ids)
    viz_errors = _check_visualizations(validated_data.get("visualizations", []))

    all_errors = entity_errors + interaction_errors + viz_errors

    if all_errors:
        return {
            "success": False,
            "data": None,
            "errors": "; ".join(all_errors),
            "warnings": warnings,
        }

    return {
        "success": True,
        "data": validated_data,
        "errors": None,
        "warnings": warnings,
    }