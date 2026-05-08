import json
from .agentic_models import SimulationBlueprint
from .llm_client import call_llm


def apply_regeneration_instruction(blueprint: SimulationBlueprint, instruction: str) -> SimulationBlueprint:
    """
    Apply natural language instructions to modify an existing simulation blueprint using LLM.
    """
    
    update_prompt = f"""
    # Task: Update Simulation Blueprint
    
    You are an expert simulation architect. You need to modify an existing simulation blueprint based on user instructions.
    
    ## Current Blueprint
    Title: {blueprint.title}
    Difficulty: {blueprint.difficulty}
    Objects: {blueprint.objects}
    Controls: {blueprint.controls}
    
    ## Instruction
    "{instruction}"
    
    ## Requirements
    1. Update the blueprint JSON to reflect the instruction.
    2. Maintain consistency with the existing objects and physics unless the instruction requires changing them.
    3. Return the full updated blueprint JSON.
    
    ## Output Format
    Return ONLY a JSON object that conforms to the SimulationBlueprint schema.
    """

    try:
        response_text = call_llm(
            update_prompt, 
            temperature=0.2, 
            response_mime_type="application/json"
        )
        updated_data = json.loads(response_text)
        
        # Merge or replace fields
        # Note: In a production system, we might want to be more careful about merging
        return SimulationBlueprint(**updated_data)
        
    except Exception as e:
        print(f"Regeneration failed: {e}. Falling back to rule-based logic.")
        return _apply_fallback_regeneration(blueprint, instruction)


def _apply_fallback_regeneration(blueprint: SimulationBlueprint, instruction: str) -> SimulationBlueprint:
    """Fallback rule-based regeneration logic."""
    instruction_lower = instruction.lower()

    if "beginner" in instruction_lower or "simpl" in instruction_lower:
        blueprint.difficulty = "beginner"
        blueprint.educational_overlays["instruction_mode"] = "step-by-step"
        for control in blueprint.controls:
            if control.get("type") == "slider":
                control["max"] = min(control.get("max", 100), 60)

    if "advanced" in instruction_lower:
        blueprint.difficulty = "advanced"
        blueprint.educational_overlays["instruction_mode"] = "challenge"
        blueprint.controls.append(
            {
                "name": "challenge_mode",
                "label": "Challenge Mode",
                "type": "button",
            }
        )

    return blueprint
