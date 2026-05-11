from typing import Dict, Any
from .schema import SimulationDSL

def validate_simulation(data: dict) -> dict:
    """
    Validate AI-generated simulation JSON against the V1 State Tree schema.
    
    This validator performs two checks:
    1. Structural: Pydantic ensures the JSON matches the schema.
    2. Contextual: Ensures 'bind' paths in interactions are logically formatted.
    """
    try:
        # Pass 1: Structural Validation via Pydantic
        # This automatically checks types, required fields, and nested objects.
        validated_model = SimulationDSL(**data)
        validated_dict = validated_model.dict()

        # Pass 2: Semantic Path Validation
        # We check if the 'bind' strings follow the correct naming convention
        # to prevent the UI from trying to update non-existent properties.
        interaction_errors = []
        valid_roots = ["objects", "forces", "environment"]
        
        for i, interaction in enumerate(validated_dict.get("interactions", [])):
            path = interaction.get("bind", "")
            
            # Ensure the path starts with a valid top-level section
            if not any(path.startswith(root) for root in valid_roots):
                interaction_errors.append(
                    f"Interaction[{i}] has invalid bind path '{path}'. "
                    f"Must start with one of: {valid_roots}"
                )

        if interaction_errors:
            return {
                "success": False,
                "data": None,
                "errors": "; ".join(interaction_errors)
            }

        return {
            "success": True,
            "data": validated_dict,
            "errors": None
        }

    except Exception as e:
        # Returns clear Pydantic error messages (e.g., "objects.0.physics.mass is not a float")
        return {
            "success": False,
            "data": None,
            "errors": str(e)
        }