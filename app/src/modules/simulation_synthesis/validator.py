from typing import Dict, Any
from .schema import EduSimResponse

def validate_simulation(data: dict) -> dict:
    """
    Validate AI-generated EduSimResponse JSON with strict runtime constraints.
    
    Checks:
    1. Structural: Pydantic ensures the JSON matches the architecture.
    2. Contextual: Ensures 'bind' paths in interactions are logically formatted.
    3. Physics: Checks for duplicate IDs and valid force targets.
    4. Runtime Optimization: Ensures SI units are used and redundant gravity is avoided.
    """
    try:
        # Pass 1: Structural Validation via Pydantic
        validated_model = EduSimResponse(**data)
        validated_dict = validated_model.dict()
        dsl = validated_dict.get("dsl", {})

        semantic_errors = []
        valid_roots = ["objects", "forces", "environment"]
        
        # Pass 2: Semantic Path Validation
        for i, interaction in enumerate(dsl.get("interactions", [])):
            path = interaction.get("bind", "")
            if not any(path.startswith(root) for root in valid_roots):
                semantic_errors.append(
                    f"Interaction[{i}] has invalid bind path '{path}'. "
                    f"Must start with one of: {valid_roots}"
                )

        # Pass 3: Physics Logic Validation
        object_ids = {obj["id"] for obj in dsl.get("objects", [])}
        all_ids = [obj["id"] for obj in dsl.get("objects", [])] + [force["id"] for force in dsl.get("forces", [])]
        
        from collections import Counter
        duplicates = [item for item, count in Counter(all_ids).items() if count > 1]
        if duplicates:
            semantic_errors.append(f"Duplicate IDs found across objects/forces: {duplicates}")

        # Check if force targets exist and type is valid
        for i, force in enumerate(dsl.get("forces", [])):
            if force["target"] not in object_ids:
                semantic_errors.append(f"Force[{i}] ('{force['id']}') targets unknown object '{force['target']}'")
            if force["type"] == "gravity":
                semantic_errors.append(f"Force[{i}] has type 'gravity'. Gravity must only be defined in 'environment.gravity'.")

        # Pass 4: SI Unit Sanity Check
        for i, obj in enumerate(dsl.get("objects", [])):
            pos = obj.get("position", {})
            if abs(pos.get("x", 0)) > 500 or abs(pos.get("y", 0)) > 500:
                semantic_errors.append(f"Object[{i}] ('{obj['id']}') position seems to use pixels. Please use SI meters (typically < 100).")
            
            shape = obj.get("shape", {})
            if shape.get("type") == "circle" and (shape.get("width") or shape.get("height")):
                semantic_errors.append(f"Object[{i}] is a circle but contains width/height. These must be omitted.")

        if semantic_errors:
            return {
                "success": False,
                "data": None,
                "errors": "; ".join(semantic_errors)
            }

        return {
            "success": True,
            "data": validated_dict,
            "errors": None
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "errors": str(e)
        }